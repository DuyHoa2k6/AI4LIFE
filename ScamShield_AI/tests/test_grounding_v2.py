import os,unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_reasoning.schema import CaseInput
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.validation import annotation_errors
from backend.local_reasoning.grounding import reconcile as actual_reconcile


class GroundingV2Tests(unittest.TestCase):
    def setUp(self):
        p=patch.dict(os.environ,{'SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_SEMANTIC_GRAPH_ENABLED':'1'})
        p.start();self.addCleanup(p.stop)

    def analyze(self,text):return analyze_local(CaseInput(messages=[{'id':'m1','scope_id':'analysis','text':text}]))

    def test_document_receipt_not_money(self):
        r=self.analyze('Anh chưa nhận được phụ lục.')
        self.assertFalse(any(e.event_type=='receive_funds' for e in r.annotations.events))
        self.assertTrue(any(e.semantic and e.semantic.normalized_action=='receive_document' for e in r.annotations.events))
        e=next(e for e in r.annotations.events if e.semantic.normalized_action=='receive_document')
        self.assertEqual((e.polarity,e.temporal_state,e.speech_role),('negative','pending','claim'))
        self.assertEqual(e.semantic.information_status,'claimed')

    def test_receipt_not_additional_payment(self):
        r=self.analyze('Tôi đã tự kiểm tra trong ứng dụng ngân hàng và nhận đủ tiền của đơn A.')
        self.assertFalse(any(e.event_type=='transfer_funds' for e in r.annotations.events))
        self.assertEqual(sum(e.event_type=='receive_funds' for e in r.annotations.events),1)

    def test_guide_not_credentials_or_login(self):
        r=self.analyze('Tôi sẽ gửi hướng dẫn đăng nhập.')
        self.assertFalse(any(e.event_type in ('provide_credentials','login') for e in r.annotations.events))
        self.assertTrue(any(e.semantic and e.semantic.normalized_action=='send_document' for e in r.annotations.events))
        self.assertTrue(any(e.semantic.normalized_action=='send_document' and e.temporal_state=='planned' for e in r.annotations.events))

    def test_conditional_loss_not_prohibition(self):
        r=self.analyze('Nếu không nộp thêm tiền hôm nay thì mất khoản cũ.')
        self.assertFalse(any(e.speech_role=='denial' for e in r.annotations.events))
        self.assertTrue(any(e.semantic and e.semantic.normalized_action=='loss_consequence' for e in r.annotations.events))
        self.assertTrue(any(r.rule_id=='GROUND-CONDITIONAL-LOSS' for r in r.annotations.relations))

    def test_denied_request_not_active_code_request(self):
        r=self.analyze('Tôi không yêu cầu bạn gửi mã đăng nhập.')
        self.assertFalse(any(e.speech_role=='request' and e.event_type=='provide_code' for e in r.annotations.events))

    def test_paid_a_hold_b(self):
        r=self.analyze('Tôi đã tự kiểm tra trong ứng dụng ngân hàng và nhận đủ tiền của đơn A. Bạn giao đúng đơn A cho đơn vị vận chuyển ghi trong đơn hàng nhé; đơn B chưa thanh toán thì giữ lại.')
        self.assertEqual(r.assessment.risk_status,'clear')
        self.assertFalse(r.assessment.follow_up_questions)
        self.assertTrue(any(e.event_type=='receive_funds' and e.scope_id.endswith('don a') for e in r.annotations.events))

    def test_missing_purpose_question_is_neutral(self):
        r=self.analyze('Anh chuyển giúp em khoản đó trước chiều nay nhé.')
        self.assertTrue(any('thanh toán việc gì' in q for q in r.assessment.follow_up_questions))
        self.assertFalse(any('rút' in q for q in r.assessment.follow_up_questions))

    def test_unknown_mentions_not_global_participant(self):
        r=self.analyze('Chuyển cho người quen của chị. Tài xế tới lấy hàng.')
        self.assertTrue(hasattr(r.annotations,'mentions'))
        self.assertGreaterEqual(len(r.annotations.mentions),2)
        self.assertNotEqual(r.annotations.mentions[0].mention_id,r.annotations.mentions[1].mention_id)
        self.assertFalse(any(e.affected_party_id=='recipient:unknown' for e in r.annotations.events))

    def test_not_yet_is_report_not_prohibition(self):
        r=self.analyze('Tôi chưa gửi mã đăng nhập.')
        e=next(e for e in r.annotations.events if e.event_type=='provide_code')
        self.assertEqual((e.speech_role,e.polarity,e.temporal_state),('claim','negative','pending'))

    def test_no_additional_payment_required(self):
        r=self.analyze('Không cần nộp thêm tiền.')
        self.assertFalse(any(e.speech_role=='request' for e in r.annotations.events))
        self.assertNotEqual(r.assessment.risk_status,'high')

    def test_verify_before_payment_is_not_immediate_payment(self):
        r=self.analyze('Kiểm tra tài khoản mới trước, xác nhận đúng rồi mới chuyển tiền.')
        self.assertFalse(any(e.event_type=='transfer_funds' and e.speech_role=='request' for e in r.annotations.events))
        self.assertTrue(any(x.rule_id=='GROUND-VERIFY-BEFORE-PAYMENT' for x in r.annotations.relations))

    def test_review_information_not_payment_and_no_fake_conflict(self):
        r=self.analyze('Bên em vừa đổi tài khoản nhận tiền cho hóa đơn này sang tài khoản cá nhân. Anh chưa nhận được phụ lục thì để em gửi sau, hiện anh kiểm tra giúp thông tin mới trước nhé.')
        self.assertFalse(any(e.event_type in ('transfer_funds','receive_funds') for e in r.annotations.events))
        self.assertTrue(any(e.semantic.normalized_action=='verify_information' for e in r.annotations.events))
        self.assertFalse(any(s.conflicting_refs for s in r.interpretation.situations))

    def test_unique_name_pronoun_and_ambiguous_alternative(self):
        one=self.analyze('Tài xế tên Nam đang chờ. Giao máy cho anh ấy.')
        refs=[m for m in one.annotations.mentions if m.role=='pronoun']
        self.assertEqual(refs[0].resolution,'unique_antecedent');self.assertTrue(refs[0].participant_id)
        two=self.analyze('Tài xế tên Nam và người quen tên Bình đang chờ. Giao máy cho anh ấy.')
        pronoun=next(m for m in two.annotations.mentions if m.role=='pronoun')
        self.assertEqual(pronoun.resolution,'unresolved');self.assertIsNone(pronoun.participant_id)
        self.assertEqual(len(pronoun.candidate_ids),2)

    def test_concurrent_conversations_do_not_share_mentions(self):
        def run(_):return self.analyze('Tài xế tên Nam đang chờ. Giao máy cho anh ấy.')
        with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,range(2)))
        self.assertTrue({m.mention_id for m in rows[0].annotations.mentions}.isdisjoint({m.mention_id for m in rows[1].annotations.mentions}))
        self.assertTrue({m.participant_id for m in rows[0].annotations.mentions}.isdisjoint({m.participant_id for m in rows[1].annotations.mentions}))

    def test_reported_threat_not_attributed_to_reporter(self):
        r=self.analyze('Họ dọa: nếu không nộp thì mất tiền.')
        loss=next(e for e in r.annotations.events if e.semantic.normalized_action=='loss_consequence')
        self.assertEqual(loss.speech_role,'reported');self.assertEqual(loss.attribution.kind,'reported')
        self.assertNotEqual(loss.semantic.requester_id,loss.semantic.speaker_id)
        self.assertNotEqual(r.assessment.risk_status,'clear')

    def test_exit_condition_without_context_not_imprisonment(self):
        r=self.analyze('Muốn về phải trả hết chi phí.')
        self.assertNotEqual(r.assessment.risk_status,'high')
        self.assertNotEqual(r.assessment.safety_urgency,'urgent')

    def test_passport_exit_debt_relationship(self):
        r=self.analyze('Hộ chiếu giao trưởng nhóm giữ, chưa trả hết chi phí bên anh ứng thì không được tự về.')
        self.assertEqual(r.assessment.risk_status,'high')
        self.assertTrue(any(x.type=='release_conditioned_on_payment' for x in r.annotations.relations))

    def test_known_purpose_not_asked_again(self):
        r=self.analyze('Bạn chuyển tiền để thanh toán hóa đơn điện tháng này nhé.')
        self.assertFalse(any('thanh toán việc gì' in q or 'rút' in q for q in r.assessment.follow_up_questions))
        self.assertTrue(any(x['field']=='payment_purpose' and x['known'] for x in r.annotations.grounding_trace['field_needs']))

    def test_module_error_is_processing_error_not_context_question(self):
        with patch('backend.local_reasoning.grounding.reconcile',side_effect=ValueError('controlled failure')),TestClient(app) as client:
            r=client.post('/api/analyze',json={'text':'Tôi đã nhận đủ tiền của đơn A.'})
        self.assertEqual(r.status_code,503)
        self.assertNotIn('risk_status',r.json())

    def test_projection_uses_only_retained_events(self):
        text='Anh chưa nhận được phụ lục. Tôi sẽ gửi hướng dẫn đăng nhập.'
        q=CaseInput(messages=[{'id':'m1','scope_id':'analysis','text':text}]);r=analyze_local(q)
        self.assertEqual(annotation_errors(q,r.annotations),[])
        ids={e.event_id for e in r.annotations.events}
        self.assertTrue(all(set(f.value.event_ids)<=ids for f in r.annotations.answers_18.__dict__.values()))
        self.assertFalse(r.annotations.answers_18.assets_and_access.value.event_ids)

    def test_known_fact_lost_by_module_is_partial_not_user_omission(self):
        def lose(input,a,frames):
            a,frames=actual_reconcile(input,a,frames)
            a.events=[e for e in a.events if e.event_type!='receive_funds']
            return a,frames
        with patch('backend.local_reasoning.grounding.reconcile',side_effect=lose),TestClient(app) as client:
            r=client.post('/api/analyze',json={'text':'Tôi đã nhận đủ tiền của đơn A.'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['analysis_status'],'partial')
        self.assertNotEqual(r.json()['risk_status'],'clear')
        self.assertFalse(r.json()['follow_up_questions'])

    def test_partial_does_not_erase_independent_high(self):
        def lose(input,a,frames):
            a,frames=actual_reconcile(input,a,frames)
            a.events=[e for e in a.events if e.event_type!='receive_funds']
            return a,frames
        with patch('backend.local_reasoning.grounding.reconcile',side_effect=lose),TestClient(app) as client:
            r=client.post('/api/analyze',json={'text':'Tôi đã nhận đủ tiền của đơn A. Gửi thông tin đăng nhập cho tôi.'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['analysis_status'],'partial')
        self.assertEqual(r.json()['risk_status'],'high')

    def test_unsupported_does_not_blame_missing_user_context(self):
        with TestClient(app) as client:r=client.post('/api/analyze',json={'text':'Mây bay trên núi.'})
        self.assertEqual(r.json()['analysis_status'],'unsupported')
        self.assertNotEqual(r.json()['risk_status'],'clear')
        self.assertFalse(r.json()['follow_up_questions'])

    def test_unknown_object_not_default_money(self):
        r=self.analyze('Bạn nhận thứ đó nhé.')
        self.assertFalse(any(e.event_type=='receive_funds' for e in r.annotations.events))
        self.assertTrue(any(e.semantic.normalized_action=='receive_unknown' for e in r.annotations.events))

    def test_different_deictic_transactions_not_merged(self):
        r=self.analyze('Khoản kia chưa nhận tiền. Đơn này cứ giao máy trước nhé.')
        self.assertEqual(r.assessment.risk_status,'need_context')
        self.assertFalse(any(x.type=='before' for x in r.annotations.relations))
        self.assertTrue(any(x['reason']=='unresolved_transaction_reference' for x in r.annotations.grounding_trace['removed_relations']))

    def test_unknown_driver_unique_pronoun_not_global_unknown(self):
        r=self.analyze('Tài xế đang chờ. Giao máy cho anh ấy.')
        p=next(q for q in r.annotations.mentions if q.role=='pronoun')
        self.assertEqual(p.resolution,'unique_antecedent')
        self.assertTrue(p.participant_id.startswith('entity:mention:'))

    def test_api_does_not_explain_document_receipt_as_money(self):
        with TestClient(app) as client:r=client.post('/api/analyze',json={'text':'Anh chưa nhận được phụ lục.'})
        self.assertEqual(r.status_code,200)
        self.assertFalse(any(f['description']=='receive_funds' for f in r.json()['findings']))
        self.assertFalse(r.json()['answers']['assets_at_risk']['evidence_refs'])

    def test_interpretation_views_share_real_bindings_not_unknown_key(self):
        r=self.analyze('Bạn nộp thêm tiền bảo chứng trước để nhận lại vốn.')
        people={p.participant_id for p in r.annotations.participants}
        self.assertNotIn('recipient:unknown',people)
        for clause in r.interpretation.clause_roles:
            for pid in (clause.requester_id,clause.performer_id,clause.affected_party_id):
                if pid:self.assertIn(pid,people)
        for action in r.interpretation.salient_actions:
            if action.affected_party_id:self.assertIn(action.affected_party_id,people)

    def test_event_budget_is_partial_not_complete_or_missing_user_data(self):
        r=self.analyze('Tôi đã nhận đủ tiền. '*60)
        self.assertEqual(r.analysis_status,'partial')
        self.assertNotEqual(r.assessment.risk_status,'clear')
        self.assertFalse(r.assessment.follow_up_questions)
        self.assertTrue(r.annotations.grounding_trace['processing_limit_reached'])


if __name__=='__main__':unittest.main()
