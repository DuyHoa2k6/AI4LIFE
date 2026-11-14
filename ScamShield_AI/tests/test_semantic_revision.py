"""Public regression assertions, authored before the semantic repair."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.diagnostics import capture_traces

def analyze(text):
    with TestClient(app) as client,capture_traces() as traces:r=client.post('/api/analyze',json={'text':text})
    assert r.status_code==200
    assert len(traces)==1 and traces[0]['request_id']==r.json()['request_id']
    return r.json(),traces[0]

@pytest.mark.parametrize('text,forbidden',[
 ('Hợp đồng đã được gửi.','transfer_funds'),('Hop dong da duoc gui.','transfer_funds'),
 ('Tôi đã gọi đầu mối.','avoid_verification'),('Toi da goi dau moi.','avoid_verification'),
 ('Đừng đợi giao dịch vào.','handover_asset'),('Dung doi giao dich vao.','handover_asset'),
 ('Chưa đồng ý thì chưa đóng tiền.','transfer_funds'),
 ('Chưa có yêu cầu chuyển tiền hay gửi mã.','provide_code'),
 ('Không biết gửi giấy hay chuyển tiền.','transfer_funds'),
 ('Tôi chưa xác minh được người đó.','avoid_verification'),
 ('Tôi có thể xem xác nhận không?','avoid_verification')])
def test_no_false_active_event(text,forbidden):
    response,trace=analyze(text)
    assert not [e for e in trace['annotations']['events'] if e['event_type']==forbidden and e['speech_role']=='request' and e['polarity']=='positive']

def test_wage_condition_never_clear():
    response,trace=analyze('Quản lý yêu cầu tôi ký nhận nợ chưa ghi số tiền. Chưa ký thì chưa được nhận lương. Muốn rời chỗ ở phải xin phép quản lý.')
    assert response['risk_status']!='clear'
    assert any(e['event_type'] in ('impose_debt','sign_obligation') for e in trace['annotations']['events'])

def test_no_trace_exposed_by_default():
    response,_=analyze('Hợp đồng đã được gửi.')
    assert 'annotations' not in response and 'graph_trace' not in str(response)
