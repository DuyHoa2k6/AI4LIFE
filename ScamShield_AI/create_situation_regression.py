"""Acceptance references from the user's table; never sent to the provider."""
import json
from pathlib import Path
from run_user_ten_cases import CASES

root=Path(__file__).resolve().parent/'fixtures/situation_regression_20261110'
root.mkdir(parents=True,exist_ok=False)
targets=['suspicious','clear','need_context','high','suspicious','clear','high','need_context','suspicious','high']
(root/'inputs.json').write_text(json.dumps(CASES,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'expected.json').write_text(json.dumps({'scope':'User-supplied ten-case acceptance table, known regression after implementation. Not independent or proof of 98% accuracy.',
 'cases':[{'id':r['id'],'group':t,'acceptable':[t],'questions_required':t=='need_context','manual_focus':r['name']} for r,t in zip(CASES,targets)]},ensure_ascii=False,indent=2),encoding='utf-8')
print('Wrote 10 acceptance inputs and separate references.')
