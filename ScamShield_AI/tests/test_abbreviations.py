"""Development references for context-gated abbreviations and exact evidence."""
import unicodedata
import unittest
from unittest.mock import patch,AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_observation.analyzer import analyze
from backend.local_observation.abbreviations import resolve
from backend.local_observation.text import normalize
from backend.schemas import AnalyzeRequest


CASES=[
 ('AB01','ck 500k cho tôi','chuyen khoan 500k cho toi','transfer_funds','positive'),
 ('AB02','ko ck tiền trước','khong chuyen khoan tien truoc','transfer_funds','negative'),
 ('AB03','k cần ck tiền','khong can chuyen khoan tien','transfer_funds','negative'),
 ('AB04','Gửi mk tk cho tôi','gui mat khau tai khoan cho toi','provide_credentials','positive'),
 ('AB05','Gửi ảnh CCCD qua chat','gui anh can cuoc cong dan qua chat','provide_documents','positive'),
 ('AB06','Gửi ảnh CMND','gui anh chung minh nhan dan','provide_documents','positive'),
 ('AB07','Cài app này','cai ung dung nay','install_app','positive'),
 ('AB08','Bật cs mh','bat chia se man hinh','share_screen','positive'),
 ('AB09','Tôi là CSKH','toi la cham soc khach hang','identity_claim','positive'),
 ('AB10','Chưa nhận đc tiền','chua nhan duoc tien','receive_funds','negative'),
 ('AB11','ck tôi về nhà với con','chong toi ve nha voi con',None,None),
 ('AB12','Thị trường ck giảm','thi truong chung khoan giam',None,None),
 ('AB13','Bản vẽ tk logo','ban ve thiet ke logo',None,None),
 ('AB14','tk clip TikTok','tiktok clip tiktok',None,None),
 ('AB15','cs bảo hành sản phẩm','chinh sach bao hanh san pham',None,None),
 ('AB16','mh học máy cần huấn luyện','mo hinh hoc may can huan luyen',None,None),
 ('AB17','bh sản phẩm máy này','bao hanh san pham may nay',None,None),
 ('AB18','bh y tế','bao hiem y te',None,None),
 ('AB19','bh phải làm gì','bay gio phai lam gi',None,None),
 ('AB20','sđt và STK','so dien thoai va so tai khoan',None,None),
 ('AB21','mk nhận đủ tiền','minh nhan du tien','receive_funds','positive'),
 ('AB22','ib cho tôi','nhan tin rieng cho toi',None,None),
]


class AbbreviationTests(unittest.TestCase):
    def test_twenty_two_context_and_action_references(self):
        for cid,text,expected,kind,polarity in CASES:
            with self.subTest(case=cid):
                self.assertEqual(normalize(text).text,expected)
                result=analyze(AnalyzeRequest(text=text))
                if kind:
                    self.assertTrue(any(e.action_type==kind and e.polarity==polarity for e in result.events))
                else:self.assertFalse(result.events)

    def test_ambiguous_or_missing_context_is_not_guessed(self):
        for text,word in [('ck','ck'),('tk','tk'),('đc','đc'),('kh','kh'),('cs','cs'),
                          ('ck tiền đầu tư','ck'),('mk ck tiền tk','mk')]:
            with self.subTest(text=text):
                rows=resolve(text)[2];item=next(r for r in rows if r['quote']==word)
                self.assertNotEqual(item['status'],'resolved')
                self.assertIsNone(item['expansion'])
                result=analyze(AnalyzeRequest(text=text))
                self.assertTrue(any(word in q for q in result.follow_up_questions))

    def test_original_quotes_and_offsets_even_when_replacement_is_long(self):
        for text in ('😀 ko ck 500k Gửi CCCD',unicodedata.normalize('NFD','Chưa nhận đc tiền')):
            result=analyze(AnalyzeRequest(text=text))
            for span in result.evidence:self.assertEqual(text[span.start:span.end],span.quote)
            for item in result.abbreviation_resolutions:self.assertEqual(text[item.start:item.end],item.quote)
            self.assertNotIn('căn cước công dân',[e.quote for e in result.evidence])
        n=normalize('ck 500k');a=n.text.index('chuyen');b=a+len('chuyen khoan')
        self.assertEqual(n.original_range(a,b),(0,2))

    def test_no_changes_inside_url_email_code_or_word(self):
        text='https://ck.example/tk?mk=ko tk@example.com `ck tk mk` abc_ck_id 500k 1234567'
        self.assertFalse(resolve(text)[2])
        self.assertEqual(normalize(text).text,text)

    def test_protected_text_cannot_supply_disambiguating_context(self):
        rows=resolve('tk https://example.com/ngan-hang/mk/otp')[2]
        self.assertNotEqual(rows[0]['status'],'resolved')

    def test_no_context_from_next_sentence_other_message_or_user_context(self):
        self.assertNotEqual(resolve('tk. Ngân hàng gửi OTP')[2][0]['status'],'resolved')
        result=analyze(AnalyzeRequest(messages=[{'id':'a','speaker':'s','text':'tk'},
            {'id':'b','speaker':'s','text':'Ngân hàng gửi OTP.'}],context='Đó là tài khoản ngân hàng.'))
        self.assertNotEqual(next(r for r in result.abbreviation_resolutions if r.message_id=='a').status,'resolved')

    def test_labels_names_and_amounts_are_not_expanded(self):
        text='Đơn A và đơn B có giá 500k Hong được gọi tên'
        self.assertFalse(resolve(text)[2])
        self.assertEqual(normalize(text).text,'don a va don b co gia 500k hong duoc goi ten')

    def test_spaced_currency_k_and_order_labels_do_not_become_negation(self):
        for text in ('500 k cần ck tiền','Đơn K cần ck tiền'):
            result=analyze(AnalyzeRequest(text=text))
            self.assertFalse(any(r.quote.lower()=='k' for r in result.abbreviation_resolutions))
            self.assertTrue(any(e.action_type=='transfer_funds' and e.polarity=='positive' for e in result.events))

    def test_literal_short_code_is_not_rewritten(self):
        self.assertFalse(resolve('Mã KO và ID tk')[2])

    def test_quotes_still_have_warning_role_after_expansion(self):
        result=analyze(AnalyzeRequest(text='Cảnh báo “ko ck tiền để nhận thưởng”'))
        self.assertTrue(result.events)
        self.assertTrue(all(e.speech_role=='quoted_warning' for e in result.events))

    def test_segmentation_and_negation_use_same_expansion(self):
        result=analyze(AnalyzeRequest(text='ko ck tiền gửi mk tk cho tôi'))
        self.assertEqual(len(result.units),2)
        money=next(e for e in result.events if e.action_type=='transfer_funds')
        password=next(e for e in result.events if e.action_type=='provide_credentials')
        self.assertEqual((money.polarity,password.polarity),('negative','positive'))
        self.assertEqual(next(s.quote for s in result.evidence if s.id==money.negation_span),'ko')

    def test_api_traces_no_live_calls(self):
        with patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as live, \
             patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('Network forbidden')) as network,TestClient(app) as client:
            for _,text,_,_,_ in CASES:
                r=client.post('/api/observe',json={'text':text})
                self.assertEqual(r.status_code,200)
                self.assertTrue(r.json()['abbreviation_version'])
            live.assert_not_called();network.assert_not_called()
