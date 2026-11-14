"""Freeze public code/config/fixtures only. Never include local_settings or keys."""
import hashlib,json,platform
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports/grounding_v2_20261113/lock.json'
paths=list((ROOT/'backend/local_reasoning').glob('*.py'))+list((ROOT/'backend/local_observation').glob('*.py'))
paths += [ROOT/'backend/local_observation/rules.json']
paths += [ROOT.parent/'data/v2'/n for n in ('semantic_phrases.json','semantic_graph_patterns.json','rulebook.json','templates.json','context_rules.json','context_templates.json','extraction_rules.json')]
paths += [ROOT/'fixtures'/n for n in ('grounding_v2_inputs.json','grounding_v2_untuned_inputs.json')]
paths += [ROOT/'fixtures/local_observation/expected_grounding_overrides.json',ROOT/'score_grounding.py']
manifest={'version':'grounding-2.0','python':platform.python_version(),'platform':platform.platform(),
    'scope':'Public local parser code/config and authored synthetic fixtures. No private settings, keys, or independent holdout.',
    'hashes':{str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Frozen',len(paths),'public files; private settings excluded.')
