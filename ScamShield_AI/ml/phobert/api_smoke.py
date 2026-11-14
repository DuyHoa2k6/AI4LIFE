"""Real API smoke in a child process; does not alter the user's configuration file."""
import json
import os
import statistics
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.environ.update({'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'phobert',
    'SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL':'1','SCAMSHIELD_PHOBERT_CHECKPOINT':str(ROOT/'artifacts/phobert/smoke_heads'),
    'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'})

def main():
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.local_reasoning.phobert_adapter import get_runtime
    out=ROOT/'reports/phobert_20261114';out.mkdir(parents=True,exist_ok=True)
    inputs=json.loads((ROOT/'reports/eight_scenarios_20261113/inputs.json').read_text(encoding='utf-8'))
    predictions=[];checks=[]
    cold=time.perf_counter()
    with TestClient(app) as client:
        startup=(time.perf_counter()-cold)*1000;model=id(get_runtime())
        invalid=client.post('/api/analyze',json={'text':'x','messages':[{'id':'m1','speaker':'sender','text':'x'}]})
        checks.append({'name':'invalid input rejected before inference','passed':invalid.status_code==422})
        for row in inputs:
            started=time.perf_counter();response=client.post('/api/analyze',json={'text':row['text']});elapsed=(time.perf_counter()-started)*1000
            predictions.append({'id':row['id'],'text':row['text'],'http_status':response.status_code,'api_ms':elapsed,'response':response.json()})
            (out/'api_eight_predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding='utf-8')
        checks.append({'name':'model loaded once','passed':id(get_runtime())==model})
        os.environ['SCAMSHIELD_PHOBERT_CHECKPOINT']=str(ROOT/'artifacts/phobert/MISSING')
        missing=client.post('/api/analyze',json={'text':'Bạn gửi mã đăng nhập cho tôi.'})
        checks.append({'name':'missing checkpoint is 503, no rule/mock fallback','passed':missing.status_code==503 and missing.json().get('code')=='PHOBERT_ANALYSIS_UNAVAILABLE'})
        os.environ['SCAMSHIELD_PHOBERT_CHECKPOINT']=str(ROOT/'artifacts/phobert/smoke_heads')
        os.environ['SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL']='0'
        unapproved=client.post('/api/analyze',json={'text':'Bạn gửi mã đăng nhập cho tôi.'})
        checks.append({'name':'unapproved research model rejected','passed':unapproved.status_code==503})
    times=sorted(x['api_ms'] for x in predictions)
    report={'scope':'Public regression inputs, experimental checkpoint; not independent quality evaluation. ASGI API timings, no browser.',
      'n':len(predictions),'checks':checks,'startup_cold_ms':startup,'p50_api_ms':statistics.median(times),'p95_nearest_rank_api_ms':times[-1],
      'status_counts':{str(code):sum(x['http_status']==code for x in predictions) for code in sorted({x['http_status'] for x in predictions})},
      'risks':{str(risk):sum(x['response'].get('risk_status')==risk for x in predictions) for risk in sorted({x['response'].get('risk_status') for x in predictions},key=str)},
      'checkpoint':str(ROOT/'artifacts/phobert/smoke_heads')}
    (out/'api_smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    if not all(c['passed'] for c in checks):raise SystemExit(1)

if __name__=='__main__':main()
