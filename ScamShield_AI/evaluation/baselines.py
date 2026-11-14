"""Rules and the already-trained four-class head; no new model training."""
import argparse,json,time,copy
from pathlib import Path
from backend.local_reasoning.legacy_engine import analyze_local
from backend.local_reasoning.schema import CaseInput
from .io import load,jsonl,dump
from .schema import runtime_input
from .metrics import diagnose,aggregate

def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',type=Path,action='append',required=True);p.add_argument('--run',type=Path,required=True);args=p.parse_args()
    rows=[r for f in args.cases for r in load(f)];saved={r['case_id']:r for r in [json.loads(x) for x in (args.run/'predictions.jsonl').read_text(encoding='utf-8').splitlines()]}
    outputs=[]
    for row in rows:
        t=time.perf_counter()
        try:
            result=analyze_local(CaseInput.model_validate(runtime_input(row)));risk=result.assessment.risk_status;status=result.analysis_status
        except Exception as exc:risk=None;status='error'
        outputs.append({'case_id':row.case_id,'risk_status':risk,'analysis_status':status,'core_ms':(time.perf_counter()-t)*1000})
    jsonl(args.run/'rules_baseline_predictions.jsonl',outputs)
    rules=[];classifier=[]
    for row,r in zip(rows,outputs):
        original=saved[row.case_id]['prediction'];rule_pred=copy.deepcopy(original);rule_pred['assessment']['risk_status']=r['risk_status'];rule_pred['analysis_status']=r['analysis_status'];rules.append(diagnose(row,rule_pred))
        head=copy.deepcopy(original);head['assessment']['risk_status']=original.get('classifier_baseline');classifier.append(diagnose(row,head))
    # Only risk summaries are meaningful: neither comparator is credited with
    # the structured pipeline's intermediate facts or explanation quality.
    keep=['n','confusion_matrix','unclassified_by_reference','per_risk','macro_f1','macro_labels','coverage','clear_as_high','high_missed']
    report={name:{k:aggregate(values)[k] for k in keep} for name,values in [('rules_core',rules),('phobert_four_class_head',classifier)]}
    report['scope']='Risk-only comparators; no structured-success credit. Rule core excludes retrieval/URL.'
    dump(args.run/'risk_baselines.json',report);print(json.dumps({k:v['macro_f1'] for k,v in report.items() if isinstance(v,dict)}))

if __name__=='__main__':main()
