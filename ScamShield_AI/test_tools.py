import argparse
import uuid
import unittest
from pathlib import Path
import tools


class EvaluationIntegrityTests(unittest.TestCase):
    def test_prediction_ignores_expected_and_unicode_quotes_survive(self):
        root = tools.ROOT / 'results'
        prefix = uuid.uuid4().hex
        dataset, lock, output, other = [root / (prefix + suffix) for suffix in
                                        ['data.jsonl', 'lock.json', 'pred.jsonl', 'other.jsonl']]
        try:
            sample = {'id': 't1', 'input': {'messages': [
                {'id': 'm1', 'text': '😀 Đừng gửi OTP cho ai.'}]},
                'expected': 'intentionally not a valid reference schema'}
            dataset.write_text(__import__('json').dumps(sample), encoding='utf-8')
            args = argparse.Namespace(config=str(tools.ROOT/'config.json'), dataset=dataset,
                                      lock=lock, output=output)
            tools.freeze(args)
            tools.predict(args)
            evidence = tools.rows(output)[0]['prediction']['evidence'][0]
            self.assertEqual(evidence['end'], len(sample['input']['messages'][0]['text']))
            with self.assertRaises(FileExistsError):
                tools.predict(args)
            dataset.write_text('{}', encoding='utf-8')
            args.output = other
            with self.assertRaises(ValueError):
                tools.predict(args)
        finally:
            for path in [dataset, lock, output, other]:
                path.unlink(missing_ok=True)

    def test_undefined_metrics_and_nearest_rank_percentile(self):
        self.assertIsNone(tools.ratio(0, 0))
        self.assertEqual(tools.quantile(list(range(1, 101)), .95), 95)


if __name__ == '__main__':
    unittest.main()
