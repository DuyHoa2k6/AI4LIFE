import hashlib,json,unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from .schema import Case

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def jsonl(path,rows):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
def load(path):
    rows=[Case.model_validate_json(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]
    if len({r.case_id for r in rows})!=len(rows):raise ValueError('duplicate case ID')
    return rows
def validate_splits(rows):
    assigned={};duplicates=[]
    for row in rows:
        for kind in ['family_id','template_id','source_group']:
            key=(kind,getattr(row,kind));old=assigned.setdefault(key,row.split)
            if old!=row.split:raise ValueError('family/template/source split leakage')
    def normalize(row):return ' '.join(unicodedata.normalize('NFC',m.text).casefold() for m in row.input.messages)
    for i,row in enumerate(rows):
        for other in rows[:i]:
            if SequenceMatcher(None,normalize(row),normalize(other)).ratio()>=.90:
                duplicates.append([row.case_id,other.case_id])
                if row.split!=other.split:raise ValueError('near duplicate across splits')
    return duplicates
