"""Run user-supplied simulated conversations, without sending scenario labels."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import time
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--rounds',type=int,default=3)
    args=parser.parse_args()
    if not 1<=args.rounds<=10:raise SystemExit('rounds must be 1..10')
    args.output.mkdir(parents=True,exist_ok=False)
    text=args.source.read_text(encoding='utf-8')
    chunks=re.split(r'(?m)^(\d{2})\. (.+)\s*$',text)
    inputs=[];metadata=[]
    for i in range(1,len(chunks),3):
        cid,title,body=chunks[i:i+3];body=body.split('Nội dung đầu vào',1)[1]
        blocks=re.findall(r'([^\n]+):\s*\n“([\s\S]*?)”(?=\s*(?:\n|$))',body)
        if not blocks:raise ValueError('No messages in '+cid)
        messages=[];roles={}
        for j,(role,content) in enumerate(blocks,1):
            # Scenario 07 uses a shorter label for the same sender later.
            canonical='Người tự nhận nhân viên' if cid=='07' and role.startswith('Người tự nhận nhân viên') else role
            if cid=='09' and canonical=='Tài khoản mới nhắn':canonical='Tài khoản mới'
            canonical='Người dùng' if canonical=='Người dùng bổ sung' else canonical
            speaker=roles.setdefault(canonical,'speaker_'+str(len(roles)+1))
            messages.append({'id':'m'+str(j),'speaker':speaker,'text':content})
        inputs.append({'id':cid,'input':{'messages':messages}})
        metadata.append({'id':cid,'title':title,'speaker_labels':roles,'source_roles':[r for r,_ in blocks]})
    if len(inputs)!=10:raise ValueError('Expected ten scenarios')
    def save(name,obj):
        (args.output/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save('inputs.json',inputs);save('metadata.json',metadata)
    records=[];timings=[]
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}), \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('External HTTP forbidden')) as network, TestClient(app) as client:
        for row in inputs:
            runs=[]
            for attempt in range(args.rounds):
                start=time.perf_counter();r=client.post('/api/analyze',json=row['input']);elapsed=round((time.perf_counter()-start)*1000,3)
                runs.append({'http_status':r.status_code,'elapsed_ms':elapsed,'response':r.json()});timings.append(elapsed)
            raw=client.post('/api/analyze-local',json={'messages':[{'id':m['id'],'speaker_id':m['speaker'],'scope_id':'analysis','text':m['text']} for m in row['input']['messages']]})
            records.append({'id':row['id'],'input':row['input'],'runs':runs,'local_http':raw.status_code,'local':raw.json()})
        network_calls=network.call_count
    # Persist all predictions before any later manual labels/review exist.
    save('predictions.json',records)
    valid=total=0;counts={};lines=['# Kết quả 10 tình huống người dùng cung cấp','',
        'Dữ liệu giả lập công khai; chạy nguyên văn các lượt nói qua API thật, không đổi mã hoặc cấu hình trong lúc đo.','',
        '| Ca | Chủ đề (không gửi API) | Kết quả thực tế | Trạng thái | API ms lần đầu |','|---|---|---|---|---:|']
    for row,meta in zip(records,metadata):
        d=row['runs'][0]['response'];risk=d.get('risk_status','error');counts[risk]=counts.get(risk,0)+1
        lines.append(f"| {row['id']} | {meta['title']} | {risk} | {d.get('analysis_status')} | {row['runs'][0]['elapsed_ms']} |")
        by_id={m['id']:m['text'] for m in row['input']['messages']}
        for run in row['runs']:
            for finding in run['response'].get('findings',[]):
                for e in finding['evidence']:
                    total+=1;valid+=int(by_id[e['message_id']][e['start']:e['end']]==e['quote'])
    lines+=['','## Từng tình huống','']
    for row,meta in zip(records,metadata):
        d=row['runs'][0]['response'];reverse={v:k for k,v in meta['speaker_labels'].items()}
        lines += [f"### {row['id']}. {meta['title']}",'']
        for m in row['input']['messages']:lines += [f"**{reverse[m['speaker']]}:** {m['text']}",'']
        lines += [f"**Thực tế:** {d.get('risk_status')}. {d.get('summary')}",'',
            '**Nên làm:** '+' '.join(d.get('recommended_actions',[])),'',
            '**Câu hỏi bổ sung:** '+' '.join(d.get('follow_up_questions',[])),'']
    (args.output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=list((ROOT/'backend/local_reasoning').glob('*.py'))+[ROOT.parent/'data/v2'/n for n in ['semantic_phrases.json','semantic_graph_patterns.json','context_rules.json','context_templates.json','rulebook.json','extraction_rules.json']]
    summary={'cases':10,'requests':len(timings),'rounds_per_case':args.rounds,'risk_counts':counts,
        'http_errors':sum(r['http_status']!=200 for row in records for r in row['runs']),
        'external_http_calls':network_calls,'exact_quotes':{'valid':valid,'total':total},
        'risk_stable':all(len({r['response'].get('risk_status') for r in row['runs']})==1 for row in records),
        'p50_ms':statistics.median(timings),'p95_ms':sorted(timings)[math.ceil(.95*len(timings))-1],
        'scope':'Sequential ASGI TestClient, local Python, actual public API; no browser/concurrency/controlled cold-start/model/URL network measurement.',
        'configuration':{'mode':'local_rules','reasoner':'legacy','context_enabled':True,'semantic_graph_enabled':os.environ.get('SCAMSHIELD_SEMANTIC_GRAPH_ENABLED','1')=='1','url_network':False},
        'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'hashes':{str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    save('summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='hashes'},ensure_ascii=False))


if __name__=='__main__':main()
