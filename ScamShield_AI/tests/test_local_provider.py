"""Local v2 behind the production client endpoint; no provider/network calls."""
import os
import unittest
from unittest.mock import AsyncMock,patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.providers import get_provider
from backend.schemas import AnalyzeResponse
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.schema import CaseInput


CASES=[
 ('P01','Gửi mã OTP cho tôi.','high','preventive'),
 ('P02','Cảnh báo: đừng gửi OTP.','clear','undetermined'),
 ('P03','Đọc sáu số vừa hiện để nhận tiền.','need_context','undetermined'),
 ('P04','Chưa thấy tiền về, nhưng cứ giao máy trước.','suspicious','preventive'),
 ('P05','Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy nhé.','clear','undetermined'),
 ('P06','Chuyển thêm tiền để rút số dư.','high','preventive'),
 ('P07','Gửi ảnh CCCD qua chat.','suspicious','preventive'),
 ('P08','Mây bay trên núi.','need_context','undetermined'),
 ('P09','Hiện tại tôi bị giữ lại và không được rời đi.','high','urgent'),
 ('P10','Hãy đi cùng và giấu gia đình.','suspicious','preventive'),
 ('P11','ko ck tiền trước gửi mk tk cho tôi','high','preventive'),
 ('P12','Bài tuyên truyền cảnh báo: có người bị ép làm việc.','clear','undetermined')]


class LocalProviderTests(unittest.TestCase):
    def setUp(self):
        mode=patch.dict(os.environ,{'SCAMSHIELD_REASONER':'legacy'})
        mode.start();self.addCleanup(mode.stop)

    def test_client_endpoint_twelve_cases_and_exact_evidence(self):
        with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules'}), \
             patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as live, \
             patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('Network forbidden')) as network,TestClient(app) as client:
            for cid,text,risk,urgency in CASES:
                with self.subTest(case=cid):
                    response=client.post('/api/analyze',json={'text':text})
                    self.assertEqual(response.status_code,200)
                    d=AnalyzeResponse.model_validate(response.json())
                    self.assertEqual((d.risk_status,d.safety_urgency),(risk,urgency))
                    self.assertEqual(d.mode,'local_rules');self.assertEqual(d.analysis.live_status,'not_used')
                    for f in d.findings:
                        self.assertEqual(f.speaker,'unknown')
                        for e in f.evidence:self.assertEqual(text[e.start:e.end],e.quote)
                    if urgency=='urgent':self.assertTrue(d.urgency_evidence)
            live.assert_not_called();network.assert_not_called()

    def test_client_notice_and_provider_are_local_and_external_modes_rejected(self):
        with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules'}),TestClient(app) as client:
            self.assertEqual(get_provider().pipeline,'local_rules')
            config=client.get('/client-config').json()
            self.assertEqual(config['url_network_enabled'],os.environ.get('SCAMSHIELD_URL_NETWORK_ENABLED','1')=='1')
            self.assertIn('không gửi tới Gemini',config['processing_notice'])
        for mode in ('live','hybrid','two_pass'):
            with patch.dict(os.environ,{'SCAMSHIELD_MODE':mode}),TestClient(app) as client:
                response=client.post('/api/analyze',json={'text':'Gửi OTP cho tôi.'})
                self.assertEqual(response.status_code,503)
                self.assertEqual(response.json()['code'],'EXTERNAL_MODEL_REMOVED')

    def test_provider_errors_do_not_create_clear(self):
        with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules'}), \
             patch('backend.local_reasoning.legacy_engine.load_assets',side_effect=ValueError('broken')),TestClient(app) as client:
            r=client.post('/api/analyze',json={'text':'Nội dung cần kiểm tra.'})
            self.assertEqual(r.status_code,503)
            self.assertEqual(r.json()['code'],'LOCAL_ANALYSIS_UNAVAILABLE')
            self.assertNotIn('risk_status',r.json())

    def test_keeps_message_ids_speakers_and_context_claim_source(self):
        messages=[{'id':'sender-msg','speaker':'Người gửi','text':'Đọc sáu số vừa hiện để nhận tiền.'},
                  {'id':'receiver-msg','speaker':'Người nhận','text':'Đó là mã đăng nhập.'}]
        with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules'}),TestClient(app) as client:
            r=client.post('/api/analyze',json={'messages':messages,'context':'Tôi chưa xác minh danh tính.'})
            self.assertEqual(r.status_code,200);self.assertEqual(r.json()['risk_status'],'high')
            by_id={m['id']:m for m in messages}
            for f in r.json()['findings']:
                for e in f['evidence']:
                    self.assertEqual(f['speaker'],by_id[e['message_id']]['speaker'])
                    self.assertEqual(by_id[e['message_id']]['text'][e['start']:e['end']],e['quote'])

    def test_reported_speech_maps_to_claim_without_changing_raw_attribution_or_risk(self):
        # Real parser reproduction of the user's 500: raw Event allows reported,
        # while public Finding intentionally retains its existing five-role schema.
        text='Họ nói sẽ giữ hộ chiếu.'
        for mode in ('legacy','facts'):
            with self.subTest(reasoner=mode),patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules',
                    'SCAMSHIELD_REASONER':mode,'SCAMSHIELD_URL_NETWORK_ENABLED':'0'}),TestClient(app) as client:
                raw=client.post('/api/analyze-local',json={'messages':[{'id':'m1','text':text}]}).json()
                self.assertIn('reported',[e['speech_role'] for e in raw['annotations']['events']])
                response=client.post('/api/analyze',json={'text':text})
                self.assertEqual(response.status_code,200,response.text)
                public=AnalyzeResponse.model_validate(response.json())
                self.assertEqual(public.risk_status,raw['assessment']['risk_status'])
                self.assertTrue(public.findings)
                self.assertTrue(all(f.speech_role=='claim' for f in public.findings))
                for f in public.findings:
                    for e in f.evidence:self.assertEqual(text[e.start:e.end],e.quote)
