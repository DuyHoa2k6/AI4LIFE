"""Check the effective local configuration through the main client API."""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import AsyncMock,patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.settings import get_setting

ROOT=Path(__file__).resolve().parent


def run(output):
    if get_setting('SCAMSHIELD_MODE')!='local_rules':raise SystemExit('Effective mode is not local_rules; no requests sent.')
    output.mkdir(parents=True,exist_ok=False)
    samples=json.loads((ROOT/'fixtures/local_switch/inputs.json').read_text(encoding='utf-8'));records=[]
    with patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as live, \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('Network forbidden')) as network,TestClient(app) as client:
        for row in samples:
            response=client.post('/api/analyze',json=row['input'])
            records.append({**row,'http_status':response.status_code,'response':response.json()})
        (output/'predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        counts={'provider_calls':live.call_count,'network_calls':network.call_count}
    refs={r['id']:r for r in json.loads((ROOT/'fixtures/local_switch/expected.json').read_text(encoding='utf-8'))['cases']}
    failed=[]
    lines=['# Main API local-rule test cases','','Known development cases; not independent accuracy.','',
           '| Case | Input | Risk | Urgency |','|---|---|---|---|']
    for row in records:
        d=row['response'];expected=refs[row['id']]
        if row['http_status']!=200 or (d.get('risk_status'),d.get('safety_urgency'))!=(expected['risk'],expected['urgency']):failed.append(row['id'])
        lines.append(f"| {row['id']} | {row['input']['text']} | {d.get('risk_status')} | {d.get('safety_urgency')} |")
    paths=[ROOT/p for p in ('backend/main.py','backend/schemas.py','backend/providers.py','backend/local_reasoning/adapter.py',
           'extension/result_view.js','fixtures/local_switch/inputs.json','fixtures/local_switch/expected.json')]
    summary={'mode':get_setting('SCAMSHIELD_MODE'),'cases':len(records),'matched':len(records)-len(failed),'failed':failed,**counts,
             'scope':'Main API with actual local backend; known development targets, not model-quality or independent accuracy.',
             'hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='hashes'}))
    if failed or any(counts.values()):raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/local_switch_20261112/api');run(p.parse_args().output)
