"""Read private backend constants without importing/compiling the secret file."""
import ast
from functools import lru_cache
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).with_name('local_settings.py')
ALLOWED = {'SCAMSHIELD_PHOBERT_CHECKPOINT','SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL','SCAMSHIELD_MODE', 'SCAMSHIELD_REASONER', 'SCAMSHIELD_CONTEXT_ENABLED', 'SCAMSHIELD_MODEL', 'SCAMSHIELD_PROVIDER_URL',
           'SCAMSHIELD_API_KEY', 'SCAMSHIELD_TIMEOUT', 'SCAMSHIELD_ALLOWED_ORIGINS',
           'SCAMSHIELD_RAG_ENABLED', 'SCAMSHIELD_SCENARIO_ENABLED', 'SCAMSHIELD_RETRIEVAL_TIMEOUT',
           'SCAMSHIELD_TOTAL_TIMEOUT', 'SCAMSHIELD_OUTPUT_FORMAT', 'SCAMSHIELD_RETRIES',
           'SCAMSHIELD_DISABLE_RESPONSE_TIMEOUTS','SCAMSHIELD_URL_NETWORK_ENABLED'}


class LocalConfigError(Exception):
    pass


@lru_cache(maxsize=1)
def _local_values():
    try:
        source = CONFIG_FILE.read_text(encoding='utf-8-sig')
    except FileNotFoundError:
        return {}
    try:
        tree = ast.parse(source)
        values = {}
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
            if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                raise ValueError()
            name = node.targets[0].id
            value = ast.literal_eval(node.value)
            if name not in ALLOWED or not isinstance(value, str):
                raise ValueError()
            values[name] = value
        return values
    except (SyntaxError, ValueError, TypeError):
        # Never include the source line or original parse exception in logs/responses.
        raise LocalConfigError('Invalid private backend configuration; use string constants only.') from None


def get_setting(name, default=None):
    if name in os.environ:
        return os.environ[name]
    return _local_values().get(name, default)


def response_timeouts_disabled():
    value = get_setting('SCAMSHIELD_DISABLE_RESPONSE_TIMEOUTS', '0')
    if value not in ('0', '1'):
        raise LocalConfigError('Response timeout switch must be 0 or 1.')
    return value == '1'
