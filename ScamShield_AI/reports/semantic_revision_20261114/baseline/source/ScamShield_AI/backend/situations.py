"""Ground scenario facts in the user's messages, then apply explicit severity rules."""
from dataclasses import dataclass,field
from .engine import verify
from .schemas import Finding, Extraction, Answer, RiskIndicator

REQUEST_ACTIONS={
 'asset_handover_requested':{'other'},'changed_payee_transfer_requested':{'transfer_funds'},
 'verification_after_payment_requested':{'other','transfer_funds'},'identity_documents_requested':{'other'},
 'screen_sharing_requested':{'grant_access'},'banking_view_requested':{'other','grant_access'},
 'code_requested':{'share_auth_code','other'},
 'payment_requested':{'transfer_funds'},
}
LINK_KINDS={
 'handover_before_payment_confirmation':{'asset_handover_requested','payment_not_confirmed'},
 'handover_after_reported_payment':{'asset_handover_requested','payment_received_reported'},
 'changed_payee_before_verification':{'changed_payee_transfer_requested','verification_after_payment_requested'},
 'screen_share_banking':{'screen_sharing_requested','banking_view_requested'},
 'code_request_is_login_code':{'code_requested','login_code_identified'},
 'ordinary_payment_context':{'payment_requested','ordinary_transaction_reported'},
}
HIGH_LINKS={'screen_share_banking','code_request_is_login_code'}
MODERATE_LINKS={'handover_before_payment_confirmation','changed_payee_before_verification'}
GAP_QUESTIONS={
 'requested_step':'Bước xác nhận hoặc xử lý tiếp yêu cầu bạn thực hiện thao tác cụ thể gì? Hãy chép nguyên văn, không gửi mã hoặc mật khẩu thật.',
 'requested_object':'Thông tin hoặc “cái đó” được yêu cầu gửi là gì? Chỉ mô tả loại thông tin, không gửi mã hoặc mật khẩu thật.',
 'withdrawal_next_requirement':'Để tiếp tục rút tiền, họ có yêu cầu chuyển tiền hoặc cung cấp thông tin gì không? Nếu chưa có hướng dẫn, hãy cho biết điều đó.',
 'payment_confirmation':'Bạn đã tự kiểm tra tiền thực nhận trong ứng dụng ngân hàng chưa, hay mới có ảnh biên lai?',
 'payment_purpose':'Khoản tiền được yêu cầu dùng để thanh toán việc gì, hay là điều kiện để nhận hoặc rút tiền?',
 'action_relation':'Họ nói phải làm bước nào trước để được nhận lợi ích hoặc xử lý tiếp? Hãy chép nguyên văn điều kiện.',
 'requester_identity':'Bạn có thể xác nhận người gửi qua đầu mối quen dùng hoặc kênh chính thức độc lập nào?',
 'file_origin':'Tệp hoặc ứng dụng do ai gửi, nhà phát hành là ai và được tải từ đâu?',
 'permission_purpose':'Họ yêu cầu quyền gì, để làm việc gì, và bạn đã xác minh đầu mối hỗ trợ chưa?',
 'channel':'Thao tác được yêu cầu trên kênh chính thức hay qua địa chỉ/tài khoản do người gửi đưa riêng?',
}
GAP_PRIORITY=['requested_step','requested_object','withdrawal_next_requirement','payment_confirmation',
              'action_relation','payment_purpose','file_origin','permission_purpose','channel','requester_identity']
CRITICAL_GAPS={'requested_step','requested_object','withdrawal_next_requirement','payment_purpose','payment_confirmation','action_relation'}
EXPLANATIONS={
 'handover_before_payment_confirmation':'Có yêu cầu giao tài sản trước khi khoản thanh toán được xác nhận; chưa đủ căn cứ kết luận biên lai giả.',
 'handover_after_reported_payment':'Người nhận tiền cho biết đã tự kiểm tra và nhận đủ tiền; đây là bối cảnh trong hội thoại, không phải xác minh ngân hàng của hệ thống.',
 'changed_payee_before_verification':'Tài khoản nhận tiền bị thay đổi và người gửi muốn thanh toán trước khi đối chiếu với đầu mối đã biết.',
 'screen_share_banking':'Yêu cầu chia sẻ màn hình đi cùng việc mở thông tin ngân hàng có thể làm lộ dữ liệu tài chính.',
 'code_request_is_login_code':'Dãy số được xác định trong hội thoại là mã đăng nhập, nhưng người gửi vẫn yêu cầu cung cấp mã đó.',
 'identity_documents_requested':'Người gửi yêu cầu giấy tờ định danh hoặc ảnh chân dung qua cuộc trò chuyện; cần xác minh kênh thu thập và mục đích.',
 'ordinary_payment_context':'Người được yêu cầu thanh toán cho biết đã đối chiếu mục đích hoặc giao dịch; bối cảnh này chỉ hỗ trợ yêu cầu thanh toán tương ứng.',
}
SUMMARIES={
 'handover_before_payment_confirmation':'Người gửi yêu cầu giao tài sản khi khoản thanh toán chưa được xác nhận. Có dấu hiệu cần xác minh trước khi giao.',
 'handover_after_reported_payment':'Người nhận tiền cho biết đã kiểm tra và nhận đủ tiền trước khi giao tài sản. Chưa ghi nhận dấu hiệu đáng ngờ trong đoạn hội thoại này.',
 'changed_payee_before_verification':'Người gửi đổi tài khoản nhận tiền và yêu cầu chuyển trước, đối chiếu sau. Cần xác minh thay đổi trước khi thanh toán.',
 'screen_share_banking':'Người gửi yêu cầu chia sẻ màn hình rồi mở thông tin ngân hàng. Chuỗi thao tác này có nguy cơ làm lộ dữ liệu tài chính.',
 'code_request_is_login_code':'Người gửi yêu cầu đọc một dãy số được xác định là mã đăng nhập tài khoản. Việc giao mã có thể khiến tài khoản bị truy cập trái phép.',
 'identity_documents_requested':'Người gửi yêu cầu cung cấp giấy tờ định danh và ảnh qua chat. Cần xác minh đơn vị tiếp nhận và mục đích trước khi gửi.',
 'ordinary_payment_context':'Người được yêu cầu thanh toán cho biết đã đối chiếu giao dịch và mục đích. Chưa ghi nhận dấu hiệu đáng ngờ trong phần nội dung này.',
}
ACTIONS={
 'handover_before_payment_confirmation':'Tự kiểm tra tiền thực nhận trong ứng dụng ngân hàng trước khi giao tài sản; không dựa riêng vào ảnh biên lai.',
 'handover_after_reported_payment':'Chỉ giao đúng tài sản và đúng người nhận theo thỏa thuận; kiểm tra lại nếu có thay đổi.',
 'changed_payee_before_verification':'Gọi đầu mối trong hợp đồng hoặc số đã biết để xác nhận tài khoản mới trước khi chuyển tiền.',
 'screen_share_banking':'Dừng chia sẻ màn hình trước khi mở ứng dụng ngân hàng và xác minh yêu cầu qua kênh chính thức.',
 'code_request_is_login_code':'Không đọc mã đăng nhập cho người khác; tự kiểm tra giao dịch trên ứng dụng hoặc kênh chính thức.',
 'identity_documents_requested':'Xác minh yêu cầu qua kênh chính thức của đơn vị được nhắc đến, trước khi gửi ảnh giấy tờ qua chat.',
 'ordinary_payment_context':'Đối chiếu lại số tiền và người nhận đã thống nhất; xác minh độc lập nếu có thay đổi mới.',
}


def overlaps(a,b):
    return a.message_id==b.message_id and max(a.start,b.start)<min(a.end,b.end)


def ground(evidence,reviewed,request):
    messages={m.id:m for m in request.as_messages()};result=[]
    for ev in evidence:
        msg=messages.get(ev.message_id)
        if msg is None:return None
        probe=Finding(id='basis',action='other',speaker=msg.speaker,speech_role='claim',description='',
                      evidence=[ev],inference=Answer(status='unknown',text='',evidence_refs=[]))
        checked=verify(Extraction(answers=reviewed.answers,findings=[probe]),request.as_messages())
        if not checked:return None
        result.extend(checked[0].evidence)
    return result


@dataclass
class SituationResult:
    facts: dict=field(default_factory=dict)
    links: list=field(default_factory=list)
    benign_ids: set=field(default_factory=set)
    high_ids: set=field(default_factory=set)
    moderate_ids: set=field(default_factory=set)
    gaps: list=field(default_factory=list)
    indicators: list=field(default_factory=list)


def inspect_situations(reviewed,request):
    result=SituationResult();issues=set()
    valid={f.id:f for f in verify(reviewed,request.as_messages())}
    messages={m.id:m for m in request.as_messages()}
    ids=[f.id for f in reviewed.situation_facts]
    if len(set(ids))!=len(ids):issues.add('duplicate_situation_fact')
    for fact in reviewed.situation_facts:
        ev=ground(fact.evidence,reviewed,request)
        if ev is None:issues.add('situation_evidence_invalid');continue
        if any(not request.context or not(0<=e.start<e.end<=len(request.context)) or
               request.context[e.start:e.end]!=e.quote for e in fact.context_evidence):
            issues.add('situation_context_invalid');continue
        if not set(fact.finding_refs)<=valid.keys():issues.add('situation_finding_ref_invalid');continue
        refs=[valid[fid] for fid in fact.finding_refs]
        if fact.speech_role=='request' and fact.kind in REQUEST_ACTIONS:
            related=[f for f in refs if f.speech_role=='request' and f.action in REQUEST_ACTIONS[fact.kind]
                     and any(overlaps(a,b) for a in f.evidence for b in ev)]
            if not related or {f.id for f in related}!=set(fact.finding_refs):issues.add('situation_request_not_grounded');continue
        result.facts[fact.id]=fact.model_copy(update={'evidence':ev},deep=True)
    used_pairs=set()
    for link in reviewed.situation_links:
        key=(link.kind,tuple(sorted(link.fact_ids)))
        if key in used_pairs:issues.add('duplicate_situation_link');continue
        used_pairs.add(key)
        if len(set(link.fact_ids))!=len(link.fact_ids) or not set(link.fact_ids)<=result.facts.keys():
            issues.add('situation_link_ref_invalid');continue
        facts=[result.facts[x] for x in link.fact_ids]
        if not LINK_KINDS[link.kind]<={f.kind for f in facts}:
            issues.add('situation_link_kind_mismatch');continue
        ev=ground(link.evidence,reviewed,request)
        if ev is None or not all(any(overlaps(a,b) for a in f.evidence for b in (ev or [])) for f in facts):
            issues.add('situation_link_evidence_invalid');continue
        if link.status=='uncertain':
            if not (link.missing_information or '').strip():issues.add('uncertain_situation_missing_gap')
            connection_gaps=[]
            for gap in reviewed.information_gaps:
                if not gap.affects_decision or gap.kind not in ('action_relation','requested_step','requested_object'):continue
                basis=ground(gap.evidence,reviewed,request)
                if basis and any(overlaps(a,b) for a in basis for f in facts for b in f.evidence):connection_gaps.append(gap)
            if not connection_gaps:issues.add('uncertain_situation_requires_connection_gap')
            continue
        if link.status!='supported':continue
        if link.missing_information is not None:issues.add('supported_situation_has_gap');continue
        reqs=[f for f in facts if f.kind in REQUEST_ACTIONS]
        states=[f for f in facts if f.kind not in REQUEST_ACTIONS]
        if any(f.speech_role!='request' for f in reqs) or any(f.speech_role!='claim' for f in states):
            issues.add('situation_link_speech_role_invalid');continue
        request_ids={fid for f in reqs for fid in f.finding_refs if fid in valid and valid[fid].speech_role=='request'}
        if not request_ids:issues.add('situation_link_without_request');continue
        reasoned={r.finding_id for r in reviewed.uncertainty_reasons}
        blocked={r.finding_id for r in reviewed.uncertainty_reasons if r.kind in ('action','relation')}|(set(reviewed.review.uncertain_finding_ids)-reasoned)
        if request_ids&blocked:issues.add('supported_situation_has_blocking_uncertainty');continue
        if link.kind in ('screen_share_banking','changed_payee_before_verification'):
            authors={valid[fid].speaker for fid in request_ids}
            if len(authors)!=1:issues.add('situation_requests_different_speakers');continue
            if authors=={'unknown'} and len({e.message_id for f in reqs for e in f.evidence})>1:
                issues.add('unknown_actor_across_messages');continue
        if link.kind in ('handover_after_reported_payment','ordinary_payment_context'):
            request_authors={valid[fid].speaker for fid in request_ids}
            state_kind='payment_received_reported' if link.kind=='handover_after_reported_payment' else 'ordinary_transaction_reported'
            paid=next(f for f in facts if f.kind==state_kind)
            paid_authors={messages[e.message_id].speaker for e in paid.evidence}
            if 'unknown' in paid_authors or not paid_authors.isdisjoint(request_authors):
                issues.add('payment_confirmation_not_recipient_attributed');continue
            result.benign_ids.update(request_ids)
        elif link.kind in HIGH_LINKS:result.high_ids.update(request_ids)
        elif link.kind in MODERATE_LINKS:result.moderate_ids.update(request_ids)
        result.links.append(link)
        result.indicators.append(RiskIndicator(kind=link.kind,evidence=ev,explanation=EXPLANATIONS[link.kind]))
    if result.benign_ids&(result.high_ids|result.moderate_ids):issues.add('contradictory_situation_context')
    for fact in result.facts.values():
        if fact.kind=='identity_documents_requested' and fact.speech_role=='request':
            result.moderate_ids.update(fact.finding_refs)
            result.indicators.append(RiskIndicator(kind=fact.kind,evidence=fact.evidence,explanation=EXPLANATIONS[fact.kind]))
    for gap in reviewed.information_gaps:
        ev=ground(gap.evidence,reviewed,request)
        if ev is None or not set(gap.finding_refs)<=valid.keys():issues.add('information_gap_evidence_invalid');continue
        result.gaps.append(gap.model_copy(update={'evidence':ev},deep=True))
    return sorted(issues),result


def apply_situation_policy(response,reviewed,request,result):
    valid={f.id:f for f in response.findings if not f.id.startswith('rule-conflict-')}
    reasoned={r.finding_id for r in reviewed.uncertainty_reasons}
    blocking={r.finding_id for r in reviewed.uncertainty_reasons if r.kind in ('action','relation')}|(set(reviewed.review.uncertain_finding_ids)-reasoned)
    benign=set(result.benign_ids)
    # The legacy context path remains available for previously supported ordinary transactions.
    if request.context and reviewed.review.context_evidence and all(
        0<=e.start<e.end<=len(request.context) and request.context[e.start:e.end]==e.quote
        for e in reviewed.review.context_evidence):benign.update(reviewed.review.benign_finding_ids)
    benign={fid for fid in benign if fid in valid and valid[fid].action!='share_auth_code'}
    active={fid for fid,f in valid.items() if f.speech_role=='request' and f.action!='inducement' and fid not in benign}
    high=(set(result.high_ids)&active)-blocking
    high.update(fid for fid in active if valid[fid].action=='share_auth_code' and fid not in blocking)
    for link in reviewed.review.risk_links:
        if link.request_id in active and link.request_id not in blocking and link.support_id not in blocking:
            f=valid[link.request_id]
            # A benefit attached to generic 'other' or identity documents is not automatically high.
            if f.action in ('transfer_funds','grant_access','install_app'):high.add(f.id)
    moderate=(result.moderate_ids&active)-blocking
    action_types={valid[fid].action for fid in active}
    relevant_gaps=[g for g in result.gaps if (g.kind!='payment_purpose' or 'transfer_funds' in action_types)
                   and (g.kind!='permission_purpose' or 'grant_access' in action_types)]
    gap_kinds={g.kind for g in relevant_gaps}
    for f in result.facts.values():
        if f.speech_role!='claim':continue
        if f.kind=='unspecified_confirmation_step':gap_kinds.add('requested_step')
        if f.kind=='withdrawal_pending_without_next_step':gap_kinds.add('withdrawal_next_requirement')
    critical={g.kind for g in relevant_gaps if g.affects_decision and g.kind in CRITICAL_GAPS}
    critical|=gap_kinds&{'requested_step','withdrawal_next_requirement'}
    unresolved=bool(response.analysis.rule_conflicts or active&blocking or any(f.speech_role=='unknown' for f in valid.values()))
    if high:status='high'
    elif moderate:status='suspicious'
    elif critical or unresolved or any(valid[fid].action=='transfer_funds' for fid in active) or (reviewed.review.needs_context and not active and not benign):status='need_context'
    elif active:status='suspicious'
    else:status='clear'
    response.risk_status=status
    response.risk_indicators=result.indicators
    response.analysis.situation_facts=len(result.facts);response.analysis.situation_links=len(result.links)
    response.analysis.information_gaps=len(result.gaps)
    if status=='clear':gap_kinds=set()
    if status=='need_context' and not gap_kinds:
        kinds={r.kind for r in reviewed.uncertainty_reasons}
        gap_kinds={'requested_step'} if 'action' in kinds else {'action_relation'} if 'relation' in kinds else {'payment_purpose'} if any(valid[fid].action=='transfer_funds' for fid in active) else {'requester_identity'}
    ordered=[k for k in GAP_PRIORITY if k in gap_kinds]
    response.follow_up_questions=[GAP_QUESTIONS[k] for k in ordered[:2]]
    descriptions={'requested_step':'Chưa biết bước được yêu cầu.',
        'withdrawal_next_requirement':'Chưa biết yêu cầu để tiếp tục rút tiền.',
        'requested_object':'Chưa xác định thông tin hoặc đối tượng được yêu cầu.',
        'payment_confirmation':'Chưa xác nhận tiền thực nhận.',
        'payment_purpose':'Chưa rõ mục đích khoản tiền.',
        'action_relation':'Chưa rõ quan hệ điều kiện giữa các thao tác.',
        'requester_identity':'Chưa xác minh người gửi qua đầu mối độc lập.',
        'file_origin':'Chưa xác minh nguồn tệp hoặc ứng dụng.',
        'permission_purpose':'Chưa rõ mục đích hoặc phạm vi quyền được yêu cầu.',
        'channel':'Chưa xác minh kênh thực hiện thao tác.'}
    response.missing_information=[descriptions[k] for k in ordered[:2]]
    priority=['code_request_is_login_code','screen_share_banking','handover_before_payment_confirmation',
              'changed_payee_before_verification','identity_documents_requested','handover_after_reported_payment','ordinary_payment_context']
    allowed_kinds=HIGH_LINKS if status=='high' else MODERATE_LINKS|{'identity_documents_requested'} if status=='suspicious' else {'handover_after_reported_payment','ordinary_payment_context'} if status=='clear' else set()
    selected=next((k for k in priority if k in allowed_kinds and any(i.kind==k for i in result.indicators)),None)
    default={'high':'Có yêu cầu có thể gây hại dựa trên bằng chứng trong nội dung.',
             'suspicious':'Có yêu cầu hoặc dấu hiệu cần xác minh trước khi thực hiện.',
             'need_context':'Chưa rõ thao tác hoặc thông tin quan trọng để đánh giá tiếp.',
             'clear':'Chưa ghi nhận dấu hiệu đáng ngờ trong phần nội dung đã kiểm tra.'}
    response.summary=SUMMARIES[selected] if selected else default[status]
    if status=='need_context' and 'requested_step' in gap_kinds:response.summary='Chưa biết bước xác nhận hoặc xử lý tiếp yêu cầu làm gì. Cần làm rõ thao tác trước khi đánh giá.'
    if status=='need_context' and 'withdrawal_next_requirement' in gap_kinds:response.summary='Nội dung mới thông báo lệnh rút đang chờ kiểm tra, chưa nêu bước tiếp theo. Chưa có căn cứ nói người gửi yêu cầu nộp phí hoặc giao mã.'
    response.display_summary=response.summary
    response.display_action=ACTIONS.get(selected,'Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.')
    response.recommended_actions=[response.display_action]
    response.answers.evidence_sufficiency.text=response.summary
    response.analysis.information_needed=bool(response.follow_up_questions)
    if request.question:response.answer_to_user=response.summary+(' '+' '.join(response.follow_up_questions) if response.follow_up_questions else '')
    return response
