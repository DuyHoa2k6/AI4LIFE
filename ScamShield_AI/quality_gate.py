"""Offline acceptance gate. No model calls, no implicit independent-evaluation claim."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def wilson_lower(successes, total):
    if not total: return 0.
    z=1.959963984540054
    p=successes/total
    return (p+z*z/(2*total)-z*math.sqrt(p*(1-p)/total+z*z/(4*total*total)))/(1+z*z/total)


def score(predictions, references, target=.98, minimum=500, independent_attested=False):
    ids=[c['id'] for c in references['cases']]
    observed=[r['id'] for r in predictions]
    if len(ids)!=len(set(ids)) or len(observed)!=len(set(observed)) or set(observed)-set(ids):
        raise ValueError('Duplicate or unexpected case IDs')
    by_id={r['id']:r for r in predictions}
    correct=errors=tp=fp=fn=0
    groups=Counter();group_correct=Counter()
    for c in references['cases']:
        allowed=set(c['acceptable'])
        if not allowed or ('high' in allowed and len(allowed)>1):
            raise ValueError('Reference needs an unambiguous high/non-high judgment')
        r=by_id.get(c['id'],{})
        ok=r.get('executed') and r.get('http_status')==200
        data=r.get('response',{})
        prediction=data.get('risk_status') if ok else None
        evidence=r.get('evidence_check',{})
        checked=(evidence.get('quote_count') is not None and
                 evidence.get('quote_count')==evidence.get('exact_quotes') and
                 evidence.get('speaker_reference_errors')==0)
        matched=bool(ok and checked and prediction in allowed)
        groups[c['group']]+=1
        correct+=matched;group_correct[c['group']]+=matched
        errors+=not ok
        expected_high='high' in allowed
        if prediction in ('high','verified_match'):
            if expected_high and checked: tp+=1
            else: fp+=1
        if expected_high and not (prediction=='high' and checked): fn+=1
    total=len(ids)
    checks={'minimum_samples':total>=minimum,
            'all_four_groups':all(groups[g]>=50 for g in ('scam','normal','suspicious','uncertain')),
            'independent_review_attested':independent_attested,
            'overall_95ci_above_target':wilson_lower(correct,total)>target,
            'high_precision_95ci_above_target':wilson_lower(tp,tp+fp)>target,
            'high_recall_95ci_above_target':wilson_lower(tp,tp+fn)>target}
    return {'target':target,'n':total,'correct_status_and_exact_evidence':correct,'errors_or_not_run':errors,
        'overall_rate':correct/total if total else None,'overall_95ci_lower':wilson_lower(correct,total),
        'high':{'TP':tp,'FP':fp,'FN_including_errors':fn,
                'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None},
        'group_counts':dict(groups),'group_correct':dict(group_correct),
        'checks':checks,'passed':all(checks.values()),
        'limits':'Review manifest is an operator attestation, not proof of independence. Quote matching does not grade semantic completeness or all eight answers. No generalization guarantee.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--predictions',type=Path,required=True)
    parser.add_argument('--references',type=Path,required=True)
    parser.add_argument('--review-manifest',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Output exists; choose a new report path')
    predictions=json.loads(args.predictions.read_text(encoding='utf-8'))
    raw=args.references.read_bytes()
    references=json.loads(raw.decode('utf-8-sig'))
    attested=False
    if args.review_manifest:
        m=json.loads(args.review_manifest.read_text(encoding='utf-8'))
        attested=(m.get('independent') is True and
                  len(set(m.get('reviewers',[])))>=2 and
                  m.get('references_sha256')==hashlib.sha256(raw).hexdigest())
    result=score(predictions,references,independent_attested=attested)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Acceptance gate:', 'PASS' if result['passed'] else 'NOT ESTABLISHED', 'n=',result['n'])
    raise SystemExit(0 if result['passed'] else 2)
