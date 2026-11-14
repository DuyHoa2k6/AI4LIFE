"""Validate a supplied v2 pilot only; never reads legacy validation/holdout."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import get_args
from backend.local_reasoning.schema import DatasetCase,EventType,RelationType,LocalResult
from backend.local_reasoning.rule_schema import Rulebook,Templates,ExtractionRules,LabelCatalog
# Pilot annotations were authored against the archived event rulebook. Keep that
# grounding check explicit; it must not silently relabel the dataset to fit a new engine.
from backend.local_reasoning.legacy_engine import load_assets,apply_rules
from backend.local_reasoning.engine import load_assets as load_fact_assets
from backend.local_reasoning.extract import DATA
from backend.local_reasoning.validation import dataset_errors
from backend.local_reasoning.splits import plan
from backend.retrieval import approved,read_records,SOURCES


def validate(path):
    cases=[DatasetCase.model_validate_json(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
    errors=dataset_errors(cases);book,templates=load_assets(include_context=False);load_fact_assets()
    ExtractionRules.model_validate_json((DATA/'extraction_rules.json').read_text(encoding='utf-8'))
    labels=LabelCatalog.model_validate_json((DATA/'labels.json').read_text(encoding='utf-8')).model_dump()
    if {x['id'] for x in labels['events']}!=set(get_args(EventType)):errors.append('event_dictionary_mismatch')
    if {x['id'] for x in labels['relations']}!=set(get_args(RelationType)):errors.append('relation_dictionary_mismatch')
    ids={c.metadata.case_id for c in cases}
    for rule in book.rules:
        if not rule.test_case_ids or not set(rule.test_case_ids)<=ids:errors.append('missing_or_unknown_rule_test_cases:'+rule.rule_id)
    for case in cases:
        if case.expected_assessment:
            computed=apply_rules(case.input,case.annotations,book,templates)
            expected=case.expected_assessment
            if (computed.risk_status,computed.safety_urgency)!=(expected.risk_status,expected.safety_urgency):errors.append('rule_grounding_mismatch:'+case.metadata.case_id)
            if not set(expected.applicable_rule_ids)<=set(computed.applicable_rule_ids):errors.append('unsupported_expected_rule:'+case.metadata.case_id)
    sources=read_records(SOURCES)
    report={'dataset':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cases':len(cases),
            'schema_version':'scamshield-case-2.0','grounding_reference':'archived event rulebook; new fact rules validated separately',
            'review_status':dict(Counter(c.metadata.review_status for c in cases)),
            'splits':dict(Counter(c.metadata.split for c in cases)),
            'candidate_sources':sum(s.get('review_status')!='approved' for s in sources),'eligible_approved_sources':sum(approved(s) for s in sources),
            'training_plan':plan(cases),'draft_split_dry_run':plan(cases,allow_draft=True),
            'errors':sorted(set(errors)),'passed':not errors,
            'not_measured':['semantic_duplicates','independent_human_label_correctness','independent_model_accuracy']}
    return report


if __name__=='__main__':
    canonical=DATA/json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))['canonical_pilot']
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,default=canonical);p.add_argument('--output',type=Path)
    args=p.parse_args();r=validate(args.dataset)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k not in ('training_plan','draft_split_dry_run')},ensure_ascii=True,indent=2))
    raise SystemExit(not r['passed'])
