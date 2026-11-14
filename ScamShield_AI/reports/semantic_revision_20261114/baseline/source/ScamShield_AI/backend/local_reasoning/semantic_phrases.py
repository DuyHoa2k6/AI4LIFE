"""Small versioned lexical patterns, not embeddings, training or dataset lookup."""
import json
from pathlib import Path
import re
from functools import lru_cache

PATH = Path(__file__).resolve().parents[3] / 'data/v2/semantic_phrases.json'


@lru_cache(maxsize=1)
def load():
    data = json.loads(PATH.read_text(encoding='utf-8'))
    required = {'payment_request','return_benefit','asset_handover','payment_unconfirmed','optional_purchase'}
    if not required <= data['groups'].keys():raise ValueError('Incomplete semantic phrase groups')
    return data


def pattern(group):
    parts=load()['groups'][group]['patterns']
    if not parts or any(len(p)>1000 for p in parts):raise ValueError('Invalid semantic phrase budget')
    return re.compile('|'.join('(?:'+p+')' for p in parts))
