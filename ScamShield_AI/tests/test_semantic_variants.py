import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from backend.local_reasoning.schema import CaseInput
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.validation import annotation_errors
from backend.local_reasoning.semantic_phrases import load

DATA=Path(__file__).resolve().parents[2]/'data/v2/semantic_variants'


class SemanticVariantTests(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ,{'SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1'})
        env.start();self.addCleanup(env.stop)

    def analyze(self,text):
        q=CaseInput(messages=[{'id':'m1','scope_id':'case','text':text}])
        r=analyze_local(q);self.assertEqual(annotation_errors(q,r.annotations),[])
        self.assertEqual(r.analysis_status,'complete')
        return r

    def test_versioned_dataset_and_exact_annotations(self):
        manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
        rows=[json.loads(s) for s in (DATA/'inputs.jsonl').read_text(encoding='utf-8').splitlines()]
        expected=[json.loads(s) for s in (DATA/'expected.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(rows),24);self.assertFalse(manifest['independent'])
        self.assertEqual({r['id'] for r in rows},{r['id'] for r in expected})
        by_id={r['id']:r for r in rows}
        for row in expected:
            text=by_id[row['id']]['input']['text']
            for e in row['evidence']:self.assertEqual(text[e['start']:e['end']],e['quote'])
            self.assertEqual(set(by_id[row['id']]['input']),{'text'})
        for name,digest in manifest['hashes'].items():self.assertEqual(hashlib.sha256((DATA/name).read_bytes()).hexdigest(),digest)

    def test_all_curated_development_variants(self):
        expected={r['id']:r for r in map(json.loads,(DATA/'expected.jsonl').read_text(encoding='utf-8').splitlines())}
        for row in map(json.loads,(DATA/'inputs.jsonl').read_text(encoding='utf-8').splitlines()):
            with self.subTest(case=row['id']):
                result=self.analyze(row['input']['text'])
                self.assertEqual(result.assessment.risk_status,expected[row['id']]['risk_status'])

    def test_phrase_config_does_not_contain_case_labels(self):
        config=load();self.assertEqual(config['version'],'semantic-phrases-1.0')
        self.assertNotIn('risk_status',json.dumps(config))

    def test_optional_purchase_does_not_cancel_other_required_payment(self):
        r=self.analyze('Bạn mua gói xác thực tùy chọn nhưng bạn nộp thêm phí trước thì mới nhận lại vốn.')
        self.assertEqual(r.assessment.risk_status,'high')

    def test_return_money_to_another_party_is_not_user_withdrawal(self):
        r=self.analyze('Bạn nộp tiền trước để trả lại vốn cho công ty.')
        self.assertNotIn('R-PAY-TO-WITHDRAW',r.assessment.applicable_rule_ids)


if __name__=='__main__':unittest.main()
