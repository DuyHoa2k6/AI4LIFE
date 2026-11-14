"""Typed graph rules. No text regex, classifier verdicts or score summation here."""
from .schema import ATTRS, RELATIONS
def verify_graph(messages,graph):
    texts={m['id']:m['text'] for m in messages};spans={};discarded=[]
    for s in graph.get('spans',[]):
        text=texts.get(s['message_id'])
        if text is None or not isinstance(s['start'],int) or not isinstance(s['end'],int) or not 0<=s['start']<s['end']<=len(text) or text[s['start']:s['end']]!=s['quote']:
            discarded.append({'kind':'span','id':s['id'],'reason':'invalid_evidence'});continue
        if s['id'] in spans:raise ValueError('duplicate predicted span')
        spans[s['id']]=s
    events={}
    speakers={m['id']:m.get('speaker_id') for m in messages}
    people={'speaker:'+s for s in speakers.values() if s}|{'recipient:unknown'}
    people|={'mention:'+s['id'] for s in spans.values() if s['label']=='entity'}
    for e in graph.get('events',[]):
        s=spans.get(e['anchor_id'])
        if not s or s['label']!='action':discarded.append({'kind':'event','id':e['id'],'reason':'invalid_anchor'});continue
        if e.get('speaker_id')!=speakers[s['message_id']]:discarded.append({'kind':'event','id':e['id'],'reason':'speaker_mismatch'});continue
        if set(e['attributes'])!=set(ATTRS) or any(v not in ATTRS[k] for k,v in e['attributes'].items()):
            discarded.append({'kind':'event','id':e['id'],'reason':'invalid_attributes'});continue
        e={**e,'roles':{role:pid for role,pid in e.get('roles',{}).items() if pid in people}}
        if e.get('speaker_id'):e['roles']['speaker']='speaker:'+e['speaker_id']
        events[e['id']]=e
    relations=[]
    for r in graph.get('relations',[]):
        a,b=events.get(r['source']),events.get(r['target']);reason=None
        if r['label'] not in RELATIONS:reason='unknown_relation'
        elif not a or not b or a['id']==b['id']:reason='invalid_endpoint'
        elif not {a['anchor_id'],b['anchor_id']}<=set(r['evidence_refs']) or not set(r['evidence_refs'])<=set(spans):reason='missing_endpoint_evidence'
        elif a.get('transaction_id') and b.get('transaction_id') and a['transaction_id']!=b['transaction_id']:reason='transaction_mismatch'
        elif r['label']=='state_update' and (a['attributes']['action_type']!=b['attributes']['action_type'] or a['attributes']['object_type']!=b['attributes']['object_type']):reason='update_object_mismatch'
        elif r['label']=='state_update':
            sa,sb=spans[a['anchor_id']],spans[b['anchor_id']];order={m['id']:i for i,m in enumerate(messages)}
            if (order[sa['message_id']],sa['start'])>=(order[sb['message_id']],sb['start']):reason='update_wrong_direction'
        if reason:discarded.append({'kind':'relation','id':r.get('id'),'reason':reason})
        else:relations.append(r)
    return {**graph,'spans':list(spans.values()),'events':list(events.values()),'relations':relations,'discarded':discarded,
      'limitations':list(dict.fromkeys(graph.get('limitations',[])+(['Có dữ kiện hoặc quan hệ bị loại khi kiểm chứng.'] if discarded else [])))}

def assess(graph):
    events={e['id']:e for e in graph['events']};relations=graph['relations'];rules=[]
    def attr(e,k):return e['attributes'].get(k)
    def requested(e):
        performer=e.get('roles',{}).get('performer');speaker='speaker:'+e['speaker_id'] if e.get('speaker_id') else None
        return attr(e,'speech_act')=='request' and attr(e,'polarity')=='positive' and attr(e,'temporal_state') not in ('completed','not_completed') and not (performer and speaker and performer==speaker)
    def rel(a,b,label):return any(r['label']==label and ((r['source'],r['target'])==(a['id'],b['id']) or label=='same_transaction' and (r['source'],r['target'])==(b['id'],a['id'])) for r in relations)
    def add(rule,risk,es,summary,action,required=()):
        ids={e['id'] for e in es};rs=[r for r in relations if r['source'] in ids and r['target'] in ids and r['label'] in required]
        rules.append({'rule_id':rule,'risk':risk,'event_ids':sorted(ids),'relation_ids':[r['id'] for r in rs],
          'evidence_refs':list(dict.fromkeys([e['anchor_id'] for e in es]+[s for r in rs for s in r['evidence_refs']])),
          'mechanism':summary,'conditions':list(required),'contradictions':[],'limitations':['Chỉ dựa trên nội dung cung cấp, chưa xác minh danh tính ngoài đời.'],'action':action})
    superseded={r['source'] for r in relations if r['label']=='state_update' and any(s['label']=='same_transaction' and {s['source'],s['target']}=={r['source'],r['target']} for s in relations)}
    active=[e for e in events.values() if e['id'] not in superseded]
    for a in active:
        if not requested(a):continue
        kind,obj=attr(a,'action_type'),attr(a,'object_type')
        if kind=='disclose_credentials' and obj in ('auth_code','credentials'):
            add('PB-CREDENTIALS','high',[a],'Người gửi yêu cầu giao mã đăng nhập hoặc thông tin truy cập; bạn có thể mất quyền kiểm soát tài khoản.','Không giao mã hoặc mật khẩu; tự mở ứng dụng chính thức để kiểm tra.')
        elif kind in ('grant_control','share_screen','install','borrow','retain_documents'):
            add('PB-SENSITIVE-REQUEST','suspicious',[a],'Có yêu cầu liên quan đến quyền thiết bị, giấy tờ hoặc nghĩa vụ tài chính cần xác minh.','Xác minh mục đích, phạm vi quyền và đầu mối độc lập trước khi thực hiện.')
        for b in active:
            if a['id']==b['id'] or not rel(a,b,'same_transaction'):continue
            bk=attr(b,'action_type')
            if kind=='transfer' and bk=='withdraw' and rel(a,b,'prerequisite_for'):
                add('PB-PAY-TO-WITHDRAW','high',[a,b],'Người gửi đặt việc nộp thêm tiền làm điều kiện để được rút; bạn có thể tiếp tục mất tiền.','Dừng nộp thêm và xác minh quyền rút qua đầu mối độc lập.',['same_transaction','prerequisite_for'])
            if kind in ('grant_control','share_screen') and bk=='login' and attr(b,'object_type')=='financial_data' and requested(b) and rel(a,b,'controls_during'):
                add('PB-REMOTE-BANKING','high',[a,b],'Yêu cầu cấp quyền thiết bị đi kèm mở dữ liệu ngân hàng có thể làm lộ thông tin hoặc cho phép thao tác ngoài ý muốn.','Ngắt điều khiển từ xa trước khi mở ngân hàng; tự liên hệ hỗ trợ chính thức.',['same_transaction','controls_during'])
            if kind=='transfer' and bk=='threaten_disclosure' and attr(b,'modality')=='threat' and rel(b,a,'threatens_unless'):
                add('PB-EXTORTION','high',[a,b],'Có yêu cầu trả tiền gắn với đe dọa phát tán nội dung; chưa xác minh nội dung bị đe dọa là thật.','Lưu bằng chứng và tìm hỗ trợ phù hợp; không gửi thêm dữ liệu riêng tư.',['same_transaction','threatens_unless'])
            if kind=='retain_documents' and bk=='restrict_exit' and rel(a,b,'prerequisite_for'):
                add('PB-CONTROL-EXIT','high',[a,b],'Việc giao giấy tờ liên quan đến điều kiện hạn chế trở về, có nguy cơ làm mất quyền tự quyết.','Nếu an toàn, giữ quyền kiểm soát giấy tờ và liên lạc với người tin cậy.',['same_transaction','prerequisite_for'])
            if kind=='handover' and bk=='receive' and attr(b,'object_type')=='money' and attr(b,'temporal_state')=='not_completed':
                add('PB-HANDOVER-UNPAID','suspicious',[a,b],'Có yêu cầu giao tài sản trong khi khoản thanh toán cùng giao dịch chưa được xác nhận.','Tự kiểm tra đã nhận đủ tiền đúng đơn trước khi giao.',['same_transaction'])
            if kind=='transfer' and bk=='avoid_verification' and rel(b,a,'obstructs_verification'):
                add('PB-TRANSFER-NO-VERIFY','suspicious',[a,b],'Yêu cầu chuyển tiền đi kèm cản xác minh trong cùng giao dịch.','Liên hệ đầu mối đã biết để xác minh trước khi chuyển tiền.',['same_transaction','obstructs_verification'])
    issues=graph.get('limitations',[])
    if rules:
        chosen=max(rules,key=lambda r:2 if r['risk']=='high' else 1)
        return {'analysis_status':'partial' if issues else 'complete','risk_status':chosen['risk'],'summary':chosen['mechanism'],'action':chosen['action'],'evidence_refs':chosen['evidence_refs'],'rules':rules,'questions':[],'missing':[]}
    if issues:
        return {'analysis_status':'unsupported','risk_status':None,'summary':'Mô hình chưa xử lý đủ phạm vi đầu vào; chưa có kết luận rủi ro.','action':'Thử chia nội dung theo từng giao dịch.','evidence_refs':[],'rules':[],'questions':[],'missing':[]}
    open_transfers=[e for e in active if requested(e) and attr(e,'action_type')=='transfer']
    contradictions=any(r['label']=='contradiction' for r in relations)
    if open_transfers or contradictions:
        return {'analysis_status':'complete','risk_status':'need_context','summary':'Chưa rõ mục đích hoặc trạng thái của yêu cầu chuyển tiền.','action':'Xác minh mục đích và đầu mối liên quan trước khi tiếp tục.','evidence_refs':[e['anchor_id'] for e in open_transfers],'rules':[],'questions':['Khoản chuyển được yêu cầu dùng để làm gì?'] if open_transfers else ['Thông tin nào là cập nhật mới nhất của giao dịch này?'],'missing':['Mục đích khoản chuyển'] if open_transfers else ['Trạng thái hiện tại']}
    return {'analysis_status':'complete','risk_status':'clear','summary':'Trong phạm vi đã phân tích, chưa thấy yêu cầu có cơ chế gây hại được nhận diện.','action':'Nếu cần, xác minh lại qua kênh quen dùng.','evidence_refs':[],'rules':[],'questions':[],'missing':[]}
