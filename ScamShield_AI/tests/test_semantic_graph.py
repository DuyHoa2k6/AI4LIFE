import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_reasoning.schema import CaseInput
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.validation import annotation_errors

ROOT=Path(__file__).resolve().parents[1]


class SemanticGraphTests(unittest.TestCase):
    def setUp(self):
        p=patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_SEMANTIC_GRAPH_ENABLED':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'})
        p.start();self.addCleanup(p.stop)

    def run_text(self,text,**kwargs):
        q=CaseInput(messages=[{'id':'m1','speaker_id':'sender','scope_id':'case','text':text}],**kwargs)
        r=analyze_local(q)
        self.assertEqual(r.analysis_status,'complete',r.annotations.limitations)
        self.assertEqual(annotation_errors(q,r.annotations),[])
        self.assertTrue(r.annotations.graph_trace['linker_called'])
        return r

    def test_public_api_contrast_suite(self):
        labels={r['id']:r['risk'] for r in json.loads((ROOT/'fixtures/semantic_graph/expected.json').read_text(encoding='utf-8'))}
        with TestClient(app) as client:
            for row in json.loads((ROOT/'fixtures/semantic_graph/inputs.json').read_text(encoding='utf-8')):
                with self.subTest(case=row['id']):
                    response=client.post('/api/analyze',json=row['input'])
                    self.assertEqual(response.status_code,200,response.text)
                    risk=response.json()['risk_status']
                    if labels[row['id']]=='not_high':self.assertNotEqual(risk,'high')
                    else:self.assertEqual(risk,labels[row['id']])
                    self.assertNotIn('graph_trace',response.json())

    def test_reporter_requester_and_performer_are_distinct(self):
        r=self.run_text('Bên hỗ trợ bảo tôi gửi thông tin đăng nhập.')
        event=next(e for e in r.annotations.events if e.semantic.normalized_action=='surrender_credentials')
        self.assertEqual(event.speech_role,'reported')
        self.assertNotEqual(event.semantic.speaker_id,event.semantic.requester_id)
        self.assertNotEqual(event.semantic.requester_id,event.semantic.performer_id)
        self.assertEqual(event.semantic.object_type,'credentials')
        self.assertEqual(r.assessment.risk_status,'high')

    def test_self_login_is_not_credential_surrender(self):
        r=self.run_text('Tôi tự đăng nhập ứng dụng chính thức để xem đơn hàng.')
        self.assertFalse(any(m.mechanism_id.startswith('M-CREDENTIAL-TRANSFER') for m in r.interpretation.mechanisms))

    def test_submit_to_page_is_distinct_from_sending_to_person(self):
        r=self.run_text('Bạn gửi thông tin đăng nhập vào trang chính thức nhé.')
        self.assertTrue(any(e.semantic.normalized_action=='submit_credentials_to_page' for e in r.annotations.events))
        self.assertFalse(any(m.mechanism_id.startswith('M-CREDENTIAL-TRANSFER') for m in r.interpretation.mechanisms))

    def test_connection_code_is_not_authentication_code(self):
        r=self.run_text('Bạn đọc mã kết nối để tôi kiểm tra từ xa.')
        self.assertTrue(any(e.semantic.object_type=='connection_code' for e in r.annotations.events))
        self.assertNotEqual(r.assessment.risk_status,'high')

    def test_negative_scope_prevents_credentials_warning(self):
        r=self.run_text('Đừng gửi thông tin đăng nhập cho người khác.')
        e=next(e for e in r.annotations.events if e.semantic.normalized_action=='surrender_credentials')
        self.assertEqual(e.speech_role,'denial');self.assertTrue(e.semantic.negation_scope_refs)
        self.assertNotEqual(r.assessment.risk_status,'high')

    def test_conditional_nonpayment_is_not_denial_of_threat(self):
        r=self.run_text('Tôi có ảnh của bạn. Chuyển 3 triệu thì tôi xóa, còn không tôi gửi cho chỗ làm.')
        self.assertEqual(r.assessment.risk_status,'high')
        edges=[x for x in r.annotations.relations if x.type=='threatens_unless']
        self.assertTrue(edges)
        self.assertTrue(all(x.evidence_refs for x in edges))

    def test_ambiguous_media_does_not_invent_reference(self):
        r=self.run_text('Tôi có ảnh của bạn. Tôi có tài liệu. Chuyển tiền thì tôi xóa, còn không tôi gửi cho chỗ làm.')
        self.assertTrue(any(x['status']=='ambiguous' for x in r.annotations.graph_trace['coreference']))
        self.assertFalse(any(x.rule_id=='SG-LINK-PAYMENT-THREAT' for x in r.annotations.relations))

    def test_plain_sending_media_is_not_coercion(self):
        r=self.run_text('Tôi có ảnh của bạn. Tôi gửi cho chỗ làm để làm thẻ nhân viên.')
        self.assertNotEqual(r.assessment.risk_status,'high')

    def test_cross_situation_candidate_has_rejection_reason(self):
        r=self.run_text('Đơn A: Bạn chuyển tiền vào tài khoản cá nhân. Đơn B: Đừng gọi số cũ.')
        self.assertTrue(any(x['reason']=='different_situation' for x in r.annotations.graph_trace['rejected']))
        self.assertFalse(any(x.type=='obstructs_verification' for x in r.annotations.relations))

    def test_two_explicit_addressees_are_not_the_same_intermediary(self):
        r=self.run_text('Bạn An nhận tiền hộ. Bạn Bình chuyển tiếp sang tài khoản khác. Nếu ngân hàng hỏi thì cứ nói tiền người nhà trả nợ.')
        self.assertNotEqual(r.assessment.risk_status,'high')
        self.assertTrue(any(x['reason']=='different_affected_party' for x in r.annotations.graph_trace['rejected']))

    def test_media_of_another_named_person_not_silently_reassigned(self):
        r=self.run_text('Tôi có ảnh của An. Bạn Bình chuyển tiền thì tôi xóa, còn không tôi gửi cho chỗ làm.')
        self.assertFalse(any(x.rule_id=='SG-LINK-PAYMENT-THREAT' for x in r.annotations.relations))
        self.assertTrue(any(x['reason']=='different_affected_party' for x in r.annotations.graph_trace['rejected']))

    def test_task_payment_needs_grounded_history(self):
        r=self.run_text('Bạn hoàn tất nhiệm vụ 3 triệu mới được rút toàn bộ.')
        self.assertNotEqual(r.assessment.risk_status,'high')
        self.assertTrue(any(x['reason']=='task_payment_not_grounded' for x in r.annotations.graph_trace['rejected']))
        self.assertIn('chi hoặc nộp tiền',r.assessment.follow_up_questions[0])

    def test_situation_state_and_decision_inputs(self):
        r=self.run_text('Bạn chuyển thêm tiền bảo chứng. Hệ thống sẽ trả cả vốn lẫn tiền bảo chứng.')
        self.assertEqual(r.assessment.risk_status,'high')
        s=r.interpretation.situations[0]
        self.assertIn('money',s.object_types);self.assertTrue(s.condition_refs);self.assertTrue(s.mechanism_refs)
        ids={x.event_id for x in r.annotations.events}
        self.assertTrue(set(r.annotations.graph_trace['decision_event_ids'])<=ids)
        self.assertTrue(r.annotations.graph_trace['decision_relation_ids'])

    def test_context_confirmation_bound_and_versioned(self):
        text='Anh đây, máy anh hỏng. Em chuyển tiền vào tài khoản người khác nhé. Đừng gọi số cũ.'
        with TestClient(app) as client:
            first=client.post('/api/analyze',json={'text':text}).json()
            self.assertEqual(first['risk_status'],'high')
            meta=first['case_context']
            link={k:meta[k] for k in ('case_id','situation_id','revision','content_version')}
            link.update(question_id=meta['question_ids'][0],answer='Tôi đã tự gọi số cũ và xác nhận người quen cùng tài khoản nhận tiền.')
            second=client.post('/api/analyze',json={'text':text,'clarification':link})
            self.assertEqual(second.status_code,200,second.text)
            self.assertNotEqual(second.json()['risk_status'],'high')
            self.assertEqual(second.json()['case_context']['revision'],2)
            self.assertEqual(client.post('/api/analyze',json={'text':text,'clarification':link}).status_code,409)

    def test_confirmation_does_not_cancel_credentials(self):
        r=self.run_text('Anh đây, em chuyển tiền vào tài khoản người khác, đừng gọi số cũ. Gửi thông tin đăng nhập cho anh.',
            context_facts=[{'id':'c1','scope_id':'case','applies_to_message_ids':['m1'],'text':'Tôi đã tự gọi số cũ và xác nhận người quen cùng tài khoản nhận tiền.'}])
        self.assertEqual(r.assessment.risk_status,'high')
        self.assertTrue(any(m.mechanism_id.startswith('M-CREDENTIAL-TRANSFER') for m in r.interpretation.mechanisms))

    def test_wrong_situation_context_is_rejected(self):
        r=self.run_text('Anh đây, em chuyển tiền vào tài khoản người khác, đừng gọi số cũ.',
            context_facts=[{'id':'c1','scope_id':'elsewhere','applies_to_message_ids':['m1'],'text':'Tôi đã tự gọi số cũ và xác nhận người quen cùng tài khoản nhận tiền.'}])
        self.assertEqual(r.assessment.risk_status,'high')
        self.assertTrue(any(x['reason']=='unbound_or_wrong_context_situation' for x in r.annotations.graph_trace['rejected']))

    def test_trace_has_no_text_or_secret_values(self):
        r=self.run_text('Gửi thông tin đăng nhập cho tôi: matkhau=VERY_SECRET_TEST_VALUE.')
        trace=json.dumps(r.annotations.graph_trace)
        self.assertNotIn('VERY_SECRET_TEST_VALUE',trace)
        self.assertNotIn('matkhau=',trace)

    def test_incremental_information_changes_each_behavioral_group(self):
        rows=[r for r in json.loads((ROOT/'fixtures/semantic_graph/inputs.json').read_text(encoding='utf-8')) if r['id'].endswith('-update')]
        self.assertEqual(len(rows),7)
        with TestClient(app) as client:
            for row in rows:
                with self.subTest(case=row['id']):
                    before=client.post('/api/analyze',json={'messages':row['input']['messages'][:-1]})
                    after=client.post('/api/analyze',json=row['input'])
                    self.assertEqual(before.status_code,200);self.assertEqual(after.status_code,200)
                    self.assertNotEqual(before.json()['risk_status'],after.json()['risk_status'])


if __name__=='__main__':unittest.main()
