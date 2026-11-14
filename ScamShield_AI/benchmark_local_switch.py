"""Real localhost HTTP timing and captured BE details for the twelve saved inputs."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import socket
import threading
import time
from unittest.mock import AsyncMock,patch
import httpx
import uvicorn
from backend.main import app
from backend.settings import get_setting
from backend.local_reasoning import adapter

ROOT=Path(__file__).resolve().parent


def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def percentiles(values):
    values=sorted(values)
    return {'n':len(values),'p50_ms':values[math.ceil(.5*len(values))-1],
            'p95_ms':values[math.ceil(.95*len(values))-1],'min_ms':values[0],'max_ms':values[-1]}


def run(output,rounds):
    if get_setting('SCAMSHIELD_MODE')!='local_rules':raise SystemExit('Effective mode must be local_rules.')
    if not 1<=rounds<=30:raise SystemExit('Rounds must be 1..30.')
    output.mkdir(parents=True,exist_ok=False)
    inputs=ROOT/'fixtures/local_switch/inputs.json';expected=ROOT/'fixtures/local_switch/expected.json'
    samples=json.loads(inputs.read_text(encoding='utf-8'))
    files=list((ROOT/'backend/local_reasoning').glob('*.py'))+list((ROOT/'backend/local_observation').glob('*.py'))
    files += [ROOT/p for p in ('backend/main.py','backend/providers.py','backend/schemas.py','backend/retrieval.py','backend/local_observation/rules.json')]
    files += [ROOT.parent/'data'/p for p in ('abbreviations_vi.json','knowledge_sources.jsonl','v2/rulebook.json','v2/templates.json','v2/fact_rules.json','v2/fact_templates.json','v2/fact_catalog.json','v2/extraction_rules.json')]
    files += [inputs,expected,Path(__file__).resolve()]
    relative=lambda p:str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../'+str(p.relative_to(ROOT.parent))
    hashes={relative(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    save(output/'lock.json',{'started_utc':datetime.now(timezone.utc).isoformat(),'mode':get_setting('SCAMSHIELD_MODE'),
        'measurement':'Real localhost TCP HTTP, persistent synchronous client, one request at a time; includes JSON decode.',
        'backend_measurement':'analysis.stage_timings_ms.local_total: v2 engine only, excludes public adapter and HTTP serialization.',
        'rounds':rounds,'concurrency':1,'python':platform.python_version(),'hashes':hashes,
        'limits':'Not browser/extension latency or controlled cold-start/load; first request recorded separately.'})
    with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error',access_log=False,log_config=None))
    captured=[];original=adapter.analyze_local
    def capture(body,**kwargs):
        result=original(body,**kwargs);captured.append(result);return result
    measurements=[];snapshots=[]
    with patch('backend.local_reasoning.adapter.analyze_local',side_effect=capture), \
         patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as model, \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('External async network forbidden')) as network:
        thread=threading.Thread(target=server.run,daemon=True);thread.start()
        try:
            deadline=time.perf_counter()+10
            while not server.started:
                if time.perf_counter()>deadline:raise RuntimeError('Local server startup timeout')
                time.sleep(.01)
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=10,trust_env=False) as client:
                for round_index in range(rounds):
                    for sample in samples:
                        count=len(captured);started=time.perf_counter()
                        response=client.post('/api/analyze',json=sample['input']);data=response.json()
                        elapsed=(time.perf_counter()-started)*1000
                        measurements.append({'round':round_index+1,'case_id':sample['id'],'http_status':response.status_code,
                            'risk_status':data.get('risk_status'),'safety_urgency':data.get('safety_urgency'),
                            'http_ms':elapsed,'engine_ms':data.get('analysis',{}).get('stage_timings_ms',{}).get('local_total')})
                        if response.status_code!=200 or len(captured)!=count+1:raise RuntimeError('Incomplete local analysis')
                        if round_index==0:
                            snapshots.append({**sample,'http_status':response.status_code,'public_response':data,
                                'backend_detail':captured[-1].model_dump(mode='json')})
                        captured.clear()
        finally:
            server.should_exit=True;thread.join(timeout=10)
        counts={'provider_calls':model.call_count,'external_async_requests':network.call_count}
    save(output/'measurements.json',measurements);save(output/'predictions.json',snapshots)
    # References are opened only after all measured predictions are saved.
    references={r['id']:r for r in json.loads(expected.read_text(encoding='utf-8'))['cases']}
    summaries=[];failures=[]
    for sample in samples:
        rows=[r for r in measurements if r['case_id']==sample['id']]
        outcomes={(r['risk_status'],r['safety_urgency']) for r in rows}
        ref=references[sample['id']]
        if outcomes!={(ref['risk'],ref['urgency'])}:failures.append(sample['id'])
        snapshot=next(s for s in snapshots if s['id']==sample['id'])
        a=snapshot['backend_detail']['assessment']
        summaries.append({'id':sample['id'],'text':sample['input']['text'],'risk_status':rows[0]['risk_status'],
            'safety_urgency':rows[0]['safety_urgency'],'first_round_http_ms':rows[0]['http_ms'],
            'http':percentiles([r['http_ms'] for r in rows]),'engine':percentiles([r['engine_ms'] for r in rows]),
            'consistent_outcomes':len(outcomes)==1,'applied_rules':a['applicable_rule_ids'],
            'summary':a['summary'],'follow_up_questions':a['follow_up_questions'],
            'path':snapshot['backend_detail']['versions'].get('path')})
    summary={'scope':'12 known development cases, repeated real localhost HTTP; not independent model accuracy.',
        'cases':len(samples),'requests':len(measurements),'rounds':rounds,
        'http':percentiles([r['http_ms'] for r in measurements]),'engine':percentiles([r['engine_ms'] for r in measurements]),
        'first_http_request_ms':measurements[0]['http_ms'],'failures':failures,**counts,'per_case':summaries}
    save(output/'summary.json',summary)
    lines=['# 12 ca: dữ kiện BE, quy tắc và thời gian HTTP','',
        f'Mỗi câu đo {rounds} lượt qua HTTP TCP localhost, tuần tự, cùng process. Không phải browser/extension hay tải đồng thời.',
        'API tính từ trước POST đến sau đọc JSON; Engine chỉ v2, chưa gồm adapter/schema/HTTP. Lượt đầu không được chứng minh là cold start hoàn toàn.','',
        '| Ca | Câu đầu vào | Kết quả | HTTP p50 ms | HTTP p95 ms | Engine p50 ms |','|---|---|---|---:|---:|---:|']
    for row in summaries:
        lines.append(f"| {row['id']} | {row['text']} | {row['risk_status']} / {row['safety_urgency']} | {row['http']['p50_ms']:.2f} | {row['http']['p95_ms']:.2f} | {row['engine']['p50_ms']:.2f} |")
    for snapshot in snapshots:
        raw=snapshot['backend_detail'];a=raw['assessment'];row=next(r for r in summaries if r['id']==snapshot['id']);spans={s['span_id']:s for s in raw['annotations']['spans']}
        lines += ['', '## '+snapshot['id'],'',snapshot['input']['text'],'',a['summary'],'',
            f"Đường chạy: {row['path']}. Rules: {', '.join(a['applicable_rule_ids']) or 'fallback, chưa đủ điều kiện rule cảnh báo'}. Template: {a['explanation_template_id']}.",'',
            '| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |','|---|---|---|---|---|---|']
        for event in raw['annotations']['events']:
            evidence=spans[event['evidence_refs'][0]]
            lines.append(f"| {event['event_type']} | {event['speech_role']} | {event['polarity']} | {event['temporal_state']} | {event['attribution']['kind']} | {evidence['quote'].replace('|','/').replace(chr(10),' ')} |")
        lines += ['', 'Quan hệ:']
        lines += [f"- {r['type']}: {r['from_id']} → {r['to_id']} ({r['status']}); {r['rule_id']}." for r in raw['annotations']['relations']] or ['- Chưa trích được quan hệ đủ điều kiện.']
        lines += ['', 'Câu hỏi:']+['- '+q for q in a['follow_up_questions']] if a['follow_up_questions'] else ['', 'Không có câu hỏi bổ sung.']
        lines += ['', f"HTTP p50/p95: {row['http']['p50_ms']:.2f}/{row['http']['p95_ms']:.2f} ms; Engine p50: {row['engine']['p50_ms']:.2f} ms; lượt đo đầu của câu: {row['first_round_http_ms']:.2f} ms."]
    (output/'DETAILS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[relative(p)] for p in files)
    print(json.dumps({k:v for k,v in summary.items() if k!='per_case'}))
    for row in summaries:print(json.dumps({k:row[k] for k in ('id','text','risk_status','safety_urgency','http','engine','applied_rules')},ensure_ascii=True))
    if failures or any(counts.values()):raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rounds',type=int,default=10)
    parser.add_argument('--output',type=Path,default=ROOT/'reports/local_switch_20261112/timing')
    args=parser.parse_args();run(args.output,args.rounds)
