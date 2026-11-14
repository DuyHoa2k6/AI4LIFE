"""Bounded clause/context extraction: requester -> request -> condition -> effect.

No trained model and no intent/identity verification. Never infer a dangerous
relationship from keyword co-occurrence alone; materialize supported relations.
"""
import re
from ..local_observation.text import normalize,quote_ranges
from ..local_observation.segmentation import segments
from .extract import scope_for
from .schema import Span,Event,Attribution,Relation,InteractionFrame
from .semantic_phrases import pattern

PAY=pattern('payment_request')
RETURN=pattern('return_benefit')
HANDOVER=pattern('asset_handover')
UNPAID=pattern('payment_unconfirmed')
OPTIONAL=pattern('optional_purchase')
DIRECT=re.compile(r'\b(?:ban|anh|chi|em)\s+(?:can|hay|phai|vui long|co the)?\s*$|\b(?:hay|vui long|can|phai|cu)\s*$')
CONNECT=re.compile(r'\b(?:truoc|thi (?:ben minh |ben toi |he thong )?moi|moi duoc|moi nhan|moi rut|de|neu muon|muon)\b')


def role_for(input,m,raw,offset):
    text=normalize(raw).text;prefix=normalize(raw[:offset]).text
    parent=next((p for p in input.messages if p.id==m.parent_message_id),None)
    if (parent and m.content_type=='ocr' and re.search(r'canh bao|canh giac',normalize(parent.text).text)) or any(a<=offset<b for a,b in quote_ranges(raw)):
        return 'quoted_warning'
    if re.search(r'canh bao|canh giac|nhac moi nguoi|dung lam theo',text):return 'quoted_warning'
    if re.search(r'\b(?:dung|khong(?: can| nen| duoc)?)\s+(?:\w+\s+){0,2}$',prefix):return 'denial'
    if re.search(r'gia su|vi du mo phong|bai tap',text):return 'hypothetical'
    if re.search(r'\b(?:ho|nguoi mua|nguoi gui|nguoi do) (?:noi|bao|yeu cau)|toi (?:nghe|doc)',prefix):return 'reported'
    if re.search(r'\b(?:toi|minh|ben minh)\s+(?:da|vua|dang|se|tu)?\s*$',prefix):return 'claim'
    if not prefix.strip(' ,:') or DIRECT.search(prefix):return 'request'
    return 'unknown'


def extract_interactions(input,a):
    frames=[];spans={s.span_id:s for s in a.spans}
    def span(m,start,end,label='action'):
        sid='ctx:s'+str(len(a.spans)+1)
        s=Span(span_id=sid,message_id=m.id,start=start,end=end,quote=m.text[start:end],label=label)
        a.spans.append(s);spans[sid]=s;return sid
    def event(m,kind,role,scope,refs,description):
        eid='ctx:e'+str(len(a.events)+1)
        e=Event(event_id=eid,event_type=kind,description=description,actor_id='recipient:unknown' if role=='request' else None,
            recipient_id=None,affected_party_id='recipient:unknown',object=None,
            polarity='negative' if role=='denial' else 'positive',modality='request' if role=='request' else 'conditional' if role=='claim' else 'assertion',
            temporal_state='requested' if role=='request' else 'planned',speech_role=role,
            attribution=Attribution(speaker_id=m.speaker_id,kind=role if role in ('quoted_warning','hypothetical','reported') else 'sender_claim'),
            status='unknown' if role=='unknown' else 'observed' if role=='request' else 'claimed',scope_id=scope,evidence_refs=refs,extractor_rule_id='CONTEXT-CLAUSE-1')
        a.events.append(e);return e
    def relation(kind,left,right,rule):
        if any(r.type==kind and r.from_id==left.event_id and r.to_id==right.event_id for r in a.relations):return
        a.relations.append(Relation(relation_id='ctx:r'+str(len(a.relations)+1),type=kind,
            from_id=left.event_id,to_id=right.event_id,evidence_refs=list(dict.fromkeys(left.evidence_refs+right.evidence_refs)),
            status='inferred',scope_id=left.scope_id,rationale='Liên hệ được nêu trong cụm câu cùng phạm vi; không xác minh sự việc ngoài đời.',rule_id=rule))
    for m in input.messages:
        if len(frames)>=24:break
        units=[];seen=set()
        for s in segments(m.text):
            key=(s.context_start,s.context_end)
            if key not in seen:seen.add(key);units.append(key)
        for unit_index,(start,end) in enumerate(units):
            if len(frames)>=24:
                a.limitations.append('Đạt giới hạn 24 khung ngữ cảnh; phần còn lại chưa kiểm tra đầy đủ.')
                break
            raw=m.text[start:end];n=normalize(raw)
            receipt=re.search(r'\b(?:da )?gui (?:anh )?bien lai\b',n.text)
            if receipt:
                x,y=n.original_range(*receipt.span());rrole=role_for(input,m,raw,x)
                rrole=rrole if rrole in ('quoted_warning','reported','hypothetical') else 'claim'
                claim=event(m,'other',rrole,scope_for(m,start+x),[span(m,start,end,'statement')],'Người viết tự nhận đã gửi biên lai; không chứng minh thanh toán')
                claim.extractor_rule_id='CONTEXT-RECEIPT-CLAIM';claim.temporal_state='completed'
            unpaid=UNPAID.search(n.text)
            if unpaid:
                x,y=n.original_range(*unpaid.span());scope=scope_for(m,start+x)
                existing=any(e.event_type=='receive_funds' and e.polarity=='negative' and e.scope_id==scope
                    and any(spans[r].message_id==m.id and start<=spans[r].start<end for r in e.evidence_refs if r in spans) for e in a.events)
                if not existing:
                    state_role=role_for(input,m,raw,x)
                    state_role=state_role if state_role in ('quoted_warning','hypothetical','reported') else 'hypothetical' if n.text.lstrip().startswith('neu ') else 'claim'
                    state=event(m,'receive_funds',state_role,scope,[span(m,start,end,'statement')],'Người viết báo chưa nhận hoặc chưa xác nhận khoản thanh toán')
                    state.polarity='negative';state.temporal_state='pending';state.modality='assertion'
            matches=[(match,kind) for pattern,kind in ((PAY,'transfer_funds'),(HANDOVER,'handover_asset')) for match in pattern.finditer(n.text)]
            for match,kind in matches:
                if len(frames)>=24:break
                left,right=n.original_range(*match.span())
                # Accent folding merges “bạn giao” and “bàn giao”. Preserve the
                # explicit addressee in the original text before role resolution.
                role_offset=left+4 if raw[left:].casefold().startswith('bạn giao') else left
                role=role_for(input,m,raw,role_offset)
                scope=scope_for(m,start+left)
                sid=span(m,start,end);request=event(m,kind,role,scope,[sid],
                    'Yêu cầu nộp/chuyển tiền trong cụm điều kiện' if kind=='transfer_funds' else 'Yêu cầu giao tài sản trong ngữ cảnh')
                frame=InteractionFrame(frame_id='frame:'+request.event_id,requester_id='speaker:'+(m.speaker_id or m.id),target_id=request.actor_id,
                    scope_id=scope,speech_role=role,action_event_id=request.event_id,requested_action=raw[left:right],
                    possible_effect='Có thể mất thêm tiền nếu thực hiện mà chưa xác minh quyền lợi.' if kind=='transfer_funds' else 'Có thể mất tài sản nếu giao trước khi xác nhận thanh toán.',evidence_refs=[sid])
                frames.append(frame)
                if kind=='handover_asset' and role=='denial' and re.search(r'truoc khi (?:nhan|thay) tien',n.text):
                    # A prohibited future handover is not an assertion that
                    # payment was already received in the subordinate clause.
                    for old in a.events:
                        if old.event_type!='receive_funds' or old.scope_id!=scope:continue
                        if any(spans[s].message_id==m.id and start<=spans[s].start<end for s in old.evidence_refs if s in spans):
                            old.speech_role='hypothetical';old.temporal_state='hypothetical';old.attribution.kind='hypothetical'
                if re.search(r'tai xe.{0,45}cho|het han|trong \d+ phut|truoc \d+ gio',n.text):frame.communication_functions.append('time_pressure_cue')
                if role!='request':continue
                if kind=='transfer_funds':
                    if match.group().startswith('mua') and OPTIONAL.search(n.text):
                        frame.stated_purpose='Lời nhắn nêu mua tùy chọn hoặc không đặt làm điều kiện nhận lại tiền.'
                        request.stated_purpose='optional_purchase'
                        continue
                    # Ignore a benefit verb embedded in the product name,
                    # e.g. "gói mở quyền rút", and seek the actual outcome.
                    benefit=RETURN.search(n.text,match.end())
                    if not benefit:
                        first=RETURN.search(n.text)
                        if first and first.end()<=match.start():benefit=first
                    benefit_n=n;benefit_start=start
                    if not benefit and re.search(r'\btruoc\b',n.text) and unit_index+1<len(units):
                        next_start,next_end=units[unit_index+1];candidate=normalize(m.text[next_start:next_end])
                        if re.match(r'\s*(?:sau do|xong buoc nay|khi do|luc do)\b',candidate.text) and not re.search(r'canh bao|dung|khong|chua',candidate.text):
                            benefit=RETURN.search(candidate.text);benefit_n=candidate;benefit_start=next_start
                    separate=benefit_start!=start
                    goal_prefix=benefit_n.text[:benefit.start()] if benefit else ''
                    other_beneficiary=bool(re.search(r'\b(?:cong ty|nguoi ban|nguoi mua|nguoi khac|ho)\s*$',goal_prefix))
                    if benefit and re.match(r'\s+cho\s+(?:cong ty|nguoi ban|nguoi khac)\b',benefit_n.text[benefit.end():]):other_beneficiary=True
                    if benefit and not other_beneficiary and not re.search(r'\b(?:khong|chua|dung)\s*$',goal_prefix) and CONNECT.search(n.text) and (separate or not (max(match.start(),benefit.start())<min(match.end(),benefit.end()))):
                        x,y=benefit_n.original_range(*benefit.span());benefit_ref=span(m,benefit_start+x,benefit_start+y,'purpose')
                        goal_scope=scope_for(m,benefit_start+x)
                        if goal_scope!=scope:continue
                        goal=event(m,'withdraw_funds' if benefit.group().startswith('rut') else 'receive_funds','claim',scope,[benefit_ref,sid],
                            'Quyền lợi nhận/rút lại tiền được nêu như điều kiện, chưa xác minh khả năng nhận')
                        goal.actor_id=frame.target_id
                        relation('prerequisite_for',request,goal,'CTX-PAYMENT-CONDITION')
                        relation('same_transaction',request,goal,'CTX-SAME-TRANSACTION')
                        frame.benefit_event_id=goal.event_id;frame.stated_purpose=m.text[benefit_start+x:benefit_start+y]
                        frame.condition='Nộp/chuyển tiền trước là điều kiện để nhận/rút lại khoản được nêu.'
                        frame.evidence_refs.append(benefit_ref)
                    else:
                        ordinary=re.search(r'\bde (?:duoc )?nhan (?:hang|san pham|chiec|cai|bo)\b[^.!?;]*',n.text)
                        if ordinary:
                            x,y=n.original_range(*ordinary.span());frame.stated_purpose=m.text[start+x:start+y]
                            request.stated_purpose='purchase_exchange'
                            for old in a.events:
                                if old.event_type!='transfer_funds' or old.scope_id!=scope or old.speech_role!='request':continue
                                if any(spans[s].message_id==m.id and spans[s].label=='verb' and start+left<=spans[s].start<start+right for s in old.evidence_refs if s in spans):
                                    old.stated_purpose='purchase_exchange'
                        else:frame.missing_information.append('Chưa xác định được quyền lợi hoặc quan hệ điều kiện của khoản phải nộp.')
                else:
                    # The asset noun is unrestricted. Require a same-message,
                    # nearby and same-transaction payment observation to bind it.
                    payments=[]
                    for old in list(a.events):
                        if old.event_type!='receive_funds' or old.scope_id!=scope or old.speech_role not in ('claim','reported'):continue
                        if old.temporal_state in ('past','hypothetical'):continue
                        locations=[spans[r] for r in old.evidence_refs if r in spans and spans[r].message_id==m.id]
                        if not locations or not any(0<=start-s.start<=450 for s in locations):continue
                        payments.append(old)
                    negative=[p for p in payments if p.polarity=='negative']
                    positive=[p for p in payments if p.polarity=='positive' and p.temporal_state=='completed' and p.speech_role=='claim']
                    if negative and re.search(r'\btruoc\b|\bcu\b',n.text):
                        state=negative[-1];request.affected_party_id=state.affected_party_id
                        relation('before',request,state,'CTX-HANDOVER-BEFORE-PAYMENT')
                        relation('same_transaction',request,state,'CTX-SAME-TRANSACTION')
                        frame.condition='Giao tài sản trước khi người nhận xác nhận thanh toán.'
                        frame.evidence_refs=list(dict.fromkeys(frame.evidence_refs+state.evidence_refs))
                    elif positive and not negative:
                        state=positive[-1];request.affected_party_id=state.affected_party_id
                        relation('before',state,request,'REL-REPORTED-PAYMENT-FIRST')
                        relation('same_transaction',state,request,'CTX-SAME-TRANSACTION')
                        frame.stated_purpose='Người viết cho biết đã nhận đủ tiền trước khi giao.'
                    else:frame.missing_information.append('Chưa xác nhận trạng thái thanh toán của đúng giao dịch.')
    # Frame all remaining requests too, using their clause instead of a verb as
    # the salient evidence. This does not invent a purpose when it is absent.
    covered={f.action_event_id for f in frames}
    for old in list(a.events):
        if len(frames)>=24:break
        if old.event_id in covered or old.speech_role!='request' or old.polarity!='positive':continue
        refs=[spans[r] for r in old.evidence_refs if r in spans and spans[r].message_id]
        if not refs:continue
        original=refs[0];m=next(m for m in input.messages if m.id==original.message_id)
        unit=next((s for s in segments(m.text) if s.start<=original.start<s.end),None)
        sid=span(m,unit.context_start,unit.context_end) if unit else original.span_id
        frames.append(InteractionFrame(frame_id='frame:'+old.event_id,requester_id='speaker:'+(m.speaker_id or m.id),
            target_id=old.actor_id or old.affected_party_id or 'recipient:unknown',scope_id=old.scope_id,
            speech_role=old.speech_role,action_event_id=old.event_id,requested_action=spans[sid].quote,
            possible_effect={'provide_code':'Có thể lộ mã nếu đây là thông tin xác thực.',
                'provide_credentials':'Có thể mất quyền truy cập tài khoản.', 'share_screen':'Có thể lộ thông tin đang hiển thị.'}.get(old.event_type,'Cần đối chiếu mục đích và quyền lợi của người được yêu cầu.'),
            evidence_refs=[sid]))
    f=a.answers_18.requested_actions
    for frame in frames:
        if frame.speech_role=='request':
            f.status='observed'
            f.value.statements=list(dict.fromkeys(f.value.statements+[spans[frame.evidence_refs[0]].quote]))
            f.value.event_ids=list(dict.fromkeys(f.value.event_ids+[frame.action_event_id]))
            f.evidence_refs=list(dict.fromkeys(f.evidence_refs+frame.evidence_refs))
    return a,frames


def finalize_interactions(assessment,frames):
    if assessment.risk_status=='need_context':
        if any(f.speech_role=='request' and f.requested_action and f.missing_information for f in frames):
            if any('thanh toán' in x for f in frames for x in f.missing_information):
                assessment.follow_up_questions=['Bạn đã tự kiểm tra và xác nhận khoản tiền vào tài khoản cho giao dịch này chưa?']
            else:
                assessment.follow_up_questions=['Khoản phải nộp dùng để làm gì, và họ có đặt nó làm điều kiện để bạn nhận hoặc rút lại tiền không?']
    return assessment
