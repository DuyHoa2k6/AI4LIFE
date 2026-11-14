"""Paired real localhost HTTP benchmark; known dev cases, no model/network URL calls."""
import argparse
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import socket
import threading
import time
from unittest.mock import patch,AsyncMock
import httpx
import uvicorn
from backend.main import app
from backend.local_reasoning import adapter,legacy_engine

ROOT=Path(__file__).resolve().parent
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def stats(values):
    xs=sorted(values)
    return {'n':len(xs),'p50_ms':xs[math.ceil(len(xs)*.5)-1],'p95_ms':xs[math.ceil(len(xs)*.95)-1],
            'min_ms':xs[0],'max_ms':xs[-1]}


def run(output,rounds):
    if not 5<=rounds<=100:raise ValueError('Use 5..100 rounds')
    output.mkdir(parents=True,exist_ok=False)
    samples=json.loads((ROOT/'fixtures/local_switch/inputs.json').read_text(encoding='utf-8'))
    files=list((ROOT/'backend/local_reasoning').glob('*.py'))+list((ROOT/'backend/local_observation').glob('*.py'))
    files += [ROOT/'backend/local_observation/rules.json',ROOT/'backend/settings.py',ROOT/'backend/schemas.py',ROOT/'backend/main.py',Path(__file__)]
    files += [ROOT.parent/'data/v2'/n for n in ('fact_catalog.json','fact_rules.json','fact_templates.json','rulebook.json','templates.json','extraction_rules.json')]
    files += [ROOT/'fixtures/local_switch'/n for n in ('inputs.json','expected.json')]
    save(output/'lock.json',{'started_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
        'rounds':rounds,'cases':len(samples),'mode':'local_rules; compare legacy vs facts',
        'url_network':False,'rag':'same current production index; no approved real sources',
        'scope':'Paired alternating sequential localhost TCP requests, persistent HTTP client; known dev cases, not independent quality.',
        'hashes':{os.path.relpath(p,ROOT):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}})
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error',access_log=False,log_config=None))
    captured=[];original=adapter.analyze_local;old_times=defaultdict(float)
    def capture(body):
        result=original(body);captured.append(result);return result
    def timed(name,fn):
        def invoke(*args,**kwargs):
            start=time.perf_counter()
            try:return fn(*args,**kwargs)
            finally:old_times[name]+=(time.perf_counter()-start)*1000
        return invoke
    measurements=[];predictions=[];first=[]
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}), \
         patch('backend.local_reasoning.adapter.analyze_local',side_effect=capture), \
         patch('backend.local_reasoning.legacy_engine.safety_extract',side_effect=timed('extraction',legacy_engine.safety_extract)), \
         patch('backend.local_reasoning.legacy_engine.extract',side_effect=timed('extraction',legacy_engine.extract)), \
         patch('backend.local_reasoning.legacy_engine.apply_rules',side_effect=timed('rule_evaluation',legacy_engine.apply_rules)), \
         patch('backend.local_reasoning.support.inspect_urls',new_callable=AsyncMock,side_effect=AssertionError('No links: skip network')) as urls, \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('No external models')) as network:
        thread=threading.Thread(target=server.run,daemon=True);thread.start()
        try:
            until=time.monotonic()+10
            while not server.started:
                if time.monotonic()>until:raise RuntimeError('Server startup timeout')
                time.sleep(.01)
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=10,trust_env=False) as client:
                def request(sample,mode,round_index):
                    os.environ['SCAMSHIELD_REASONER']=mode;captured.clear();old_times.clear()
                    t=time.perf_counter();response=client.post('/api/analyze',json=sample['input']);data=response.json();elapsed=(time.perf_counter()-t)*1000
                    if response.status_code!=200 or len(captured)!=1:raise RuntimeError('Analysis failed')
                    result=captured[0]
                    stages=dict(result.core_timings_ms) if mode=='facts' else {'extraction':old_times['extraction'],'fact_build':0.,'rule_evaluation':old_times['rule_evaluation']}
                    row={'id':sample['id'],'mode':mode,'round':round_index,'http_ms':elapsed,'engine_ms':result.elapsed_ms,
                         **stages,'risk':data['risk_status'],'urgency':data['safety_urgency'],'http_status':response.status_code}
                    if round_index==0:predictions.append({'id':sample['id'],'mode':mode,'input':sample['input'],
                        'public_response':data,'backend_detail':result.model_dump(mode='json')})
                    return row
                # One warm-up pair per case; first requests reported separately, no
                # claim that either process started cold under controlled conditions.
                for sample in samples:
                    for mode in ('legacy','facts'):first.append(request(sample,mode,0))
                for round_index in range(1,rounds+1):
                    for sample in samples:
                        modes=('legacy','facts') if round_index%2 else ('facts','legacy')
                        for mode in modes:measurements.append(request(sample,mode,round_index))
            counts={'url_checker_calls':urls.call_count,'external_async_calls':network.call_count}
        finally:server.should_exit=True;thread.join(timeout=10)
    save(output/'predictions.json',predictions)  # Predictions persisted BEFORE expected labels opened.
    save(output/'measurements.json',measurements);save(output/'first_requests.json',first)
    expected={x['id']:x for x in json.loads((ROOT/'fixtures/local_switch/expected.json').read_text(encoding='utf-8'))['cases']}
    summary={'requests':len(measurements),'warmup_requests':len(first),'rounds':rounds,'counts':counts,'modes':{},'per_case':[]}
    for mode in ('legacy','facts'):
        rows=[r for r in measurements if r['mode']==mode]
        summary['modes'][mode]={key:stats([r[key] for r in rows]) for key in ('http_ms','engine_ms','extraction','fact_build','rule_evaluation')}
        summary['modes'][mode]['matched_cases']=sum(all((r['risk'],r['urgency'])==(expected[s['id']]['risk'],expected[s['id']]['urgency']) for r in rows if r['id']==s['id']) for s in samples)
    for sample in samples:
        case={'id':sample['id'],'input':sample['input']}
        for mode in ('legacy','facts'):
            rows=[r for r in measurements if r['id']==sample['id'] and r['mode']==mode]
            case[mode]={'risk':rows[0]['risk'],'urgency':rows[0]['urgency'],'http':stats([r['http_ms'] for r in rows]),'engine':stats([r['engine_ms'] for r in rows])}
        case['http_p50_reduction_pct']=(1-case['facts']['http']['p50_ms']/case['legacy']['http']['p50_ms'])*100
        summary['per_case'].append(case)
    summary['http_p50_reduction_pct']=(1-summary['modes']['facts']['http_ms']['p50_ms']/summary['modes']['legacy']['http_ms']['p50_ms'])*100
    save(output/'summary.json',summary)
    lines=['# 12 known development sentences: paired comparison','',
        'Measured real localhost TCP HTTP including JSON decode. No URL networking or external model. Same RAG production index.',
        'Positive reduction means faster; negative means slower. Known cases, not independent accuracy.','',
        '| ID | Input | Old risk | New risk | Old HTTP p50 ms | New HTTP p50 ms | Reduction % |',
        '|---|---|---|---|---:|---:|---:|']
    for c in summary['per_case']:
        lines.append(f"| {c['id']} | {c['input']['text']} | {c['legacy']['risk']} | {c['facts']['risk']} | {c['legacy']['http']['p50_ms']:.3f} | {c['facts']['http']['p50_ms']:.3f} | {c['http_p50_reduction_pct']:.2f} |")
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'requests':len(measurements),'modes':summary['modes'],'http_p50_reduction_pct':summary['http_p50_reduction_pct'],'counts':counts}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--rounds',type=int,default=30)
    args=p.parse_args();run(args.output,args.rounds)
