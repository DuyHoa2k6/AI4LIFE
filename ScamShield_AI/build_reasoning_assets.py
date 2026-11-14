"""Author-controlled label/rule/template specifications; never evaluates expressions."""
import json
from pathlib import Path
from backend.local_reasoning.schema import DatasetCase,LocalResult,EventType,RelationType
from backend.local_reasoning.rule_schema import Rulebook
from typing import get_args

ROOT=Path(__file__).resolve().parent.parent/'data/v2'


def save(name,data):
    p=ROOT/name
    if p.exists():raise FileExistsError('Version assets instead of overwriting '+name)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def fact(*kinds,roles=None,times=None,attribution=None,negative=False,auth=False):
    return {'event_types':list(kinds),'polarities':['negative' if negative else 'positive'],
            'speech_roles':roles or ['request','claim','reported'],'temporal_states':times or [],
            'attribution_kinds':attribution or [],'requires_authentication_meaning':auth}


def build():
    ROOT.mkdir(exist_ok=True)
    rules=[];templates={}
    def add(rid,description,facts,risk,summary,action,relation=None,exclude=(),urgent=False,question=None):
        tid='TPL-'+rid
        rules.append({'rule_id':rid,'version':'1.0','description':description,
            'scope':'same_event' if len(facts)==1 else 'same_scope_same_affected_party',
            'required_facts':facts,'required_relations':relation or [],'exclusions':list(exclude),
            'missing_fact_policy':'ask','conclusion':risk,'safety_urgency':'urgent' if urgent else 'preventive',
            'evidence_requirements':'all_required_facts_and_relations','follow_up_question_template':question,
            'explanation_template_id':tid,'supported_conclusion':rid.lower(),'test_case_ids':[]})
        templates[tid]={'summary':summary,'recommended_actions':[action],
                        'required_slots':['verified_quotes'],'fallback_template_id':'TPL-UNKNOWN'}
    add('R-HANDOVER','Giao tài sản trước khi xác nhận tiền',
        {'request':fact('handover_asset',roles=['request']),'state':fact('receive_funds',negative=True)},'suspicious',
        'Nội dung yêu cầu giao tài sản khi người nhận tiền cho biết chưa xác nhận thanh toán. Chưa đủ căn cứ nói biên lai giả.',
        'Tự kiểm tra tiền thực nhận qua kênh ngân hàng quen dùng trước khi giao tài sản.',
        [{'type':'before','from_fact':'request','to_fact':'state'}],['later_payment_confirmed'])
    add('R-CREDENTIAL','Giao mật khẩu hoặc mã xác thực rõ loại',{'request':fact('provide_credentials','provide_code',roles=['request'],auth=True)},'high',
        'Nội dung yêu cầu giao thông tin xác thực cho người khác; có nguy cơ mất quyền truy cập tài khoản.',
        'Không gửi mã hoặc mật khẩu; tự kiểm tra yêu cầu bằng kênh chính thức quen dùng.')
    add('R-CODE-IDENTITY','Dãy số được tin liên quan xác định là mã đăng nhập',
        {'request':fact('provide_code',roles=['request']),'meaning':fact('code_identity')},'high',
        'Dãy số được xác định trong hội thoại là mã đăng nhập, trong khi người gửi yêu cầu bạn cung cấp.',
        'Không đọc mã cho người khác; tự kiểm tra bằng ứng dụng chính thức.',
        [{'type':'state_update','from_fact':'request','to_fact':'meaning'}])
    add('R-PAY-TO-WITHDRAW','Trả thêm tiền là điều kiện để rút',
        {'request':fact('transfer_funds',roles=['request']),'benefit':fact('withdraw_funds','receive_funds')},'high',
        'Nội dung liên kết việc chuyển thêm tiền với điều kiện nhận hoặc rút tiền.',
        'Tạm dừng nộp thêm và đối chiếu giao dịch qua đầu mối độc lập.',
        [{'type':'prerequisite_for','from_fact':'request','to_fact':'benefit'}])
    add('R-DATA','Giấy tờ nhạy cảm qua cuộc trò chuyện',{'request':fact('provide_documents',roles=['request'])},'suspicious',
        'Có yêu cầu cung cấp giấy tờ cá nhân; cần xác minh đơn vị tiếp nhận và kênh gửi.',
        'Chưa gửi ảnh giấy tờ cho đến khi đã xác minh mục đích và kênh tiếp nhận.')
    add('R-ACCESS','Cài ứng dụng hoặc giao quyền chưa được xác minh',{'request':fact('install_app','share_screen','grant_control',roles=['request'])},'suspicious',
        'Có yêu cầu cài ứng dụng hoặc chia sẻ quyền truy cập cần xác minh.',
        'Kiểm tra nguồn ứng dụng và đầu mối hỗ trợ độc lập trước khi cấp quyền.')
    add('R-TRAVEL-SECRET','Di chuyển gắn với giấu gia đình',
        {'travel':fact('invite_travel_or_meeting'),'secret':fact('request_secrecy')},'suspicious',
        'Lời mời di chuyển đi cùng yêu cầu giấu người thân; cần xác minh điều kiện và đầu mối.',
        'Nếu an toàn, trao đổi với người tin cậy và xác minh độc lập trước khi di chuyển.',
        [{'type':'travel_conditioned_on_secrecy','from_fact':'travel','to_fact':'secret'}])
    for rid,kind,rel,summary in [
        ('R-DEBT-EXIT','impose_debt','movement_restricted_by_debt','Nội dung gắn khoản nợ với việc không được rời đi.'),
        ('R-DOC-EXIT','retain_identity_documents','document_retention_limits_exit','Nội dung nêu việc giữ giấy tờ cùng hạn chế quyền rời đi.')]:
        add(rid,summary,{'control':fact(kind),'exit':fact('restrict_movement')},'high',summary,
            'Nếu an toàn, tìm cách liên hệ người tin cậy hoặc đơn vị hỗ trợ phù hợp; không đối đầu với người kiểm soát.',
            [{'type':rel,'from_fact':'control','to_fact':'exit'}])
    add('R-CONTROL','Hạn chế liên lạc hoặc giữ giấy tờ chưa rõ mục đích',
        {'control':fact('restrict_communication','retain_identity_documents')},'suspicious',
        'Có thông tin về kiểm soát liên lạc hoặc giữ giấy tờ; cần làm rõ khả năng tự quyết và nhận lại.',
        'Nếu an toàn, kiểm tra bạn có thể nhận lại giấy tờ, liên lạc và tự do rời đi không.',exclude=['documents_returnable'])
    add('R-CHANGE-WORK','Điều kiện công việc khác lời mời',
        {'offer':fact('offer_employment'),'change':fact('change_destination_or_terms')},'suspicious',
        'Nội dung nêu thay đổi công việc hoặc điều kiện so với lời mời ban đầu.',
        'Chưa chấp nhận điều kiện mới trước khi đối chiếu thỏa thuận và quyền từ chối.',
        [{'type':'work_differs_from_agreement','from_fact':'offer','to_fact':'change'}])
    add('R-RELEASE','Đòi tiền để được rời đi hoặc thả người',{'payment':fact('demand_release_payment')},'high',
        'Có lời đòi tiền để được rời đi hoặc để thả người. Lời đòi tiền chưa chứng minh việc bắt giữ đã xảy ra.',
        'Nếu an toàn, xác minh qua đầu mối độc lập và tìm hỗ trợ phù hợp; không tự đối đầu.')
    add('R-COERCION','Thông tin về cưỡng ép hoặc đe dọa',
        {'coercion':fact('compel_work','compel_illegal_activity','bodily_integrity_threat','threaten_harm','threaten_disclosure')},'high',
        'Nội dung có thông tin về đe dọa hoặc cưỡng ép; chưa xác minh độc lập người gây ra hay toàn bộ sự việc.',
        'Không gửi thêm thông tin riêng tư. Nếu an toàn, tìm sự hỗ trợ từ người tin cậy hoặc đơn vị phù hợp.')
    add('R-URGENT-CURRENT','Người dùng báo đang bị kiểm soát hoặc cưỡng ép',
        {'danger':fact('restrict_movement','compel_work','compel_illegal_activity','bodily_integrity_threat',
            times=['ongoing','imminent'],attribution=['self_report','user_report'])},'high',
        'Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.',
        'Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.',
        urgent=True,question='Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.')
    add('R-URGENT-THREAT','Lời đe dọa gây hại trực tiếp sắp xảy ra',
        {'danger':fact('threaten_harm',roles=['request','claim'],times=['ongoing','imminent'])},'high',
        'Nội dung có lời đe dọa gây hại ở thời điểm hiện tại hoặc sắp tới; cần ưu tiên an toàn.',
        'Nếu an toàn, tìm người tin cậy hoặc hỗ trợ khẩn cấp phù hợp; không tự điều tra hay đối đầu.',
        urgent=True,question='Bạn có thể tiếp tục trao đổi ở đây một cách an toàn không? Có thể bỏ qua.')
    templates.update({
        'TPL-UNKNOWN':{'summary':'Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.','recommended_actions':['Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.'],'required_slots':[],'fallback_template_id':None},
        'TPL-CLEAR':{'summary':'Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.','recommended_actions':['Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.'],'required_slots':[],'fallback_template_id':None},
        'TPL-ERROR':{'summary':'Chưa kiểm tra được nội dung; không có kết luận ít rủi ro.','recommended_actions':['Nếu đang gặp nguy hiểm và có thể làm an toàn, tìm người tin cậy hoặc hỗ trợ khẩn cấp phù hợp; tránh đối đầu.'],'required_slots':[],'fallback_template_id':None}})
    book=Rulebook.model_validate({'version':'local-rulebook-1.0','rules':rules})
    save('rulebook.json',book.model_dump());save('templates.json',{'version':'controlled-templates-1.0','templates':templates})
    definitions={
        'build_trust':'Tạo lòng tin/tự nhận thân quen; riêng lẻ không chứng minh gian lận.',
        'invite_travel_or_meeting':'Lời mời di chuyển/gặp; không dùng quốc gia/giới tính làm dấu hiệu.',
        'offer_employment':'Lời mời việc làm; chưa xác minh người tuyển.',
        'change_destination_or_terms':'Đổi nơi đến hoặc điều kiện đã nêu.',
        'impose_debt':'Áp khoản nợ hoặc ràng buộc trả chi phí.',
        'request_secrecy':'Yêu cầu giấu thông tin với người thân/đầu mối khác.',
        'restrict_communication':'Hạn chế liên lạc/giữ điện thoại.',
        'retain_identity_documents':'Giữ giấy tờ, phải phân biệt trả lại tự do với kiểm soát.',
        'restrict_movement':'Ngăn tự do rời đi; không suy từ mất liên lạc.',
        'threaten_harm':'Đe dọa gây hại có căn cứ lời nói; không chứng minh đã gây hại.',
        'threaten_disclosure':'Đe dọa phát tán riêng tư; không yêu cầu mô tả/ảnh chi tiết.',
        'demand_release_payment':'Đòi tiền để rời đi/thả người; lời đòi không chứng minh bắt giữ thật.',
        'compel_work':'Ép làm việc, phân biệt thỏa thuận tự nguyện.',
        'compel_illegal_activity':'Ép làm hoạt động trái pháp luật có lời gốc.',
        'bodily_integrity_threat':'Cưỡng ép/đe dọa thân thể có căn cứ trực tiếp; không suy lấy nội tạng từ đi xa.'}
    save('labels.json',{'version':'labels-2.0','events':[{'id':x,'definition':definitions.get(x,x.replace('_',' ')),
        'counterexample':'Phủ định, trích để cảnh báo, tự nguyện có quyền từ chối hoặc chưa nêu hành vi không phải hành vi đang xảy ra.'} for x in get_args(EventType)],
        'relations':[{'id':x,'definition':'Quan hệ '+x+' phải có hai đầu mút hợp lệ, cùng phạm vi/người và quote hỗ trợ.'} for x in get_args(RelationType)],
        'span_labels':['verb','action','object','negation','state','time','condition','purpose','participant','organization','url','account','application','quotation','reported_speech','persuasion','statement'],
        'risk_status':['clear','need_context','suspicious','high'],'safety_urgency':['undetermined','preventive','urgent'],
        'disallowed_shortcuts':['nationality_as_risk','gender_as_risk','travel_alone_as_trafficking','uncontactable_as_organ_removal','absence_as_negative_fact']})
    save('case.schema.json',DatasetCase.model_json_schema());save('output.schema.json',LocalResult.model_json_schema());save('rulebook.schema.json',Rulebook.model_json_schema())
    print('Created versioned labels, schemas, rules and templates.')


if __name__=='__main__':build()
