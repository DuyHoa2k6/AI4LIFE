import hashlib
import json
import random
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from .schema import Sample, RELATIONS, RISKS

def load(path, supervised=False, allow_draft=False):
    rows=[Sample.model_validate_json(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    if len({x.id for x in rows})!=len(rows):raise ValueError('duplicate sample ID')
    if supervised and not allow_draft and any(x.review_status=='draft' or x.source=='public_regression' for x in rows):
        raise ValueError('Unreviewed/public regression data is permitted only in explicit smoke mode')
    return rows

def audit(rows):
    return {'samples':len(rows),'families':dict(Counter(r.family_id for r in rows)),
      'risk':dict(Counter(r.risk_reference for r in rows)),
      'relations':dict(Counter(r.label for x in rows for r in x.relations)),
      'review':dict(Counter(x.review_status for x in rows)),
      'span_labels':dict(Counter(s.label for x in rows for s in x.spans)),
      'span_coverage':{label:dict(Counter(r.span_label_status[label] for r in rows)) for label in rows[0].span_label_status} if rows else {},
      'tasks':{t:dict(Counter(r.task_status[t] for r in rows)) for t in ['spans','attributes','roles','relations','risk']}}

def grouped_split(rows, seed=17):
    """Connected components over ALL leakage keys and near duplicates, before splitting."""
    parent=list(range(len(rows)))
    def find(i):
        while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(i,j):parent[find(i)]=find(j)
    texts=[' '.join(m.text.casefold() for m in x.messages) for x in rows]
    texts=[re.sub(r'\d+','<number>',t) for t in texts]
    for i,a in enumerate(rows):
        for j in range(i):
            b=rows[j]
            if any(getattr(a,k)==getattr(b,k) for k in ['family_id','conversation_group','template_group','source_group']) or SequenceMatcher(None,texts[i],texts[j]).ratio()>=.88:union(i,j)
    groups={}
    for i in range(len(rows)):groups.setdefault(find(i),[]).append(rows[i])
    keys=list(groups);random.Random(seed).shuffle(keys)
    result={'train':[],'validation':[],'test_locked':[]}
    for i,key in enumerate(keys):
        split='test_locked' if i%5==0 else 'validation' if i%5==1 else 'train'
        result[split].extend(groups[key])
    return result

def write_manifest(path, splits):
    output=Path(path);output.mkdir(parents=True,exist_ok=True);manifest={}
    for split,rows in splits.items():
        data=''.join(r.model_dump_json()+'\n' for r in rows).encode('utf-8')
        (output/(split+'.jsonl')).write_bytes(data)
        manifest[split]={'sha256':hashlib.sha256(data).hexdigest(),'ids':[r.id for r in rows],'stats':audit(rows)}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest
