"""Predict first, score draft abbreviation references second; no live models."""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch,AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_observation.text import normalize
from backend.local_observation.abbreviations import LEXICON,lexicon

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'fixtures/abbreviation_checks'


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    paths=[ROOT/'backend/local_observation'/name for name in ('abbreviations.py','text.py','analyzer.py','schema.py','segmentation.py','rules.json')]
    paths += [LEXICON,DATA/'inputs.json',DATA/'expected.json',Path(__file__).resolve()]
    rel=lambda p:str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../'+str(p.relative_to(ROOT.parent))
    hashes={rel(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    rows=json.loads((DATA/'inputs.json').read_text(encoding='utf-8'));records=[]
    with patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as provider, \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('Network forbidden')) as network,TestClient(app) as client:
        for row in rows:
            response=client.post('/api/observe',json=row['input'])
            records.append({**row,'http_status':response.status_code,'normalized_matching_view':normalize(row['input']['text']).text,
                            'response':response.json()})
        save(output/'predictions.json',records)
        calls={'provider_calls':provider.call_count,'network_calls':network.call_count}
    refs={r['id']:r for r in json.loads((DATA/'expected.json').read_text(encoding='utf-8'))['cases']}
    failed=[];exact=total=resolved=ambiguous=0
    lines=['# Phân giải viết tắt — 29 ca phát triển','','Chỉ kiểm tra /api/observe; chưa đo chất lượng cảnh báo cuối.','']
    for row in records:
        expected=refs[row['id']];d=row['response'];passed=row['http_status']==200
        if 'normalized' in expected:passed &= row['normalized_matching_view']==expected['normalized']
        if expected.get('event_type'):
            passed &= any(e['action_type']==expected['event_type'] and e['polarity']==expected['polarity'] for e in d['events'])
        elif 'event_type' in expected:passed &= not d['events']
        if expected.get('unresolved_required'):
            passed &= any(r['status']!='resolved' for r in d['abbreviation_resolutions']) and bool(d['follow_up_questions'])
        if not passed:failed.append(row['id'])
        text=row['input']['text']
        for e in d['evidence']:
            total+=1;exact+=text[e['start']:e['end']]==e['quote']
        for r in d['abbreviation_resolutions']:
            total+=1;exact+=text[r['start']:r['end']]==r['quote']
            resolved+=r['status']=='resolved';ambiguous+=r['status']!='resolved'
        lines += [f"## {row['id']}",'',text,'','Bản khớp luật: `'+row['normalized_matching_view']+'`','']
        for r in d['abbreviation_resolutions']:
            lines += [f"- {r['quote']} → {r['expansion'] or 'chưa chọn nghĩa'} ({r['status']}); "+', '.join(r['alternatives'])]
        lines += ['']+['- '+q for q in d['follow_up_questions']]+['']
    config=json.loads(LEXICON.read_text(encoding='utf-8'))
    summary={'scope':'29 known synthetic development cases, draft references; not independent accuracy or final risk evaluation.',
             'lexicon_version':lexicon()[0],'entries':len(config['entries']),
             'distinct_aliases':len({a.casefold() for e in config['entries'] for a in e['aliases']}),
             'cases':len(rows),'matched':len(rows)-len(failed),'failed':failed,
             'resolved_occurrences':resolved,'abstained_occurrences':ambiguous,
             'original_offset_checks':total,'exact_offsets':exact,**calls,'hashes':hashes}
    save(output/'summary.json',summary)
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[rel(p)] for p in paths)
    print(json.dumps({k:v for k,v in summary.items() if k!='hashes'}))
    if failed or exact!=total or any(calls.values()):raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'reports/abbreviations_20261112')
    run(parser.parse_args().output)
