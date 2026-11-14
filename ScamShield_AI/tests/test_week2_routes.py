import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app


class WebsiteRoutesTests(unittest.TestCase):
    def test_web_assets_and_fixture(self):
        with TestClient(app) as client:
            for url in ['/', '/assets/style.css', '/assets/app.js', '/shared.js', '/result-view.js', '/fixture', '/assets/fixture.js']:
                with self.subTest(url=url):
                    self.assertEqual(client.get(url).status_code, 200)

    def test_config_rejects_removed_provider_without_secrets(self):
        with patch.dict(os.environ, {'SCAMSHIELD_MODE': 'live',
                'SCAMSHIELD_PROVIDER_URL': 'https://user:secret@provider.example/private?key=secret',
                'SCAMSHIELD_API_KEY': 'NEVER_EXPOSE_ME'}):
            response = TestClient(app).get('/client-config')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'EXTERNAL_MODEL_REMOVED')
        self.assertNotIn('provider.example', response.text)
        self.assertNotIn('secret', response.text)
        self.assertNotIn('NEVER_EXPOSE_ME', response.text)


if __name__ == '__main__':
    unittest.main()
