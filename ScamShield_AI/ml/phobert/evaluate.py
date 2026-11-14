"""Save all predictions first, then score reference labels. Test is opt-in and locked."""
import argparse
import hashlib
import json
import statistics
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import psutil
import torch
from .schema import runtime_input,SPAN_LABELS,ATTRS,ROLES,RELATIONS,RISKS
from .tasks import canonical_participant
from .data import load
from .inference import Runtime,ModelBusy

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'reports/phobert_20261114'

def counts(tp,fp,fn):
    p=tp/(tp+fp) if tp+fp else 0.;r=tp/(tp+fn) if tp+fn else 0.
    return {'tp':tp,'fp':fp,'fn':fn,'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0.}

def span_key(s):return (s['message_id'],s['start'],s['end'],s['label'])
def rel_key(r,events,spans):
    a=span_key(spans[events[r['source']]['anchor_id']]);b=span_key(spans[events[r['target']]['anchor_id']])
    if r['label']=='same_transaction':a,b=sorted([a,b])
    return (a,b,r['label'])

def score(rows,predictions):
    matrix={k:{v:0 for v in RISKS} for k in RISKS};unscored=Counter();span_counts={k:[0,0,0] for k in SPAN_LABELS};relation_counts={k:[0,0,0] for k in RELATIONS};attributes={k:{'correct':0,'gold_events':0,'matched_events':0} for k in ATTRS}
    role_counts={k:[0,0,0] for k in ROLES};wrong_direction=0;valid_none=0;total_none=0
    for row,p in zip(rows,predictions):
        risk=p['assessment']['risk_status']
        if row.risk_reference in RISKS and row.task_status['risk']!='unannotated':
            if risk in RISKS:matrix[row.risk_reference][risk]+=1
            else:unscored[row.risk_reference]+=1
        gold_spans={s.id:s.model_dump() for s in row.spans};pred_spans={s['id']:s for s in p['graph']['spans']}
        for label in SPAN_LABELS:
            if row.task_status['spans']=='unannotated' or row.span_label_status[label]!='complete':continue
            gold={span_key(s) for s in gold_spans.values() if s['label']==label};pred={span_key(s) for s in pred_spans.values() if s['label']==label}
            for i,v in enumerate([len(gold&pred),len(pred-gold),len(gold-pred)]):span_counts[label][i]+=v
        gold_events={e.id:{**e.model_dump(),'attributes':e.attributes} for e in row.events};pred_events={e['id']:e for e in p['graph']['events']}
        matched={span_key(pred_spans[e['anchor_id']]):e for e in pred_events.values()}
        gold_anchors={span_key(gold_spans[e.anchor_id]) for e in row.events}
        for e in pred_events.values():
            if span_key(pred_spans[e['anchor_id']]) not in gold_anchors:
                for role in e.get('roles',{}) if row.task_status['roles']!='unannotated' else []:
                    if role in role_counts:role_counts[role][1]+=1
        for e in row.events:
            match=matched.get(span_key(gold_spans[e.anchor_id]))
            participants={p.id:p for p in row.participants}
            for role in ROLES if row.task_status['roles']!='unannotated' else []:
                gold=next((canonical_participant(participants[a.participant_id]) for a in row.event_arguments if a.event_id==e.id and a.role==role),None)
                if gold is None and row.task_status['roles']!='complete':continue
                predicted=match.get('roles',{}).get(role) if match else None
                if gold is not None and predicted==gold:role_counts[role][0]+=1
                else:
                    if predicted is not None:role_counts[role][1]+=1
                    if gold is not None:role_counts[role][2]+=1
            for k,value in e.attributes.items():
                if value is None or row.task_status['attributes']=='unannotated':continue
                attributes[k]['gold_events']+=1
                if match:attributes[k]['matched_events']+=1;attributes[k]['correct']+=match['attributes'][k]==value
        if row.task_status['relations']=='complete':
            gold={rel_key(r.model_dump(),gold_events,gold_spans) for r in row.relations}
            pred={rel_key(r,pred_events,pred_spans) for r in p['graph']['relations']}
            wrong_direction+=sum(r not in gold and r[2]!='same_transaction' and (r[1],r[0],r[2]) in gold for r in pred)
            anchors=[span_key(s) for s in gold_spans.values() if s['label']=='action']
            for a in anchors:
                for b in anchors:
                    if a==b:continue
                    if not any((r[0]==a and r[1]==b) or r[2]=='same_transaction' and r[1]==a and r[0]==b for r in gold):
                        total_none+=1;valid_none+=not any(r[0]==a and r[1]==b for r in pred)
            for label in RELATIONS:
                a={r for r in gold if r[2]==label};b={r for r in pred if r[2]==label}
                for i,v in enumerate([len(a&b),len(b-a),len(a-b)]):relation_counts[label][i]+=v
    risk_metrics={}
    for risk in RISKS:
        tp=matrix[risk][risk];fp=sum(matrix[g][risk] for g in RISKS if g!=risk);fn=sum(matrix[risk][p] for p in RISKS if p!=risk)+unscored[risk]
        risk_metrics[risk]=counts(tp,fp,fn)
    return {'risk':{'confusion_matrix':matrix,'unscored_by_reference':dict(unscored),'per_label':risk_metrics,'macro_f1':sum(m['f1'] for m in risk_metrics.values())/4 if any(r.risk_reference in RISKS and r.task_status['risk']!='unannotated' for r in rows) else None,
        'clear_as_high':matrix['clear']['high'],'high_missed':sum(matrix['high'][p] for p in RISKS if p!='high')+unscored['high']},
      'spans':{k:counts(*v) if any(r.task_status['spans']!='unannotated' and r.span_label_status[k]=='complete' for r in rows) else {'not_measured':'no complete annotations for this label'} for k,v in span_counts.items()},
      'attributes':{k:{**v,'end_to_end_accuracy':v['correct']/v['gold_events'] if v['gold_events'] else None} for k,v in attributes.items()},
      'relations':{k:counts(*v) for k,v in relation_counts.items()},'relation_direction_errors':wrong_direction,'no_relation':{'correct':valid_none,'total':total_none},
      'roles':{k:counts(*v) for k,v in role_counts.items()},'speaker_note':'speaker binding is supplied metadata, not a learned accuracy claim',
      'analysis_status':dict(Counter(p['analysis_status'] for p in predictions))}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--checkpoint',default='artifacts/phobert/smoke_heads');parser.add_argument('--split',choices=['train','validation','test_locked'],default='validation');parser.add_argument('--final-test',action='store_true');args=parser.parse_args()
    if args.split=='test_locked' and not args.final_test:raise ValueError('Test is locked; freeze model/config and explicitly use --final-test')
    REPORT.mkdir(parents=True,exist_ok=True);file=ROOT.parent/'data/phobert/splits'/f'{args.split}.jsonl';rows=load(file)
    runtime=Runtime(ROOT/args.checkpoint,allow_experimental=True);outputs=[]
    if args.split=='test_locked':
        lock=REPORT/'test_freeze.json';freeze={'checkpoint':runtime.manifest['heads_sha256'],'config':runtime.config,'data_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
        if lock.exists() and json.loads(lock.read_text())!=freeze:raise ValueError('Test freeze differs; cannot reuse final evaluation after changes')
        lock.write_text(json.dumps(freeze,indent=2),encoding='utf-8')
    for row in rows:
        result=runtime.predict(runtime_input(row));outputs.append(result)
        (REPORT/f'{args.split}_predictions.json').write_text(json.dumps([{'id':r.id,'prediction':p} for r,p in zip(rows,outputs)],ensure_ascii=False,indent=2),encoding='utf-8')
    # Only after predictions have been persisted do we consult expected labels.
    metrics=score(rows,outputs);oracle=[runtime.predict(runtime_input(row),oracle=row.spans) for row in rows]
    ablations={name:[runtime.predict(runtime_input(row),ablation=name) for row in rows] for name in ['no_relations','no_roles']}
    from backend.local_reasoning.legacy_engine import analyze_local
    from backend.local_reasoning.schema import CaseInput
    rules=[]
    for row in rows:
        result=analyze_local(CaseInput.model_validate(runtime_input(row)));rules.append({'id':row.id,'risk':result.assessment.risk_status,'elapsed_ms':result.elapsed_ms})
    baseline=[{**p,'assessment':{**p['assessment'],'risk_status':p['classifier_baseline']}} for p in outputs]
    rules_predictions=[{**p,'assessment':{**p['assessment'],'risk_status':r['risk']}} for p,r in zip(outputs,rules)]
    timings=[p['timings_ms']['total'] for p in outputs];sorted_times=sorted(timings)
    def concurrent(_):
        try:return runtime.predict(runtime_input(rows[0]))['analysis_status']
        except ModelBusy:return 'busy_rejected'
    with ThreadPoolExecutor(max_workers=3) as pool:concurrency=list(pool.map(concurrent,range(3)))
    report={'scope':'draft synthetic smoke; no independent gold or generalization claim','split':args.split,'n':len(rows),'predicted_spans':metrics,'oracle_spans':score(rows,oracle),
      'ablations':{name:score(rows,p) for name,p in ablations.items()},'four_class_classifier':score(rows,baseline)['risk'],'rules_baseline':rules,'rules_baseline_metrics':score(rows,rules_predictions)['risk'],
      'classifier_disagreements':sum(p['classifier_disagrees'] for p in outputs),
      'timings':{'cold_model_load_ms':runtime.cold_load_ms,'p50_ms':statistics.median(timings),'p95_nearest_rank_ms':sorted_times[max(0,__import__('math').ceil(.95*len(timings))-1)],'per_case_ms':timings,'rss_bytes':psutil.Process().memory_info().rss,'cuda_available':torch.cuda.is_available(),'max_vram_bytes':torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0,'concurrency_3':concurrency},
      'alignment':{'predicted_quotes':sum(len(p['graph']['spans']) for p in outputs),'invalid_quote_count':sum(sum(x['kind']=='span' for x in p['graph']['discarded']) for p in outputs)},
      'roles_note':'Research fixture mostly has one known speaker and an unknown recipient; mention/coreference quality is not established.',
      'explanation_review':'manual review pending; structural evidence checks are not proof of semantic correctness',
      'test':'not opened' if args.split!='test_locked' else 'explicit final research evaluation; draft synthetic labels are not independent gold'}
    (REPORT/f'{args.split}_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (REPORT/f'{args.split}_oracle_predictions.json').write_text(json.dumps(oracle,ensure_ascii=False,indent=2),encoding='utf-8')
    (REPORT/f'{args.split}_ablations.json').write_text(json.dumps(ablations,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'n':len(rows),'risk_macro_f1':metrics['risk']['macro_f1'],'span_action':metrics['spans']['action'],'timings':report['timings']},ensure_ascii=False))

if __name__=='__main__':main()
