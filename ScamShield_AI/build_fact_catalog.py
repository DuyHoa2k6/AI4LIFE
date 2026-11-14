"""Emit a versioned fact dictionary, not training labels or runtime code."""
import json
from pathlib import Path
from typing import get_args
from backend.local_reasoning.schema import EventType,RelationType
from backend.local_reasoning.facts import fact_type

entries={}
for event in get_args(EventType):
    name=fact_type(event)
    entries[name]={'type':name,'source_event':event,
        'TRUE':'Có bằng chứng về khẳng định/hành vi dương tính; phải xét direct_request, speech_role, thời gian và nguồn trước khi dùng làm nguy cơ.',
        'FALSE':'Có bằng chứng phủ định hành vi hoặc trạng thái; không phải do vắng thông tin.',
        'UNKNOWN':'Chưa bóc tách được, thiếu bằng chứng hoặc ý nghĩa/trạng thái chưa rõ.'}
entries['payment_confirmed'].update(TRUE='Người được gán nguồn báo đã nhận đủ tiền/hoàn tất; không phải xác minh ngân hàng độc lập.',
    FALSE='Có lời báo chưa nhận/chưa xác nhận thanh toán trong phạm vi cụ thể.',UNKNOWN='Không có trạng thái thanh toán đủ rõ; không chuyển thành FALSE.')
for name,definition in {
    'direct_request':('Có lời yêu cầu trực tiếp.','Được xác định là vai khác: cảnh báo, phủ định, tự thuật.','Chưa rõ vai câu nói.'),
    'quoted_warning':('Lời trích/cảnh báo được nhận diện.','Được nhận diện là vai khác.','Vai chưa rõ.'),
    'denial':('Lời phủ định được nhận diện.','Vai đã rõ và không phải phủ định.','Vai chưa rõ.'),
    'authentication_meaning':('Mật khẩu hoặc mã được nhận diện là mã đăng nhập/xác thực.','Có loại mã không phải xác thực rõ ràng, như mã đơn hàng.','Dãy số chưa rõ mục đích.'),
    'bank_information_requested':('Có nội dung mở thông tin ngân hàng; cần xét vai request để dùng luật.','Có phủ định mở thông tin ngân hàng.','Chưa rõ hoặc chưa có nội dung này.'),
    'payment_resolution':('Không dùng TRUE trong bản hiện tại.','Không dùng FALSE trong bản hiện tại.','Các nguồn thanh toán xung đột chưa giải quyết; giữ từng claim.'),
    'analysis_coverage':('Đã có sự kiện trong phạm vi bộ trích, không thấy tín hiệu chạm giới hạn đã biết; không chứng minh hiểu hết ngữ nghĩa.','Có giới hạn/phần chưa phân tích được nhận diện.','Không trích được sự kiện hoặc chưa xác định độ phủ.'),
    'user_context_provided':('Có bối cảnh do người dùng cung cấp.','Không suy ra FALSE từ việc thiếu bối cảnh.','Chưa có bối cảnh.'),
    'strong_url_signal_detected':('Bộ kiểm tra ghi nhận tín hiệu cấu trúc mạnh.','Đã chạy kiểm tra cấu trúc và không có tín hiệu mạnh; không có nghĩa URL an toàn.','URL chưa kiểm tra được.'),
    'url_supports_requested_action':('Đã ghép yêu cầu có căn cứ với tín hiệu URL hợp lệ.','Không dùng FALSE từ việc không ghép được.','Chưa thiết lập được liên hệ.'),
    'approved_behavior_passage_used':('Đoạn nguồn đã qua cổng duyệt và được dùng.','Không suy ra FALSE từ no_match.','Chưa có nguồn dùng được.'),
    'official_behavior_support':('Đã ghép tài liệu được duyệt với hành vi có căn cứ.','Không suy ra FALSE từ no_match.','Chưa xác định được nguồn hỗ trợ.')}.items():
    entries[name]={'type':name,'TRUE':definition[0],'FALSE':definition[1],'UNKNOWN':definition[2]}
for relation in get_args(RelationType):
    name='relation:'+relation
    entries[name]={'type':name,'TRUE':'Có quan hệ kèm bằng chứng, phạm vi và nguồn suy ra đã kiểm tra.',
        'FALSE':'Chỉ có thể dùng khi có phủ định quan hệ rõ; bộ trích hiện không tự sinh trường hợp này.',
        'UNKNOWN':'Thiếu quan hệ hoặc quan hệ chưa rõ; không nối chỉ vì hai sự kiện cùng xuất hiện.'}
path=Path(__file__).resolve().parent.parent/'data/v2/fact_catalog.json'
path.write_text(json.dumps({'version':'three-valued-fact-catalog-1.0','absence_policy':'UNKNOWN',
    'sources':['observed_content','sender_claim','user_report','technical_check','derived'],
    'facts':list(entries.values())},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Wrote fact_catalog.json')
