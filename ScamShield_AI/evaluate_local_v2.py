"""Local API acceptance run; predictions saved before reading authored targets."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time
from unittest.mock import AsyncMock,patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_reasoning.schema import CaseInput,LocalResult
from backend.local_reasoning.validation import annotation_errors
from backend.local_reasoning.extract import DATA

ROOT=Path(__file__).resolve().parent


def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def pct(values):
    ordered=sorted(values)
    return {'n':len(values),'p50_ms':ordered[math.ceil(len(values)*.5)-1] if values else None,
            'p95_ms':ordered[math.ceil(len(values)*.95)-1] if values else None}


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    inputs=DATA/manifest['runtime_inputs'];targets=DATA/manifest['acceptance_targets']
    files=list((ROOT/'backend/local_reasoning').glob('*.py'))+list((ROOT/'backend/local_observation').glob('*.py'))
    files += [ROOT/'backend/local_observation/rules.json',ROOT.parent/'data/abbreviations_vi.json',ROOT/'backend/main.py',ROOT/'backend/retrieval.py',ROOT/'backend/schemas.py',Path(__file__).resolve(),inputs,targets,DATA/manifest['canonical_pilot']]
    files += [ROOT.parent/'data/knowledge_sources.jsonl',DATA/'community_reports.jsonl']+list(DATA.glob('*.schema.json'))
    files += [DATA/n for n in ('rulebook.json','templates.json','fact_rules.json','fact_templates.json','fact_catalog.json','labels.json','extraction_rules.json','support_directory.json','manifest.json')]
    rel=lambda p:str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../'+str(p.relative_to(ROOT.parent))
    hashes={rel(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    save(output/'lock.json',{'mode':'local_rules','hashes':hashes,'provider':'none','measurement':'ASGI TestClient, actual local extract/rule code; no browser latency'})
    samples=json.loads(inputs.read_text(encoding='utf-8'));records=[]
    with patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as live, \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('External network forbidden')) as network,TestClient(app) as client:
        for sample in samples:
            start=time.perf_counter();response=client.post('/api/analyze-local',json=sample['input'])
            records.append({'case_id':sample['case_id'],'input':sample['input'],'http_status':response.status_code,
                            'api_ms':(time.perf_counter()-start)*1000,'response':response.json()})
        save(output/'predictions.json',records)
        calls={'provider_calls':live.call_count,'network_calls':network.call_count}
    expected={r['case_id']:r for r in json.loads(targets.read_text(encoding='utf-8'))['cases']}
    matrix={};urgency_matrix={};errors=[];mismatches=[];urgent_missed=[];urgent_false=[];quotes=exact=0;unknown=Counter();rules=Counter();paths=Counter()
    binary=Counter();latencies=[];by_case=[]
    for row in records:
        cid=row['case_id'];target=expected.get(cid);response=LocalResult.model_validate(row['response']);a=response.assessment
        if response.analysis_status!='complete':errors.append(cid)
        input=CaseInput.model_validate(row['input']);issues=annotation_errors(input,response.annotations)
        if issues:errors.append(cid+':'+','.join(issues))
        messages={m.id:m.text for m in input.messages};contexts={c.id:c.text for c in input.context_facts}
        for span in response.annotations.spans:
            text=messages[span.message_id] if span.message_id else contexts[span.context_id]
            quotes+=1;exact+=text[span.start:span.end]==span.quote
        for key,f in response.annotations.answers_18.__dict__.items():unknown[key]+=f.status=='unknown'
        rules.update(a.applicable_rule_ids);paths[response.versions.get('path','unknown')]+=1;latencies.append(row['api_ms'])
        if target:
            gold=target['risk_status'];got=a.risk_status or 'error';matrix.setdefault(gold,{}).setdefault(got,0);matrix[gold][got]+=1
            gu=target['safety_urgency'];au=a.safety_urgency;urgency_matrix.setdefault(gu,{}).setdefault(au,0);urgency_matrix[gu][au]+=1
            if (gold,gu)!=(got,au):mismatches.append(cid)
            if gu=='urgent' and au!='urgent':urgent_missed.append(cid)
            if gu!='urgent' and au=='urgent':urgent_false.append(cid)
            binary['tp' if gold=='high' and got=='high' else 'fn' if gold=='high' else 'fp' if got=='high' else 'tn']+=1
        by_case.append({'case_id':cid,'risk':a.risk_status,'urgency':a.safety_urgency,'rules':a.applicable_rule_ids,
                        'unknown_answers':sum(f.status=='unknown' for f in response.annotations.answers_18.__dict__.values()),'api_ms':row['api_ms']})
    summary={'scope':'Known synthetic development acceptance, not independent accuracy; detailed event annotations are automatic weak labels.',
        'executed':len(records),'authored_targets':len(expected),'matching_authored_targets':len(expected)-len(mismatches),
        'unscored_legacy_inputs':len(records)-len(expected),'errors':errors,'mismatches':mismatches,'risk_matrix':matrix,'urgency_matrix':urgency_matrix,
        'high_counts':dict(binary),'high_precision_on_authored_targets':binary['tp']/(binary['tp']+binary['fp']) if binary['tp']+binary['fp'] else None,
        'high_recall_on_authored_targets':binary['tp']/(binary['tp']+binary['fn']) if binary['tp']+binary['fn'] else None,
        'urgent_missed':urgent_missed,'urgent_false_alarms':urgent_false,'quotes':quotes,'exact_offsets':exact,
        'unknown_answers':dict(unknown),'applied_rules':dict(rules),'execution_paths':dict(paths),
        'api_latency':pct(latencies),'first_request_ms':latencies[0],'later_requests':pct(latencies[1:]),**calls,
        'not_measured':['semantic_span_event_relation_F1_requires_human_gold','semantic_actor_recipient_precision_recall',
            'independent_real_world_accuracy','trained_model_quality','real_approved_RAG_quality','controlled_load_or_cold_start']}
    save(output/'summary.json',summary);save(output/'case_summary.json',by_case)
    lines=['# Kết quả từng ca cục bộ','','Dữ liệu tổng hợp phát triển; nhãn chi tiết máy tạo, chưa là độ chính xác độc lập.','',
           '| Ca | Mức rủi ro | Khẩn cấp | Quy tắc | Thời gian API ms |','|---|---|---|---|---:|']
    for r in by_case:lines.append(f"| {r['case_id']} | {r['risk']} | {r['urgency']} | {', '.join(r['rules'])} | {r['api_ms']:.2f} |")
    for row in records:
        a=row['response']['assessment'];spans={s['span_id']:s for s in row['response']['annotations']['spans']}
        lines += ['', '## '+row['case_id'],'','```json',json.dumps(row['input'],ensure_ascii=False,indent=2),'```','',a['summary'],'']
        lines += ['- '+action for action in a['recommended_actions']]
        seen=set()
        for sid in a['evidence_refs']:
            span=spans[sid]
            if span['quote'] in seen:continue
            seen.add(span['quote']);lines += ['', '> '+span['quote'].replace('\n','\n> ')]
        lines += ['']+['- '+q for q in a['follow_up_questions']]
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[rel(p)] for p in files)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('unknown_answers','applied_rules','not_measured')},ensure_ascii=True))
    if errors or mismatches or quotes!=exact or any(calls.values()):raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/local_v2_20261112/api');run(p.parse_args().output)
