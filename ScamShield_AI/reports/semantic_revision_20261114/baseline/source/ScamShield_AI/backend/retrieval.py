"""Bounded local retrieval. No dev/validation/holdout access, browsing or embeddings."""
import asyncio
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlsplit
from .schemas import RetrievalBranch

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / 'knowledge/scenarios.jsonl'
SOURCES = ROOT.parent / 'data/knowledge_sources.jsonl'
STOP = set('va la cua cho toi ban nay mot de trong voi cac da co khong duoc nguoi nhung khi thi'.split())


def tokens(text):
    text = unicodedata.normalize('NFD', text.lower().replace('đ', 'd'))
    return set(re.findall(r'[a-z0-9]+', ''.join(c for c in text if not unicodedata.combining(c)))) - STOP


def read_records(path):
    if path.stat().st_size > 2_000_000:
        raise ValueError('Index too large')
    records = []
    with path.open(encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip():
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError('Invalid index record')
                records.append(record)
                if len(records) > 500:
                    raise ValueError('Too many records')
    if len({r.get('id') for r in records}) != len(records):
        raise ValueError('Duplicate index ID')
    return records


def approved(record, today=None):
    """Approval is external metadata. Never promote candidate records automatically."""
    today = today or date.today()
    try:
        url = urlsplit(record['source_url'])
        host = url.hostname or ''
        return (url.scheme == 'https' and host.endswith('.gov.vn') and not url.username
                and record['review_status'] == 'approved'
                and bool(record['reviewer'].strip()) and record.get('reuse_approved') is True
                and date.fromisoformat(record['approved_at']) <= today
                and date.fromisoformat(record['checked_at']) <= today
                and (not record.get('valid_until') or date.fromisoformat(record['valid_until']) >= today)
                and record.get('source_role') in ('background_only', 'behavior_support')
                and isinstance(record['text'], str) and 0 < len(record['text']) <= 4000)
    except (ValueError, TypeError, KeyError, AttributeError):
        return False


def search(kind, query, actions, path=None):
    path = path or (SCENARIOS if kind == 'scenarios' else SOURCES)
    records = read_records(path)
    if kind == 'official_sources':
        records = [r for r in records if approved(r)]
        if not records:
            return 'no_approved_sources', []
    q = tokens(query)
    counts = Counter(t for r in records for t in tokens(r.get('text', '')))
    scored = []
    for r in records:
        text = r.get('text', '')
        if not isinstance(text, str) or not 0 < len(text) <= 4000:
            continue
        overlap = q & tokens(text)
        tags = set(r.get('actions', [])) & set(actions)
        # Two lexical terms, or a grounded action plus one term. A hit is never a verdict.
        if len(overlap) < 2 and not (tags and overlap):
            continue
        score = sum(1 / counts[t] for t in overlap) + len(tags)
        item = {'id': r['id'], 'text': text[:1600], 'actions': r.get('actions', []),
                'score': round(score, 5), 'kind': 'synthetic_scenario' if kind == 'scenarios' else 'approved_official'}
        if kind == 'official_sources':
            item.update(url=r['source_url'], reviewed_at=r['approved_at'],
                        valid_until=r.get('valid_until'), source_role=r['source_role'])
        scored.append(item)
    scored.sort(key=lambda r: (-r['score'], r['id']))
    return ('matched' if scored else 'no_match'), scored[:3]


async def branch(kind, query, actions, enabled=True, timeout=.8, path=None):
    started = time.perf_counter()
    if not enabled:
        return RetrievalBranch(status='disabled', retrieved_count=0, elapsed_ms=0.), []
    try:
        status, records = await asyncio.wait_for(asyncio.to_thread(search, kind, query, actions, path), timeout)
    except asyncio.TimeoutError:
        status, records = 'timeout', []
    except (OSError, ValueError, TypeError, KeyError):
        status, records = 'error', []
    return RetrievalBranch(status=status, retrieved_count=len(records),
                           elapsed_ms=(time.perf_counter()-started)*1000), records
