import unittest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from backend.main import app
from backend.schemas import AnalyzeResponse


class RiskStatesTests(unittest.TestCase):
    def test_openapi_exposes_exactly_four_risk_states(self):
        schema=TestClient(app).get('/openapi.json').json()
        values=schema['components']['schemas']['AnalyzeResponse']['properties']['risk_status']['enum']
        self.assertEqual(values,['clear','need_context','suspicious','high'])

    def test_removed_state_is_rejected_by_response_schema(self):
        with self.assertRaises(ValidationError) as error:
            AnalyzeResponse.model_validate({'risk_status':'verified_match'})
        self.assertTrue(any(e['loc']==('risk_status',) and e['type']=='literal_error'
                            for e in error.exception.errors()))
