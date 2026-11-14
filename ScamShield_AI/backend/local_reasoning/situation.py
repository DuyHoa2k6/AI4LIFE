"""Named interpretation stages over validated events, never a generated story."""
from collections import defaultdict
import time
from .interpretation_schema import Behavior,Situation,Hypothesis,Consequence,Interpretation
from .schema import Relation
from .validation import annotation_errors

INACTIVE={'quoted_warning','denial','hypothetical','unknown'}
BEHAVIORS={'transfer_funds':'request_payment','handover_asset':'request_asset_handover','provide_code':'request_code',
 'provide_credentials':'request_credentials','provide_documents':'request_documents','install_app':'request_installation',
 'share_screen':'request_screen_sharing','grant_control':'request_device_control','keep_secret':'request_secrecy',
 'request_secrecy':'request_secrecy','avoid_verification':'avoid_independent_verification',
 'identity_claim':'claimed_identity','relationship_claim':'claimed_relationship','receive_funds':'payment_or_benefit_claim',
 'withdraw_funds':'withdrawal_state_claim','offer_employment':'employment_offer','invite_travel_or_meeting':'travel_or_meeting_invitation'}


def participant_resolver(input,a):
    by_id={p.participant_id:p for p in a.participants};spans={s.span_id:s for s in a.spans}
    for p in a.participants:
        if p.interaction_role=='speaker':p.information_status='observed'
    for e in a.events:
        if e.actor_id is None and 'actor_identity' not in e.unknown_fields:e.unknown_fields.append('actor_identity')
        if e.event_type=='identity_claim' and e.actor_id in by_id:
            p=by_id[e.actor_id];p.claimed_identity=' '.join(spans[s].quote for s in e.evidence_refs)[:300]
            p.identity_status='claimed';p.information_status='claimed'
    for relationship in a.personal_relationships:
        for pid in relationship.participant_ids:
            if pid in by_id:
                by_id[pid].relationship_to_user=relationship.relationship_type
                by_id[pid].information_status='user_reported' if relationship.status=='user_reported' else 'claimed'
    return a.participants


def behavior_interpreter(a,frames):
    result=[];purposes={f.action_event_id:f.stated_purpose for f in frames if f.stated_purpose};by_frame={f.action_event_id:f for f in frames}
    for e in a.events:
        kind='warning_or_reminder' if e.speech_role=='quoted_warning' else 'denial' if e.speech_role=='denial' else BEHAVIORS.get(e.event_type,e.description)
        status='user_reported' if e.attribution.kind=='user_report' else 'claimed' if e.speech_role in ('claim','reported') else 'unknown' if e.speech_role=='unknown' else 'observed'
        if e.event_id in purposes:e.stated_purpose=e.stated_purpose or purposes[e.event_id]
        frame=by_frame.get(e.event_id)
        result.append(Behavior(behavior_id='behavior:'+e.event_id,behavior_type=kind,actor_id=frame.requester_id if frame and e.speech_role=='request' else e.actor_id,
            affected_party_id=frame.target_id if frame and e.speech_role=='request' else e.affected_party_id,event_refs=[e.event_id],description=e.description,information_status=status,
            evidence_refs=e.evidence_refs,rule_id=e.extractor_rule_id,scope_id=e.scope_id))
        if frame and 'time_pressure_cue' in frame.communication_functions:
            result.append(Behavior(behavior_id='pressure:'+e.event_id,behavior_type='time_pressure_cue',actor_id=frame.requester_id,
                affected_party_id=frame.target_id,event_refs=[e.event_id],description='Có chi tiết chờ hoặc thời hạn trong lời nhắn, có thể tạo sức ép; chưa chứng minh ý định xấu.',
                information_status='inferred',evidence_refs=frame.evidence_refs,rule_id='BEHAVIOR-TIME-PRESSURE',scope_id=e.scope_id))
    return result


def event_linker(a):
    spans={s.span_id:s for s in a.spans}
    # Self-claimed identity + avoidance must be by the same textual source in
    # the same situation; adjacency alone is insufficient across conversations.
    for identity in [e for e in a.events if e.event_type in ('identity_claim','relationship_claim') and e.speech_role not in INACTIVE]:
        for avoid in [e for e in a.events if e.event_type=='avoid_verification' and e.speech_role=='request' and e.polarity=='positive']:
            if identity.scope_id!=avoid.scope_id or identity.affected_party_id!=avoid.affected_party_id:continue
            left={spans[s].message_id for s in identity.evidence_refs};right={spans[s].message_id for s in avoid.evidence_refs}
            if len(left)!=1 or left!=right:continue
            if any(r.type=='reason_given_for' and r.from_id==identity.event_id and r.to_id==avoid.event_id for r in a.relations):continue
            a.relations.append(Relation(relation_id='situation:r'+str(len(a.relations)+1),type='reason_given_for',from_id=identity.event_id,to_id=avoid.event_id,
                scope_id=identity.scope_id,status='inferred',evidence_refs=list(dict.fromkeys(identity.evidence_refs+avoid.evidence_refs)),
                rationale='Danh tính tự nhận và yêu cầu tránh xác minh do cùng nguồn đưa ra; chưa xác minh quan hệ ngoài đời.',rule_id='LINK-IDENTITY-AVOID-VERIFY'))
    return a.relations


def situation_builder(a):
    groups=defaultdict(list);spans={s.span_id:s for s in a.spans}
    for e in a.events:groups[e.scope_id].append(e)
    result=[]
    for scope,events in groups.items():
        ids={e.event_id for e in events};relations=[r for r in a.relations if r.scope_id==scope]
        updates={(r.from_id,r.to_id) for r in relations if r.type=='state_update' and r.status!='unknown'}
        superseded={left for left,_ in updates}
        payments=[e for e in events if e.event_type=='receive_funds' and e.speech_role not in INACTIVE]
        conflicts=[]
        for old in payments:
            for new in payments:
                if old.event_id>=new.event_id or old.polarity==new.polarity:continue
                if old.event_id in superseded or new.event_id in superseded:continue
                if old.temporal_state=='planned' or new.temporal_state=='planned':continue
                if (old.event_id,new.event_id) in updates or (new.event_id,old.event_id) in updates:continue
                conflicts.extend([old.event_id,new.event_id])
        result.append(Situation(situation_id=scope,participant_ids=list(dict.fromkeys(p for e in events for p in (e.actor_id,e.affected_party_id,e.recipient_id) if p)),
            message_ids=list(dict.fromkeys(spans[s].message_id for e in events for s in e.evidence_refs if spans[s].message_id)),
            event_refs=list(ids),relation_refs=[r.relation_id for r in relations],
            active_request_refs=[e.event_id for e in events if e.speech_role=='request' and e.polarity=='positive' and e.temporal_state not in ('completed','past','hypothetical')],
            conflicting_refs=list(dict.fromkeys(conflicts)),unknown_information=['Danh tính ngoài đời chưa được xác minh.']+
                (['Có người thực hiện chưa xác định.'] if any(e.actor_id is None for e in events) else [])))
    return result


def hypothesis_evaluator(a,situations):
    events={e.event_id:e for e in a.events};result=[]
    for situation in situations:
        purchases=[events[e] for e in situation.event_refs if events[e].stated_purpose=='purchase_exchange' and events[e].speech_role=='request']
        if purchases:result.append(Hypothesis(hypothesis_id='hypothesis:purchase:'+situation.situation_id,scope_id=situation.situation_id,
            description='Mục đích được nêu là thanh toán để nhận hàng; chưa xác minh người bán hoặc việc giao hàng.',
            supporting_refs=[e.event_id for e in purchases],missing_information=['Độ tin cậy của người bán chưa được kiểm chứng.'],status='supported',rule_id='H-ORDINARY-PURCHASE'))
        for r in a.relations:
            if r.scope_id!=situation.situation_id or r.type not in ('prerequisite_for','before','after'):continue
            left=events.get(r.from_id);right=events.get(r.to_id)
            if not left or not right or left.speech_role in INACTIVE or right.speech_role in INACTIVE:continue
            description=None;rule=None
            if r.type=='prerequisite_for' and left.event_type=='transfer_funds' and right.event_type in ('receive_funds','withdraw_funds'):
                description='Khoản phải nộp được đặt làm điều kiện để nhận hoặc rút khoản được nêu.';rule='H-PAYMENT-CONDITION'
            elif r.type=='before' and left.event_type=='handover_asset' and right.event_type=='receive_funds' and right.polarity=='negative':
                description='Yêu cầu giao tài sản khi thanh toán chưa được người liên quan xác nhận.';rule='H-HANDOVER-UNPAID'
            elif r.type=='before' and left.event_type=='receive_funds' and left.polarity=='positive' and left.temporal_state=='completed':
                description='Người liên quan báo đã nhận tiền trước khi giao tài sản; chưa xác minh ngân hàng.';rule='H-REPORTED-PAID'
            elif r.type=='after' and left.extractor_rule_id=='FACT-BANK-INFO-1' and right.event_type=='share_screen':
                description='Yêu cầu nối tiếp có thể làm lộ thông tin ngân hàng trong lúc chia sẻ màn hình.';rule='H-SCREEN-BANK'
            if description:result.append(Hypothesis(hypothesis_id='hypothesis:'+r.relation_id,scope_id=r.scope_id,description=description,
                supporting_refs=[left.event_id,right.event_id,r.relation_id],conflicting_refs=situation.conflicting_refs,
                missing_information=situation.unknown_information,status='possible' if situation.conflicting_refs else 'supported',rule_id=rule))
        docs=[e for e in a.events if e.scope_id==situation.situation_id and e.event_type=='retain_identity_documents' and e.speech_role not in INACTIVE]
        if docs:result.append(Hypothesis(hypothesis_id='hypothesis:docs:'+situation.situation_id,scope_id=situation.situation_id,
            description='Giữ giấy tờ cần phân biệt thủ tục có thể lấy lại với hạn chế quyền rời đi.',supporting_refs=[e.event_id for e in docs],
            missing_information=['Ai giữ giấy tờ và bạn có thể lấy lại khi muốn không?'],status='undetermined',rule_id='H-DOCUMENT-CUSTODY'))
    return result


def consequence_evaluator(a):
    categories={'transfer_funds':('money','Có thể mất thêm tiền nếu làm theo yêu cầu chưa xác minh.'),
        'retain_identity_documents':('freedom','Nếu không chủ động lấy lại được giấy tờ, người giao có thể gặp bất lợi khi muốn rời đi hoặc tìm hỗ trợ.'),
        'handover_asset':('assets','Có thể giao mất tài sản khi chưa xác nhận thanh toán.'),
        'provide_documents':('personal_data','Giấy tờ cá nhân có thể bị sử dụng ngoài mục đích được nêu.'),
        'provide_code':('account_access','Nếu là mã xác thực, việc giao mã có thể làm lộ quyền đăng nhập.'),
        'provide_credentials':('account_access','Cung cấp mật khẩu có thể làm mất quyền truy cập tài khoản.'),
        'share_screen':('device_access','Người khác có thể nhìn thấy dữ liệu trên màn hình.'),
        'grant_control':('device_access','Người khác có thể thao tác trên thiết bị.'),
        'install_app':('device_access','Ứng dụng có thể truy cập dữ liệu tùy quyền được cấp; chưa kiểm tra mã độc.'),
        'restrict_movement':('freedom','Nội dung cho biết quyền rời đi có thể đang bị hạn chế.'),
        'restrict_communication':('freedom','Khả năng liên lạc hoặc tìm hỗ trợ có thể bị hạn chế.'),
        'threaten_harm':('physical_safety','Có nguy cơ an toàn thân thể theo lời đe dọa được nêu.'),
        'compel_work':('freedom','Nội dung có dấu hiệu cưỡng ép thực hiện công việc.')}
    result=[]
    for e in a.events:
        if e.event_type not in categories or e.polarity!='positive' or e.speech_role in INACTIVE:continue
        if e.speech_role!='request' and e.temporal_state not in ('ongoing','imminent'):continue
        category,description=categories[e.event_type]
        relations=[r for r in a.relations if e.event_id in (r.from_id,r.to_id) and r.scope_id==e.scope_id]
        result.append(Consequence(consequence_id='consequence:'+e.event_id,scope_id=e.scope_id,category=category,description=description,
            action_refs=[e.event_id],condition_refs=[r.relation_id for r in relations],evidence_refs=list(dict.fromkeys(e.evidence_refs+[s for r in relations for s in r.evidence_refs])),
            rule_id='CONSEQUENCE-'+e.event_type.upper()))
    return result


def prepare_interpretation(input,a,frames):
    if annotation_errors(input,a):raise ValueError('Invalid annotations before interpretation')
    timings={}
    def step(name,fn,*args):
        start=time.perf_counter();value=fn(*args);timings[name]=(time.perf_counter()-start)*1000;return value
    step('participants',participant_resolver,input,a)
    behaviors=step('behaviors',behavior_interpreter,a,frames)
    step('event_linking',event_linker,a)
    situations=step('situations',situation_builder,a)
    hypotheses=step('hypotheses',hypothesis_evaluator,a,situations)
    consequences=step('consequences',consequence_evaluator,a)
    if annotation_errors(input,a):raise ValueError('Invalid interpreted relationship')
    return Interpretation(behaviors=behaviors,situations=situations,hypotheses=hypotheses,consequences=consequences,
        stage_timings_ms=timings,limitations=['Các bộ trích/diễn giải dùng quy tắc cục bộ, chưa phải mô hình đã huấn luyện; chủ thể hoặc liên hệ ngoài độ phủ giữ chưa rõ.'])


def select_clarification(assessment,interpretation,frames):
    conflicts=[s for s in interpretation.situations if s.conflicting_refs]
    if conflicts:
        assessment.follow_up_questions=['Các bên đang mô tả khác nhau. Người nhận đã tự kiểm tra khoản tiền vào đúng tài khoản của giao dịch này chưa?']
        assessment.missing_information.append('Khẳng định thanh toán khác nguồn chưa thống nhất.')
    elif assessment.risk_status=='need_context':
        missing=[x for f in frames for x in f.missing_information if f.speech_role=='request']
        if any('thanh toán' in x for x in missing):assessment.follow_up_questions=['Bạn đã tự kiểm tra và xác nhận khoản tiền vào tài khoản cho giao dịch này chưa?']
        elif missing:assessment.follow_up_questions=['Khoản phải nộp dùng để làm gì, và họ có đặt nó làm điều kiện để bạn nhận hoặc rút lại tiền không?']
    assessment.follow_up_questions=list(dict.fromkeys(assessment.follow_up_questions))[:2]


def risk_assessor(assessment,a,interpretation,frames):
    active=[e for e in a.events if e.speech_role=='request' and e.polarity=='positive']
    ordinary=[e for e in active if e.stated_purpose in ('purchase_exchange','optional_purchase')]
    if assessment.risk_status=='clear' and any(s.conflicting_refs for s in interpretation.situations):
        assessment.risk_status='need_context';assessment.summary='Các nguồn đang mô tả khác nhau về thanh toán; cần xác minh trạng thái của đúng giao dịch.'
    paid=any(h.rule_id=='H-REPORTED-PAID' and not h.conflicting_refs for h in interpretation.hypotheses)
    if assessment.risk_status=='clear' and paid and any(r.rule_id=='LINK-EXPLICIT-PAYMENT-UPDATE' for r in a.relations):
        assessment.summary='Người bán cho biết vừa kiểm tra và đã nhận đủ tiền, cập nhật thông tin chưa nhận lúc trước; chưa ghi nhận yêu cầu đáng ngờ còn hiệu lực. Đây là lời xác nhận trong hội thoại, chưa phải kiểm chứng ngân hàng.'
        assessment.applicable_rule_ids=list(dict.fromkeys(assessment.applicable_rule_ids+['R-CONTEXT-REPORTED-PAID']))
    if assessment.risk_status=='need_context' and not assessment.applicable_rule_ids and paid and active and all(e.event_type=='handover_asset' for e in active):
        assessment.risk_status='clear';assessment.summary='Người liên quan cho biết đã nhận tiền trước khi giao tài sản; chưa ghi nhận dấu hiệu đáng ngờ còn hiệu lực trong phần đã kiểm tra.'
        assessment.follow_up_questions=[];assessment.missing_information=[]
        assessment.evidence_refs=list(dict.fromkeys(s for e in a.events if e.event_type in ('handover_asset','receive_funds') for s in e.evidence_refs))
        assessment.applicable_rule_ids=['R-CONTEXT-REPORTED-PAID']
    # A supported ordinary purchase is an alternative explanation, not an
    # identity verification. It cannot override a matched warning rule.
    if assessment.risk_status=='need_context' and not assessment.applicable_rule_ids and ordinary and len(ordinary)==len(active) and not any(s.conflicting_refs for s in interpretation.situations):
        assessment.risk_status='clear';assessment.summary='Trong yêu cầu thanh toán để nhận hàng được mô tả, chưa ghi nhận dấu hiệu đáng ngờ thuộc phạm vi kiểm tra.'
        if all(e.stated_purpose=='optional_purchase' for e in ordinary):
            assessment.summary='Lời nhắn nêu việc mua gói là tùy chọn hoặc không phải điều kiện nhận lại tiền; chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần đã kiểm tra.'
        assessment.follow_up_questions=[];assessment.missing_information=[]
        assessment.recommended_actions=['Xác minh người bán và điều kiện giao nhận trước khi thanh toán; kết quả này không xác nhận người bán đáng tin cậy.']
        assessment.evidence_refs=list(dict.fromkeys(s for e in ordinary for s in e.evidence_refs))
        assessment.applicable_rule_ids=['R-CONTEXT-ORDINARY-PURCHASE']
    select_clarification(assessment,interpretation,frames)
    return assessment


def summarize_18(a,interpretation,assessment):
    for field in a.answers_18.__dict__.values():
        field.extraction_method=field.extraction_method or 'local_python_rules'
    for key,items in [('participants',a.participants),('claims',[b for b in interpretation.behaviors if b.information_status in ('claimed','user_reported')])]:
        field=getattr(a.answers_18,key)
        refs=list(dict.fromkeys(r for item in items for r in item.evidence_refs))
        if refs:field.evidence_refs=list(dict.fromkeys(field.evidence_refs+refs))
    purpose=a.answers_18.stated_purpose
    for e in a.events:
        if e.stated_purpose:
            purpose.status='claimed';purpose.value.statements.append(e.stated_purpose)
            purpose.value.event_ids.append(e.event_id);purpose.evidence_refs+=e.evidence_refs
    purpose.evidence_refs=list(dict.fromkeys(purpose.evidence_refs))
    alternatives=a.answers_18.contradictions_and_alternatives
    pressure=[b for b in interpretation.behaviors if b.behavior_type=='time_pressure_cue']
    if pressure:
        f=a.answers_18.persuasion;f.status='inferred';f.extraction_method='behavior_interpreter'
        f.value.statements+=[b.description for b in pressure];f.value.event_ids+=[e for b in pressure for e in b.event_refs]
        f.evidence_refs=list(dict.fromkeys(f.evidence_refs+[r for b in pressure for r in b.evidence_refs]));f.rule_ids+=['BEHAVIOR-TIME-PRESSURE']
    alternatives.value.statements=[h.description for h in interpretation.hypotheses]
    alternatives.value.event_ids=list(dict.fromkeys(e for s in interpretation.situations for e in s.conflicting_refs))
    events={e.event_id:e for e in a.events}
    referenced={ref for h in interpretation.hypotheses for ref in h.supporting_refs+h.conflicting_refs}
    sources={**events,**{r.relation_id:r for r in a.relations}}
    alternatives.evidence_refs=list(dict.fromkeys(r for ref in referenced if ref in sources for r in sources[ref].evidence_refs))
    alternatives.status='inferred' if interpretation.hypotheses else 'unknown'
    alternatives.extraction_method='hypothesis_evaluator';alternatives.rule_ids=[h.rule_id for h in interpretation.hypotheses]
    a.answers_18.assessment.extraction_method='risk_assessor';a.answers_18.assessment.rule_ids=assessment.applicable_rule_ids
