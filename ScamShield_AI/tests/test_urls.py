import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.providers import get_provider,MockProvider
from backend.schemas import AnalyzeRequest
from backend.urls import analyze_urls,model_input



class UrlTests(unittest.TestCase):

    def analyze(self,url,label=''):
        text=label or 'Liên kết đính kèm.'
        req=AnalyzeRequest(text=text,links=[{'id':'u','message_id':'m1','url':url,'display_text':label}])
        return analyze_urls(req)[0]

    def codes(self,u):return {s.code for s in u.signals}

    def test_psl_and_private_suffix(self):
        self.assertEqual(self.analyze('https://a.example.co.uk/').registered_domain,'example.co.uk')
        self.assertEqual(self.analyze('https://alice.github.io/').registered_domain,'alice.github.io')

    def test_lookalike_and_brand_subdomain(self):
        self.assertIn('lookalike_reference_domain',self.codes(self.analyze('https://youtubee.com/')))
        self.assertIn('brand_in_subdomain',self.codes(self.analyze('https://youtube.com.evil.net/')))

    def test_unicode_confusable_and_legitimate_idn_not_automatically_bad(self):
        u=self.analyze('https://gооgle.com/') # both o are Cyrillic
        self.assertIn('unicode_confusable_reference',self.codes(u))
        self.assertIn('punycode_hostname',self.codes(u))
        valid=self.analyze('https://vídụ.vn/')
        self.assertEqual(valid.status,'parsed')
        self.assertNotIn('unicode_confusable_reference',self.codes(valid))

    def test_userinfo_ip_and_port_observed_without_fetch(self):
        u=self.analyze('https://youtube.com:PRIVATE@127.0.0.1:8080/p?token=SECRET#x')
        self.assertEqual(u.hostname,'127.0.0.1')
        self.assertTrue({'userinfo_present','ip_literal','nonstandard_port'}<=self.codes(u))
        self.assertNotIn('PRIVATE',u.model_dump_json())
        self.assertNotIn('SECRET',u.model_dump_json())

    def test_display_destination_mismatch_and_no_false_www_difference(self):
        self.assertIn('display_target_mismatch',self.codes(self.analyze('https://evil.net/','https://youtube.com')))
        self.assertNotIn('display_target_mismatch',self.codes(self.analyze('https://www.youtube.com/watch','https://youtube.com')))

    def test_invalid_schemes_controls_and_ports_are_data_not_requests(self):
        for value in ('javascript:alert(1)','file:///etc/passwd','https://a.com:99999','https://a.com\\evil','https://a.com\n.evil'):
            with self.subTest(url=value):self.assertEqual(self.analyze(value).status,'invalid')

    def test_exact_reference_is_not_reputation_or_safety(self):
        u=self.analyze('https://accounts.google.com/')
        self.assertEqual(u.reference_domain,'google.com')
        self.assertEqual(u.reputation_status,'not_checked')
        self.assertNotIn('lookalike_reference_domain',self.codes(u))

    def test_offline_no_dns_or_http_request(self):
        with patch('socket.getaddrinfo',side_effect=AssertionError('Unexpected DNS')),patch('httpx.get',side_effect=AssertionError('Unexpected HTTP')):
            self.assertEqual(self.analyze('https://youtubee.com/login').status,'parsed')

    def test_visible_label_url_not_extracted_as_second_destination(self):
        p=AnalyzeRequest(text='Đăng nhập https://youtube.com',links=[{'id':'u','message_id':'m1','url':'https://evil.net/','display_text':'https://youtube.com'}])
        result=analyze_urls(p)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].hostname,'evil.net')





    def test_bad_label_ids_rejected_before_provider(self):
        app.dependency_overrides[get_provider]=lambda:MockProvider()
        for link in ({'id':'u','message_id':'missing','url':'https://a.com'},
                     {'id':'u','message_id':'m1','url':'https://a.com','display_text':'not in message'}):
            self.assertEqual(TestClient(app).post('/api/analyze',json={'text':'Hello','links':[link]}).status_code,422)



    def test_text_and_ocr_urls_are_collected_with_message_provenance(self):
        p=AnalyzeRequest(text='https://youtubee.com',ocr_sources=[{'message_id':'m1','source_id':'test-only'}])
        self.assertEqual(analyze_urls(p)[0].origin,'ocr')
        self.assertEqual(analyze_urls(AnalyzeRequest(text='https://example.com'))[0].origin,'text')
