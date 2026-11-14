"""Actual API snapshots for semantic regression and matched latency comparison."""
import argparse,json,os,time,statistics,math,hashlib
from pathlib import Path
from unittest.mock import AsyncMock,patch
from fastapi.testclient import TestClient
from backend.main import app

ROOT=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--inputs',type=Path,default=ROOT/'fixtures/grounding_v2_inputs.json');args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False);records=[];timings=[]
    args.inputs=args.inputs.resolve()
    rows=json.loads(args.inputs.read_text(encoding='utf-8'))
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_SEMANTIC_GRAPH_ENABLED':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}),patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('External HTTP forbidden')) as network,TestClient(app) as client:
        for row in rows:
            runs=[]
            for _ in range(3):
                t=time.perf_counter();r=client.post('/api/analyze',json={'text':row['text']});ms=round((time.perf_counter()-t)*1000,3)
                timings.append(ms);runs.append({'http':r.status_code,'elapsed_ms':ms,'response':r.json()})
            raw=client.post('/api/analyze-local',json={'messages':[{'id':'m1','scope_id':'analysis','text':row['text']}]})
            records.append({**row,'runs':runs,'local_http':raw.status_code,'local':raw.json()})
        calls=network.call_count
    (args.output/'predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    paths=list((ROOT/'backend/local_reasoning').glob('*.py'))+list((ROOT/'backend/local_observation').glob('*.py'))+[args.inputs]
    summary={'cases':len(rows),'requests':len(timings),'http_errors':sum(r['http']!=200 for x in records for r in x['runs']),
        'external_requests':calls,'p50_ms':statistics.median(timings),'p95_ms':sorted(timings)[math.ceil(.95*len(timings))-1],
        'configuration':'local_rules/legacy/context=1/graph=1/url_network=0; sequential ASGI TestClient, 3 calls/case',
        'hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='hashes'},ensure_ascii=False))


if __name__=='__main__':main()
