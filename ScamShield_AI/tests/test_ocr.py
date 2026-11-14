import io
import time
import unittest
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.providers import get_provider, MockProvider
from backend import ocr


class OcrTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        app.dependency_overrides[get_provider]=lambda:MockProvider()
        self.source={'text':'Ứng tiền để nhận hoa hồng.','image_sha256':'a'*64,
                     'confidence':91,'width':300,'height':100,'blocks':[]}
        ocr._sources['unit-source']=(time.monotonic()+100,self.source)

    def tearDown(self):
        app.dependency_overrides.clear()
        ocr._sources.pop('unit-source',None)

    def payload(self):
        return {'messages':[{'id':'img','speaker':'unknown','text':self.source['text']}],
                'ocr_sources':[{'message_id':'img','source_id':'unit-source'}]}

    def test_provenance_and_quote_in_common_analyze_endpoint(self):
        r=self.client.post('/api/analyze',json=self.payload())
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['risk_status'],'high')
        self.assertEqual(r.json()['schema_version'],'1.6')
        self.assertEqual(r.json()['input_sources'][0]['message_id'],'img')
        self.assertTrue(r.json()['input_warnings'])
        self.assertTrue(all(e['message_id']=='img' for f in r.json()['findings'] for e in f['evidence']))

    def test_changed_ocr_rejected_before_provider(self):
        class Never:
            async def extract(self,request):raise AssertionError('Provider called for modified OCR')
        app.dependency_overrides[get_provider]=lambda:Never()
        p=self.payload();p['messages'][0]['text']='Đã sửa bản OCR.'
        r=self.client.post('/api/analyze',json=p)
        self.assertEqual(r.status_code,422)
        self.assertEqual(r.json()['code'],'OCR_TEXT_CHANGED')

    def test_expired_or_forged_source_rejected(self):
        p=self.payload();p['ocr_sources'][0]['source_id']='forged'
        self.assertEqual(self.client.post('/api/analyze',json=p).status_code,422)
        ocr._sources['unit-source']=(0,self.source)
        r=self.client.post('/api/analyze',json=self.payload())
        self.assertEqual(r.json()['code'],'OCR_SOURCE_EXPIRED')

    def test_reference_missing_or_duplicate_message_rejected(self):
        for refs in ([{'message_id':'absent','source_id':'unit-source'}],
                     [{'message_id':'img','source_id':'unit-source'}]*2):
            p=self.payload();p['ocr_sources']=refs
            self.assertEqual(self.client.post('/api/analyze',json=p).status_code,422)

    def test_image_body_limits_and_bad_format(self):
        self.assertEqual(self.client.post('/api/ocr',content=b'a'*(4*1024*1024+1),headers={'Content-Type':'image/png'}).status_code,413)
        self.assertEqual(self.client.post('/api/ocr',content=b'<svg/>',headers={'Content-Type':'image/svg+xml'}).status_code,415)
        self.assertEqual(self.client.post('/api/ocr',content=b'not an image',headers={'Content-Type':'image/png'}).status_code,422)

    def test_large_pixel_image_rejected_before_node(self):
        buf=io.BytesIO();Image.new('RGB',(3000,3000),'white').save(buf,format='PNG')
        with patch('backend.ocr.subprocess.run',side_effect=AssertionError('Must not invoke node')):
            self.assertEqual(self.client.post('/api/ocr',content=buf.getvalue(),headers={'Content-Type':'image/png'}).status_code,422)

    def test_blank_ocr_does_not_call_analyze(self):
        blank={**self.source,'status':'no_text','text':'','source_id':None,
               'engine':'tesseract.js-7.0.0-vie+eng','ocr_ms':1.0,'notice':'Check the original image.'}
        with patch('backend.main.recognize',return_value=blank):
            r=self.client.post('/api/ocr',content=b'placeholder',headers={'Content-Type':'image/png'})
        self.assertEqual(r.json()['status'],'no_text')

