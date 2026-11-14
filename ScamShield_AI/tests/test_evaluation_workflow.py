import copy,json,subprocess,sys
from pathlib import Path
import pytest
from evaluation.schema import Case,runtime_input,oracle_graph
from evaluation.io import load,validate_splits
from evaluation.metrics import aggregate,diagnose,div
from evaluation.compare_runs import compare
from evaluation.training import prepare
from ml.phobert.policy_v2 import verify,assess
from ml.phobert.schema import ATTRS

ROOT=Path(__file__).resolve().parents[1]

def cases():return load(ROOT/'evaluation/data/novel_cases.jsonl')

def minimal(text,specs,links=()):
    spans=[];events=[]
    for i,(word,kind,obj,*options) in enumerate(specs):
        s=text.index(word);opts=options[0] if options else {};sid='s'+str(i)
        spans.append({'id':sid,'message_id':'m1','start':s,'end':s+len(word),'quote':word,'label':'action'})
        attrs=dict(zip(ATTRS,[kind,obj,opts.get('speech','request'),opts.get('polarity','positive'),opts.get('temporal','requested'),opts.get('modality','request')]))
        events.append({'id':'e'+str(i),'anchor_id':sid,'attributes':attrs,'speaker_id':'sender','roles':{'performer':'recipient:unknown'},'transaction_id':opts.get('scope','A')})
    relations=[{'id':'r'+str(i),'source':'e'+str(a),'target':'e'+str(b),'label':label,'evidence_refs':['s'+str(a),'s'+str(b)]} for i,(a,b,label) in enumerate(links)]
    return [{'id':'m1','speaker_id':'sender','text':text}],{'spans':spans,'events':events,'relations':relations,'limitations':[]}

def test_dataset_valid_and_family_disjoint():
    rows=cases();validate_splits(rows)
    assert len(rows)==35 and len({r.domain for r in rows})==7
    assert all(r.review_status=='draft' and not r.reviewer_reference for r in rows)

def test_expected_never_enters_runtime():
    for r in cases():
        payload=runtime_input(r)
        assert set(payload)=={'messages'}
        assert set(payload['messages'][0])=={'id','speaker_id','text'}

def test_bad_offsets_and_dangling_refs_rejected():
    row=cases()[0].model_dump();row['expected']['spans'][0]['quote']='FABRICATED'
    with pytest.raises(ValueError):Case.model_validate(row)
    row=cases()[0].model_dump();row['expected']['event_arguments'][0]['event_id']='none'
    with pytest.raises(ValueError):Case.model_validate(row)

def test_global_unknown_not_a_gold_identity():
    row=cases()[0].model_dump();p=next(p for p in row['expected']['participants'] if p['kind']=='unknown');p['id']='unknown'
    with pytest.raises(ValueError):Case.model_validate(row)

def test_family_cannot_cross_split():
    rows=cases()[:1];clone=rows[0].model_copy(deep=True);clone.case_id='clone';clone.split='validation';rows.append(clone)
    with pytest.raises(ValueError):validate_splits(rows)

def test_undefined_rates_are_null_not_zero_or_perfect():
    result=aggregate([])
    assert div(0,0) is None and result['coverage'] is None and result['macro_f1'] is None
    assert result['evidence']['after_rate'] is None

def test_draft_cannot_become_training(tmp_path):
    result=prepare(cases(),None,None,ROOT/'artifacts/phobert/smoke_heads',tmp_path)
    assert result['status']=='blocked' and result['reviewed_new']==0 and not result['weights_changed']
    assert not (tmp_path/'candidate_checkpoint').exists()

def test_review_gate_cli_exit_code(tmp_path):
    p=subprocess.run([sys.executable,'-m','evaluation.training','--cases',str(ROOT/'evaluation/data/novel_cases.jsonl'),'--out',str(tmp_path)],cwd=ROOT,capture_output=True)
    assert p.returncode==3

def test_unknown_participants_are_not_shared_across_messages():
    ms,g=minimal('Gửi tài liệu.',[('Gửi','handover','document')]);m2={'id':'m2','speaker_id':'second','text':'Giữ giấy tờ.'};ms.append(m2)
    g['spans'].append({'id':'s2','message_id':'m2','start':0,'end':3,'quote':'Giữ','label':'action'})
    second=copy.deepcopy(g['events'][0]);second.update(id='e2',anchor_id='s2',speaker_id='second');g['events'].append(second)
    checked=verify(ms,g)
    assert checked['events'][0]['roles']['performer']=='unknown:m1:addressee'
    assert checked['events'][1]['roles']['performer']=='unknown:m2:addressee'

def test_incompatible_object_cannot_create_clear():
    ms,g=minimal('Gửi phụ lục.',[('Gửi','disclose_credentials','document')]);r=assess(verify(ms,g))
    assert r['risk_status'] is None and r['analysis_status']=='unsupported'

def test_request_is_not_a_state_update():
    ms,g=minimal('Đã nhận. Nhận thêm.',[('Đã nhận','receive','money',{'speech':'claim','temporal':'completed'}),('Nhận thêm','receive','money')],[(0,1,'state_update')])
    checked=verify(ms,g)
    assert not checked['relations'] and checked['discarded'][0]['reason']=='update_requires_reports_not_requests'

def test_other_transaction_update_does_not_clear_risk():
    ms,g=minimal('Chưa xong A. Xác nhận A. Xong B.',[('Chưa xong','receive_service','service_confirmation',{'speech':'claim','temporal':'not_completed'}),('Xác nhận','confirm_completion','service_confirmation'),('Xong B','receive_service','service_confirmation',{'speech':'claim','temporal':'completed','scope':'B'})],[(0,1,'same_transaction'),(0,2,'state_update')])
    checked=verify(ms,g);r=assess(checked)
    assert any(x['reason']=='transaction_mismatch' for x in checked['discarded']) and r['risk_status']=='high'

def test_valid_same_transaction_update_recomputes():
    ms,g=minimal('Chưa xong. Xác nhận. Đã xong.',[('Chưa xong','receive_service','service_confirmation',{'speech':'claim','temporal':'not_completed'}),('Xác nhận','confirm_completion','service_confirmation'),('Đã xong','receive_service','service_confirmation',{'speech':'claim','temporal':'completed'})],[(0,1,'same_transaction'),(0,2,'same_transaction'),(0,2,'state_update')])
    assert assess(verify(ms,g))['risk_status']=='clear'

def test_same_keywords_in_warning_not_active_request():
    ms,g=minimal('Đừng vay rồi khai sai; đó là lời cảnh báo.',[('vay','borrow','money',{'speech':'quoted_warning'}),('khai sai','misstate_information','information',{'speech':'quoted_warning'})],[(0,1,'same_transaction')])
    assert assess(verify(ms,g))['risk_status']=='clear'

def test_specific_explanation_does_not_mix_devices_and_debt():
    ms,g=minimal('Đứng tên vay.',[('vay','borrow','money')]);r=assess(verify(ms,g))
    assert 'nghĩa vụ trả nợ' in r['summary'] and 'thiết bị' not in r['summary']

def test_invalid_important_evidence_cannot_pass():
    ms,g=minimal('Ký giấy.',[('Ký','sign_obligation','contract')]);g['spans'][0]['quote']='fake'
    assert assess(verify(ms,g))['risk_status'] is None

def test_correct_risk_with_wrong_basis_is_not_success():
    row=cases()[3];ms,g=minimal(row.input.messages[0].text,[('đứng tên vay','disclose_credentials','credentials')])
    g['events'][0]['speaker_id']=row.input.messages[0].speaker_id
    p={'analysis_status':'complete','graph':g,'assessment':{'risk_status':'high','rules':[{'rule_id':'PB-CREDENTIALS'}],'questions':[]}}
    d=diagnose(row,p)
    assert d['right_level_wrong_basis'] and not d['supported_success']

def test_candidate_does_not_relabel_old_heads():
    from evaluation.ontology import POLICY_ATTRS
    assert 'sign_obligation' in POLICY_ATTRS['action_type'] and 'sign_obligation' not in ATTRS['action_type']

def test_unknown_acceptance_never_passes():
    import yaml
    path=ROOT/'evaluation/reports/20261114_rounds'
    b=json.loads((path/'baseline/metrics.json').read_text());c=json.loads((path/'candidate_01/metrics.json').read_text())
    result=compare(b,c,yaml.safe_load((ROOT/'evaluation/configs/acceptance.yaml').read_text()))
    assert not result['accepted'] and 'reviewed_validation' in result['undefined_block_promotion']

def test_locked_predict_rejects_expected_fields_before_model_load(tmp_path):
    from argparse import Namespace
    from evaluation.locked_runner import predict
    inp=tmp_path/'inputs.jsonl';inp.write_text(json.dumps({'case_id':'x','input':{'messages':[]},'expected':'high'}),encoding='utf-8')
    with pytest.raises(ValueError,match='only'):predict(Namespace(out=tmp_path/'out',inputs=inp,checkpoint=tmp_path/'missing',allow_experimental=True))

def test_private_labels_not_read_without_explicit_access(tmp_path):
    from argparse import Namespace
    from evaluation.locked_runner import score
    with pytest.raises(ValueError,match='explicit'):score(Namespace(out=tmp_path,allow_private_labels=False))

def test_new_eval_instructions_remain_data():
    row=next(r for r in cases() if 'prompt_injection_as_data' in r.phenomena)
    assert 'bỏ qua quy tắc' in runtime_input(row)['messages'][0]['text'] and row.expected.risk_status=='high'

def test_real_rollback_heads_match_baseline_lock():
    from evaluation.io import digest
    choice=json.loads((ROOT/'evaluation/models/model_manifest.json').read_text());lock=json.loads((ROOT/'evaluation/reports/20261114_rounds/baseline_lock.json').read_text())
    assert digest(ROOT/choice['selected_checkpoint']/'heads.pt')==lock['heads_sha256']==choice['heads_sha256']

def test_real_api_text_messages_no_key_no_network(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    import socket
    monkeypatch.setenv('SCAMSHIELD_MODE','local_rules');monkeypatch.setenv('SCAMSHIELD_REASONER','phobert')
    monkeypatch.setenv('SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL','1');monkeypatch.setenv('SCAMSHIELD_PHOBERT_CHECKPOINT',str(ROOT/'evaluation/models/rollback_baseline'))
    monkeypatch.setenv('SCAMSHIELD_API_KEY','');monkeypatch.setenv('SCAMSHIELD_RAG_ENABLED','1');monkeypatch.setenv('SCAMSHIELD_URL_NETWORK_ENABLED','0')
    original_connect=socket.socket.connect
    def denied(sock,address):
        # Windows asyncio constructs its internal socketpair over loopback.
        if isinstance(address,tuple) and address[0] in ('127.0.0.1','::1'):return original_connect(sock,address)
        raise AssertionError('No external network provider calls are permitted')
    monkeypatch.setattr(socket.socket,'connect',denied)
    with TestClient(app) as client:
        text='Bạn gửi mã đăng nhập cho tôi.'
        a=client.post('/api/analyze',json={'text':text});b=client.post('/api/analyze',json={'messages':[{'id':'m1','speaker':'unknown','text':text}]})
        assert a.status_code==b.status_code==200
        assert a.json()['risk_status']==b.json()['risk_status']
        assert 'debug' not in a.json() and not a.json()['source_matches']
        assert a.json()['retrieval']['official_sources']['status'] in ('no_approved_sources','no_match')
        assert client.post('/api/analyze',json={'text':'x'*10001}).status_code==422

def test_actual_api_timeout_and_busy_are_not_risk_labels(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.local_reasoning.phobert_adapter import get_runtime
    monkeypatch.setenv('SCAMSHIELD_MODE','local_rules');monkeypatch.setenv('SCAMSHIELD_REASONER','phobert')
    monkeypatch.setenv('SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL','1');monkeypatch.setenv('SCAMSHIELD_PHOBERT_CHECKPOINT',str(ROOT/'evaluation/models/rollback_baseline'))
    monkeypatch.setenv('SCAMSHIELD_RAG_ENABLED','0');monkeypatch.setenv('SCAMSHIELD_URL_NETWORK_ENABLED','0')
    with TestClient(app) as client:
        runtime=get_runtime();runtime.lock.acquire()
        try:
            response=client.post('/api/analyze',json={'text':'Bạn gửi mã đăng nhập cho tôi.'})
            assert response.status_code==503 and response.json()['code']=='PHOBERT_BUSY' and 'risk_status' not in response.json()
        finally:runtime.lock.release()
        monkeypatch.setenv('SCAMSHIELD_DISABLE_RESPONSE_TIMEOUTS','0');monkeypatch.setenv('SCAMSHIELD_TIMEOUT','0.001')
        response=client.post('/api/analyze',json={'text':'Bạn gửi mã đăng nhập cho tôi.'})
        assert response.status_code==504 and response.json()['code']=='PROVIDER_TIMEOUT' and 'risk_status' not in response.json()

def test_warm_start_real_weights_and_mapping_check(monkeypatch,tmp_path):
    import torch
    from ml.phobert.inference import Runtime
    from ml.phobert.warm_start import load_heads
    runtime=Runtime(ROOT/'artifacts/phobert/smoke_heads',allow_experimental=True)
    before=runtime.model.span_head.weight.detach().clone()
    report=load_heads(runtime.model,ROOT/'evaluation/models/rollback_baseline')
    assert torch.equal(before,runtime.model.span_head.weight) and report['heads_sha256']
    (tmp_path/'labels.json').write_text(json.dumps({'attributes':{}}),encoding='utf-8')
    with pytest.raises(ValueError,match='mapping'):load_heads(runtime.model,tmp_path)

def test_budget_stops_a_third_configuration_before_inference(tmp_path):
    from evaluation.run_evaluation import preflight_budget
    for i in range(2):
        directory=tmp_path/str(i);directory.mkdir()
        (directory/'run_manifest.json').write_text(json.dumps({'model_version':'model','policy_file_sha256':str(i),'planned_inference_calls':10}),encoding='utf-8')
    limits={'max_iterations_including_baseline':3,'max_configurations':2,'max_inference_requests':500,'max_wall_seconds':1200}
    with pytest.raises(ValueError,match='Configuration budget'):preflight_budget(tmp_path/'next',limits,'model','new_policy',10)

def test_budget_counts_requests_across_rounds(tmp_path):
    from evaluation.run_evaluation import preflight_budget
    d=tmp_path/'old';d.mkdir();(d/'run_manifest.json').write_text(json.dumps({'model_version':'m','policy_file_sha256':'p','planned_inference_calls':499}),encoding='utf-8')
    limits={'max_iterations_including_baseline':3,'max_configurations':2,'max_inference_requests':500,'max_wall_seconds':1200}
    with pytest.raises(ValueError,match='Cumulative inference'):preflight_budget(tmp_path/'next',limits,'m','p',2)
