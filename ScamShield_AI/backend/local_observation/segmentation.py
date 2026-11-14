"""Clause boundaries with local scope; never insert punctuation in evidence."""
from dataclasses import dataclass, field
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata
from .text import normalize, quote_ranges


@dataclass
class Segment:
    sentence_id: int
    context_start: int
    context_end: int
    start: int
    end: int
    quoted: bool
    reason: str
    status: str
    limitations: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def anchors():
    config=json.loads(Path(__file__).with_name('rules.json').read_text(encoding='utf-8'))
    types=set(config['segmentation']['restart_action_types'])
    return [(r,re.compile(r['pattern']),re.compile(r['context']) if r['context'] else None)
            for r in config['rules'] if r['type'] in types]


def candidates(text):
    found={}
    for rule,pattern,context in anchors():
        for m in pattern.finditer(text):
            a,b=m.span('verb')
            if context and not context.search(text[a:a+100]):continue
            if rule['type']=='transfer_funds' and m.group('verb')=='dong' and re.search(r'\d\s*$',text[:a]):continue
            if rule['type']=='login' and re.search(r'\bma\s*$',text[:a]):continue
            found.setdefault(a,(a,b))
    return sorted(found.values())


def segments(text):
    quotes=quote_ranges(text)
    urls=[(m.start(),m.start()+len(m.group().rstrip('.,!?;'))) for m in re.finditer(r'https?://[^\s<>"“”‘’]+',text)]
    inside=lambda p,ranges:any(a<=p<b for a,b in ranges)
    physical=[];start=0
    for i,c in enumerate(text):
        number=c in '.,' and i>0 and i+1<len(text) and text[i-1].isdigit() and text[i+1].isdigit()
        if c in '.!?;\n' and not number and not inside(i,urls) and not inside(i,quotes):
            physical.append((start,i+1));start=i+1
    if start<len(text):physical.append((start,len(text)))
    result=[];scope_id=0
    for a,b in physical:
        n=normalize(text[a:b]);s=n.text
        heads=[(x,y) for x,y in candidates(s) if not inside(a+n.starts[x],quotes) and not inside(a+n.starts[x],urls)]
        cuts={a:('sentence_start','observed')};restarts=set()
        transactions=list(re.finditer(r'\b(?:don|giao dich|hop dong)\s+([a-z0-9]+)\s+(?=(?:da|chua|dang|khong)\b)',s))
        for prev,current in zip(transactions,transactions[1:]):
            cut=a+n.starts[current.start()]
            if prev.group(1)!=current.group(1) and not inside(cut,quotes) and not inside(cut,urls):
                cuts[cut]=('transaction_change','inferred');restarts.add(cut)
        for m in re.finditer(r'\b(?:nhung|neu|thi|de|truoc khi|sau khi|roi|xong)\b|,',s):
            x,y=n.original_range(*m.span());x+=a;y+=a
            if inside(x,quotes) or inside(x,urls):continue
            if m.group()==',':
                if x>0 and y<len(text) and text[x-1].isdigit() and text[y].isdigit():continue
                cuts[y]=('punctuation','observed');continue
            original=unicodedata.normalize('NFC',text[x:y]).casefold()
            if m.group()=='de' and original not in ('để','de'):continue
            predicate=re.search(r'\b(?:giao|nhan|rut|chuyen|gui|doc|cai|cap|mo|nhap|kiem tra|xac minh|hoan|thanh toan|dung|khong|chua)\b',s[m.end():m.end()+100])
            if x>a and predicate:cuts[x]=('connector','inferred')
        for i,(x,y) in enumerate(heads):
            prefix=s[:x]
            marker=re.search(r'\b(?:(?:ban|anh|chi|em|toi|ben minh)\s+(?:(?:hay|can|phai|dung|khong can|chua)\s+)?|(?:hay|vui long|dung|khong can|chua)\s+)$',prefix)
            begin=marker.start() if marker else x
            previous=heads[i-1] if i else None
            between=s[previous[1]:begin] if previous else prefix[:begin]
            coordination=re.search(r'\b(?:va|hoac|de|neu|thi|nhung|truoc khi|sau khi|roi|xong)\b',between)
            relative=re.search(r'\b(?:nguoi|ai|don vi)\s+(?:ma\s+)?(?:vua|da|dang)\s*$',prefix)
            complete=re.search(r'\b(?:nhe|da xong|dang cho|vay nhe|duoc roi)\s*$',between)
            candidate_start=a+n.starts[begin]
            quoted_cut=None
            for qa,qb in quotes:
                if qa<a or qb>candidate_start:continue
                gap=normalize(text[qb:candidate_start]).text.strip()
                if gap in ('','nhung','tuy nhien') and re.search(r'canh bao|canh giac',normalize(text[a:qa]).text):
                    quoted_cut=qb
                    while quoted_cut<candidate_start and text[quoted_cut].isspace():quoted_cut+=1
            quoted_warning_end=quoted_cut is not None
            if not relative and ((previous and between.strip(' ,') and not coordination) or (not previous and complete) or quoted_warning_end):
                cut=quoted_cut if quoted_cut is not None else a+n.starts[begin]
                if cut>a:cuts[cut]=('action_restart','inferred');restarts.add(cut)
        scopes=[a]+sorted(restarts)+[b]
        positions=sorted(set(cuts)|{b})
        for left,right in zip(positions,positions[1:]):
            origin=left
            while left<right and text[left].isspace():left+=1
            while right>left and text[right-1].isspace():right-=1
            if left>=right:continue
            if all(unicodedata.category(c)[0] in ('P','Z','C') for c in text[left:right]) and result:
                result[-1].end=right;continue
            index=max(i for i in range(len(scopes)-1) if scopes[i]<=left)
            reason,status=cuts.get(origin,('sentence_start','observed'));limits=[]
            chunk=normalize(text[left:right]).text
            if re.search(r'\b(?:dung|khong(?: can| nen| duoc)?)\b.*\b(?:va|hoac)\b',chunk) and len(candidates(chunk))>1:
                status='uncertain';limits.append('Chưa chắc phạm vi phủ định qua và/hoặc; không ép tách.')
            if reason=='action_restart':limits.append('Ranh giới suy ra từ cụm hành động, không phải dấu câu có sẵn.')
            result.append(Segment(scope_id+index,scopes[index],scopes[index+1],left,right,inside(left,quotes),reason,status,limits))
        scope_id+=len(scopes)-1
    return result
