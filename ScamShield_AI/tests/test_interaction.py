import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.schema import CaseInput
from backend.local_reasoning.validation import annotation_errors

PHONE='Mình đã gửi ảnh biên lai rồi. Bạn chưa thấy tiền vào thì có thể ngân hàng cập nhật chậm. Tài xế đang đứng chờ, bạn giao điện thoại trước giúp mình nhé.'
COMMISSION='Khoản hoa hồng của bạn đã được ghi nhận. Tuy nhiên, số dư đang chờ mở quyền rút. Bạn cần nộp thêm tiền bảo chứng trước thì mới nhận lại cả vốn lẫn hoa hồng.'


class InteractionTests(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy',
            'SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'})
        env.start();self.addCleanup(env.stop)

    def run_text(self,text):
        q=CaseInput(messages=[{'id':'m1','speaker_id':'sender','scope_id':'case','text':text}])
        result=analyze_local(q)
        self.assertEqual(result.analysis_status,'complete')
        self.assertEqual(annotation_errors(q,result.annotations),[])
        for frame in result.interaction_frames:
            self.assertTrue(frame.requester_id)
            if frame.speech_role=='request':self.assertTrue(frame.target_id)
            spans={s.span_id:s for s in result.annotations.spans}
            for ref in frame.evidence_refs:
                s=spans[ref];self.assertEqual(text[s.start:s.end],s.quote)
        return result

    def test_original_missed_cases_now_have_grounded_relations(self):
        for text,risk,rule in [(PHONE,'suspicious','R-HANDOVER'),(COMMISSION,'high','R-PAY-TO-WITHDRAW')]:
            r=self.run_text(text);self.assertEqual(r.assessment.risk_status,risk)
            self.assertIn(rule,r.assessment.applicable_rule_ids)
            self.assertTrue(any(f.condition for f in r.interaction_frames))

    def test_new_asset_names_do_not_need_keyword_entries(self):
        for item in ['chiếc đàn','đồng hồ','bộ máy ảnh','chiếc tủ']:
            r=self.run_text('Tôi chưa nhận được tiền. Bạn giao '+item+' trước nhé.')
            self.assertEqual(r.assessment.risk_status,'suspicious',item)
        r=self.run_text('Chưa thấy khoản thanh toán vào tài khoản. Anh đưa chiếc đồng hồ cho người đến lấy trước nhé.')
        self.assertEqual(r.assessment.risk_status,'suspicious')

    def test_return_condition_reworded_and_next_sentence(self):
        for text in ['Bạn đóng thêm phí xác minh trước thì mới rút được số dư.',
                     'Bạn bổ sung khoản bảo đảm trước để nhận lại tiền đã nạp.',
                     'Bạn nộp phí kích hoạt trước. Sau đó mới nhận lại tiền gốc.']:
            self.assertEqual(self.run_text(text).assessment.risk_status,'high',text)

    def test_warning_denial_and_self_report_not_direct_requests(self):
        for text in ['Cảnh giác: đừng nộp phí để rút tiền đang bị giữ.',
                     'Nếu chưa nhận tiền thì đừng giao đồng hồ.',
                     'Tôi sẽ nộp phí trước để nhận lại tiền.']:
            r=self.run_text(text)
            self.assertFalse(any(f.speech_role=='request' and f.condition for f in r.interaction_frames))
            self.assertNotIn('R-PAY-TO-WITHDRAW',r.assessment.applicable_rule_ids)

    def test_normal_purchase_not_pay_to_withdraw(self):
        r=self.run_text('Bạn thanh toán tiền chiếc ghế trước để nhận hàng nhé.')
        self.assertNotIn('R-PAY-TO-WITHDRAW',r.assessment.applicable_rule_ids)
        self.assertNotEqual(r.assessment.risk_status,'high')

    def test_missing_payment_stays_question_not_negative_claim(self):
        r=self.run_text('Bạn giao chiếc đàn cho người tới lấy nhé.')
        self.assertEqual(r.assessment.risk_status,'need_context')
        self.assertFalse(any(e.event_type=='receive_funds' for e in r.annotations.events))
        self.assertTrue(any('tài khoản' in q for q in r.assessment.follow_up_questions))

    def test_confirmed_payment_before_new_asset_is_not_suspicious(self):
        r=self.run_text('Tôi đã tự kiểm tra và nhận đủ tiền. Bạn giao chiếc đàn cho người đến lấy nhé.')
        self.assertEqual(r.assessment.risk_status,'clear')

    def test_unrelated_transactions_not_bound(self):
        r=self.run_text('Đơn A chưa nhận tiền. Đơn B bạn giao điện thoại trước nhé.')
        self.assertNotIn('R-HANDOVER',r.assessment.applicable_rule_ids)

    def test_other_beneficiary_does_not_become_users_withheld_money(self):
        r=self.run_text('Bạn nộp tiền trước để công ty nhận lại vốn.')
        self.assertFalse(any(f.benefit_event_id for f in r.interaction_frames))

    def test_public_schema_and_rollback(self):
        with TestClient(app) as client:
            d=client.post('/api/analyze',json={'text':COMMISSION})
            self.assertEqual(d.status_code,200,d.text);self.assertEqual(d.json()['risk_status'],'high')
            self.assertNotIn('interaction_frames',d.json())
        with patch.dict(os.environ,{'SCAMSHIELD_CONTEXT_ENABLED':'0'}):
            r=self.run_text(COMMISSION);self.assertEqual(r.assessment.risk_status,'need_context')
            self.assertEqual(r.interaction_frames,[])


if __name__=='__main__':unittest.main()
