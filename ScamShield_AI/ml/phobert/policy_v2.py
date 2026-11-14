"""Opt-in typed candidate. No text patterns or reference labels decide risk here."""
import copy
from .policy_ontology import POLICY_ATTRS,VERSION
from .schema import RELATIONS,ROLES
from .decision import assess as stable_assess

def verify(messages,raw):
    graph=copy.deepcopy(raw);texts={m['id']:m['text'] for m in messages};speakers={m['id']:m.get('speaker_id') for m in messages}
    order={m['id']:i for i,m in enumerate(messages)};discarded=[];spans={};events={};relations=[]
    def reject(kind,identifier,reason):discarded.append({'kind':kind,'id':identifier,'reason':reason})
    for s in graph.get('spans',[]):
        text=texts.get(s.get('message_id'));a,b=s.get('start'),s.get('end')
        if text is None or type(a) is not int or type(b) is not int or not 0<=a<b<=len(text) or text[a:b]!=s.get('quote'):reject('span',s.get('id'),'invalid_evidence');continue
        if s['id'] in spans:reject('span',s['id'],'duplicate_id');continue
        spans[s['id']]=s
    people={'speaker:'+s for s in speakers.values() if s}|{'unknown:'+mid+':addressee' for mid in speakers}
    people|={'mention:'+s['id'] for s in spans.values() if s['label']=='entity'}
    for e in graph.get('events',[]):
        identifier=e.get('id');s=spans.get(e.get('anchor_id'));attrs=e.get('attributes',{})
        if identifier in events:reject('event',identifier,'duplicate_id');continue
        if not s or s['label']!='action':reject('event',identifier,'invalid_anchor');continue
        if e.get('speaker_id')!=speakers[s['message_id']]:reject('event',identifier,'speaker_mismatch');continue
        if set(attrs)!=set(POLICY_ATTRS) or any(v not in POLICY_ATTRS[k] for k,v in attrs.items()):reject('event',identifier,'invalid_policy_attribute');continue
        e['roles']={k:('unknown:'+s['message_id']+':addressee' if pid=='recipient:unknown' else pid) for k,pid in e.get('roles',{}).items() if k in ROLES}
        for role,pid in list(e['roles'].items()):
            if pid not in people:del e['roles'][role];reject('role',identifier+':'+role,'unbound_participant')
        if e.get('speaker_id'):e['roles']['speaker']='speaker:'+e['speaker_id']
        refs=e.get('argument_refs',[])
        if not set(refs)<=set(spans):reject('event',identifier,'invalid_argument');continue
        events[identifier]=e
    seen=set()
    for r in graph.get('relations',[]):
        a,b=events.get(r.get('source')),events.get(r.get('target'));reason=None
        if r.get('id') in seen:reason='duplicate_id'
        elif r.get('label') not in RELATIONS:reason='unknown_relation'
        elif not a or not b or a['id']==b['id']:reason='invalid_endpoint'
        elif not {a['anchor_id'],b['anchor_id']}<=set(r.get('evidence_refs',[])) or not set(r.get('evidence_refs',[]))<=set(spans):reason='missing_endpoint_evidence'
        elif a.get('transaction_id') and b.get('transaction_id') and a['transaction_id']!=b['transaction_id']:reason='transaction_mismatch'
        elif r['label']=='state_update':
            aa,ba=a['attributes'],b['attributes'];sa,sb=spans[a['anchor_id']],spans[b['anchor_id']]
            if aa['action_type']!=ba['action_type'] or aa['object_type']!=ba['object_type']:reason='update_object_mismatch'
            elif aa['speech_act'] not in ('claim','reported') or ba['speech_act'] not in ('claim','reported'):reason='update_requires_reports_not_requests'
            elif not a.get('transaction_id') or a['transaction_id']!=b.get('transaction_id'):reason='update_requires_resolved_scope'
            elif (order[sa['message_id']],sa['start'])>=(order[sb['message_id']],sb['start']):reason='update_wrong_direction'
            elif a['roles'].get('performer') and b['roles'].get('performer') and a['roles']['performer']!=b['roles']['performer']:reason='update_actor_mismatch'
        if reason:reject('relation',r.get('id'),reason)
        else:seen.add(r.get('id'));relations.append(r)
    limitations=list(graph.get('limitations',[]))
    if discarded:limitations.append('Một phần dữ kiện hoặc quan hệ không qua kiểm chứng.')
    return {**graph,'spans':list(spans.values()),'events':list(events.values()),'relations':relations,'discarded':discarded,'limitations':list(dict.fromkeys(limitations)),'policy_version':VERSION}

COMPATIBLE_OBJECTS={'transfer':{'money'},'withdraw':{'money'},'borrow':{'money'},'disclose_credentials':{'auth_code','credentials'},'grant_control':{'device'},'share_screen':{'device','financial_data'},'install':{'device'},'retain_documents':{'identity_document','document'}}

def assess(graph):
    graph=copy.deepcopy(graph);events=graph['events'];relations=graph['relations'];spans={s['id']:s for s in graph['spans']};rules=[]
    def attr(e,k):return e['attributes'][k]
    def requested(e):
        speaker='speaker:'+e['speaker_id'] if e.get('speaker_id') else None
        return attr(e,'speech_act')=='request' and attr(e,'polarity')=='positive' and attr(e,'temporal_state') not in ('completed','not_completed') and not (speaker and e.get('roles',{}).get('performer')==speaker)
    invalid=set()
    for e in events:
        if attr(e,'action_type') in COMPATIBLE_OBJECTS and attr(e,'object_type') not in COMPATIBLE_OBJECTS[attr(e,'action_type')]:invalid.add(e['id'])
    if invalid:
        graph['events']=[e for e in events if e['id'] not in invalid];graph['relations']=[r for r in relations if r['source'] not in invalid and r['target'] not in invalid]
        graph['limitations'].append('Action/object dự đoán không tương thích; chưa dùng để kết luận.')
        events=graph['events'];relations=graph['relations']
    def relation(a,b,label):return any(r['label']==label and ((r['source'],r['target'])==(a['id'],b['id']) or label=='same_transaction' and {r['source'],r['target']}=={a['id'],b['id']}) for r in relations)
    def same(a,b):return a['id']!=b['id'] and relation(a,b,'same_transaction')
    def conclusion(rule,risk,items,tags,summary,action):
        ids={e['id'] for e in items};rs=[r for r in relations if r['source'] in ids and r['target'] in ids]
        refs=list(dict.fromkeys([e['anchor_id'] for e in items]+[s for e in items for s in e.get('argument_refs',[])]+[s for r in rs for s in r['evidence_refs']]))
        rules.append({'rule_id':rule,'risk':risk,'event_ids':sorted(ids),'relation_ids':[r['id'] for r in rs],'evidence_refs':refs,'mechanism_tags':tags,
          'mechanism':summary,'conditions':[r['label'] for r in rs],'contradictions':[],'limitations':['Chưa xác minh người gửi hoặc sự việc ngoài đời.'],'action':action})
    # Reuse stable typed rules; replace its mixed-mechanism generic explanation.
    inherited=stable_assess(graph)
    for rule in inherited.get('rules',[]):
        if rule['rule_id']!='PB-SENSITIVE-REQUEST':rules.append(rule)
    summaries={
      'install':('Có yêu cầu cài ứng dụng; cần xác minh nguồn và phạm vi truy cập.','Kiểm tra nhà phát hành và mục đích trước khi cài.'),
      'grant_control':('Có yêu cầu cấp quyền điều khiển thiết bị; cần xác minh phạm vi và đầu mối hỗ trợ.','Chưa cấp quyền trước khi tự xác minh đầu mối.'),
      'share_screen':('Có yêu cầu chia sẻ màn hình; cần kiểm tra dữ liệu có thể bị lộ.','Đóng dữ liệu nhạy cảm và xác minh người hỗ trợ.'),
      'borrow':('Có yêu cầu đứng tên vay; người đứng tên có thể phải chịu nghĩa vụ trả nợ.','Đọc đầy đủ nghĩa vụ và tham khảo đầu mối độc lập trước khi đồng ý.'),
      'retain_documents':('Có yêu cầu giao giấy tờ để bên khác giữ; cần xác minh quyền lấy lại.','Giữ quyền kiểm soát giấy tờ và kiểm tra điều kiện nhận lại.')}
    superseded={r['source'] for r in relations if r['label']=='state_update' and any(s['label']=='same_transaction' and {s['source'],s['target']}=={r['source'],r['target']} for s in relations)}
    active=[e for e in events if e['id'] not in superseded]
    for a in active:
        kind=attr(a,'action_type')
        if requested(a) and kind in summaries:
            summary,action=summaries[kind];conclusion('PV2-SENSITIVE-'+kind,'suspicious',[a],['sensitive_request'],summary,action)
        if kind=='promise_income' and attr(a,'speech_act') not in ('quoted_warning','hypothetical'):
            for b in active:
                if same(a,b) and attr(b,'action_type')=='conceal_terms':conclusion('PV2-UNSUPPORTED-PROMISE','suspicious',[a,b],['unverifiable_promise'],'Có cam kết lợi ích nhưng điều kiện chưa được nêu rõ để đối chiếu.','Yêu cầu điều kiện bằng văn bản và xác minh độc lập.')
        if kind in ('change_work','payee_mismatch','trade_off_platform','collect_identity') and attr(a,'speech_act') not in ('quoted_warning','hypothetical','prohibition'):
            tag={'change_work':'changed_work_terms','payee_mismatch':'identity_payment_mismatch','trade_off_platform':'lost_platform_protection','collect_identity':'disproportionate_data_collection'}[kind]
            conclusion('PV2-VERIFY-'+kind,'suspicious',[a],[tag],'Có thay đổi hoặc yêu cầu vượt phạm vi đã biết cần xác minh trước khi tiếp tục.','Đối chiếu yêu cầu với điều khoản và đầu mối độc lập.')
        if not requested(a):continue
        for b in active:
            if not same(a,b):continue
            bk=attr(b,'action_type')
            if kind=='borrow' and bk=='misstate_information':
                hidden=[e for e in active if attr(e,'action_type')=='conceal_terms' and same(a,e)]
                if hidden:conclusion('PV2-DEBT-MISREPRESENTATION','high',[a,b,hidden[0]],['coerced_debt','misrepresentation'],'Yêu cầu vay đi kèm khai sai thông tin và che điều khoản có thể buộc người dùng chịu nghĩa vụ chưa hiểu rõ.','Dừng ký hoặc khai sai; xem đầy đủ điều khoản và hỏi tư vấn độc lập.')
            if kind=='grant_authority' and bk=='pressure_relationship':
                blocked=[e for e in active if attr(e,'action_type')=='avoid_verification' and same(a,e) and relation(e,a,'obstructs_verification')]
                if blocked:conclusion('PV2-OWNERSHIP-COERCION','high',[a,b,blocked[0]],['ownership_control','coercion'],'Yêu cầu chuyển quyền tài sản đi kèm sức ép quan hệ và cản xác minh có thể làm mất quyền kiểm soát tài sản.','Chưa chuyển quyền; giữ khả năng tham khảo người tin cậy và tư vấn độc lập.')
            if kind in ('sign_obligation','grant_authority') and bk=='conceal_terms':
                blocked=[e for e in active if attr(e,'action_type')=='avoid_verification' and same(a,e) and relation(e,a,'obstructs_verification')]
                if blocked:conclusion('PV2-HIDDEN-LIABILITY','high',[a,b,blocked[0]],['hidden_liability','ownership_control' if attr(a,'object_type')=='ownership_right' else 'excessive_authority'],'Yêu cầu nhận nghĩa vụ hoặc trao quyền trước khi xem giới hạn, kèm cản xác minh, có thể tạo nghĩa vụ vượt dự định.','Không ký trước khi xem phạm vi, giới hạn và điều kiện đầy đủ.')
                elif kind=='sign_obligation':conclusion('PV2-UNCLEAR-LIABILITY','suspicious',[a,b],['unclear_liability'],'Yêu cầu nhận nghĩa vụ nhưng điều kiện chấm dứt hoặc giới hạn chưa rõ.','Yêu cầu bản điều khoản đầy đủ trước khi quyết định.')
            if kind=='grant_authority' and bk=='purpose_mismatch':conclusion('PV2-EXCESSIVE-AUTHORITY','suspicious',[a,b],['excessive_authority'],'Phạm vi ủy quyền không khớp mục đích được nêu.','Đối chiếu và giới hạn quyền đúng giao dịch trước khi ký.')
            if kind=='sign_obligation' and bk=='grant_authority' and relation(a,b,'prerequisite_for'):
                mismatch=[e for e in active if attr(e,'action_type')=='purpose_mismatch' and same(a,e)]
                if mismatch:conclusion('PV2-MISREPRESENTED-SIGNATURE','high',[a,b,mismatch[0]],['misrepresented_signature','excessive_authority'],'Lời giải thích việc ký khác với quyền được trao trong nội dung văn bản, có thể làm mất quyền ngoài dự định.','Chưa ký; đọc và đối chiếu đúng nội dung văn bản qua đầu mối độc lập.')
            if kind=='control_income' and bk=='restrict_exit':
                debt=[e for e in active if attr(e,'action_type')=='sign_obligation' and same(a,e) and relation(e,b,'prerequisite_for')]
                if debt:conclusion('PV2-INCOME-EXIT-CONTROL','high',[a,b,debt[0]],['income_control','coerced_exit'],'Kiểm soát thu nhập kết hợp nhận nợ và điều kiện hạn chế nghỉ việc có thể tạo lệ thuộc và mất quyền tự quyết.','Nếu an toàn, giữ kênh liên lạc độc lập và tìm hỗ trợ từ người tin cậy.')
            if kind=='confirm_completion' and bk=='receive_service' and attr(b,'temporal_state')=='not_completed':conclusion('PV2-PREMATURE-CONFIRMATION','high',[a,b],['premature_confirmation','loss_of_recoursing_right'],'Có yêu cầu xác nhận hoàn thành khi dịch vụ cùng đơn chưa được cung cấp; quyền khiếu nại có thể bị ảnh hưởng.','Chỉ xác nhận đúng trạng thái thực tế của đơn; giữ bằng chứng và kiểm tra chính sách.')
    if rules:
        chosen=max(rules,key=lambda r:2 if r['risk']=='high' else 1)
        return {'analysis_status':'partial' if graph['limitations'] else 'complete','risk_status':chosen['risk'],'summary':chosen['mechanism'],'action':chosen['action'],
          'evidence_refs':chosen['evidence_refs'],'rules':rules,'mechanism_tags':chosen.get('mechanism_tags',[]),'questions':[],'question_targets':[],'missing':[],'policy_version':VERSION}
    if graph['limitations']:return {**inherited,'analysis_status':'unsupported','risk_status':None,'rules':[],'question_targets':[],'policy_version':VERSION}
    gaps=[e for e in active if attr(e,'action_type')=='unspecified_step']
    if gaps:
        obj=attr(gaps[0],'object_type');target={'contract':'document_scope','service_confirmation':'requested_item','information':'requested_fields'}.get(obj,'requested_step')
        return {'analysis_status':'complete','risk_status':'need_context','summary':'Nội dung còn thiếu phạm vi cụ thể của bước được đề cập.','action':'Làm rõ yêu cầu và phạm vi trước khi tiếp tục.',
          'evidence_refs':[gaps[0]['anchor_id']],'rules':[],'questions':['Bước hoặc nội dung được đề cập cụ thể gồm những gì?'],'question_targets':[target],'missing':[target],'policy_version':VERSION}
    if any(requested(e) and attr(e,'action_type') in ('other','none') for e in active):
        return {'analysis_status':'unsupported','risk_status':None,'summary':'Chưa hiểu đủ hành động để đưa ra mức rủi ro.','action':'Thử chia nhỏ theo tình huống.','evidence_refs':[],'rules':[],'questions':[],'question_targets':[],'missing':[],'policy_version':VERSION}
    return {**inherited,'question_targets':['payment_purpose'] if inherited.get('questions') and inherited['risk_status']=='need_context' else [],'policy_version':VERSION}
