"""Score stored predictions only after all inputs have passed the actual API."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app

ROOT=Path(__file__).resolve().parent
DATA=ROOT.parent/'data/v2/semantic_variants'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    rows=[json.loads(line) for line in (DATA/'inputs.jsonl').read_text(encoding='utf-8').splitlines()]
    records=[]
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}), \
        patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('Network forbidden')) as network, TestClient(app) as client:
        for row in rows:
            started=time.perf_counter();r=client.post('/api/analyze',json=row['input']);elapsed=(time.perf_counter()-started)*1000
            records.append({**row,'http_status':r.status_code,'elapsed_ms':round(elapsed,3),'response':r.json()})
        requests=network.call_count
    (args.output/'predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    expected={r['id']:r for r in map(json.loads,(DATA/'expected.jsonl').read_text(encoding='utf-8').splitlines())}
    failed=[];counts={};valid=total=0
    lines=['# Kiểm thử biến thể ngữ nghĩa','',
        '24 ca tổng hợp dùng để phát triển; không phải độ chính xác độc lập. Dự đoán được lưu trước khi đọc expected.','',
        '| Ca | Nội dung | Kỳ vọng | Thực tế | ms |','|---|---|---|---|---:|']
    for row in records:
        d=row['response'];truth=expected[row['id']]['risk_status'];pred=d.get('risk_status','error')
        counts.setdefault(truth,{});counts[truth][pred]=counts[truth].get(pred,0)+1
        if row['http_status']!=200 or truth!=pred:failed.append(row['id'])
        for finding in d.get('findings',[]):
            for e in finding['evidence']:
                total+=1;valid+=int(row['input']['text'][e['start']:e['end']]==e['quote'])
        lines.append(f"| {row['id']} | {row['input']['text']} | {truth} | {pred} | {row['elapsed_ms']} |")
    timing=sorted(r['elapsed_ms'] for r in records)
    files=[DATA/'inputs.jsonl',DATA/'expected.jsonl',ROOT.parent/'data/v2/semantic_phrases.json',
        ROOT/'backend/local_reasoning/semantic_phrases.py',ROOT/'backend/local_reasoning/interaction.py',ROOT/'backend/local_reasoning/situation.py']
    summary={'cases':len(records),'matched':len(records)-len(failed),'failed':failed,'confusion_matrix':counts,
        'exact_quote':{'valid':valid,'total':total},'external_requests':requests,'p50_ms':statistics.median(timing),
        'p95_ms':timing[max(0,__import__('math').ceil(.95*len(timing))-1)],
        'scope':'Development cases, one request per case, sequential ASGI TestClient; no browser/network latency or independent accuracy.',
        'hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='hashes'},ensure_ascii=False))
    if failed or requests:raise SystemExit(1)


if __name__=='__main__':main()
