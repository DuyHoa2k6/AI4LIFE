import json
import os
from pathlib import Path
import time
from unittest.mock import AsyncMock,patch
from fastapi.testclient import TestClient
from backend.main import app

ROOT=Path(__file__).resolve().parent


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    records=[]
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}),patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('No network')) as network,TestClient(app) as client:
        for row in json.loads((ROOT/'fixtures/semantic_graph/inputs.json').read_text(encoding='utf-8')):
            start=time.perf_counter();r=client.post('/api/analyze',json=row['input'])
            raw=client.post('/api/analyze-local',json={'messages':[{'id':m['id'],'speaker_id':m['speaker'],'scope_id':'analysis','text':m['text']} for m in row['input']['messages']]})
            records.append({**row,'http':r.status_code,'elapsed_ms':round((time.perf_counter()-start)*1000,3),'response':r.json(),'local':raw.json()})
        calls=network.call_count
    (args.output/'predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    labels={r['id']:r for r in json.loads((ROOT/'fixtures/semantic_graph/expected.json').read_text(encoding='utf-8'))}
    failed=[];lines=['# 42 ca đối chứng theo cấu trúc hành vi','','Ca development, not_high cho phép clear/need_context/suspicious, không mặc định mọi đối chứng clear.','',
        '| Ca | Kỳ vọng | Thực tế |','|---|---|---|']
    for row in records:
        pred=row['response'].get('risk_status');want=labels[row['id']]['risk']
        ok=row['http']==200 and (pred==want if want!='not_high' else pred in ('clear','need_context','suspicious'))
        if not ok:failed.append({'id':row['id'],'expected':want,'actual':pred})
        lines.append(f"| {row['id']} | {want} | {pred} |")
    summary={'cases':len(records),'matched':len(records)-len(failed),'failed':failed,'external_requests':calls,'scope':'authored development contrast suite; not independent accuracy'}
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if failed or calls:raise SystemExit(1)


if __name__=='__main__':main()
