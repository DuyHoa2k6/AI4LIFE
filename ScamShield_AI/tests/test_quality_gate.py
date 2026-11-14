import unittest
from quality_gate import score, wilson_lower


class QualityGateTests(unittest.TestCase):
    def case(self,key,group='scam',allowed=None):
        return {'id':key,'group':group,'acceptable':allowed or ['high']}

    def prediction(self,key,status='high',http=200):
        return {'id':key,'executed':True,'http_status':http,'response':{'risk_status':status},
                'evidence_check':{'quote_count':1,'exact_quotes':1,'speaker_reference_errors':0}}

    def test_all_correct_small_sample_cannot_claim_98(self):
        result=score([self.prediction('a')],{'cases':[self.case('a')]})
        self.assertEqual(result['overall_rate'],1.)
        self.assertFalse(result['passed'])
        self.assertFalse(result['checks']['minimum_samples'])

    def test_error_and_missing_cases_count_against_overall_and_recall(self):
        result=score([self.prediction('a',http=504)],{'cases':[self.case('a'),self.case('b')]})
        self.assertEqual(result['errors_or_not_run'],2)
        self.assertEqual(result['high']['FN_including_errors'],2)
        self.assertEqual(result['overall_rate'],0.)

    def test_fabricated_evidence_cannot_pass_as_correct_warning(self):
        p=self.prediction('a');p['evidence_check']['exact_quotes']=0
        result=score([p],{'cases':[self.case('a')]})
        self.assertEqual(result['correct_status_and_exact_evidence'],0)
        self.assertEqual(result['high']['FN_including_errors'],1)

    def test_duplicate_predictions_rejected_not_inflated(self):
        with self.assertRaises(ValueError):score([self.prediction('a')]*2,{'cases':[self.case('a')]})

    def test_wilson_requires_evidence_not_only_observed_rate(self):
        self.assertLess(wilson_lower(100,100),.98)
        self.assertGreater(wilson_lower(500,500),.98)
