import os
import unittest
from unittest.mock import Mock, patch
import httpx
from fastapi.testclient import TestClient
from backend.main import app
from backend import settings
from backend.schemas import AnalyzeRequest
import asyncio


class PrivateBackendSettingsTests(unittest.TestCase):
    def tearDown(self):
        settings._local_values.cache_clear()

    def test_local_constants_and_environment_override(self):
        source = Mock()
        source.read_text.return_value = 'SCAMSHIELD_API_KEY="TEST_SECRET"\nSCAMSHIELD_MODEL="configured-model"\n'
        settings._local_values.cache_clear()
        with patch.object(settings,'CONFIG_FILE',source), patch.dict(os.environ,{},clear=True):
            self.assertEqual(settings.get_setting('SCAMSHIELD_API_KEY'),'TEST_SECRET')
            self.assertEqual(settings.get_setting('SCAMSHIELD_MODEL'),'configured-model')
            with patch.dict(os.environ,{'SCAMSHIELD_MODEL':'environment-model'}):
                self.assertEqual(settings.get_setting('SCAMSHIELD_MODEL'),'environment-model')

    def test_config_is_not_executed_and_errors_do_not_echo_secret(self):
        source = Mock()
        source.read_text.return_value = 'import os\nSCAMSHIELD_API_KEY="TEST_SECRET"'
        settings._local_values.cache_clear()
        with patch.object(settings,'CONFIG_FILE',source), patch.dict(os.environ,{},clear=True):
            with self.assertRaises(settings.LocalConfigError) as ctx:
                settings.get_setting('SCAMSHIELD_API_KEY')
        self.assertNotIn('TEST_SECRET',str(ctx.exception))

    def test_secret_not_served_or_disclosed(self):
        source = Mock()
        source.read_text.return_value = ('SCAMSHIELD_API_KEY="TEST_SECRET"\nSCAMSHIELD_MODE="local_rules"\n'
                                       'SCAMSHIELD_PROVIDER_URL="https://provider.example/chat/completions"\n')
        settings._local_values.cache_clear()
        with patch.object(settings,'CONFIG_FILE',source), patch.dict(os.environ,{},clear=True), TestClient(app) as client:
            response = client.get('/client-config')
            self.assertEqual(response.json()['mode'],'local_rules')
            self.assertNotIn('TEST_SECRET',response.text)
            for url in ['/backend/local_settings.py','/assets/../backend/local_settings.py',
                        '/assets/%2e%2e/backend/local_settings.py','/local_settings.py']:
                self.assertEqual(client.get(url).status_code,404)

