import argparse,json
from pathlib import Path
import yaml
from .io import dump,digest

def compare(baseline,candidate,acceptance):
    b,c=baseline['all'],candidate['all'];checks={}
    checks['main_improvement']=None if b['end_to_end_supported_success_rate'] is None or c['end_to_end_supported_success_rate'] is None else c['end_to_end_supported_success_rate']-b['end_to_end_supported_success_rate']>=acceptance['minimum_absolute_improvement']
    checks['protect_clear']=c['clear_as_high']-b['clear_as_high']<=acceptance['maximum_clear_as_high_increase']
    checks['protect_high']=c['high_missed']-b['high_missed']<=acceptance['maximum_high_miss_increase']
    checks['coverage']=None if b['coverage'] is None or c['coverage'] is None else b['coverage']-c['coverage']<=acceptance['maximum_supported_coverage_drop']
    checks['sample_count']=c['n']>=acceptance['minimum_evaluable_cases']
    checks['latency']=None if candidate['timings']['p95_nearest_rank_ms'] is None else candidate['timings']['p95_nearest_rank_ms']<=acceptance['maximum_p95_seconds']*1000
    checks['ram']=candidate['timings']['rss_bytes']<=acceptance['maximum_rss_gib']*1024**3
    validation=candidate.get('by_split',{}).get('validation')
    checks['reviewed_validation']=True if validation and validation['n']>0 and not validation['draft_count'] and not validation['ambiguous_count'] else None
    independent=candidate['independent_holdout']
    checks['independent_holdout']=True if independent.get('available') and independent.get('score') is not None and independent.get('n',0)>0 else None
    for domain in acceptance['protected_domains']:
        bd,cd=baseline['by_domain'].get(domain),candidate['by_domain'].get(domain)
        if bd is None or cd is None:
            checks['protected_domain:'+domain]=None;continue
        checks['protected_domain:'+domain]=(cd['clear_as_high']-bd['clear_as_high']<=acceptance['maximum_clear_as_high_increase'] and cd['high_missed']-bd['high_missed']<=acceptance['maximum_high_miss_increase'] and bd['coverage'] is not None and cd['coverage'] is not None and bd['coverage']-cd['coverage']<=acceptance['maximum_supported_coverage_drop'])
    changes={domain:{'baseline':baseline['by_domain'][domain]['macro_f1'],'candidate':candidate['by_domain'][domain]['macro_f1'],
      'supported_before':baseline['by_domain'][domain]['supported_success_count'],'supported_after':candidate['by_domain'][domain]['supported_success_count']} for domain in baseline['by_domain']}
    return {'accepted':all(v is True for v in checks.values()),'checks':checks,'undefined_block_promotion':[k for k,v in checks.items() if v is None],
      'selected_model':'baseline','candidate_status':'not_promoted','per_domain':changes,'reason':'Only predeclared conditions may select a new version; drafts and absent holdout cannot silently pass.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--acceptance',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    a=yaml.safe_load(args.acceptance.read_text(encoding='utf-8'));b=json.loads((args.baseline/'metrics.json').read_text());c=json.loads((args.candidate/'metrics.json').read_text())
    mb=json.loads((args.baseline/'run_manifest.json').read_text());mc=json.loads((args.candidate/'run_manifest.json').read_text())
    if mb['datasets']!=mc['datasets'] or mb['acceptance_sha256']!=mc['acceptance_sha256'] or mb['acceptance_sha256']!=digest(args.acceptance):raise SystemExit('Incomparable data/acceptance versions')
    result=compare(b,c,a);result['acceptance_sha256']=digest(args.acceptance)
    if result['accepted']:result['selected_model']='candidate';result['candidate_status']='accepted_research'
    dump(args.out,result);print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['accepted'] else 2)

if __name__=='__main__':main()
