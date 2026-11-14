"""Offline W3 tools. No third-party dependencies; never send labels to inference."""
import argparse
import csv
import hashlib
import json
import math
import platform
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LABELS = ['clear', 'need_context', 'suspicious', 'high', 'verified_match', 'error']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def rows(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def baseline(payload, config):
    messages = payload.get('messages', [{'id': 'm1', 'text': payload.get('text', '')}])
    hits = []
    for msg in messages:
        # Whole original message avoids lowercasing offsets changing Unicode positions.
        if any(word in msg['text'].lower() for word in config['keywords']):
            hits.append({'message_id': msg['id'], 'quote': msg['text'],
                         'start': 0, 'end': len(msg['text']), 'speech_role': 'unknown'})
    return {'risk_status': config['matched_status'] if hits else config['unmatched_status'],
            'evidence': hits, 'follow_up_questions': [], 'source_matches': []}


def freeze(args):
    config = read(args.config)
    manifest = {'config': config, 'config_sha256': digest(args.config),
                'tool_sha256': digest(__file__), 'dataset_sha256': digest(args.dataset),
                'dataset_name': Path(args.dataset).name,
                'scope': 'synthetic validation; not independent final evaluation',
                'index_sha256': None, 'model': config['model'], 'prompt': config['prompt']}
    with Path(args.lock).open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)


def predict(args):
    lock = read(args.lock)
    if digest(args.dataset) != lock['dataset_sha256'] or digest(__file__) != lock['tool_sha256']:
        raise ValueError('Dataset/tool differs from frozen version')
    # Input export is a separate phase; expected is neither accessed nor sent here.
    samples = rows(args.dataset)
    ids = [r['id'] for r in samples]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate IDs')
    with Path(args.output).open('x', encoding='utf-8') as stream:
        for sample in samples:
            started = time.perf_counter()
            result = baseline(sample['input'], lock['config'])
            record = {'id': sample['id'], 'prediction': result,
                      'latency_ms': (time.perf_counter() - started) * 1000,
                      'lock_sha256': digest(args.lock)}
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')
            stream.flush()


def ratio(a, b):
    return a / b if b else None


def score(args):
    lock = read(args.lock)
    if digest(args.dataset) != lock['dataset_sha256']:
        raise ValueError('Dataset differs from lock')
    # Load persisted predictions fully BEFORE opening reference labels.
    predictions = rows(args.predictions)
    if any(p['lock_sha256'] != digest(args.lock) for p in predictions):
        raise ValueError('Prediction lock mismatch')
    samples = rows(args.dataset)
    by_id = {p['id']: p for p in predictions}
    if len(by_id) != len(predictions) or set(by_id) != {s['id'] for s in samples}:
        raise ValueError('Missing, extra or duplicate prediction IDs')
    matrix = {label: {p: 0 for p in LABELS} for label in LABELS}
    missed, false_alerts, cases = [], [], []
    exact = evidence_total = expected_total = recovered = 0
    groups = {}
    for sample in samples:
        record = by_id[sample['id']]
        pred = record['prediction']
        expected = sample['expected']
        actual, wanted = pred['risk_status'], expected['risk_status']
        matrix[wanted][actual] += 1
        if wanted == 'high' and actual != 'high':
            missed.append(sample['id'])
        if actual == 'high' and wanted != 'high':
            false_alerts.append(sample['id'])
        msgs = {m['id']: m['text'] for m in sample['input']['messages']}
        evidence = pred['evidence']
        for ev in evidence:
            evidence_total += 1
            text = msgs.get(ev['message_id'], '')
            exact += bool(ev['quote'] and text[ev['start']:ev['end']] == ev['quote'])
        for finding in expected['findings']:
            expected_total += 1
            recovered += any(ev['message_id'] == finding['message_id'] and
                             finding['quote'] in ev['quote'] for ev in evidence)
        family = groups.setdefault(sample['family_id'], {'n': 0, 'errors': 0})
        family['n'] += 1
        family['errors'] += actual != wanted
        cases.append({'id': sample['id'], 'family_id': sample['family_id'],
                      'expected': wanted, 'predicted': actual, 'passed': actual == wanted,
                      'latency_ms': record['latency_ms'],
                      'speaker_role_review': 'pending', 'question_review': 'pending'})
    tp = matrix['high']['high']
    fp, fn = len(false_alerts), len(missed)
    report = {'n': len(samples), 'scope': lock['scope'], 'mode': 'keyword baseline offline',
              'confusion_matrix_rows_expected': matrix, 'high': {'tp': tp, 'fp': fp, 'fn': fn,
              'tn': len(samples) - tp - fp - fn, 'precision': ratio(tp, tp + fp),
              'recall': ratio(tp, tp + fn)}, 'missed_high': missed, 'false_high': false_alerts,
              'evidence': {'verbatim_correct': exact, 'emitted': evidence_total,
              'verbatim_rate': ratio(exact, evidence_total), 'expected_quotes_covered': recovered,
              'expected_quotes': expected_total, 'quote_coverage': ratio(recovered, expected_total),
              'semantic_action_speaker_context': 'not measured; manual review required'},
              'families': groups, 'live': 'not measured', 'rag': 'not implemented',
              'questions': 'baseline emits none; usefulness not measured',
              'source_support_and_verified_match': 'not applicable; no index',
              'predictions_sha256': digest(args.predictions), 'lock_sha256': digest(args.lock)}
    write(args.output, report)
    with Path(args.cases).open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cases[0]))
        writer.writeheader()
        writer.writerows(cases)


def quantile(values, q):
    return sorted(values)[max(0, math.ceil(len(values) * q) - 1)]


def bench(args):
    config = read(args.config)
    payload = {'text': 'Ví dụ tổng hợp: vui lòng gửi OTP để nhận quà.'}
    measurements = []
    for i in range(101):
        start = time.perf_counter()
        baseline(payload, config)
        measurements.append((time.perf_counter() - start) * 1000)
    write(args.output, {'mode': 'keyword baseline offline; NOT API/mock/live',
          'python': platform.python_version(), 'platform': platform.platform(),
          'concurrency': 1, 'input_characters': len(payload['text']), 'network': 'none',
          'first_call_ms': measurements[0], 'cold_process': 'not measured',
          'warm_n': 100, 'warm_p50_ms': quantile(measurements[1:], .5),
          'warm_p95_ms': quantile(measurements[1:], .95), 'errors': 0,
          'raw_ms': measurements, 'config_sha256': digest(args.config),
          'web_extension_api_provider_queue_retrieval': 'not measured; implementations absent',
          'duplicate_requests_deferred_items': 'not measured; no requests'})


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['freeze', 'predict', 'score', 'bench']:
        p = sub.add_parser(name)
        p.add_argument('--config', default=str(ROOT / 'config.json'))
        p.add_argument('--dataset', default=str(ROOT.parent / 'data/validation.jsonl'))
        p.add_argument('--lock', default=str(ROOT / 'results/lock.json'))
        p.add_argument('--output', required=name != 'freeze')
        if name == 'score':
            p.add_argument('--predictions', required=True)
            p.add_argument('--cases', required=True)
    args = parser.parse_args()
    globals()[args.command](args)


if __name__ == '__main__':
    main()
