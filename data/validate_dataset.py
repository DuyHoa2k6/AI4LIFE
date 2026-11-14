"""Dataset audit only: never export holdout text or labels to the development report."""
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path


def audit():
    root = Path(__file__).resolve().parent
    result, errors, families, texts, ids = {}, [], {}, {}, set()
    for split in ('dev', 'validation', 'holdout'):
        path = root / (split + '.jsonl')
        samples = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
        counts = Counter()
        split_families = set()
        for sample in samples:
            sid = sample['id']
            if sid in ids or sample['split'] != split:
                errors.append(f'{split}: duplicate ID or incorrect split')
            ids.add(sid)
            family = sample['family_id']
            split_families.add(family)
            if family in families and families[family] != split:
                errors.append(f'{split}: family overlap')
            families[family] = split
            messages = sample['input']['messages']
            by_id = {m['id']: m for m in messages}
            if not messages or len(by_id) != len(messages):
                errors.append(f'{split}: missing messages or duplicate message ID')
            for m in messages:
                if not all(isinstance(m.get(k), str) and m[k].strip() for k in ('id', 'speaker', 'text')):
                    errors.append(f'{split}: malformed message')
            normalized = ' '.join(unicodedata.normalize('NFC', '\n'.join(m['text'] for m in messages)).casefold().split())
            if normalized in texts:
                errors.append(f'{split}: normalized duplicate')
            texts[normalized] = split
            expected = sample['expected']
            if expected['risk_status'] not in ('clear', 'need_context', 'suspicious', 'high', 'verified_match'):
                errors.append(f'{split}: invalid risk label')
            for f in expected['findings']:
                if f['message_id'] not in by_id or not f['quote'] or f['quote'] not in by_id[f['message_id']]['text']:
                    errors.append(f'{split}: invalid quote')
            counts[expected['risk_status']] += 1
        result[split] = {'n': len(samples), 'families': len(split_families),
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        # Do not expose holdout label distribution while tuning.
        if split != 'holdout':
            result[split]['labels'] = dict(counts)
    return {'datasets': result, 'total': len(ids), 'family_count': len(families),
            'errors': errors, 'passed': not errors,
            'note': 'synthetic seed; semantic duplicates and two-reviewer labeling not assessed'}


if __name__ == '__main__':
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(not report['passed'])
