"""Local analysis providers. External model execution has been removed."""
from .settings import get_setting, LocalConfigError
from .mock_rules import extract as extract_mock, MockLimitExceeded
from .schemas import Answer


def unknown():
    return Answer(status='unknown', text='Chưa đủ căn cứ.', evidence_refs=[])

class ProviderFailure(Exception):
    def __init__(self, code, status, diagnostic=None):
        self.code, self.status = code, status
        self.diagnostic = diagnostic


class MockProvider:
    """Deterministic integration stub; not a language model or quality baseline."""
    async def extract(self, request):
        try:
            return extract_mock(request)
        except MockLimitExceeded:
            raise ProviderFailure('MOCK_FINDING_LIMIT', 502) from None


def get_provider():
    try:
        mode = get_setting('SCAMSHIELD_MODE', 'local_rules')
    except LocalConfigError:
        raise ProviderFailure('PROVIDER_CONFIG_INVALID', 503) from None
    if mode == 'local_rules':
        from .local_reasoning.adapter import LocalRulesProvider
        return LocalRulesProvider()
    if mode == 'mock':
        return MockProvider()
    if mode in ('live', 'hybrid', 'two_pass'):
        raise ProviderFailure('EXTERNAL_MODEL_REMOVED', 503)
    raise ProviderFailure('PROVIDER_CONFIG_INVALID', 503)
