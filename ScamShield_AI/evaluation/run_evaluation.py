"""Real local inference -> persisted predictions -> reference scoring."""
import argparse,copy,importlib.util,json,math,os,random,statistics,time
from pathlib import Path
from datetime import datetime,timezone
import psutil,yaml
from ml.phobert.inference import Runtime
from .schema import oracle_graph,runtime_input
from .io import load,dump,jsonl,digest,validate_splits
from .metrics import diagnose,aggregate
ROOT=Path(__file__).resolve().parents[1]

def preflight_budget(out,acceptance,model_id,policy_id,calls):
    prior=[];elapsed=0.
    for path in out.parent.glob('*/run_manifest.json'):
        item=json.loads(path.read_text(encoding='utf-8'));prior.append(item)
        metric=path.parent/'metrics.json'
        if metric.exists():elapsed+=json.loads(metric.read_text())['timings']['total_wall_seconds']
    if len(prior)>=acceptance['max_iterations_including_baseline']:raise ValueError('Iteration budget exhausted')
    configs={(r['model_version'],r['policy_file_sha256']) for r in prior}
    if (model_id,policy_id) not in configs and len(configs)>=acceptance['max_configurations']:raise ValueError('Configuration budget exhausted')
    if sum(r['planned_inference_calls'] for r in prior)+calls>acceptance['max_inference_requests']:raise ValueError('Cumulative inference budget exhausted')
    if elapsed>=acceptance['max_wall_seconds']:raise ValueError('Cumulative wall-time budget exhausted')
    return acceptance['max_wall_seconds']-elapsed

def frozen_policy(path):
    spec=importlib.util.spec_from_file_location('ml.phobert._evaluation_baseline',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.verify_graph,module.assess

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cases',type=Path,action='append',required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path,default=ROOT/'artifacts/phobert/smoke_heads');parser.add_argument('--acceptance',type=Path,default=ROOT/'evaluation/configs/acceptance.yaml')
    parser.add_argument('--policy',choices=['baseline','candidate'],default='baseline');parser.add_argument('--baseline-policy',type=Path,required=True);parser.add_argument('--oracle-spans',action='store_true');args=parser.parse_args()
    if args.out.exists() and (args.out/'predictions.jsonl').exists():raise SystemExit('Run output already exists; use a new directory')
    rows=[r for path in args.cases for r in load(path)];validate_splits(rows)
    if any(r.split=='locked' for r in rows):raise SystemExit('Use locked_runner for independent custodian inputs, not the public harness')
    acceptance=yaml.safe_load(args.acceptance.read_text(encoding='utf-8'));args.out.mkdir(parents=True,exist_ok=True)
    calls=len(rows)*(2 if args.oracle_spans else 1)
    if calls>acceptance['max_inference_requests']:raise SystemExit('Inference request budget exceeded before run')
    policy_path=ROOT/'ml/phobert/policy_v2.py' if args.policy=='candidate' else args.baseline_policy
    remaining=preflight_budget(args.out,acceptance,digest(args.checkpoint/'heads.pt'),digest(policy_path),calls)
    acceptance['max_wall_seconds']=remaining
    started=time.perf_counter();runtime=Runtime(args.checkpoint,allow_experimental=True)
    verify,assess=frozen_policy(args.baseline_policy)
    if args.policy=='candidate':
        from ml.phobert.policy_v2 import verify as verify_candidate,assess as assess_candidate
        verify,assess=verify_candidate,assess_candidate
    manifest={'run_id':args.out.name,'utc':datetime.now(timezone.utc).isoformat(),'policy':args.policy,
      'checkpoint':str(args.checkpoint.resolve()),'model_version':runtime.manifest['heads_sha256'],
      'dataset_version':'evaluation-case-1.0','datasets':{str(p):digest(p) for p in args.cases},'acceptance_sha256':digest(args.acceptance),
      'baseline_policy_sha256':digest(args.baseline_policy),'policy_file_sha256':digest(ROOT/'ml/phobert/policy_v2.py') if args.policy=='candidate' else digest(args.baseline_policy),
      'label_mapping':digest(args.checkpoint/'labels.json'),'preprocessing':runtime.manifest['preprocessing_sha256'],'seed':acceptance['seed'],
      'n':len(rows),'planned_inference_calls':calls,'max_wall_seconds':acceptance['max_wall_seconds'],'scope':'public_draft; no independent holdout',
      'reviewed_count':sum(r.review_status!='draft' for r in rows),'runtime_expected_fields':'none; messages whitelist only'}
    dump(args.out/'run_manifest.json',manifest)
    records=[]
    with (args.out/'predictions.jsonl').open('w',encoding='utf-8') as stream:
        for row in rows:
            if time.perf_counter()-started>acceptance['max_wall_seconds']:raise SystemExit('Wall-time budget exceeded; partial predictions retained')
            payload=runtime_input(row);t=time.perf_counter()
            try:
                if row.input.context is not None:raise NotImplementedError('Explicit context channel is not supported by this research checkpoint')
                predicted=runtime.predict(payload,include_debug=True)
                raw=predicted['debug']['pre_verification_graph']
                graph=verify(payload['messages'],copy.deepcopy(raw));a=assess(graph)
                predicted.update(graph=graph,assessment=a,analysis_status=a['analysis_status'])
            except Exception as exc:
                predicted={'analysis_status':'unsupported' if isinstance(exc,NotImplementedError) else 'error','assessment':{'risk_status':None,'rules':[],'questions':[]},'graph':{'spans':[],'events':[],'relations':[],'limitations':['inference_error']},'error_type':type(exc).__name__}
            record={'case_id':row.case_id,'input_sha256':__import__('hashlib').sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'prediction':predicted,'total_ms':(time.perf_counter()-t)*1000}
            records.append(record);stream.write(json.dumps(record,ensure_ascii=False)+'\n');stream.flush()
    # Expected fields are only consulted after every E2E prediction is on disk.
    diagnostics=[];oracles=[];oracle_spans=[]
    for row,record in zip(rows,records):
        if time.perf_counter()-started>acceptance['max_wall_seconds']:
            dump(args.out/'incomplete_run.json',{'reason':'wall_time_budget','planned_cases':len(rows),'e2e_predictions_saved':len(records),'oracle_cases_completed':len(oracles)})
            raise SystemExit(3)
        d=diagnose(row,record['prediction']);diagnostics.append(d)
        gold=oracle_graph(row);graph=verify(runtime_input(row)['messages'],copy.deepcopy(gold));a=assess(graph)
        oracles.append({'case_id':row.case_id,'scope':'ORACLE_ANNOTATIONS_NOT_PRODUCT','prediction':{'graph':graph,'assessment':a,'analysis_status':a['analysis_status']}})
        if args.oracle_spans:
            try:
                if row.input.context is not None:raise NotImplementedError('Context is outside the trained input contract')
                p=runtime.predict(runtime_input(row),oracle=row.expected.spans,include_debug=True)
                graph=verify(runtime_input(row)['messages'],copy.deepcopy(p['debug']['pre_verification_graph']));a=assess(graph);p.update(graph=graph,assessment=a,analysis_status=a['analysis_status'])
                p['oracle_skipped_anchor_count']=sum(s.label=='action' for s in row.expected.spans)-len(p['debug']['pre_verification_graph']['spans'])
            except Exception as exc:p={'analysis_status':'error','assessment':{'risk_status':None},'graph':{'spans':[],'events':[],'relations':[]},'error_type':type(exc).__name__}
            oracle_spans.append({'case_id':row.case_id,'scope':'ORACLE_SPANS_NOT_PRODUCT','prediction':p})
    jsonl(args.out/'case_diagnostics.jsonl',diagnostics);jsonl(args.out/'oracle_predictions.jsonl',oracles)
    if oracle_spans:jsonl(args.out/'oracle_span_predictions.jsonl',oracle_spans)
    errors=[]
    for row,d in zip(rows,diagnostics):
        for error in d['errors']:errors.append({'case_id':row.case_id,'model_version':manifest['model_version'],'dataset_version':manifest['dataset_version'],**error})
    jsonl(args.out/'error_log.jsonl',errors)
    values=[r['total_ms'] for r in records];ordered=sorted(values)
    result={'all':aggregate(diagnostics),'by_domain':{domain:aggregate([d for d in diagnostics if d['domain']==domain]) for domain in sorted({r.domain for r in rows})},
      'by_split':{split:aggregate([d for d in diagnostics if d['split']==split]) for split in sorted({r.split for r in rows})},
      'oracle_annotations':aggregate([diagnose(r,p['prediction']) for r,p in zip(rows,oracles)]),
      'oracle_model_spans':aggregate([diagnose(r,p['prediction']) for r,p in zip(rows,oracle_spans)]) if oracle_spans else None,
      'timings':{'n':len(values),'p50_ms':statistics.median(values) if values else None,'p95_nearest_rank_ms':ordered[math.ceil(.95*len(ordered))-1] if ordered else None,
        'cold_model_load_ms':runtime.cold_load_ms,'rss_bytes':psutil.Process().memory_info().rss,'vram_bytes':0,'concurrency':1,'input_codepoints':[sum(len(m.text) for m in r.input.messages) for r in rows],
        'total_wall_seconds':time.perf_counter()-started},
      'review_status':'diagnostic only; all automated semantic judgments need independent review',
      'count_error_types':dict(__import__('collections').Counter(e['error_type'] for e in errors)),
      'independent_holdout':{'available':False,'score':None},'training_performed':False}
    # Family bootstrap on public drafts only, never portrayed as population accuracy.
    rng=random.Random(acceptance['seed']);families=sorted({d['family_id'] for d in diagnostics});samples=[]
    for _ in range(acceptance['bootstrap_family_repetitions']):
        chosen=rng.choices(families,k=len(families));sample=[d for family in chosen for d in diagnostics if d['family_id']==family]
        samples.append(aggregate(sample)['end_to_end_supported_success_rate'])
    samples=sorted(x for x in samples if x is not None)
    result['public_family_bootstrap_95']=[samples[int(.025*(len(samples)-1))],samples[int(.975*(len(samples)-1))]] if samples else None
    dump(args.out/'metrics.json',result)
    (args.out/'report.md').write_text('# '+args.out.name+'\n\nPublic draft diagnostic; not a blind holdout.\n\n'+f"Cases: {len(rows)}. Risk Macro-F1: {result['all']['macro_f1']}. Supported successes: {result['all']['supported_success_count']}. Right level, wrong basis: {result['all']['right_level_wrong_basis']}.\n\nFull layer results: metrics.json, case_diagnostics.jsonl, error_log.jsonl.\n",encoding='utf-8')
    print(json.dumps({'run':str(args.out),'n':len(rows),'macro_f1':result['all']['macro_f1'],'supported_success_count':result['all']['supported_success_count'],'oracle_risk_macro_f1':result['oracle_annotations']['macro_f1'],'wall_seconds':result['timings']['total_wall_seconds']}))

if __name__=='__main__':main()
