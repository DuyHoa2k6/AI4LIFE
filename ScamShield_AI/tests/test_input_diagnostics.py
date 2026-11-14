import unittest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.providers import get_provider


class InputDiagnosticsTests(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_invalid_link_reports_location_without_echoing_content(self):
        provider = AsyncMock()
        app.dependency_overrides[get_provider] = lambda: provider
        r = TestClient(app).post('/api/analyze', json={'text': 'test', 'links': [{
            'id': 'u', 'message_id': 'm1', 'url': 'https://example.invalid/SECRET',
            'start': 'SECRET_OFFSET'}]})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()['diagnostic']['issues'][0]['path'], ['body','links',0,'start'])
        self.assertNotIn('SECRET', r.text)
        provider.extract.assert_not_called()

    def test_arbitrary_unknown_keys_are_redacted(self):
        r = TestClient(app).post('/api/analyze', json={'text':'test', 'SECRET_UNKNOWN_FIELD':'SECRET_VALUE'})
        self.assertEqual(r.status_code, 422)
        self.assertNotIn('SECRET', r.text)

    def test_label_offset_validation_remains_strict(self):
        r = TestClient(app).post('/api/analyze', json={'text':'test', 'links':[{
            'id':'u','message_id':'m1','url':'https://example.invalid',
            'display_text':'test','start':1,'end':4}]})
        self.assertEqual(r.status_code, 422)

