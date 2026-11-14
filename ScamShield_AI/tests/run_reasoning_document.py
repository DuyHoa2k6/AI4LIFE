"""User's public synthetic document: isolated inputs -> actual API -> separate scoring.

No rule/model changes and no expected labels in inference payloads.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def rows(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def jsonl(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in data),encoding='utf-8')

def prepare(source,out):
    if (out/'inputs.jsonl').exists():raise ValueError('Refuse overwrite of prepared public test data')
    text=source.read_text(encoding='utf-8-sig');a=text.split('PHẦN A — NỘI DUNG ĐẦU VÀO',1)[1].split('PHẦN B —',1)[0]
    matches=list(re.finditer(r'^TH(\d{2}) — (.+)$',a,re.M));inputs=[];meta=[]
    for i,m in enumerate(matches):
        body=a[m.end():matches[i+1].start() if i+1<len(matches) else len(a)].split('Nội dung đầu vào',1)[1].strip()
        messages=[]
        for j,paragraph in enumerate(re.split(r'\n\s*\n',body)):
            speaker,sep,content=paragraph.partition(': ')
            if not sep:raise ValueError('Unlabelled turn; do not guess the speaker')
            messages.append({'id':'m'+str(j+1),'speaker':speaker.strip(),'text':content.strip()})
        cid='TH'+m.group(1);inputs.append({'case_id':cid,'request':{'messages':messages}});meta.append({'case_id':cid,'title':m.group(2),'turns':len(messages)})
    if len(inputs)!=16 or [r['case_id'] for r in inputs]!=['TH'+str(i).zfill(2) for i in range(1,17)]:raise ValueError('Expected 16 distinct cases')
    # Reference is stored apart; the run subcommand never opens it.
    b=text.split('PHẦN B —',1)[1].split('PHẦN C —',1)[0]
    refs=list(re.finditer(r'^TH(\d{2}) — Kỳ vọng: (high|suspicious|need_context|clear)\s*$',b,re.M))
    expected=[{'case_id':'TH'+m.group(1),'risk_status':m.group(2),'reference_text':b[m.end():refs[i+1].start() if i+1<len(refs) else len(b)].strip(),'review_status':'public_author_draft_not_independently_reviewed'} for i,m in enumerate(refs)]
    if len(expected)!=16:raise ValueError('Reference count mismatch')
    jsonl(out/'inputs.jsonl',inputs);jsonl(out/'reference_draft.jsonl',expected);dump(out/'case_metadata.json',meta)
    dump(out/'data_manifest.json',{'source_document_sha256':sha(source),'input_sha256':sha(out/'inputs.jsonl'),'reference_sha256':sha(out/'reference_draft.jsonl'),'cases':16,'messages':sum(len(r['request']['messages']) for r in inputs),'public_development_only':True,'human_reviewed':0,'note':'Speaker labels retained literally. TH02 uses two different labels for a possible same scholarship representative; no account alias is assumed. TH16 remains one user report with embedded quotations, not invented original chat turns.'})
    print(json.dumps({'prepared':len(inputs),'out':str(out)},ensure_ascii=False))

def run(data,out):
    if (out/'predictions.jsonl').exists():raise ValueError('Refuse overwrite of completed predictions; choose another run directory')
    os.environ.setdefault('HF_HUB_OFFLINE','1');os.environ.setdefault('TRANSFORMERS_OFFLINE','1')
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.settings import get_setting
    cases=rows(data/'inputs.jsonl');out.mkdir(parents=True,exist_ok=True)
    config={key:get_setting(key,default) for key,default in [('SCAMSHIELD_MODE','local_rules'),('SCAMSHIELD_REASONER','legacy'),('SCAMSHIELD_RAG_ENABLED','1'),('SCAMSHIELD_SCENARIO_ENABLED','1'),('SCAMSHIELD_URL_NETWORK_ENABLED','1'),('SCAMSHIELD_CONTEXT_ENABLED','1'),('SCAMSHIELD_DISABLE_RESPONSE_TIMEOUTS','0')]}
    if config['SCAMSHIELD_MODE']!='local_rules':raise ValueError('This run requires actual configured local_rules, not mock or removed external modes')
    paths=['backend/main.py','backend/local_reasoning/adapter.py','backend/local_reasoning/engine.py','backend/local_reasoning/legacy_engine.py','backend/local_reasoning/extract.py','backend/local_reasoning/grounding.py','backend/local_reasoning/support.py']
    assets=list((ROOT.parent/'data/v2').glob('*.json'))
    manifest={'configuration':config,'input_sha256':sha(data/'inputs.jsonl'),'versions_sha256':{p:sha(ROOT/p) for p in paths if (ROOT/p).exists()},'asset_sha256':{str(p.relative_to(ROOT.parent)):sha(p) for p in assets},'method':'Actual FastAPI TestClient, POST /api/analyze, no dependency override or mock. One independent request per case. Separate /api/analyze-local debug pass after all public predictions. No expected labels read by this subcommand.','cases':len(cases),'public_prediction_order':[r['case_id'] for r in cases]}
    all_predictions=[];traces=[];start=time.perf_counter()
    with TestClient(app) as client:
        for index,r in enumerate(cases):
            began=time.perf_counter();response=client.post('/api/analyze',json=r['request']);elapsed=(time.perf_counter()-began)*1000
            row={'case_id':r['case_id'],'http_status':response.status_code,'elapsed_ms':elapsed,'sequence':index+1,'response':response.json()};all_predictions.append(row)
            jsonl(out/'predictions.jsonl',all_predictions)
            print(json.dumps({'case_id':r['case_id'],'risk':row['response'].get('risk_status'),'http':response.status_code,'ms':round(elapsed,2)},ensure_ascii=False),flush=True)
        manifest['predictions_sha256_before_scoring']=sha(out/'predictions.jsonl');manifest['all_public_predictions_saved_before_debug']=True
        # Separate diagnostic run, explicitly not the trace of the earlier API call.
        for r in cases:
            body={'messages':[{'id':m['id'],'speaker_id':None if m['speaker']=='unknown' else m['speaker'],'text':m['text'],'scope_id':'analysis'} for m in r['request']['messages']]}
            began=time.perf_counter();response=client.post('/api/analyze-local',json=body)
            traces.append({'case_id':r['case_id'],'http_status':response.status_code,'elapsed_ms':(time.perf_counter()-began)*1000,'separate_debug_execution':True,'response':response.json()})
            jsonl(out/'debug_traces.jsonl',traces)
    manifest.update(elapsed_all_calls_ms=(time.perf_counter()-start)*1000,completed=True,debug_traces_sha256=sha(out/'debug_traces.jsonl'))
    dump(out/'run_manifest.json',manifest)

def score(data,out):
    predictions=rows(out/'predictions.jsonl');manifest=json.loads((out/'run_manifest.json').read_text(encoding='utf-8'))
    if sha(out/'predictions.jsonl')!=manifest['predictions_sha256_before_scoring']:raise ValueError('Predictions changed after inference')
    expected={r['case_id']:r for r in rows(data/'reference_draft.jsonl')};inputs={r['case_id']:r['request'] for r in rows(data/'inputs.jsonl')};debug={r['case_id']:r for r in rows(out/'debug_traces.jsonl')}
    labels=['high','suspicious','need_context','clear'];matrix={e:{p:0 for p in labels+['error']} for e in labels};audit=[]
    for row in predictions:
        cid=row['case_id'];response=row['response'];ref=expected[cid]['risk_status'];risk=response.get('risk_status');pred=risk if row['http_status']==200 and risk in labels else 'error';matrix[ref][pred]+=1
        texts={m['id']:m for m in inputs[cid]['messages']};bad=[];evidence_count=0
        for finding in response.get('findings',[]):
            for e in finding.get('evidence',[]):
                evidence_count+=1;m=texts.get(e['message_id'])
                if not m or not 0<=e['start']<e['end']<=len(m['text']) or m['text'][e['start']:e['end']]!=e['quote'] or finding.get('speaker')!=m['speaker']:bad.append({'location':'finding','finding_id':finding.get('id'),'evidence':e})
        for indicator in response.get('risk_indicators',[]):
            for e in indicator.get('evidence',[]):
                evidence_count+=1;m=texts.get(e['message_id'])
                if not m or not 0<=e['start']<e['end']<=len(m['text']) or m['text'][e['start']:e['end']]!=e['quote']:bad.append({'location':'risk_indicator','evidence':e})
        trace=debug[cid]['response'];a=trace.get('annotations',{});events=a.get('events',[]);relations=a.get('relations',[])
        audit.append({'case_id':cid,'expected_draft':ref,'predicted':pred,'level_match':pred==ref,'ms':row['elapsed_ms'],'evidence_checked':evidence_count,'invalid_evidence':bad,'debug_predicted':trace.get('assessment',{}).get('risk_status'),'public_debug_level_consistent':risk==trace.get('assessment',{}).get('risk_status'),'events':len(events),'relations':len(relations),'semantic_review_status':'agent_review_required_not_human_gold'})
    metrics={};n=len(audit)
    for label in labels:
        tp=matrix[label][label];support=sum(matrix[label].values());predicted=sum(matrix[e][label] for e in labels);precision=tp/predicted if predicted else None;recall=tp/support if support else None
        metrics[label]={'support':support,'predicted':predicted,'tp':tp,'precision':precision,'recall':recall,'f1':2*tp/(support+predicted) if support+predicted else None}
    times=sorted(r['elapsed_ms'] for r in predictions);rank=lambda ts,q:ts[math.ceil(len(ts)*q)-1] if ts else None
    result={'draft_reference_only':True,'cases':n,'http_errors':sum(r['http_status']!=200 for r in predictions),'level_matches':sum(r['level_match'] for r in audit),'level_agreement':sum(r['level_match'] for r in audit)/n,'semantic_accuracy':None,'human_reviewed':0,'confusion_matrix':matrix,'per_level':metrics,'macro_f1':sum(v['f1'] for v in metrics.values())/len(labels),'high_missed':[r['case_id'] for r in audit if r['expected_draft']=='high' and r['predicted']!='high'],'clear_as_high':[r['case_id'] for r in audit if r['expected_draft']=='clear' and r['predicted']=='high'],'evidence_checked':sum(r['evidence_checked'] for r in audit),'invalid_evidence':sum(len(r['invalid_evidence']) for r in audit),'public_debug_mismatches':[r['case_id'] for r in audit if not r['public_debug_level_consistent']],'latency_ms':{'n':n,'p50':rank(times,.5),'p95':rank(times,.95),'first_request':predictions[0]['elapsed_ms'],'remaining_15_p50':rank(sorted(r['elapsed_ms'] for r in predictions[1:]),.5),'cold_model_load_controlled':False,'browser_measured':False}}
    dump(out/'metrics.json',result);jsonl(out/'case_audit.jsonl',audit);print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','score']);p.add_argument('--source',type=Path);p.add_argument('--data',type=Path,default=ROOT/'fixtures/reasoning_document_20261114');p.add_argument('--out',type=Path,default=ROOT/'reports/reasoning_document_20261114');args=p.parse_args()
    if args.action=='prepare':prepare(args.source,args.data)
    elif args.action=='run':run(args.data,args.out)
    else:score(args.data,args.out)
