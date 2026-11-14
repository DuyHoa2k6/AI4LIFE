"""Mock v2 development report. Only dev inputs are predicted; never evaluate holdout."""
import hashlib
import json
import platform
import time
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.mock_rules import VERSION, catalog
from backend.providers import MockProvider, get_provider

ROOT = Path(__file__).resolve().parent


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    report = ROOT/'reports/mock_v2'
    report.mkdir(parents=True, exist_ok=True)
    dev_path = ROOT.parent/'data/dev.jsonl'
    samples = [json.loads(line) for line in dev_path.read_text(encoding='utf-8').splitlines() if line]
    app.dependency_overrides[get_provider] = lambda: MockProvider()
    predictions = []
    try:
        with TestClient(app) as client:
            for sample in samples:
                started = time.perf_counter()
                r = client.post('/api/analyze', json=sample['input'])
                predictions.append({'id': sample['id'], 'status_code': r.status_code,
                    'response': r.json(), 'elapsed_ms': (time.perf_counter()-started)*1000})
    finally:
        app.dependency_overrides.clear()
    write(report/'dev_predictions.json', predictions)
    # Predictions are persisted before expected labels are accessed for scoring.
    previous = json.loads((ROOT/'reports/week1/dev_predictions.json').read_text(encoding='utf-8'))
    before = {s['id']: s['response'].get('risk_status') for s in previous}
    cases = []
    for sample, prediction in zip(samples, predictions):
        expected = sample['expected']['risk_status']
        actual = prediction['response'].get('risk_status')
        cases.append({'id': sample['id'], 'expected': expected, 'previous_mock': before.get(sample['id']),
                      'current_mock': actual, 'status_match': expected == actual})
    write(report/'summary.json', {'rules_version': VERSION, 'rule_count': len(catalog()),
        'scope': 'synthetic dev used in development; not independent evaluation',
        'n': len(samples), 'matched': sum(c['status_match'] for c in cases), 'cases': cases,
        'python': platform.python_version(), 'live': 'not measured', 'rag': 'not implemented',
        'validation_holdout': 'not used for rule tuning or prediction'})
    write(report/'rules.json', catalog())
    paths = [*[p for p in sorted((ROOT/'backend').glob('*.py')) if p.name != 'local_settings.py'], ROOT/'tests/test_mock_rules.py',
             ROOT/'tests/test_backend.py', ROOT/'tests/browser_week2.mjs', ROOT/'MOCK_RULES.md',
             ROOT/'mock_report.py', dev_path,
             *[ROOT.parent/name for name in ('01_Y_Tuong.md', '02_Cong_Cu.md', '03_Luong.md',
                                            '04_API.md', '05_Dataset.md', '06_Kiem_Thu.md', '07_Lo_Trinh.md',
                                            'prompts/01_Tuan_1.md')]]
    write(report/'hashes.json', {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    print(f'{VERSION}: dev {sum(c["status_match"] for c in cases)}/{len(samples)}, {len(catalog())} rules; not independent quality')


if __name__ == '__main__':
    main()
