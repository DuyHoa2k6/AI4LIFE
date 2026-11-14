"""Default: original verified event rules plus RAG/URL enrichment in the caller.

The experimental fact pipeline below is disabled by default. It is retained only
for explicit comparison with SCAMSHIELD_REASONER=facts.
"""
import hashlib
import json
from functools import lru_cache
import time
from typing import get_args
from ..settings import get_setting,LocalConfigError
from .extract import DATA,base,safety_extract,extract,fill_safety_fields,link_events
from .schema import Assessment,LocalResult,RelationType
from .fact_schema import FactRulebook,FactTrace,Truth
from .facts import build_facts
from .fact_decision import assess,PROHIBITED
from .fact_validation import sanitize
from .semantic_events import extend_banking
from .rule_schema import Templates


@lru_cache(maxsize=4)
def _assets(rule_signature,template_signature,catalog_signature):
    book=FactRulebook.model_validate_json((DATA/'fact_rules.json').read_text(encoding='utf-8'))
    templates=Templates.model_validate_json((DATA/'fact_templates.json').read_text(encoding='utf-8')).model_dump()['templates']
    catalog=json.loads((DATA/'fact_catalog.json').read_text(encoding='utf-8'))
    known={f['type'] for f in catalog['facts']};relations=set(get_args(RelationType))
    for r in book.rules:
        if any(not set(c.fact_types)<=known for c in r.required_conditions.values()):raise ValueError('Unknown fact type')
        if any(rel.type not in relations for rel in r.required_relations):raise ValueError('Unknown relation type')
        if r.explanation_template not in templates:raise ValueError('Missing explanation template')
        if r.safety_urgency=='urgent' and (r.conclusion!='high' or any(not c.temporal_states or not set(c.temporal_states)<={'ongoing','imminent'} for c in r.required_conditions.values())):
            raise ValueError('Urgent rule requires explicit current danger')
    return book,templates


def load_assets():
    paths=[DATA/'fact_rules.json',DATA/'fact_templates.json',DATA/'fact_catalog.json']
    return _assets(*[(p.stat().st_mtime_ns,p.stat().st_size) for p in paths])


def apply_rules(input,a,book,templates):
    store=build_facts(input,a)
    return assess(store,book,templates)[0]


def analyze_local(input):
    mode=get_setting('SCAMSHIELD_REASONER','legacy')
    if mode=='phobert':
        from .phobert_adapter import analyze
        return analyze(input)
    if mode=='legacy':
        from .legacy_engine import analyze_local as previous
        result=previous(input);result.versions['reasoner']='legacy-event-rules';return result
    if mode!='facts':raise LocalConfigError('Unknown local reasoner mode')
    started=time.perf_counter();precheck=base(input);annotations=precheck;status='complete';path='full_local'
    timings={'extraction':0.,'fact_build':0.,'rule_evaluation':0.};store=None;evaluations=[];discarded=[]
    def decide(a,urgent_only=False):
        nonlocal store,evaluations
        t=time.perf_counter();store=build_facts(input,a);timings['fact_build']+=(time.perf_counter()-t)*1000
        selected=book.model_copy(update={'rules':[r for r in book.rules if r.safety_urgency=='urgent']}) if urgent_only else book
        t=time.perf_counter();assessment,evaluations=assess(store,selected,templates);timings['rule_evaluation']+=(time.perf_counter()-t)*1000
        return assessment
    try:book,templates=load_assets()
    except (ValueError,OSError,KeyError,TypeError):
        return LocalResult(analysis_status='error',input_sha256=hashlib.sha256(input.model_dump_json().encode()).hexdigest(),
            annotations=precheck,assessment=Assessment(risk_status=None,safety_urgency='undetermined',supported_conclusions=[],evidence_refs=[],
            applicable_rule_ids=[],missing_information=['Cấu hình suy luận chưa kiểm tra được.'],follow_up_questions=[],
            recommended_actions=['Nếu có nguy hiểm hiện tại, ưu tiên tìm hỗ trợ an toàn.'],explanation_template_id='TPL-ERROR',
            prohibited_conclusions=PROHIBITED,summary='Chưa kiểm tra được; không có kết luận ít rủi ro.'),knowledge_status='not_checked',
            versions={'path':'config_error','reasoner':'three-valued-facts-1.0'},elapsed_ms=(time.perf_counter()-started)*1000)
    try:
        t=time.perf_counter();precheck=safety_extract(input);link_events(precheck);precheck,bad=sanitize(input,precheck)
        discarded.extend(bad);timings['extraction']+=(time.perf_counter()-t)*1000
        early=decide(precheck,urgent_only=True) if precheck.events else None
        if early is not None and early.safety_urgency=='urgent':
            annotations=precheck;assessment=early;path='urgent_precheck'
            annotations.limitations.append('Ưu tiên tín hiệu khẩn đã có căn cứ; chưa chạy bộ trích toàn bộ cấu trúc còn lại. Các trường thiếu giữ unknown.')
        else:
            t=time.perf_counter();annotations=extend_banking(input,extract(input,precheck));annotations,bad=sanitize(input,annotations)
            discarded.extend(bad);timings['extraction']+=(time.perf_counter()-t)*1000
            assessment=decide(annotations)
        if discarded or any('phân tích một phần' in x for x in annotations.limitations) or (store and store.by_id['quality:coverage'].value is Truth.FALSE):status='partial'
    except (ValueError,OSError,RuntimeError,KeyError):
        status='error';annotations=precheck
        try:assessment=decide(precheck)
        except (ValueError,KeyError):assessment=None;annotations=base(input);store=None;evaluations=[]
        if assessment is None or assessment.safety_urgency!='urgent':
            t=templates['TPL-ERROR'];assessment=Assessment(risk_status=None,safety_urgency='undetermined',supported_conclusions=[],evidence_refs=[],
                applicable_rule_ids=[],missing_information=['Phân tích chưa hoàn tất.'],follow_up_questions=[],recommended_actions=t['recommended_actions'],
                explanation_template_id='TPL-ERROR',prohibited_conclusions=PROHIBITED,summary=t['summary'])
    fill_safety_fields(annotations)
    annotations.answers_18.assessment.status='inferred' if assessment.risk_status is not None else 'unknown'
    annotations.answers_18.assessment.value.statements=[assessment.summary]
    annotations.answers_18.assessment.evidence_refs=assessment.evidence_refs
    annotations.answers_18.missing_information.missing_information=assessment.missing_information
    annotations.answers_18.missing_information.value.statements=assessment.follow_up_questions
    trace=FactTrace(facts=store.facts,rule_evaluations=evaluations,conflicts=store.conflicts,discarded_event_ids=discarded,
                    stage_timings_ms=timings) if store else None
    return LocalResult(analysis_status=status,input_sha256=hashlib.sha256(input.model_dump_json().encode()).hexdigest(),annotations=annotations,
        assessment=assessment,knowledge_status='not_checked_urgent' if assessment.safety_urgency=='urgent' else 'not_checked',
        versions={'dataset':'scamshield-case-2.0','rulebook':book.version,'extractor':'python-rules-plus-bank-context-1.0',
                  'templates':'controlled-templates-1.1','path':path,'reasoner':'three-valued-facts-1.0'},
        elapsed_ms=(time.perf_counter()-started)*1000,fact_trace=trace,core_timings_ms=timings)
