"""First-stage-only predictions, draft-reference metrics and local timing. No live API."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from backend.main import app
from backend.schemas import AnalyzeRequest
from backend.local_observation.analyzer import analyze
from backend.local_observation.dataset import AnnotatedSample, Annotation, Provenance

ROOT=Path(__file__).resolve().parent
FIXTURES=ROOT/'fixtures/local_observation'


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def metrics(tp,actual,gold):
    return {'true_positive':tp,'predicted':actual,'reference':gold,
            'precision':tp/actual if actual else None,'recall':tp/gold if gold else None}


def percentile(values):
    values=sorted(values)
    return {'n':len(values),'p50_ms':values[math.ceil(len(values)*.5)-1],
            'p95_ms':values[math.ceil(len(values)*.95)-1]}


def evaluate(output):
    output.mkdir(parents=True,exist_ok=False)
    paths=[ROOT/'backend/local_observation'/name for name in ('analyzer.py','schema.py','text.py','syntax.py','segmentation.py','rules.json','dataset.py','abbreviations.py')]
    paths += [ROOT.parent/'data/abbreviations_vi.json']
    paths += [FIXTURES/name for name in ('inputs.json','expected.json','expected_grounding_overrides.json')]
    paths += [Path(__file__).resolve(),ROOT/'backend/main.py']
    relative=lambda p:str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../'+str(p.relative_to(ROOT.parent))
    hashes={relative(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    save(output/'hashes.json',hashes)
    inputs=json.loads((FIXTURES/'inputs.json').read_text(encoding='utf-8'))
    records=[]
    with patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as provider, \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('External request forbidden')) as network, TestClient(app) as client:
        for sample in inputs:
            start=time.perf_counter()
            response=client.post('/api/observe',json=sample['input'])
            records.append({'id':sample['id'],'input':sample['input'],'http_status':response.status_code,
                            'api_ms':(time.perf_counter()-start)*1000,'response':response.json()})
        save(output/'predictions.json',records)
        provider_calls,network_calls=provider.call_count,network.call_count
    # Read semantic references only after predictions have been persisted.
    refs={r['id']:r for r in json.loads((FIXTURES/'expected.json').read_text(encoding='utf-8'))['cases']}
    refs.update({r['id']:r for r in json.loads((FIXTURES/'expected_grounding_overrides.json').read_text(encoding='utf-8'))['cases']})
    event_tp=event_n=event_gold=span_tp=relation_tp=relation_n=relation_gold=exact_spans=span_n=author_ok=author_n=0
    failures=[];unknown=Counter();per_case=[]
    for row in records:
        expected=refs[row['id']];r=row['response'];spans={s['id']:s for s in r['evidence']}
        request=AnalyzeRequest.model_validate(row['input']);texts={m.id:m.text for m in request.as_messages()};authors={m.id:m.speaker for m in request.as_messages()}
        predicted=[];gold=[];pred_spans=[];gold_spans=[]
        for e in r['events']:
            s=spans[e['verb_span']];key=(s['message_id'],s['start'],s['end'],e['action_type'])
            pred_spans.append(key);predicted.append(key+(e['polarity'],e['speech_role'],e['temporal_state']))
        for e in expected['events']:
            positions=[];start=0;text=texts[e['message_id']]
            while (at:=text.find(e['verb'],start))>=0:
                positions.append(at);start=at+len(e['verb'])
            at=positions[e['occurrence']];key=(e['message_id'],at,at+len(e['verb']),e['action_type'])
            gold_spans.append(key);gold.append(key+(e['polarity'],e['speech_role'],e['temporal_state']))
        event_tp+=sum((Counter(predicted)&Counter(gold)).values());span_tp+=sum((Counter(pred_spans)&Counter(gold_spans)).values())
        event_n+=len(predicted);event_gold+=len(gold)
        rel=Counter(x['rule_id'] for x in r['relations']);target_rel=Counter(expected['relation_rules'])
        relation_tp+=sum((rel&target_rel).values());relation_n+=sum(rel.values());relation_gold+=sum(target_rel.values())
        passed=Counter(predicted)==Counter(gold) and rel==target_rel
        if not passed:failures.append(row['id'])
        for s in spans.values():
            text=texts[s['message_id']] if s['source']=='message' else request.context
            span_n+=1;exact_spans+=text[s['start']:s['end']]==s['quote']
            if s['source']=='message':author_n+=1;author_ok+=s['speaker']==authors[s['message_id']]
        for name,f in r['answers_18'].items():
            if f['status']=='unknown':unknown[name]+=1
        per_case.append({'id':row['id'],'passed_draft_reference':passed,'events':len(predicted),'relations':sum(rel.values()),
                         'unknown_fields':sum(f['status']=='unknown' for f in r['answers_18'].values()),'api_ms':row['api_ms']})
    timings=[]
    for kind,seed in [('no_rule','Nội dung chưa nằm trong bộ mẫu. '),('many_events','Chuyển tiền. ')]:
        for length in (100,1000,10000):
            text=(seed*math.ceil(length/len(seed)))[:length]
            request=AnalyzeRequest(text=text);samples=[]
            for _ in range(30):
                start=time.perf_counter();result=analyze(request);samples.append((time.perf_counter()-start)*1000)
            timings.append({'kind':kind,'characters':length,**percentile(samples),'events_last':len(result.events),
                            'limited':any('giới hạn 50' in s for s in result.limitations)})
    # Export three development inputs only; original files and labels are untouched.
    dev=[json.loads(line) for line in (ROOT.parent/'data/dev.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()][:3]
    pilot=[]
    for sample in dev:
        request=AnalyzeRequest.model_validate(sample['input']);r=analyze(request)
        pilot.append(AnnotatedSample(id='LOCAL-'+sample['id'],input=request,
            annotations=Annotation(participants=r.participants,spans=r.evidence,events=r.events,relations=r.relations,expected_answers_18=r.answers_18),
            provenance=Provenance(source_split='dev',source_id=sample['id'],label_method='weak_label',rules_version=r.rules_version,
                rule_ids=sorted({e.rule_id for e in r.events}|{x.rule_id for x in r.relations})),review_status='weak_label'))
    (output/'dev_pilot.jsonl').write_text('\n'.join(json.dumps(s.model_dump(),ensure_ascii=False) for s in pilot)+'\n',encoding='utf-8')
    save(output/'annotation.schema.json',AnnotatedSample.model_json_schema())
    summary={'scope':'First-stage rules only. 30 known development cases with draft manual references, NOT independent accuracy or final warning results.',
             'cases':len(records),'case_matches':len(records)-len(failures),'failed_cases':failures,
             'verb_span_and_type':metrics(span_tp,event_n,event_gold),'event_polarity_role_state':metrics(event_tp,event_n,event_gold),
             'relation_rule_annotations':metrics(relation_tp,relation_n,relation_gold),
             'exact_quote_offsets':{'correct':exact_spans,'total':span_n},'speaker_metadata_binding':{'correct':author_ok,'total':author_n},
             'participant_semantic_precision_recall':'not measured; metadata binding only, no fully human-reviewed actor/recipient gold',
             'unknown_fields':dict(unknown),'provider_calls':provider_calls,'network_calls':network_calls,
             'timings':timings,'api_timing_30_cases':percentile([r['api_ms'] for r in records]),
             'pilot':'3 dev inputs, weak_label, not gold training data; risk_label_reference=null',
             'final_risk_quality':'not measured; downstream excluded by user scope'}
    save(output/'summary.json',summary);save(output/'case_summary.json',per_case)
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[relative(p)] for p in paths)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('unknown_fields','timings')},ensure_ascii=True))
    if failures or provider_calls or network_calls:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'reports/local_observation_20261112')
    evaluate(parser.parse_args().output)
