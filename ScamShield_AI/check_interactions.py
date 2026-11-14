"""Known development examples: original vs context extraction; no external models."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app

ROOT=Path(__file__).resolve().parent


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    fixture=ROOT/'fixtures/interaction_20261113'
    samples=json.loads((fixture/'inputs.json').read_text(encoding='utf-8'))
    rows=[]
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}),TestClient(app) as client:
        for sample in samples:
            row={**sample}
            for label,enabled in [('before','0'),('after','1')]:
                os.environ['SCAMSHIELD_CONTEXT_ENABLED']=enabled
                start=time.perf_counter();r=client.post('/api/analyze',json={'text':sample['text']})
                elapsed=(time.perf_counter()-start)*1000
                raw=client.post('/api/analyze-local',json={'messages':[{'id':'m1','text':sample['text'],'scope_id':'analysis'}]})
                row[label]={'http_status':r.status_code,'testclient_ms':elapsed,'response':r.json(),'backend':raw.json()}
            rows.append(row)
    (output/'predictions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    targets={c['id']:c['risk'] for c in json.loads((fixture/'expected.json').read_text(encoding='utf-8'))['cases']}
    lines=['# Novel development cases — real local API; no network URL or model','',
        'Targets authored for development; not independent quality. X cases deliberately probe broader unsupported reasoning.','',
        '| ID | Input | Expected | Before | After |','|---|---|---|---|---|']
    mismatches=[]
    for row in rows:
        old=row['before']['response'].get('risk_status');new=row['after']['response'].get('risk_status')
        if new!=targets[row['id']]:mismatches.append(row['id'])
        lines.append(f"| {row['id']} | {row['text']} | {targets[row['id']]} | {old} | {new} |")
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    summary={'cases':len(rows),'mismatches':mismatches,'new_core_matched':sum(r['id'].startswith('N') and r['after']['response'].get('risk_status')==targets[r['id']] for r in rows),
             'all_http_200':all(r[m]['http_status']==200 for r in rows for m in ('before','after')),
             'scope':'Known authored development examples, not independent accuracy; single TestClient timing is not a latency benchmark.'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    files=list((ROOT/'backend/local_reasoning').glob('*.py'))+[fixture/'inputs.json',fixture/'expected.json']
    (output/'hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
