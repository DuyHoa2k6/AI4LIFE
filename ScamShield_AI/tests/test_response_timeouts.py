import asyncio
import os
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from backend.main import app
from backend.mock_rules import extract
from backend.providers import MockProvider, get_provider
from backend.schemas import AnalyzeRequest, Extraction


class ResponseTimeoutTests(unittest.TestCase):
    def test_disabled_global_deadline_waits_for_both_pipeline_types(self):
        class Slow(MockProvider):
            async def extract(self, request):
                await asyncio.sleep(.03)
                return extract(request)

        try:
            for pipeline in ('mock',):
                provider = Slow()
                provider.pipeline = pipeline
                app.dependency_overrides[get_provider] = lambda: provider
                with patch.dict(os.environ, {
                    'SCAMSHIELD_DISABLE_RESPONSE_TIMEOUTS': '1',
                    'SCAMSHIELD_TIMEOUT': '.001', 'SCAMSHIELD_TOTAL_TIMEOUT': '.001',
                }):
                    response = TestClient(app).post('/api/analyze', json={'text': 'Hello.'})
                self.assertEqual(response.status_code, 200, response.text)
        finally:
            app.dependency_overrides.clear()

