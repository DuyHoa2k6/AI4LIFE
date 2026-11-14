"""Run user-provided cases through the real API route; no labels in requests."""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from backend.main import app
from backend.settings import get_setting

CASES = [
    ('01', 'Giả người quen nhờ chuyển tiền', 'Anh đổi tài khoản nhắn tin rồi nhé. Anh đang cần thanh toán gấp nên em chuyển giúp vào tài khoản của người này. Đừng gọi số cũ, máy anh đang hỏng. Chuyển xong anh giải thích sau.'),
    ('02', 'Thu phí để mở khóa khoản tiền', 'Khoản rút của bạn đã được duyệt nhưng đang bị giữ ở bước bảo chứng. Bạn phải nộp thêm một khoản thì hệ thống mới trả toàn bộ. Nếu bỏ dở, số tiền đã nộp trước đó sẽ không được hoàn lại.'),
    ('03', 'Giả nhân viên giao hàng xin mã đăng nhập', 'Em đang xử lý hoàn phí vận chuyển cho chị. Chị đọc mã vừa nhận giúp em. Tin nhắn ghi mã đăng nhập là mẫu thông báo chung thôi, chị không đọc thì em không hoàn tiền được.'),
    ('04', 'Tuyển dụng rồi yêu cầu đứng tên nhận tiền', 'Công việc của em là nhận tiền khách vào tài khoản cá nhân rồi chuyển tiếp theo danh sách công ty gửi. Em giữ lại phần hoa hồng. Nếu ngân hàng hỏi, cứ nói người quen trả nợ, không cần nhắc đến công việc.'),
    ('05', 'Mượn quan hệ tình cảm để ép vay tiền', 'Nếu em tin anh thì đứng tên vay giúp anh lần này. Anh sẽ trả góp hằng tháng, em không phải lo. Đừng kể với gia đình vì họ không hiểu chuyện của mình. Nếu em từ chối thì anh biết em chưa từng nghiêm túc.'),
    ('06', 'Mạo danh hỗ trợ để lấy quyền thiết bị', 'Tài khoản của anh có giao dịch bất thường. Anh bật ứng dụng điều khiển từ xa và cấp quyền cho tôi kiểm tra. Trong lúc kết nối, mở ngân hàng để tôi đối chiếu số dư. Anh không cần gọi tổng đài xác minh nữa.'),
    ('07', 'Đòi tiền để tránh phát tán nội dung', 'Tôi có đoạn ghi hình của bạn và biết nơi bạn làm việc. Chuyển tiền thì tôi không gửi cho đồng nghiệp. Dù bạn nói hình bị ghép, người khác vẫn sẽ xem. Đừng báo cho ai.'),
    ('08', 'Mời đi làm nhưng đặt điều kiện hạn chế trở về', 'Em cứ đi theo xe bên anh, đến nơi mới ký hợp đồng. Hộ chiếu giao trưởng nhóm giữ. Muốn nghỉ hoặc về thì phải trả hết chi phí công ty ứng, số tiền tới nơi mới tính. Đừng báo lịch trình cho gia đình.'),
]

out = ROOT / 'reports/eight_scenarios_20261113'
out.mkdir(parents=True, exist_ok=True)
inputs = [{'id': cid, 'text': text} for cid, _, text in CASES]
encoded = json.dumps(inputs, ensure_ascii=False, indent=2).encode('utf-8')
(out / 'inputs.json').write_bytes(encoded)
report = {'method': 'FastAPI ASGI TestClient -> POST /api/analyze; real configured backend, no dependency override; sequential single run per case, not browser latency',
          'configuration': {k: get_setting(k, default) for k, default in [('SCAMSHIELD_MODE', 'local_rules'), ('SCAMSHIELD_REASONER', 'legacy'), ('SCAMSHIELD_CONTEXT_ENABLED', '1'), ('SCAMSHIELD_RAG_ENABLED', '1'), ('SCAMSHIELD_URL_NETWORK_ENABLED', '1')]},
          'input_sha256': hashlib.sha256(encoded).hexdigest(), 'cases': []}
with TestClient(app) as client:
    for cid, title, text in CASES:
        start = time.perf_counter()
        response = client.post('/api/analyze', json={'text': text})
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        data = response.json()
        row = {'id': cid, 'title': title, 'http_status': response.status_code, 'elapsed_ms': elapsed, 'response': data}
        report['cases'].append(row)
        # Persist every prediction before any semantic review/expected comparison.
        (out / 'predictions.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'id': cid, 'status': response.status_code, 'risk': data.get('risk_status'), 'ms': elapsed, 'summary': data.get('display_summary', data.get('summary')), 'action': data.get('display_action'), 'questions': data.get('follow_up_questions'), 'indicators': data.get('risk_indicators'), 'decision': data.get('analysis', {}).get('decision_version')}, ensure_ascii=False))
