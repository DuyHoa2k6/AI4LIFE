"""Reproduce the reported public synthetic message; never open its URL."""
import json
import time
from pathlib import Path
import httpx

TEXT = ('Chào bạn,\n\nTài khoản sinh viên của bạn đang chờ xác minh. Nếu chưa hoàn tất trước 18 giờ hôm nay, '
        'quyền truy cập cổng sinh viên sẽ tạm thời bị khóa.\n\n'
        'Bạn mở https://xacthuc-sinhvien.invalid/kiem-tra, nhập mật khẩu tài khoản trường, '
        'sau đó điền dãy sáu số vừa hiện trên điện thoại để hoàn tất xác minh.\n\nBộ phận hỗ trợ sinh viên')
URL = 'https://xacthuc-sinhvien.invalid/kiem-tra'
start = TEXT.index(URL)
PAYLOAD = {'text': TEXT, 'links': [{'id': 'link-0', 'message_id': 'm1', 'url': URL,
    'display_text': URL, 'start': start, 'end': start + len(URL), 'origin': 'dom_href'}]}

if __name__ == '__main__':
    output = Path(__file__).resolve().parents[1] / 'reports' / 'student_input_fix'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'input.json').write_text(json.dumps(PAYLOAD, ensure_ascii=False, indent=2), encoding='utf-8')
    begun = time.perf_counter()
    r = httpx.post('http://127.0.0.1:8000/api/analyze', json=PAYLOAD, timeout=180)
    result = {'http_status': r.status_code, 'seconds': time.perf_counter()-begun, 'response': r.json()}
    (output / 'live.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'http_status': r.status_code, 'seconds': result['seconds'],
                      'risk_status': result['response'].get('risk_status'),
                      'mode': result['response'].get('mode'), 'code': result['response'].get('code')}))
