"""Active original event-based decider, restored as default by user request.

The API caller still adds RAG and URL support. No external model calls.
"""
import hashlib
from itertools import product
import json
import time
from ..local_observation.text import normalize
from .extract import DATA,base,safety_extract,extract,fill_safety_fields,link_events
from .schema import Assessment,LocalResult
from .rule_schema import Rulebook,Templates
from .validation import annotation_errors
from ..settings import get_setting

PROHIBITED=['receipt_is_fake','trafficking_confirmed','kidnapping_proven','organ_removal_inferred',
            'identity_verified_by_system','safe_because_no_rag_match']
RANK={'clear':0,'need_context':1,'suspicious':2,'high':3}


def load_assets(include_context=None):
    book=Rulebook.model_validate_json((DATA/'rulebook.json').read_text(encoding='utf-8'))
    templates=Templates.model_validate_json((DATA/'templates.json').read_text(encoding='utf-8')).model_dump()['templates']
    if include_context is True or (include_context is None and get_setting('SCAMSHIELD_CONTEXT_ENABLED','1')=='1'):
        extra=Rulebook.model_validate_json((DATA/'context_rules.json').read_text(encoding='utf-8'))
        book.rules+=extra.rules;book.version+='+'+extra.version
        templates.update(Templates.model_validate_json((DATA/'context_templates.json').read_text(encoding='utf-8')).model_dump()['templates'])
    if len({r.rule_id for r in book.rules})!=len(book.rules):raise ValueError('duplicate rule')
    for r in book.rules:
        if not r.required_facts or r.explanation_template_id not in templates:raise ValueError('missing rule facts/template')
        if r.safety_urgency=='urgent':
            if r.conclusion!='high' or not all(f.temporal_states and set(f.temporal_states)<= {'ongoing','imminent'} for f in r.required_facts.values()):
                raise ValueError('urgency requires current danger constraints')
        for rel in r.required_relations:
            if not {rel.from_fact,rel.to_fact}<=r.required_facts.keys():raise ValueError('invalid fact slot')
    return book,templates


def match_fact(e,fact,spans):
    if fact.extractor_rule_ids and e.extractor_rule_id not in fact.extractor_rule_ids:return False
    if e.event_type not in fact.event_types or e.polarity not in fact.polarities or e.speech_role not in fact.speech_roles:return False
    if e.speech_role in ('quoted_warning','hypothetical','denial','unknown') or e.status=='unknown':return False
    if e.temporal_state in ('past','hypothetical') and e.temporal_state not in fact.temporal_states:return False
    if fact.temporal_states and e.temporal_state not in fact.temporal_states:return False
    if fact.attribution_kinds and e.attribution.kind not in fact.attribution_kinds:return False
    if fact.requires_authentication_meaning and e.event_type!='provide_credentials':
        text=normalize(' '.join(spans[x].quote for x in e.evidence_refs)).text
        if not any(t in text for t in ('otp','ma dang nhap','ma xac thuc','ma xac nhan')):return False
    return True


def excluded(rule,selected,a):
    scopes={e.scope_id for e in selected.values()}
    for exclusion in rule.exclusions:
        if exclusion=='later_payment_confirmed':
            neg={e.event_id for e in selected.values() if e.event_type=='receive_funds' and e.polarity=='negative'}
            by_id={e.event_id:e for e in a.events}
            if any(r.type=='state_update' and r.from_id in neg and r.to_id in by_id and by_id[r.to_id].event_type=='receive_funds'
                   and by_id[r.to_id].polarity=='positive' and by_id[r.to_id].temporal_state=='completed' for r in a.relations):return True
        elif exclusion=='documents_returnable':
            if all(e.event_type=='retain_identity_documents' for e in selected.values()) and any(e.event_type=='return_documents_available' and e.scope_id in scopes and e.polarity=='positive' and e.speech_role not in ('quoted_warning','hypothetical') for e in a.events):return True
        elif exclusion=='consent_without_coercion':
            if any(e.event_type=='consent_and_exit_available' and e.scope_id in scopes and e.polarity=='positive' for e in a.events):return True
    return False


def apply_rules(input,a,book,templates):
    issues=annotation_errors(input,a)
    if issues:raise ValueError('invalid annotations: '+','.join(issues))
    spans={s.span_id:s for s in a.spans};matches=[]
    for rule in book.rules:
        keys=list(rule.required_facts)
        pools=[[e for e in a.events if match_fact(e,rule.required_facts[key],spans)] for key in keys]
        for combo in product(*pools):
            chosen=dict(zip(keys,combo))
            if len({e.event_id for e in combo})!=len(combo):continue
            if rule.scope=='same_scope_same_affected_party':
                if len({e.scope_id for e in combo})!=1 or None in {e.scope_id for e in combo}:continue
                parties={e.affected_party_id for e in combo}
                if len(parties)!=1 or None in parties:continue
            used=[]
            for requirement in rule.required_relations:
                relation=next((r for r in a.relations if r.type==requirement.type and
                    r.from_id==chosen[requirement.from_fact].event_id and r.to_id==chosen[requirement.to_fact].event_id and r.status!='unknown'),None)
                if relation is None:break
                used.append(relation)
            else:
                if excluded(rule,chosen,a):continue
                refs=list(dict.fromkeys([x for e in combo for x in e.evidence_refs]+[x for r in used for x in r.evidence_refs]))
                if refs:matches.append((rule,refs))
    matches.sort(key=lambda x:(x[0].safety_urgency!='urgent',-RANK[x[0].conclusion],x[0].rule_id))
    if matches:
        selected=matches[0][0];tid=selected.explanation_template_id;template=templates[tid]
        risk=max((r.conclusion for r,_ in matches),key=lambda x:RANK[x]);urgency='urgent' if any(r.safety_urgency=='urgent' for r,_ in matches) else 'preventive'
        refs=list(dict.fromkeys(x for _,ids in matches for x in ids))
        urgent_refs=list(dict.fromkeys(x for r,ids in matches if r.safety_urgency=='urgent' for x in ids))
        questions=([selected.follow_up_question_template] if selected.follow_up_question_template else [])
        return Assessment(risk_status=risk,safety_urgency=urgency,supported_conclusions=list(dict.fromkeys(r.supported_conclusion for r,_ in matches)),
            evidence_refs=refs,urgency_evidence_refs=urgent_refs,applicable_rule_ids=list(dict.fromkeys(r.rule_id for r,_ in matches)),
            missing_information=[] if urgency=='urgent' else ['Danh tính hoặc toàn bộ sự việc chưa được hệ thống xác minh độc lập.'],
            follow_up_questions=questions,recommended_actions=template['recommended_actions'],explanation_template_id=tid,
            prohibited_conclusions=PROHIBITED,summary=template['summary'])
    active=[e for e in a.events if e.polarity=='positive' and e.speech_role not in ('quoted_warning','denial','hypothetical','unknown') and e.temporal_state not in ('past','hypothetical')]
    def verification_report_for(event):
        message_ids={spans[s].message_id for s in event.evidence_refs if spans[s].message_id}
        for c in input.context_facts:
            if not any(t in normalize(c.text).text for t in ('da goi','tu kiem tra','da doi chieu')):continue
            targets=set(c.applies_to_message_ids) or ({input.messages[0].id} if len(input.messages)==1 else set())
            if message_ids and message_ids<=targets:return True
        return False
    benign_types={'build_trust','offer_employment','invite_travel_or_meeting','identity_claim','relationship_claim','return_documents_available','free_to_leave','consent_and_exit_available'}
    benign=bool(active) and all(e.event_type in benign_types for e in active) and all(
        verification_report_for(e) for e in active if e.event_type in ('offer_employment','invite_travel_or_meeting'))
    paid=any(r.type=='before' and r.rule_id=='REL-REPORTED-PAYMENT-FIRST' for r in a.relations)
    if paid and all(e.event_type in ('receive_funds','handover_asset') for e in active):benign=True
    if any(e.event_type=='retain_identity_documents' for e in active) and any(e.event_type=='return_documents_available' for e in active) and all(e.event_type in ('retain_identity_documents','return_documents_available','free_to_leave') for e in active):benign=True
    clear=benign or (bool(a.events) and not active and all(e.speech_role!='unknown' and e.polarity!='uncertain' for e in a.events))
    tid='TPL-CLEAR' if clear else 'TPL-UNKNOWN';template=templates[tid]
    questions=[]
    if not clear:
        if any(e.event_type in ('offer_employment','invite_travel_or_meeting') for e in active):
            questions=['Bạn có biết người mời ngoài đời hoặc có thể xác minh công việc, địa điểm qua đầu mối độc lập không?',
                       'Họ có yêu cầu giữ bí mật, giao giấy tờ hoặc hạn chế liên lạc không?']
        elif any(e.event_type=='provide_code' for e in active):questions=['Dãy số đó được thông báo dùng để làm gì? Chỉ mô tả loại mã, không gửi mã thật.']
        else:questions=['Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.']
    return Assessment(risk_status='clear' if clear else 'need_context',safety_urgency='undetermined',supported_conclusions=[],
        evidence_refs=list(dict.fromkeys(s for e in a.events for s in e.evidence_refs)) if clear else [],applicable_rule_ids=[],
        missing_information=[] if clear else ['Thiếu hành động, quan hệ hoặc xác minh cần thiết trong phạm vi bộ luật.'],
        follow_up_questions=questions,recommended_actions=template['recommended_actions'],explanation_template_id=tid,
        prohibited_conclusions=PROHIBITED,summary=template['summary'])


def analyze_local(input):
    started=time.perf_counter();precheck=base(input);status='complete';path='full_local';frames=[];interpretation=None;timings={}
    context_enabled=get_setting('SCAMSHIELD_CONTEXT_ENABLED','1')=='1'
    asset_started=time.perf_counter()
    try:
        book,templates=load_assets();timings['asset_load']=(time.perf_counter()-asset_started)*1000
    except (ValueError,OSError,KeyError,TypeError):
        assessment=Assessment(risk_status=None,safety_urgency='undetermined',supported_conclusions=[],evidence_refs=[],applicable_rule_ids=[],
            missing_information=['Cấu hình suy luận chưa kiểm tra được.'],follow_up_questions=[],
            recommended_actions=['Nếu đang gặp nguy hiểm và có thể làm an toàn, tìm người tin cậy hoặc hỗ trợ khẩn cấp phù hợp; tránh đối đầu.'],
            explanation_template_id='TPL-ERROR',prohibited_conclusions=PROHIBITED,summary='Chưa kiểm tra được; không có kết luận ít rủi ro.')
        return LocalResult(analysis_status='error',input_sha256=hashlib.sha256(input.model_dump_json().encode()).hexdigest(),annotations=precheck,
            assessment=assessment,knowledge_status='not_checked',versions={'path':'config_error'},elapsed_ms=(time.perf_counter()-started)*1000)
    try:
        precheck_started=time.perf_counter()
        precheck=safety_extract(input)
        link_events(precheck)
        if annotation_errors(input,precheck):raise ValueError('invalid precheck')
        early=apply_rules(input,precheck,book,templates)
        timings['safety_precheck']=(time.perf_counter()-precheck_started)*1000
        if early.safety_urgency=='urgent':
            annotations=precheck;assessment=early;path='urgent_precheck'
            annotations.limitations.append('Ưu tiên tín hiệu khẩn đã có căn cứ; chưa chạy bộ trích toàn bộ cấu trúc còn lại. Các trường thiếu giữ unknown.')
        else:
            step_started=time.perf_counter()
            annotations=extract(input,precheck)
            if context_enabled:
                from .interaction import extract_interactions
                annotations,frames=extract_interactions(input,annotations)
                from .clause_context import extend_clause_context
                annotations=extend_clause_context(input,annotations,frames)
                from .semantic_events import extend_banking
                annotations=extend_banking(input,annotations)
                from .context_updates import apply_user_updates
                annotations=apply_user_updates(input,annotations)
                graph_enabled=get_setting('SCAMSHIELD_SEMANTIC_GRAPH_ENABLED','1')=='1'
                if graph_enabled:
                    from .semantic_graph import construct
                    annotations=construct(input,annotations)
                from .grounding import reconcile,check_coverage
                annotations,frames=reconcile(input,annotations,frames)
                annotations=check_coverage(input,annotations)
                from .fact_validation import sanitize
                relations_before={r.relation_id for r in annotations.relations}
                annotations,discarded=sanitize(input,annotations)
                annotations.graph_trace['relations_after_validation']=len(annotations.relations)
                annotations.graph_trace['validation_discarded_event_ids']=discarded
                annotations.graph_trace['validation_removed_relations']=[{'relation_id':rid,'reason':'dependency_validation_pruned'} for rid in sorted(relations_before-{r.relation_id for r in annotations.relations})]
                reached_limit=any('Đạt giới hạn' in x for x in annotations.limitations)
                annotations.grounding_trace['processing_limit_reached']=reached_limit
                if discarded or reached_limit or any('phân tích một phần' in x for x in annotations.limitations):status='partial'
                from .semantic_contract import refine
                annotations=refine(input,annotations)
                valid_events={e.event_id for e in annotations.events}
                frames=[f for f in frames if f.action_event_id in valid_events]
                annotations,semantic_discarded=sanitize(input,annotations)
                if semantic_discarded:status='partial'
                from .situation import prepare_interpretation
                try:
                    interpretation=prepare_interpretation(input,annotations,frames)
                    from .clause_context import add_role_and_salience
                    interpretation=add_role_and_salience(input,annotations,interpretation)
                    if graph_enabled:
                        from .semantic_graph import interpret
                        interpretation=interpret(annotations,interpretation)
                except (ValueError,RuntimeError,KeyError):
                    status='partial';interpretation=None
                    annotations.limitations.append('Tầng diễn giải chưa hoàn tất; chỉ giữ dữ kiện và luật có bằng chứng hợp lệ.')
            timings['local_extraction_interpretation']=(time.perf_counter()-step_started)*1000
            step_started=time.perf_counter()
            # Interpretation can propose relations. Validate them before any policy.
            from .fact_validation import sanitize
            annotations,_=sanitize(input,annotations)
            assessment=apply_rules(input,annotations,book,templates)
            timings['risk_assessment']=(time.perf_counter()-step_started)*1000
            if context_enabled:
                from .interaction import finalize_interactions
                assessment=finalize_interactions(assessment,frames)
                if interpretation:
                    from .situation import risk_assessor
                    assessment=risk_assessor(assessment,annotations,interpretation,frames)
                    from .clause_context import assess_contextual_choices
                    assessment=assess_contextual_choices(annotations,interpretation,assessment)
                    from .semantic_graph import assess,clarify
                    assessment=assess(assessment,interpretation)
                    assessment=clarify(annotations,interpretation,assessment)
                    from .grounding import finalize
                    assessment=finalize(input,annotations,interpretation,assessment)
                if status=='partial' and assessment.risk_status=='clear':
                    assessment.risk_status='need_context';assessment.summary='Chưa kiểm tra đầy đủ nội dung; cần làm rõ phần dữ kiện còn thiếu.'
                    assessment.follow_up_questions=['Bạn có thể bổ sung nguyên văn phần yêu cầu và bối cảnh chưa được kiểm tra không?']
                if annotations.grounding_trace.get('coverage_gaps'):
                    assessment.follow_up_questions=[]
                    assessment.missing_information=['Bộ phân tích chưa biểu diễn đầy đủ một dữ kiện đã có trong đầu vào.']
                    if assessment.risk_status not in ('high','suspicious'):assessment.summary='Hệ thống chưa xử lý đầy đủ một phần nội dung đã cung cấp; chưa có kết luận an toàn.'
                if annotations.grounding_trace.get('processing_limit_reached'):
                    assessment.follow_up_questions=[]
                    assessment.missing_information=['Bộ phân tích đạt giới hạn xử lý trong một lượt; một phần nội dung đã cung cấp chưa được kiểm tra đầy đủ.']
                    if assessment.risk_status not in ('high','suspicious'):assessment.summary='Bộ phân tích đạt giới hạn xử lý, chưa kiểm tra đầy đủ toàn bộ nội dung; chưa có kết luận an toàn.'
                if any(e.attribution.kind=='user_report' for e in annotations.events) and assessment.risk_status in ('clear','high'):
                    assessment.summary='Theo thông tin bạn bổ sung, '+assessment.summary[0].lower()+assessment.summary[1:]
                if not annotations.events and not annotations.grounding_trace.get('coverage_gaps'):
                    status='unsupported';assessment.summary='Bộ phân tích hiện chưa nhận diện được hành động trong nội dung đã cung cấp; chưa có kết luận an toàn.'
                    assessment.follow_up_questions=[]
                from .semantic_contract import assess as semantic_assess
                assessment,status=semantic_assess(input,annotations,assessment,status)
    except (ValueError,OSError,RuntimeError):
        status='error';annotations=precheck
        # Preserve a verified urgent safety signal even if the broader parser fails.
        try:assessment=apply_rules(input,precheck,book,templates)
        except ValueError:assessment=None;annotations=base(input)
        if assessment is None or assessment.safety_urgency!='urgent':
            t=templates['TPL-ERROR']
            assessment=Assessment(risk_status=None,safety_urgency='undetermined',supported_conclusions=[],evidence_refs=[],
                applicable_rule_ids=[],missing_information=['Phân tích chưa hoàn tất.'],follow_up_questions=[],recommended_actions=t['recommended_actions'],
                explanation_template_id='TPL-ERROR',prohibited_conclusions=PROHIBITED,summary=t['summary'])
    fill_safety_fields(annotations)
    annotations.answers_18.assessment.status='inferred' if status=='complete' or assessment.safety_urgency=='urgent' else 'unknown'
    annotations.answers_18.assessment.value.statements=[assessment.summary]
    annotations.answers_18.assessment.evidence_refs=assessment.evidence_refs
    annotations.answers_18.missing_information.missing_information=assessment.missing_information
    annotations.answers_18.missing_information.value.statements=assessment.follow_up_questions
    if interpretation:
        from .situation import summarize_18
        summarize_18(annotations,interpretation,assessment)
        from .semantic_graph import summarize
        summarize(annotations)
        from .grounding import project
        project(annotations)
    sources=[];knowledge_status='not_checked'
    if assessment.safety_urgency=='urgent':knowledge_status='not_checked_urgent'
    return LocalResult(analysis_status=status,input_sha256=hashlib.sha256(input.model_dump_json().encode()).hexdigest(),annotations=annotations,
        assessment=assessment,knowledge_status=knowledge_status,source_matches=sources,support_contacts=[],
        versions={'dataset':'scamshield-case-2.0','rulebook':book.version,'extractor':'safety-extraction-1.0','templates':'controlled-templates-1.0','path':path,
                  'context':'interaction-context-1.0' if context_enabled else 'disabled',
                  'interpretation':'local-situation-1.0' if context_enabled else 'disabled',
                  'semantic_contract':'semantic-contract-1.0' if context_enabled else 'disabled'},
        elapsed_ms=(time.perf_counter()-started)*1000,interaction_frames=frames,interpretation=interpretation,
        core_timings_ms={**timings,**(interpretation.stage_timings_ms if interpretation else {})})
