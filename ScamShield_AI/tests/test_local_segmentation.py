"""Unpunctuated instructions and contrast cases, not general NLP accuracy."""
import unicodedata
import unittest
from unittest.mock import AsyncMock,patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.schemas import AnalyzeRequest
from backend.local_observation.analyzer import analyze
from backend.local_observation.segmentation import segments


CASES=[
 ('S01','Chiều nay giao hàng nhé gửi mã OTP cho tôi',
  ['Chiều nay giao hàng nhé','gửi mã OTP cho tôi']),
 ('S02','Đừng gửi OTP cho người lạ gửi mã đăng nhập cho tôi để hoàn tiền',
  ['Đừng gửi OTP cho người lạ','gửi mã đăng nhập cho tôi','để hoàn tiền']),
 ('S03','Chưa thấy tiền về, nhưng cứ giao máy trước.',
  ['Chưa thấy tiền về,','nhưng cứ giao máy trước.']),
 ('S04','Nếu chưa nhận tiền thì đừng giao máy',
  ['Nếu chưa nhận tiền','thì đừng giao máy']),
 ('S05','Đừng chuyển tiền và gửi OTP', ['Đừng chuyển tiền và gửi OTP']),
 ('S06','Gửi mã đăng nhập cho tôi',['Gửi mã đăng nhập cho tôi']),
 ('S07','Mở liên kết để đăng nhập',['Mở liên kết','để đăng nhập']),
 ('S08','Tôi đã chuyển tiền rồi',['Tôi đã chuyển tiền rồi']),
 ('S09','Công việc đã xong',['Công việc đã xong']),
 ('S10','Tôi đi trên đê rồi về nhà',['Tôi đi trên đê rồi về nhà']),
 ('S11','😀 Chuyển 500.000,50 đồng mở https://example.invalid/a?x=1&y=2',
  ['😀 Chuyển 500.000,50 đồng','mở https://example.invalid/a?x=1&y=2']),
 ('S12','Cảnh báo “gửi OTP rồi chuyển tiền” gửi OTP cho tôi',
  ['Cảnh báo “gửi OTP rồi chuyển tiền”','gửi OTP cho tôi']),
 ('S13','Tài xế đang chờ bạn giao hàng nhé',['Tài xế đang chờ','bạn giao hàng nhé']),
 ('S14','Đơn A chưa thanh toán đơn B đã nhận đủ giao đơn B nhé',
  ['Đơn A chưa thanh toán','đơn B đã nhận đủ','giao đơn B nhé']),
 ('S15','Cài ứng dụng và cấp quyền điều khiển',['Cài ứng dụng và cấp quyền điều khiển']),
 ('S16','Đọc sáu số để nhận tiền',['Đọc sáu số','để nhận tiền']),
]


class LocalSegmentationTests(unittest.TestCase):
    def test_sixteen_explicit_boundary_references(self):
        for cid,text,expected in CASES:
            with self.subTest(case=cid):
                actual=segments(text)
                self.assertEqual([text[u.start:u.end] for u in actual],expected)
                self.assertTrue(all(u.start<u.end for u in actual))
                # No non-whitespace character is dropped or synthesized.
                self.assertEqual(''.join(c for u in actual for c in text[u.start:u.end] if not c.isspace()),
                                 ''.join(c for c in text if not c.isspace()))

    def test_negation_stops_at_independent_request(self):
        result=analyze(AnalyzeRequest(text=CASES[1][1]))
        codes=[e for e in result.events if e.action_type=='provide_code']
        self.assertEqual([e.polarity for e in codes],['negative','positive'])
        self.assertEqual([f.speech_role for f in result.adapter.findings if f.description=='provide_code'],['denial','request'])
        self.assertTrue(any(u.boundary_reason=='action_restart' and u.boundary_status=='inferred' for u in result.units))

    def test_warning_attribution_stops_at_new_request(self):
        result=analyze(AnalyzeRequest(text=CASES[11][1]))
        codes=[e for e in result.events if e.action_type=='provide_code']
        self.assertEqual([e.speech_role for e in codes],['quoted_warning','request'])

    def test_coordinated_negation_is_uncertain_not_positive(self):
        result=analyze(AnalyzeRequest(text=CASES[4][1]))
        self.assertEqual(len(result.units),1)
        self.assertEqual(result.units[0].boundary_status,'uncertain')
        code=next(e for e in result.events if e.action_type=='provide_code')
        self.assertEqual(code.polarity,'uncertain')
        self.assertTrue(result.follow_up_questions)

    def test_transaction_change_without_punctuation(self):
        result=analyze(AnalyzeRequest(text=CASES[13][1]))
        # "đơn B đã nhận đủ" omits the object; A's money cannot supply it.
        self.assertEqual([e.transaction_id for e in result.events],['don a','don b'])
        self.assertFalse(any(e.action_type=='receive_funds' for e in result.events))
        events={e.action_id:e for e in result.events}
        for r in result.relations:
            if r.from_id in events and r.to_id in events:
                self.assertEqual(events[r.from_id].transaction_id,events[r.to_id].transaction_id)

    def test_decomposed_unicode_preserves_original(self):
        text=unicodedata.normalize('NFD',CASES[1][1])
        result=analyze(AnalyzeRequest(text=text))
        self.assertEqual(len(result.units),3)
        for e in result.evidence:self.assertEqual(text[e.start:e.end],e.quote)
        self.assertEqual([e.polarity for e in result.events if e.action_type=='provide_code'],['negative','positive'])

    def test_context_question_and_other_speaker_do_not_supply_split_text(self):
        request=AnalyzeRequest(messages=[{'id':'a','speaker':'one','text':'Đừng gửi OTP'},
            {'id':'b','speaker':'two','text':'Gửi OTP cho tôi'}],context='Đừng làm theo.',question='Đó có phải cảnh báo không?')
        result=analyze(request)
        self.assertEqual([f.speaker for f in result.adapter.findings],['one','two'])
        self.assertEqual([e.polarity for e in result.events],['negative','positive'])

    def test_api_zero_external_calls_and_original_quotes(self):
        with patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as provider, \
             patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('Network forbidden')) as network,TestClient(app) as client:
            for _,text,_ in CASES:
                response=client.post('/api/observe',json={'text':text})
                self.assertEqual(response.status_code,200)
                for span in response.json()['evidence']:self.assertEqual(text[span['start']:span['end']],span['quote'])
            provider.assert_not_called();network.assert_not_called()

    def test_relative_clause_not_forced_into_new_direct_request(self):
        text='Đừng gửi OTP cho người vừa gửi mã cho tôi'
        result=analyze(AnalyzeRequest(text=text))
        self.assertEqual(len(result.units),1)
        codes=[e for e in result.events if e.action_type=='provide_code']
        self.assertEqual(codes[1].speech_role,'unknown')
        self.assertEqual(codes[1].polarity,'uncertain')

    def test_warning_then_contrast_instruction_has_separate_scope(self):
        text='Cảnh báo “gửi OTP cho người lạ” nhưng hãy gửi OTP cho tôi'
        result=analyze(AnalyzeRequest(text=text))
        self.assertEqual([u.quote for u in result.units],['Cảnh báo “gửi OTP cho người lạ”','nhưng hãy gửi OTP cho tôi'])
        self.assertEqual([e.speech_role for e in result.events if e.action_type=='provide_code'],['quoted_warning','request'])
