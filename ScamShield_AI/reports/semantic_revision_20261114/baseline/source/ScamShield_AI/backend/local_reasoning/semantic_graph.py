"""Typed local event graph. Rules inspect grounded edges, never a keyword score.

This is a bounded symbolic parser, not a trained language model. Debug trace
contains IDs/counts/rejection codes; original evidence stays in annotations.
"""
import json
from functools import lru_cache
import re
from pathlib import Path
from ..local_observation.text import normalize, quote_ranges
from .clause_context import units
from .extract import scope_for
from .schema import Event, Span, Relation, Attribution, Participant, SemanticEvent, InputMessage
from .interpretation_schema import RiskMechanism

DATA=Path(__file__).resolve().parents[3]/'data/v2/semantic_graph_patterns.json'
INACTIVE={'quoted_warning','denial','hypothetical','unknown'}
ASSERTIONS={'changed_payee','third_party_payee','agreement_account','unverified_identity','unknown_counterparty',
    'blocked_withdrawal','promised_return','private_content_claim','other_content_claim','recovery_promise','independent_confirmation'}


@lru_cache(maxsize=1)
def patterns():
    data=json.loads(DATA.read_text(encoding='utf-8'))
    return [(r,re.compile(r['pattern'])) for r in data['rules']]


def construct(input,a):
    trace={'version':'semantic-graph-1.0','linker_called':True,'clauses':0,'events_before':len(a.events),
        'rules_run':[],'candidates':[],'retained_relation_ids':[],'rejected':[],'coreference':[],
        'decision_event_ids':[],'decision_relation_ids':[]}
    spans={s.span_id:s for s in a.spans};nodes=[];locations={};targets_by_source={}
    context_map={};extended=list(input.messages)
    for context in input.context_facts:
        targets=set(context.applies_to_message_ids) or {m.id for m in input.messages}
        scopes={e.scope_id for e in a.events if any(s in spans and spans[s].message_id in targets for s in e.evidence_refs)}
        scope=context.scope_id or (next(iter(scopes)) if len(scopes)==1 else None)
        if not scope or scope not in scopes:
            trace['rejected'].append({'context_id':context.id,'reason':'unbound_or_wrong_context_situation'});continue
        mid='context-graph:'+context.id;context_map[mid]=context.id
        extended.append(InputMessage(id=mid,text=context.text,scope_id=scope))
    working=input.model_copy(update={'messages':extended})
    messages={m.id:m for m in input.messages}
    for m,start,end,raw,source in units(working):
        trace['clauses']+=1
        if len(nodes)>=100:
            a.limitations.append('Phân tích một phần: đạt giới hạn 100 sự kiện đồ thị ngữ nghĩa.');break
        text=normalize(raw).text
        header=normalize(m.text).text
        warning=bool(re.match(r'\s*(?:canh bao|bai tuyen truyen|gia su trong bai tap)\s*:',header))
        parent=messages.get(m.parent_message_id)
        warning=warning or bool(parent and m.content_type=='ocr' and re.search(r'canh bao|canh giac',normalize(parent.text).text))
        ranges=quote_ranges(m.text)
        for rule,pattern in patterns():
            if rule['id'] not in trace['rules_run']:trace['rules_run'].append(rule['id'])
            found=pattern.search(text)
            if not found:continue
            n=normalize(raw);x,y=n.original_range(*found.span());offset=start+x
            if any(e.semantic and e.semantic.normalized_action==rule['action'] and e.semantic.message_id==m.id
                and e.evidence_refs and spans[e.evidence_refs[0]].start==start for e in nodes):continue
            quoted=any(left<=offset<right for left,right in ranges)
            prefix=text[:found.start()];action=rule['action']
            negated=bool(re.search(r'\b(?:dung|khong(?: can| nen| duoc)?)\s+(?:\w+\s+){0,2}$',prefix))
            if action=='disclosure_threat' and re.search(r'con khong|neu khong',prefix):negated=False
            if action in ('restricted_exit','avoid_verification','secrecy'):negated=False
            if action=='misstate_origin' and re.search(r'noi dung|khai dung|noi that|khai that',text):negated=True
            if action=='payment' and re.search(r'neu khong|khong tra',prefix) and re.search(r'gui cho|phat tan|dang len',text):negated=False
            role='quoted_warning' if warning or quoted or re.search(r'neu co ai|dung lam theo|canh giac',text) else 'denial' if negated else 'claim' if action in ASSERTIONS else 'request'
            if re.search(r'gia su|vi du mo phong',text):role='hypothetical'
            self_action=bool(re.search(r'\b(?:toi|minh)\s+(?:da|vua|se)\b',prefix))
            if self_action and action in ('payment','forward_funds'):role='claim'
            reported=bool(re.search(r'(?:ben ho tro|ho|nguoi do) (?:bao|yeu cau|noi)[^.!?;]{0,25}toi\b',prefix))
            if reported and role=='request':role='reported'
            if action=='independent_confirmation' and (
                not re.search(r'\b(?:toi|minh)\b',text) or re.search(r'(?:chua|khong) xac nhan|nguoi gui noi|ho noi',text)
                or not re.search(r'tai khoan|nguoi quen|nguoi nhan|nguoi gui|yeu cau chuyen',text)):
                role='unknown'
            same_clause=[e for e in a.events if not e.semantic and any(s in spans and spans[s].message_id==m.id and start<=spans[s].start<end for s in e.evidence_refs)]
            if action=='promised_return' and any(e.speech_role=='denial' and e.event_type=='transfer_funds' for e in same_clause):role='hypothetical'
            sid='graph:s'+str(len(a.spans)+1)
            s=Span(span_id=sid,message_id=None if m.id in context_map else m.id,context_id=context_map.get(m.id),start=start,end=end,quote=raw,label='action')
            a.spans.append(s);spans[sid]=s
            requester=source
            if reported:
                requester='mentioned:requester:'+m.id
            if requester not in {p.participant_id for p in a.participants}:
                a.participants.append(Participant(participant_id=requester,label='Nguồn yêu cầu được thuật lại, chưa rõ danh tính' if reported else 'Nguồn lời nói trong văn bản',interaction_role='requester',evidence_refs=[sid]))
            scope=scope_for(m,offset)
            target_key=(source,scope)
            named=re.search(r'\b(?:Bạn|Anh|Chị|Em|bạn|anh|chị|em)\s+([A-ZĐ][^\W\d_]{1,20})\s*,?\s+(?:hãy|cần|phải|chuyển|nhận|gửi|giao|mở)',raw)
            if named:
                pid='addressee:'+scope+':'+normalize(named.group(1)).text
                targets_by_source[target_key]=pid
                if pid not in {p.participant_id for p in a.participants}:
                    a.participants.append(Participant(participant_id=pid,label='Người được gọi tên trong yêu cầu, chưa xác minh danh tính',interaction_role='recipient',evidence_refs=[sid]))
            affected=targets_by_source.get(target_key,'recipient:unknown')
            owner=re.search(r'(?:ảnh|video|tài khoản|giấy tờ) của ([A-ZĐ][^\W\d_]{1,20})',raw)
            if owner and action in ('private_content_claim','other_content_claim'):
                affected='addressee:'+scope+':'+normalize(owner.group(1)).text
                if affected not in {p.participant_id for p in a.participants}:
                    a.participants.append(Participant(participant_id=affected,label='Chủ thể được nhắc trong đối tượng, chưa xác minh danh tính',interaction_role='affected_party',evidence_refs=[sid]))
            performer=affected if role in ('request','reported') else source
            status='claimed' if role in ('claim','reported') else 'unknown' if role=='unknown' else 'observed'
            semantic=SemanticEvent(message_id=m.id,situation_id=scope,speaker_id=source,requester_id=requester if role in ('request','reported') else None,
                performer_id=performer,affected_party_id=affected,normalized_action=action,object_type=rule['object'],
                transfer_source='unidentified_external_sender' if action=='receive_on_behalf' else 'addressee' if action in ('payment','forward_funds','surrender_credentials') else None,
                transfer_destination='another_account' if action=='forward_funds' else 'addressee_account' if action=='receive_on_behalf' else 'requester_or_designated_party' if action in ('payment','surrender_credentials') else None,
                negation_scope_refs=[sid] if negated else [],information_status=status,is_reported_request=reported)
            if m.id in context_map:
                semantic.message_id=None;semantic.context_id=context_map[m.id];semantic.information_status='user_reported'
            if re.search(r'\b(?:de|thi|moi|neu|muon)\b',text):semantic.stated_condition='condition_explicit_in_evidence'
            if re.search(r'\b(?:hom qua|sau do|truoc|khi|trong luc|muoi phut|hom nay)\b',text):semantic.stated_time='time_explicit_in_evidence'
            event=Event(event_id='graph:e'+str(len(a.events)+1),event_type=rule['event'],description=action,
                actor_id=performer,affected_party_id=affected,object=found.group(),polarity='negative' if negated else 'positive',
                modality='threat' if action=='disclosure_threat' else 'request' if role=='request' else 'report' if reported else 'assertion',
                temporal_state='completed' if self_action and role=='claim' else 'requested' if role=='request' else 'unknown',speech_role=role,
                attribution=Attribution(speaker_id=m.speaker_id,kind='quoted_warning' if role=='quoted_warning' else 'hypothetical' if role=='hypothetical' else 'user_report' if m.id in context_map else 'reported' if reported else 'sender_claim'),
                status=status,scope_id=scope,evidence_refs=[sid],extractor_rule_id=rule['id'],semantic=semantic)
            if action=='disclosure_threat':
                # Do not expose an unresolved "send it" as a disclosure fact
                # to the older coercion rules before reference resolution.
                event.event_type='other'
                if re.search(r'phat tan (?:anh|video)|gui (?:anh|video)',text):
                    event.semantic.object_type='private_media'
            if action=='payment':
                event.stated_purpose=next((e.stated_purpose for e in same_clause if e.event_type=='transfer_funds' and e.stated_purpose in ('purchase_exchange','optional_purchase')),None)
            if action=='surrender_credentials' and re.search(r'vao (?:trang|ung dung)',text) and not re.search(r'cho (?:toi|minh|anh|chi|em|nguoi khac|ben ho tro)',text):
                event.event_type='login';event.semantic.normalized_action='submit_credentials_to_page'
            a.events.append(event);nodes.append(event);locations[event.event_id]=(m.id,start,end,text,source)
    by_id={e.event_id:e for e in nodes}
    def active(e):return e.speech_role not in INACTIVE and e.polarity=='positive'
    def same_source(left,right):return locations[left.event_id][4]==locations[right.event_id][4]
    def link(kind,left,right,method,*,require_source=True):
        candidate={'type':kind,'from_id':left.event_id,'to_id':right.event_id,'method':method}
        trace['candidates'].append(candidate)
        reason=None
        if left.scope_id!=right.scope_id:reason='different_situation'
        elif left.affected_party_id!=right.affected_party_id:reason='different_affected_party'
        elif not active(left) or not active(right):reason='inactive_or_negated_endpoint'
        elif require_source and not same_source(left,right):reason='different_source'
        if reason:
            trace['rejected'].append({**candidate,'reason':reason});return None
        existing=next((r for r in a.relations if r.type==kind and r.from_id==left.event_id and r.to_id==right.event_id),None)
        if existing:return existing
        r=Relation(relation_id='graph:r'+str(len(a.relations)+1),type=kind,from_id=left.event_id,to_id=right.event_id,
            evidence_refs=list(dict.fromkeys(left.evidence_refs+right.evidence_refs)),scope_id=left.scope_id,status='inferred',
            rationale='Quan hệ có điều kiện ngôn ngữ và đối tượng/nguồn cùng phạm vi; không dựa vào khoảng cách đơn thuần.',rule_id=method)
        a.relations.append(r);trace['retained_relation_ids'].append(r.relation_id);return r
    def kind(name):return [e for e in nodes if e.semantic.normalized_action==name]
    # Transfer destinations and agreement are distinct entities, not a single
    # "account" keyword. Cross-source contradiction needs an explicit agreement.
    for pay in kind('payment'):
        for account in kind('changed_payee')+kind('third_party_payee'):
            link('same_object',pay,account,'SG-LINK-PAYEE')
        for avoid in kind('avoid_verification'):
            link('obstructs_verification',pay,avoid,'SG-LINK-OBSTRUCTS')
        for identity in kind('unverified_identity'):
            link('reason_given_for',identity,pay,'SG-LINK-IDENTITY')
    for account in kind('third_party_payee')+kind('changed_payee'):
        for agreement in kind('agreement_account'):
            link('contradiction',account,agreement,'SG-LINK-AGREEMENT',require_source=False)
    for receive in kind('receive_on_behalf'):
        for forward in kind('forward_funds'):
            # Need a routing expression, not just two unrelated payments.
            if re.search(r'khi nhan|chuyen tiep|nhan ho',locations[forward.event_id][3]):
                link('transfer_via',receive,forward,'SG-LINK-INTERMEDIARY')
    for forward in kind('forward_funds'):
        for instruction in kind('misstate_origin')+kind('secrecy'):
            link('reason_given_for',instruction,forward,'SG-LINK-CONCEAL-ROUTING')
    for custody in kind('document_custody'):
        for restriction in kind('restricted_exit'):
            link('document_retention_limits_exit',custody,restriction,'SG-LINK-DOCUMENT-EXIT')
        for debt in kind('exit_payment'):
            link('release_conditioned_on_payment',debt,custody,'SG-LINK-EXIT-COST')
    for request in kind('payment')+kind('priced_task'):
        for benefit in kind('promised_return'):
            text=locations[request.event_id][3];other=locations[benefit.event_id][3]
            condition=bool(re.search(r'\b(?:de|thi|moi|truoc|bao chung)\b',text) and re.search(r'se (?:tra|hoan)|moi|nhan lai|nha lai',other))
            if request.stated_purpose in ('purchase_exchange','optional_purchase') or re.search(r'(?:cong ty|nguoi khac)\s+(?:nhan|lay|rut) lai|(?:von|tien)\s+cho\s+(?:cong ty|nguoi khac)',other):
                condition=False
                trace['rejected'].append({'from_id':request.event_id,'to_id':benefit.event_id,'reason':'ordinary_purchase_or_other_beneficiary'})
            if request.semantic.normalized_action=='priced_task':
                # A task price alone is not proof of payment. Require an
                # explicitly reported deposit/blocked withdrawal in this scope.
                history=[e for e in nodes if e.scope_id==request.scope_id and active(e) and
                    (e.semantic.normalized_action=='payment' and e.speech_role=='claim' or e.semantic.normalized_action=='blocked_withdrawal')]
                condition=condition and bool(history)
                if not history:trace['rejected'].append({'from_id':request.event_id,'to_id':benefit.event_id,'reason':'task_payment_not_grounded'})
            if condition:link('prerequisite_for',request,benefit,'SG-LINK-PAYMENT-BENEFIT')
    for control in kind('remote_control'):
        for bank in kind('open_financial_data'):
            text=locations[bank.event_id][3]
            if re.search(r'trong luc|trong khi|khi (?:toi|ben minh) thao tac|dong thoi',text):
                link('controls_during',control,bank,'SG-LINK-CONTROL-BANK')
    for threat in kind('disclosure_threat'):
        candidates=[e for e in kind('private_content_claim')+kind('other_content_claim') if e.scope_id==threat.scope_id and same_source(e,threat) and active(e)]
        # Resolve omitted object from a unique same-source media antecedent.
        if len(candidates)==1 and candidates[0].semantic.object_type=='private_media':
            resolved=link('same_object',candidates[0],threat,'SG-LINK-MEDIA-COREFERENCE')
            if resolved:threat.semantic.object_type='private_media'
        else:
            trace['coreference'].append({'event_id':threat.event_id,'candidates':[e.event_id for e in candidates],'status':'ambiguous' if candidates else 'unknown'})
        for pay in kind('payment'):
            text=locations[threat.event_id][3]
            if threat.semantic.object_type=='private_media' and re.search(r'con khong|neu khong|khong tra|thi toi xoa|neu muon',text):
                retained=link('threatens_unless',threat,pay,'SG-LINK-PAYMENT-THREAT')
                if retained:threat.event_type='threaten_disclosure';threat.semantic.information_status='inferred'
    # Confirmation is a user-reported independent check, not system identity
    # verification. It never suppresses unrelated credential/exit threats.
    for confirmed in kind('independent_confirmation'):
        for target in kind('changed_payee')+kind('third_party_payee')+kind('unverified_identity'):
            link('state_update',target,confirmed,'SG-LINK-USER-CONFIRMATION',require_source=False)
    trace['events_added']=len(nodes);trace['relations_kept']=len(trace['retained_relation_ids'])
    trace['relations_before_validation']=len(a.relations)
    for e in a.events:
        if e.semantic:continue
        evidence=[spans[s] for s in e.evidence_refs if s in spans]
        if not evidence:continue
        first=evidence[0]
        e.semantic=SemanticEvent(message_id=first.message_id,context_id=first.context_id,situation_id=e.scope_id,
            speaker_id='speaker:'+e.attribution.speaker_id if e.attribution.speaker_id else None,
            requester_id=('speaker:'+e.attribution.speaker_id if e.attribution.speaker_id else None) if e.speech_role=='request' else None,
            performer_id=e.actor_id,affected_party_id=e.affected_party_id,normalized_action=e.event_type,
            object_type={'transfer_funds':'money','receive_funds':'money','withdraw_funds':'money','handover_asset':'asset',
                'provide_code':'code','code_identity':'code','provide_credentials':'credentials','provide_documents':'identity_documents',
                'share_screen':'device_access','grant_control':'device_access','retain_identity_documents':'identity_documents'}.get(e.event_type),
            negation_scope_refs=e.evidence_refs if e.polarity=='negative' else [],
            stated_time=e.event_time,information_status=e.status)
    a.graph_trace=trace
    return a


def interpret(a,interpretation):
    events={e.event_id:e for e in a.events};relations={r.relation_id:r for r in a.relations}
    def action(e):return e.semantic.normalized_action if e.semantic else None
    def edges(method):return [r for r in a.relations if r.rule_id==method]
    def related(method,source):return [r for r in edges(method) if r.from_id==source]
    confirmations={r.from_id for r in edges('SG-LINK-USER-CONFIRMATION')}
    def add(name,scope,links,asset,summary,recommendation,level='high'):
        if not links:return
        refs=list(dict.fromkeys(s for r in links for s in r.evidence_refs))
        nodes=list(dict.fromkeys(x for r in links for x in (r.from_id,r.to_id)))
        interpretation.mechanisms.append(RiskMechanism(mechanism_id=name+':'+scope,situation_id=scope,risk_status=level,
            action_refs=nodes,relation_refs=[r.relation_id for r in links],evidence_refs=refs,affected_party_id=events[links[0].from_id].affected_party_id or 'recipient:unknown',asset_or_right=asset,
            summary=summary,recommended_action=recommendation,limitations=['Danh tính và thiệt hại ngoài đời chưa được xác minh.']))
    for route in edges('SG-LINK-PAYEE'):
        if route.to_id in confirmations:continue
        obstruction=related('SG-LINK-OBSTRUCTS',route.from_id)
        conflict=related('SG-LINK-AGREEMENT',route.to_id)
        identity=[r for r in edges('SG-LINK-IDENTITY') if r.to_id==route.from_id and r.from_id not in confirmations]
        if obstruction and (conflict or identity and action(events[route.to_id])=='third_party_payee'):
            add('M-DESTINATION-UNVERIFIED',route.scope_id,[route,*obstruction,*conflict,*identity],'money',
                'Người gửi yêu cầu chuyển tiền sang nơi nhận khác thỏa thuận hoặc khác danh tính tự nhận, đồng thời cản trở xác minh qua kênh đã biết. Có nguy cơ chuyển tiền sai người nhận; chưa xác minh người gửi giả mạo.',
                'Tạm dừng chuyển tiền; tự liên hệ đầu mối hợp đồng hoặc người quen qua kênh đã biết để đối chiếu tài khoản.')
    for routing in edges('SG-LINK-INTERMEDIARY'):
        conceal=[r for r in edges('SG-LINK-CONCEAL-ROUTING') if r.to_id==routing.to_id]
        lying=[r for r in conceal if action(events[r.from_id])=='misstate_origin']
        unknown=[e for e in events.values() if action(e)=='unknown_counterparty' and e.scope_id==routing.scope_id and e.speech_role not in INACTIVE]
        if lying or conceal and unknown:
            add('M-INTERMEDIARY-CONCEALMENT',routing.scope_id,[routing,*conceal],'money/account',
                'Bạn được yêu cầu nhận tiền rồi chuyển tiếp cho bên khác và che giấu hoặc khai khác mục đích nhận tiền. Có nguy cơ bị lợi dụng tài khoản; chưa xác minh nguồn tiền hoặc hành vi phạm pháp.',
                'Không nhận/chuyển hộ hoặc khai khác mục đích khi chưa xác minh được các bên và lý do giao dịch.')
    for exit in edges('SG-LINK-DOCUMENT-EXIT'):
        costs=[r for r in edges('SG-LINK-EXIT-COST') if r.to_id==exit.from_id]
        add('M-CONTROL-EXIT',exit.scope_id,[exit,*costs],'freedom/documents',
            'Yêu cầu giao giấy tờ đi kèm hạn chế tự rời chỗ ở có thể làm mất quyền chủ động di chuyển; điều kiện trả chi phí để về càng tạo bất lợi. Chưa xác minh đã xảy ra mua bán người hay cưỡng ép.',
            'Tạm dừng giao giấy tờ và di chuyển; cùng người tin cậy xác minh hợp đồng, nơi làm việc và quyền rời đi.')
    for condition in edges('SG-LINK-PAYMENT-BENEFIT'):
        add('M-PAYMENT-BENEFIT',condition.scope_id,[condition],'money',
            'Người gửi đặt việc trả thêm hoặc hoàn tất bước chi tiền làm điều kiện nhận lại vốn hay mở quyền rút. Có nguy cơ tiếp tục mất tiền; số dư được hiển thị chưa được hệ thống xác minh.',
            'Tạm dừng nộp thêm và kiểm tra giao dịch qua đầu mối độc lập; không dựa vào số dư hiển thị để tiếp tục chuyển tiền.')
    for exposure in edges('SG-LINK-CONTROL-BANK'):
        add('M-CONTROL-FINANCIAL-DATA',exposure.scope_id,[exposure],'device/account',
            'Người khác yêu cầu truy cập hoặc thao tác từ xa trong lúc bạn mở dữ liệu ngân hàng. Có nguy cơ lộ thông tin hoặc bị thao tác ngoài ý muốn; chưa xác minh thiết bị nhiễm mã độc hay tiền đã bị chuyển.',
            'Dừng phiên hỗ trợ từ xa trước khi mở ngân hàng; xác minh yêu cầu qua tổng đài quen dùng.')
    for threat in edges('SG-LINK-PAYMENT-THREAT'):
        media=[r for r in edges('SG-LINK-MEDIA-COREFERENCE') if r.to_id==threat.from_id]
        add('M-PAYMENT-DISCLOSURE',threat.scope_id,[threat,*media],'privacy/money',
            'Có lời đe dọa phát tán nội dung tới người khác nhằm buộc bạn trả tiền. Chưa xác minh ảnh là thật hoặc người gửi có dữ liệu như tự nhận.',
            'Không vội trả tiền; lưu bằng chứng và tìm hỗ trợ từ người tin cậy, dùng chức năng báo cáo tài khoản.')
    for e in events.values():
        if action(e)!='surrender_credentials' or e.speech_role in INACTIVE or e.polarity!='positive':continue
        interpretation.mechanisms.append(RiskMechanism(mechanism_id='M-CREDENTIAL-TRANSFER:'+e.event_id,situation_id=e.scope_id,risk_status='high',
            action_refs=[e.event_id],relation_refs=[],evidence_refs=e.evidence_refs,affected_party_id=e.affected_party_id,asset_or_right='account_access',
            summary='Người gửi yêu cầu cung cấp thông tin đăng nhập cho bên khác, có thể làm mất quyền kiểm soát tài khoản. Chưa xác minh đã có truy cập hoặc thiệt hại.',
            recommended_action='Không gửi thông tin đăng nhập; tự mở ứng dụng chính thức và xác minh đơn vị hỗ trợ.'))
    a.graph_trace['decision_event_ids']=list(dict.fromkeys(e for m in interpretation.mechanisms for e in m.action_refs))
    a.graph_trace['decision_relation_ids']=list(dict.fromkeys(r for m in interpretation.mechanisms for r in m.relation_refs))
    a.graph_trace['mechanisms']=[m.mechanism_id for m in interpretation.mechanisms]
    for s in interpretation.situations:
        nodes=[e for e in events.values() if e.scope_id==s.situation_id and e.semantic]
        s.object_types=list(dict.fromkeys(e.semantic.object_type for e in nodes if e.semantic.object_type))
        s.condition_refs=[r.relation_id for r in a.relations if r.scope_id==s.situation_id and r.type in ('prerequisite_for','threatens_unless','release_conditioned_on_payment')]
        s.reported_state_refs=[e.event_id for e in nodes if e.speech_role in ('claim','reported')]
        s.verification_report_refs=[e.event_id for e in nodes if action(e)=='independent_confirmation' and e.speech_role not in INACTIVE]
        s.mechanism_refs=[m.mechanism_id for m in interpretation.mechanisms if m.situation_id==s.situation_id]
    return interpretation


def assess(assessment,interpretation):
    rank={'clear':0,'need_context':1,'suspicious':2,'high':3}
    if not interpretation.mechanisms:return assessment
    selected=max(interpretation.mechanisms,key=lambda m:rank[m.risk_status])
    if rank[selected.risk_status]<rank.get(assessment.risk_status,0) or assessment.safety_urgency=='urgent':return assessment
    assessment.risk_status=selected.risk_status;assessment.summary=selected.summary
    assessment.recommended_actions=[selected.recommended_action];assessment.safety_urgency='preventive'
    assessment.follow_up_questions=[]
    assessment.evidence_refs=list(dict.fromkeys(assessment.evidence_refs+[s for m in interpretation.mechanisms for s in m.evidence_refs]))
    assessment.applicable_rule_ids=list(dict.fromkeys(assessment.applicable_rule_ids+[m.mechanism_id.split(':')[0] for m in interpretation.mechanisms]))
    assessment.supported_conclusions=list(dict.fromkeys(assessment.supported_conclusions+[m.mechanism_id.split(':')[0] for m in interpretation.mechanisms]))
    return assessment


def clarify(a,interpretation,assessment):
    if assessment.risk_status=='high':return assessment
    active=[e for e in a.events if e.semantic and e.speech_role not in INACTIVE and e.polarity=='positive']
    actions={e.semantic.normalized_action for e in active}
    question=None;field=None
    if 'priced_task' in actions and 'promised_return' in actions:
        question='Nhiệm vụ đó có yêu cầu bạn chi hoặc nộp tiền không? Chỉ mô tả yêu cầu, không gửi thông tin tài khoản.';field='task_requires_payment'
    elif 'changed_payee' in actions or 'third_party_payee' in actions:
        question='Bạn đã tự xác nhận người nhận và tài khoản mới qua đầu mối hoặc số liên lạc quen dùng chưa?';field='independent_confirmation'
    elif 'remote_control' in actions:
        question='Trong lúc hỗ trợ từ xa, họ có yêu cầu mở ngân hàng hoặc thông tin nhạy cảm không?';field='sensitive_data_during_control'
    if question:
        assessment.follow_up_questions=[question]
        a.graph_trace['question_bindings']=[{'situation_id':next((e.scope_id for e in active),None),'missing_field':field,
            'may_change_to':['high','suspicious','need_context','clear']}]
    return assessment


def summarize(a):
    """Project graph facts to the existing 18-field view, never vote on fields."""
    spans={s.span_id:s for s in a.spans}
    requested=[e for e in a.events if e.semantic and e.semantic.extraction_method=='local_structural_patterns_v1'
        and (e.speech_role=='request' or e.semantic.is_reported_request) and e.polarity=='positive']
    field=a.answers_18.requested_actions
    if requested:
        field.status='observed';field.extraction_method='local_semantic_graph'
        field.value.event_ids=list(dict.fromkeys(field.value.event_ids+[e.event_id for e in requested]))
        field.evidence_refs=list(dict.fromkeys(field.evidence_refs+[s for e in requested for s in e.evidence_refs]))
        field.value.statements=list(dict.fromkeys(field.value.statements+[spans[e.evidence_refs[0]].quote for e in requested]))
    for name,relations in [('conditions_and_sequence',[r for r in a.relations if r.rule_id.startswith('SG-LINK-')]),
                           ('contradictions_and_alternatives',[r for r in a.relations if r.type in ('contradiction','state_update')])]:
        field=getattr(a.answers_18,name)
        if not relations:continue
        field.status='inferred';field.extraction_method='local_semantic_graph'
        field.value.relation_ids=list(dict.fromkeys(field.value.relation_ids+[r.relation_id for r in relations]))
        field.value.event_ids=list(dict.fromkeys(field.value.event_ids+[x for r in relations for x in (r.from_id,r.to_id)]))
        field.evidence_refs=list(dict.fromkeys(field.evidence_refs+[s for r in relations for s in r.evidence_refs]))
        field.value.statements=list(dict.fromkeys(field.value.statements+[r.rationale for r in relations]))
