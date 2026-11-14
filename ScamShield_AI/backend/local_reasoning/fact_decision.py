"""Reference Enum reasoner. Only typed facts/relations are evaluated here; no raw text."""
from itertools import product
from .fact_schema import Truth,conjunction,RuleEvaluation
from .schema import Assessment

RANK={'clear':0,'need_context':1,'suspicious':2,'high':3}
PROHIBITED=['receipt_is_fake','trafficking_confirmed','kidnapping_proven','organ_removal_inferred',
            'identity_verified_by_system','safe_because_no_rag_match']
INACTIVE={'quoted_warning','hypothetical','denial','unknown'}


def condition_state(fact,condition,store):
    if fact.superseded_by is not None:return Truth.FALSE
    attrs=fact.attributes
    if fact.event_id is None:return Truth.UNKNOWN
    role=attrs.get('speech_role','unknown')
    if role in ('quoted_warning','hypothetical','denial'):return Truth.FALSE
    if role=='unknown' or attrs.get('status')=='unknown':return Truth.UNKNOWN
    if role not in condition.speech_roles:return Truth.FALSE
    temporal=attrs.get('temporal_state','unknown')
    if temporal in ('past','hypothetical') and temporal not in condition.temporal_states:return Truth.FALSE
    if condition.temporal_states and temporal not in condition.temporal_states:
        return Truth.UNKNOWN if temporal=='unknown' else Truth.FALSE
    if condition.attribution_kinds and attrs.get('attribution_kind') not in condition.attribution_kinds:return Truth.FALSE
    if fact.value is Truth.UNKNOWN:return Truth.UNKNOWN
    if fact.value is not condition.value:return Truth.FALSE
    if condition.authentication_meaning is not None:
        auth=store.by_id.get(fact.fact_id+':auth')
        if auth is None or auth.value is Truth.UNKNOWN:return Truth.UNKNOWN
        if auth.value is not condition.authentication_meaning:return Truth.FALSE
    return Truth.TRUE


def exclusion_state(rule,selected,store):
    states=[]
    scopes={f.scope_id for f in selected.values()}
    for exclusion in rule.exclusion_conditions:
        if exclusion=='later_payment_confirmed':
            states.append(Truth.TRUE if any(f.superseded_by for f in selected.values() if f.fact_type=='payment_confirmed') else Truth.UNKNOWN)
        else:
            kind='return_documents_available' if exclusion=='documents_returnable' else 'consent_and_exit_available'
            parties={f.attributes.get('affected_party') for f in selected.values()}
            applies=any(f.scope_id in scopes and f.attributes.get('affected_party') in parties and f.value is Truth.TRUE and f.attributes.get('speech_role') not in INACTIVE
                        for f in store.by_type[kind])
            if exclusion=='documents_returnable' and not all(f.fact_type=='retain_identity_documents' for f in selected.values()):
                states.append(Truth.FALSE)
            else:states.append(Truth.TRUE if applies else Truth.UNKNOWN)
    if any(s is Truth.TRUE for s in states):return Truth.TRUE
    if any(s is Truth.UNKNOWN for s in states):return Truth.UNKNOWN
    return Truth.FALSE


def evaluate_rule(rule,store):
    pools={};slot_states=[];all_refs=[];missing=[]
    for slot,condition in rule.required_conditions.items():
        candidates=store.candidates(condition.fact_types)
        evaluated=[(f,condition_state(f,condition,store)) for f in candidates]
        pools[slot]=[f for f,state in evaluated if state is Truth.TRUE]
        all_refs.extend(f.fact_id for f,_ in evaluated)
        state=Truth.TRUE if pools[slot] else Truth.UNKNOWN if not evaluated or any(s is Truth.UNKNOWN for _,s in evaluated) else Truth.FALSE
        slot_states.append(state)
        if state is Truth.UNKNOWN:missing.append(slot)
    state=conjunction(slot_states)
    if state is not Truth.TRUE:
        return RuleEvaluation(rule_id=rule.rule_id,version=rule.version,status='NOT_MATCHED' if state is Truth.FALSE else 'UNDETERMINED',
            fact_refs=list(dict.fromkeys(all_refs)),missing_information=missing),[]
    unknown_relation=False;excluded=False
    keys=list(pools)
    for combination in product(*(pools[k] for k in keys)):
        selected=dict(zip(keys,combination))
        if len({f.event_id for f in combination})!=len(combination):continue
        if rule.scope=='same_scope_same_affected_party':
            scope={f.scope_id for f in combination};party={f.attributes.get('affected_party') for f in combination}
            if len(scope)!=1 or None in scope or len(party)!=1 or '' in party:continue
        relation_facts=[]
        for requirement in rule.required_relations:
            relation=store.relations.get((requirement.type,selected[requirement.from_fact].event_id,selected[requirement.to_fact].event_id))
            if relation is None or relation.value is Truth.UNKNOWN:unknown_relation=True;break
            relation_facts.append(relation)
        else:
            exclusion=exclusion_state(rule,selected,store)
            if exclusion is Truth.TRUE:excluded=True;continue
            if exclusion is Truth.UNKNOWN and rule.unknown_exclusion_policy=='undetermined':unknown_relation=True;continue
            used=list(combination)+relation_facts
            # Explicit authentication predicates are dependencies too, not hidden text checks.
            for slot,c in rule.required_conditions.items():
                if c.authentication_meaning is not None:
                    used.append(store.by_id[selected[slot].fact_id+':auth'])
            return RuleEvaluation(rule_id=rule.rule_id,version=rule.version,status='MATCHED',
                fact_refs=list(dict.fromkeys(f.fact_id for f in used)),
                evidence_refs=list(dict.fromkeys(x for f in used for x in f.evidence_refs)),
                exclusion_state=exclusion,scope_id=combination[0].scope_id),used
    return RuleEvaluation(rule_id=rule.rule_id,version=rule.version,
        status='NOT_MATCHED' if excluded and not unknown_relation else 'UNDETERMINED',fact_refs=list(dict.fromkeys(all_refs)),
        missing_information=['same_scope_same_party_or_required_relation']),[]


def assess(store,book,templates):
    evaluations=[];matched=[]
    for rule in book.rules:
        evaluation,used=evaluate_rule(rule,store);evaluations.append(evaluation)
        if evaluation.status=='MATCHED':matched.append((rule,evaluation))
    matched.sort(key=lambda item:(item[0].safety_urgency!='urgent',-RANK[item[0].conclusion],item[0].rule_id))
    questions=[]
    if store.conflicts:questions.append('Hai bên đang mô tả khác nhau về thanh toán. Người nhận đã tự kiểm tra khoản tiền vào đúng tài khoản của giao dịch này chưa?')
    if matched:
        selected=matched[0][0];template=templates[selected.explanation_template]
        if selected.follow_up_template:questions.append(selected.follow_up_template)
        urgency='urgent' if any(r.safety_urgency=='urgent' for r,_ in matched) else 'preventive'
        a=Assessment(risk_status=max((r.conclusion for r,_ in matched),key=RANK.get),safety_urgency=urgency,
            supported_conclusions=[r.supported_conclusion for r,_ in matched],
            evidence_refs=list(dict.fromkeys(s for _,e in matched for s in e.evidence_refs)),
            urgency_evidence_refs=list(dict.fromkeys(s for r,e in matched if r.safety_urgency=='urgent' for s in e.evidence_refs)),
            applicable_rule_ids=[r.rule_id for r,_ in matched],
            missing_information=[] if urgency=='urgent' else ['Danh tính và sự việc ngoài đời chưa được xác minh độc lập.'],
            follow_up_questions=questions[:2],recommended_actions=template['recommended_actions'],
            explanation_template_id=selected.explanation_template,prohibited_conclusions=PROHIBITED,summary=template['summary'])
        if store.conflicts:a.missing_information.append('Các khẳng định thanh toán chưa thống nhất; không ghi đè lời người nhận bằng lời người trả.')
        return a,evaluations
    active=[f for f in store.by_event.values() if f.superseded_by is None and f.value is Truth.TRUE
            and f.attributes['speech_role'] not in INACTIVE and f.attributes['temporal_state'] not in ('past','hypothetical')]
    benign_types={'build_trust','offer_employment','invite_travel_or_meeting','identity_claim','relationship_claim',
                  'return_documents_available','free_to_leave','consent_and_exit_available'}
    benign=bool(active) and all(f.fact_type in benign_types for f in active) and all(f.scope_id in store.verified_scopes
        for f in active if f.fact_type in ('offer_employment','invite_travel_or_meeting'))
    paid=any(f.rule_id=='REL-REPORTED-PAYMENT-FIRST' for f in store.by_type['relation:before'])
    if any(f.value is Truth.TRUE and f.attributes.get('user_reports_verification')=='true' for f in active if f.fact_type=='payment_confirmed'):
        paid=True
    if paid and not store.conflicts and all(f.fact_type in ('payment_confirmed','handover_requested') for f in active):benign=True
    types={f.fact_type for f in active}
    if 'retain_identity_documents' in types and 'return_documents_available' in types and types<={'retain_identity_documents','return_documents_available','free_to_leave'}:benign=True
    known_inactive=bool(store.by_event) and not active and all(f.attributes['speech_role']!='unknown' and f.value is not Truth.UNKNOWN for f in store.by_event.values())
    coverage=store.by_id['quality:coverage'].value
    clear=(benign or known_inactive) and coverage is Truth.TRUE and not store.conflicts
    if not clear:
        if 'handover_requested' in types:
            questions.append('Bạn đã kiểm tra và xác nhận khoản tiền vào tài khoản chưa?')
        elif 'code_requested' in types:
            questions.append('Dãy số đó được thông báo dùng để làm gì? Chỉ mô tả loại mã, không gửi mã thật.')
        elif types&{'offer_employment','invite_travel_or_meeting'}:
            questions.extend(['Bạn có thể xác minh công việc, địa điểm qua đầu mối độc lập không?',
                              'Họ có yêu cầu giữ bí mật, giao giấy tờ hoặc hạn chế liên lạc không?'])
        else:questions.append('Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.')
    tid='TPL-CLEAR' if clear else 'TPL-UNKNOWN';template=templates[tid]
    a=Assessment(risk_status='clear' if clear else 'need_context',safety_urgency='undetermined',supported_conclusions=[],
        evidence_refs=list(dict.fromkeys(s for f in store.by_event.values() for s in f.evidence_refs)) if clear else [],
        applicable_rule_ids=[],missing_information=[] if clear else ['Thiếu dữ kiện hoặc quan hệ quyết định trong phạm vi hỗ trợ.'],
        follow_up_questions=list(dict.fromkeys(questions))[:2],recommended_actions=template['recommended_actions'],
        explanation_template_id=tid,prohibited_conclusions=PROHIBITED,summary=template['summary'])
    if clear and any(f.attributes.get('user_reports_verification')=='true' for f in active):
        a.summary='Theo thông tin bổ sung, bạn cho biết đã tự kiểm tra và nhận đủ tiền. Chưa ghi nhận dấu hiệu đáng ngờ còn hiệu lực trong phần đã kiểm tra; hệ thống không xác minh tài khoản ngân hàng.'
    return a,evaluations
