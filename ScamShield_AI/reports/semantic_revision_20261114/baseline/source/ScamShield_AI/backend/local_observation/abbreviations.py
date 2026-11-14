"""Context-gated lexical expansions with original offsets, never risk labels."""
from bisect import bisect_left, bisect_right
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import unicodedata

LEXICON=Path(__file__).resolve().parents[3]/'data/abbreviations_vi.json'


@lru_cache(maxsize=1)
def lexicon():
    raw=LEXICON.read_bytes();data=json.loads(raw)
    if data['review_status']!='controlled_project_rules' or len(data['entries'])>200:
        raise ValueError('Invalid abbreviation lexicon')
    by_alias={};ids=set()
    for entry in data['entries']:
        if entry['id'] in ids:raise ValueError('Duplicate abbreviation rule ID')
        ids.add(entry['id'])
        if not isinstance(entry['canonical'],str) or not 0<len(entry['canonical'])<=120:
            raise ValueError('Invalid canonical abbreviation text')
        for group in ('context_any','left_any','right_any','exclude_any'):
            values=entry.get(group,[])
            if not isinstance(values,list) or len(values)>30 or any(not isinstance(v,str) or not 0<len(v)<=100 for v in values):
                raise ValueError('Invalid abbreviation context conditions')
        for alias in entry['aliases']:
            if not isinstance(alias,str) or not re.fullmatch(r'\w{1,30}',alias):raise ValueError('Invalid abbreviation alias')
            key=unicodedata.normalize('NFC',alias).casefold()
            by_alias.setdefault(key,[]).append(entry)
    pattern=re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(k) for k in sorted(by_alias,key=len,reverse=True))+r')(?!\w)',re.I)
    return data['version'],hashlib.sha256(raw).hexdigest(),by_alias,pattern


def resolve(text):
    from .text import _fold
    version,digest,index,pattern=lexicon()
    base=_fold(text)
    protected=[m.span() for m in re.finditer(r'https?://[^\s<>"“”‘’]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|`[^`]*`',text)]
    context_chars=list(base.text)
    for pa,pb in protected:
        x=bisect_right(base.ends,pa);y=bisect_left(base.starts,pb)
        context_chars[x:y]=[' ']*(y-x)
    context_text=''.join(context_chars)
    output=[]
    for match in pattern.finditer(text):
        a,b=match.span()
        if any(x<=a<y for x,y in protected):continue
        key=unicodedata.normalize('NFC',match.group()).casefold()
        entries=index.get(key,[])
        left_at=bisect_right(base.ends,a);right_at=bisect_left(base.starts,b)
        raw_left=base.text[max(0,left_at-50):left_at]
        if key=='k' and re.search(r'\d[\d.,]*\s*$',raw_left):continue
        if re.search(r'\b(?:ma|id|ky hieu|so hieu|ten tep|don|muc|lo|khu|nhom)\s*$',raw_left):continue
        left=context_text[max(0,left_at-60):left_at];right=context_text[right_at:right_at+60]
        # A different physical sentence is not supporting context for this alias.
        boundary=r'(?<!\d)\.|\.(?!\d)|[!?;\n]'
        left=re.split(boundary,left)[-1];right=re.split(boundary,right)[0]
        window=left+' '+key+' '+right

        def has(term,where):
            if term=='$amount':return bool(re.search(r'\b\d[\d.,]*\s*(?:k|tr|nghin|trieu|dong)\b',where))
            return bool(re.search(r'(?<!\w)'+re.escape(_fold(term).text)+r'(?!\w)',where))

        def side(term,where,left_side):
            t=re.escape(_fold(term).text)
            return bool(re.search((r'(?<!\w)'+t+r'\s*$') if left_side else (r'^\s*'+t+r'(?!\w)'),where))

        eligible=[]
        for entry in entries:
            if entry['context_any'] and not any(has(t,window) for t in entry['context_any']):continue
            if entry.get('left_any') and not any(side(t,left,True) for t in entry['left_any']):continue
            if entry.get('right_any') and not any(side(t,right,False) for t in entry['right_any']):continue
            if any(has(t,window) for t in entry['exclude_any']):continue
            eligible.append(entry)
        meanings=list(dict.fromkeys(e['canonical'] for e in eligible))
        possibilities=list(dict.fromkeys(e['canonical'] for e in entries))
        resolved=len(meanings)==1
        output.append({'start':a,'end':b,'quote':text[a:b],
                       'status':'resolved' if resolved else 'ambiguous' if len(meanings)>1 or len(possibilities)>1 else 'unresolved',
                       'expansion':meanings[0] if resolved else None,
                       'alternatives':[] if resolved else (meanings or possibilities),
                       'rule_ids':[e['id'] for e in eligible] if resolved else [e['id'] for e in entries],
                       'basis':'context_or_lexicon' if resolved else 'insufficient_or_conflicting_context'})
    return version,digest,output


def expand_normalized(text,base):
    from .text import Normalized,_fold
    _,_,resolutions=resolve(text)
    resolved=[r for r in resolutions if r['status']=='resolved']
    if not resolved:return base
    chars=[];starts=[];ends=[];cursor=0
    for item in resolved:
        left=bisect_right(base.ends,item['start']);right=bisect_left(base.starts,item['end'])
        chars.append(base.text[cursor:left]);starts.extend(base.starts[cursor:left]);ends.extend(base.ends[cursor:left])
        replacement=_fold(item['expansion']).text
        chars.append(replacement);starts.extend([item['start']]*len(replacement));ends.extend([item['end']]*len(replacement))
        cursor=right
    chars.append(base.text[cursor:]);starts.extend(base.starts[cursor:]);ends.extend(base.ends[cursor:])
    return Normalized(''.join(chars),starts,ends)
