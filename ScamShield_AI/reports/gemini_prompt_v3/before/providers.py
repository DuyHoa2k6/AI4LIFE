import json
from pathlib import Path
import httpx
from .settings import get_setting, LocalConfigError
from .schemas import Answer, Extraction, HybridReview
from .mock_rules import extract as extract_mock, MockLimitExceeded


class ProviderFailure(Exception):
    def __init__(self, code, status):
        self.code, self.status = code, status


def unknown():
    return Answer(status='unknown', text='Chưa đủ căn cứ.', evidence_refs=[])


class MockProvider:
    """Deterministic integration stub; not a language model or quality baseline."""
    async def extract(self, request):
        try:
            return extract_mock(request)
        except MockLimitExceeded:
            raise ProviderFailure('MOCK_FINDING_LIMIT', 502) from None


class LiveProvider:
    """Configured chat-completions-compatible service; no dataset access."""
    async def extract(self, request):
        return await self.complete(request.model_dump(exclude_none=True), Extraction, 'extraction_prompt.txt')

    async def complete(self, payload, schema, prompt_name):
        try:
            url, model = get_setting('SCAMSHIELD_PROVIDER_URL'), get_setting('SCAMSHIELD_MODEL')
        except LocalConfigError:
            raise ProviderFailure('PROVIDER_CONFIG_INVALID', 503) from None
        if not url or not model:
            raise ProviderFailure('PROVIDER_NOT_CONFIGURED', 503)
        if not url.startswith('https://') and not url.startswith(('http://127.0.0.1:', 'http://localhost:')):
            raise ProviderFailure('PROVIDER_CONFIG_INVALID', 503)
        prompt = Path(__file__).with_name(prompt_name).read_text(encoding='utf-8')
        prompt += '\nSchema: ' + json.dumps(schema.model_json_schema(), ensure_ascii=False)
        headers = {}
        key = get_setting('SCAMSHIELD_API_KEY')
        if key:
            headers['Authorization'] = 'Bearer ' + key
        try:
            async with httpx.AsyncClient(timeout=float(get_setting('SCAMSHIELD_TIMEOUT', '20')), follow_redirects=False) as client:
                response = await client.post(url, headers=headers, json={
                    'model': model, 'messages': [{'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}],
                    'response_format': {'type': 'json_object'}})
            if response.status_code != 200:
                raise ProviderFailure('PROVIDER_UNAVAILABLE', 503 if response.status_code in (429, 503) else 502)
            content = response.json()['choices'][0]['message']['content']
            return schema.model_validate_json(content)
        except httpx.TimeoutException:
            raise ProviderFailure('PROVIDER_TIMEOUT', 504) from None
        except httpx.RequestError:
            raise ProviderFailure('PROVIDER_UNAVAILABLE', 503) from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderFailure('PROVIDER_INVALID_OUTPUT', 502) from None


class HybridProvider:
    """Rules propose hypotheses; one live call reviews the complete original input."""
    def __init__(self, live=None):
        self.live = live if live is not None else LiveProvider()

    async def extract(self, request):
        from .engine import verify
        from .hybrid import HybridBundle
        from .mock_rules import VERSION, assess
        limited = False
        try:
            preliminary = extract_mock(request)
            preliminary.findings = verify(preliminary, request.as_messages())
        except MockLimitExceeded:
            preliminary = None
            limited = True
        status = assess(preliminary.findings, request.as_messages())[0] if preliminary is not None else None
        # Bounded hints: original input remains complete; hints are not independent sources.
        hints = []
        for f in (preliminary.findings if preliminary is not None else [])[:12]:
            evidence = []
            for e in f.evidence:
                quote = e.quote[:512]
                evidence.append({'message_id': e.message_id, 'quote': quote,
                                 'start': e.start, 'end': e.start + len(quote),
                                 'abbreviated': len(quote) != len(e.quote)})
            hints.append({'id': f.id, 'action': f.action, 'speech_role': f.speech_role,
                          'speaker': f.speaker, 'evidence': evidence})
        payload = {'input': request.model_dump(exclude_none=True), 'preliminary': {
            'rules_version': VERSION, 'status': 'limited' if limited else 'completed',
            'risk_hypothesis': status, 'findings': hints,
            'omitted_findings': max(0, len(preliminary.findings) - len(hints)) if preliminary is not None else 0}}
        reviewed = await self.live.complete(payload, HybridReview, 'hybrid_prompt.txt')
        return HybridBundle(preliminary=preliminary, reviewed=reviewed,
                            preliminary_risk=status, limited=limited)


def get_provider():
    try:
        mode = get_setting('SCAMSHIELD_MODE', 'mock')
    except LocalConfigError:
        raise ProviderFailure('PROVIDER_CONFIG_INVALID', 503) from None
    if mode == 'mock':
        return MockProvider()
    if mode == 'live':
        return LiveProvider()
    if mode == 'hybrid':
        return HybridProvider()
    raise ProviderFailure('PROVIDER_CONFIG_INVALID', 503)
