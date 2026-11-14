import os
import unittest
from unittest.mock import patch
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.schema import CaseInput
from backend.local_reasoning.validation import annotation_errors

ACCOUNT='Anh dùng tài khoản này vì điện thoại cũ đang hỏng. Em chuyển giúp anh tiền vào tài khoản đứng tên người khác nhé. Anh đang gấp nên đừng gọi số cũ, tối anh giải thích sau.'
INVOICE='Hóa đơn vẫn như tháng trước, nhưng tài khoản nhận tiền vừa đổi. Bạn chuyển theo thông tin mình gửi riêng trước nhé. Đầu mối trên hợp đồng đang nghỉ, ngày mai gọi xác nhận cũng được.'
TRAVEL='Công việc ở nước ngoài đã có người sắp xếp. Bạn chưa cần xem hợp đồng, cứ đi gặp bên tuyển dụng trước. Đừng kể với gia đình vì họ dễ ngăn cản. Giấy tờ cá nhân giao cho người đón để họ giữ trong thời gian làm việc.'
PAID='Người bán: Lúc sáng tôi chưa thấy tiền vào.\nNgười bán: Tôi vừa kiểm tra lại, khoản tiền của đơn điện thoại đã vào đủ rồi.\nNgười mua: Vậy bạn giao điện thoại cho tài xế giúp mình nhé.'


class ClauseContextTests(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ,{'SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1'})
        env.start();self.addCleanup(env.stop)

    def run_case(self,text=None,messages=None):
        q=CaseInput(messages=messages or [{'id':'m1','scope_id':'case','text':text}])
        r=analyze_local(q)
        self.assertEqual(r.analysis_status,'complete',r.annotations.limitations)
        self.assertEqual(annotation_errors(q,r.annotations),[])
        self.assertIsNotNone(r.interpretation)
        spans={s.span_id:s for s in r.annotations.spans}
        for c in r.interpretation.clause_roles:
            self.assertTrue(c.evidence_refs)
            self.assertTrue(all(s in spans for s in c.evidence_refs))
            if c.affected_status=='textual_role':self.assertTrue(c.affected_party_id)
        return r

    def test_account_and_invoice_linked(self):
        for text in (ACCOUNT,INVOICE):
            # Revised policy G: unverified identity + third-party payee +
            # blocked verification is high; invoice alone remains suspicious.
            r=self.run_case(text);self.assertEqual(r.assessment.risk_status,'high' if text==ACCOUNT else 'suspicious')
            self.assertIn('R-CLAUSE-PAYMENT-VERIFY',r.assessment.applicable_rule_ids)
            self.assertTrue(any(s.is_primary for s in r.interpretation.salient_actions))

    def test_travel_loss_of_autonomy_not_identity(self):
        r=self.run_case(TRAVEL)
        self.assertEqual(r.assessment.risk_status,'high')
        self.assertEqual(r.assessment.safety_urgency,'preventive')
        self.assertTrue(any(p.participant_id.startswith('custodian:unknown:') for p in r.annotations.participants))
        primary=[s for s in r.interpretation.salient_actions if s.is_primary]
        self.assertTrue(any('giấy tờ' in s.consequence for s in primary))
        self.assertNotIn('trafficking_confirmed',r.assessment.supported_conclusions)

    def test_payment_update_same_speaker(self):
        r=self.run_case(PAID);self.assertEqual(r.assessment.risk_status,'clear')
        self.assertTrue(any(s.type=='state_update' for s in r.annotations.relations))

    def test_buyers_reassurance_does_not_replace_sellers_report(self):
        r=self.run_case(PAID.replace('Người bán: Tôi vừa','Người mua: Tôi vừa'))
        self.assertNotEqual(r.assessment.risk_status,'clear')
        self.assertFalse(any(s.rule_id=='LINK-EXPLICIT-PAYMENT-UPDATE' for s in r.annotations.relations))

    def test_warning_hypothesis_and_denial_do_not_trigger(self):
        for text in ['Cảnh báo: '+TRAVEL,'Giả sử trong bài tập: '+TRAVEL,
                     'Nếu có ai nói “'+TRAVEL+'”, đừng làm theo.']:
            r=self.run_case(text)
            self.assertNotIn('R-CLAUSE-TRAVEL-CONTROL',r.assessment.applicable_rule_ids)

    def test_no_high_for_unknown_identity_or_travel_alone(self):
        for text in ['Bạn cứ đi gặp bên tuyển dụng trước.',
                     'Bạn chưa cần xem hợp đồng, cứ đi gặp bên tuyển dụng trước.',
                     'Giấy tờ cá nhân giao cho người đón để họ giữ trong thời gian làm việc.']:
            r=self.run_case(text);self.assertNotEqual(r.assessment.risk_status,'high')

    def test_document_custody_with_secret_is_level_three(self):
        r=self.run_case('Bạn cứ đi gặp bên tuyển dụng trước. Đừng kể với gia đình. Giấy tờ cá nhân giao cho người đón để họ giữ trong thời gian làm việc.')
        self.assertEqual(r.assessment.risk_status,'suspicious')

    def test_returnable_documents_not_control_rule(self):
        text='Bạn cứ đi gặp bên tuyển dụng trước. Đừng kể với gia đình. Giấy tờ cá nhân giao cho người đón để họ giữ giúp, bạn có thể lấy lại bất cứ lúc nào.'
        r=self.run_case(text)
        self.assertNotIn('R-CLAUSE-TRAVEL-CONTROL',r.assessment.applicable_rule_ids)
        self.assertNotIn('R-CLAUSE-TRAVEL-CUSTODY',r.assessment.applicable_rule_ids)

    def test_document_handover_denial_not_control(self):
        text='Bạn chưa cần xem hợp đồng, cứ đi gặp bên tuyển dụng trước. Đừng kể với gia đình. Bạn không nên giao giấy tờ cá nhân cho người đón để họ giữ trong thời gian làm việc.'
        r=self.run_case(text)
        self.assertNotIn('R-CLAUSE-TRAVEL-CONTROL',r.assessment.applicable_rule_ids)
        self.assertFalse(any(e.description=='documents_custody' and e.speech_role=='request' for e in r.annotations.events))

    def test_buyer_checking_own_account_is_not_seller_receipt(self):
        r=self.run_case('Người mua: Tôi vừa kiểm tra lại, khoản tiền của đơn điện thoại đã vào đủ rồi.\nNgười mua: Bạn giao điện thoại cho tài xế nhé.')
        self.assertNotEqual(r.assessment.risk_status,'clear')

    def test_different_scopes_not_linked(self):
        r=self.run_case(messages=[{'id':'a','speaker_id':'S','scope_id':'A','text':'Tài khoản nhận tiền vừa đổi. Bạn chuyển theo thông tin mình gửi riêng trước nhé.'},
            {'id':'b','speaker_id':'S','scope_id':'B','text':'Ngày mai gọi xác nhận cũng được.'}])
        self.assertNotIn('R-CLAUSE-PAYMENT-VERIFY',r.assessment.applicable_rule_ids)

    def test_different_speakers_not_linked(self):
        r=self.run_case('Người bán: Tài khoản nhận tiền vừa đổi. Bạn chuyển theo thông tin mình gửi riêng trước nhé.\nNgười mua: Ngày mai gọi xác nhận cũng được.')
        self.assertNotIn('R-CLAUSE-PAYMENT-VERIFY',r.assessment.applicable_rule_ids)

    def test_unknown_affected_party_remains_unknown(self):
        r=self.run_case('Tài khoản nhận tiền vừa đổi.')
        self.assertTrue(any(c.affected_status=='unknown' and c.affected_party_id is None for c in r.interpretation.clause_roles))
        self.assertNotEqual(r.assessment.risk_status,'high')

    def test_unicode_offsets_and_same_transaction(self):
        r=self.run_case('📩 '+INVOICE)
        self.assertEqual(r.assessment.risk_status,'suspicious')
        r=self.run_case('Đơn A: tài khoản nhận tiền vừa đổi. Đơn B: Bạn chuyển theo thông tin mình gửi riêng trước nhé. Ngày mai gọi xác nhận cũng được.')
        self.assertNotIn('R-CLAUSE-PAYMENT-VERIFY',r.assessment.applicable_rule_ids)


if __name__=='__main__':unittest.main()
