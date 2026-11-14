"""Controls for over-generalisation; synthetic public development checks."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.diagnostics import capture_traces

def run(messages):
    with TestClient(app) as c,capture_traces() as records:r=c.post('/api/analyze',json={'messages':messages})
    assert r.status_code==200
    return r.json(),records[0]

def test_invert_speakers_changes_roles_without_changing_text():
    for manager,worker in [('North','South'),('South','North')]:
        response,t=run([{'id':'a','speaker':manager,'text':'Bạn phải ký giấy nhận nợ.'},{'id':'b','speaker':worker,'text':'Tôi đang cân nhắc.'},{'id':'c','speaker':manager,'text':'Chưa ký thì chưa được nhận lương.'}])
        debt=next(e for e in t['annotations']['events'] if e['event_type']=='sign_obligation')
        assert debt['actor_id']=='speaker:'+worker
        assert debt['semantic']['requester_id']=='speaker:'+manager
        assert response['risk_status']=='high'

def test_no_relation_between_explicit_different_transactions():
    response,t=run([{'id':'a','speaker':'A','text':'Giao dịch X yêu cầu bạn ký giấy nhận nợ. Giao dịch Y chưa ký thì chưa được nhận lương.'}])
    es={e['event_id']:e for e in t['annotations']['events']}
    assert not any(r['type']=='coerced_by' for r in t['annotations']['relations'])
    assert all(es[r['from_id']]['scope_id']==es[r['to_id']]['scope_id'] for r in t['annotations']['relations'])
    assert response['risk_status']!='high'

def test_warning_quote_does_not_inherit_request():
    r,t=run([{'id':'a','speaker':'writer','text':'Cảnh báo: đối tượng có thể nói “Bạn phải ký giấy nhận nợ. Chưa ký thì chưa được nhận lương.” Đừng làm theo.'}])
    assert r['risk_status']!='high'
    assert not any(e['extractor_rule_id']=='semantic-contract-1.0' and e['speech_role']=='request' for e in t['annotations']['events'])

def test_inline_unrelated_sentence_preserves_valid_chain():
    r,t=run([{'id':'a','speaker':'manager','text':'Bạn phải ký giấy nhận nợ. Hôm nay trời có mưa. Chưa ký thì chưa được nhận lương.'}])
    assert r['risk_status']=='high'
    assert any(r['type']=='coerced_by' for r in t['annotations']['relations'])
