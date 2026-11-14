import argparse,json
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher
from ml.phobert.schema import ATTRS
from .io import load,dump,digest
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    known=[];sources=[]
    for split in ['train','validation']:
        path=ROOT.parent/'data/phobert/splits'/f'{split}.jsonl';sources.append({'path':str(path),'sha256':digest(path)})
        for line in path.read_text(encoding='utf-8').splitlines():
            x=json.loads(line);known.append((x['id'],' '.join(m['text'] for m in x['messages'])))
    prior=ROOT/'reports/eight_scenarios_20261113/inputs.json';sources.append({'path':str(prior),'sha256':digest(prior)})
    for x in json.loads(prior.read_text(encoding='utf-8')):known.append(('prior-user-'+x['id'],x['text']))
    rows=load(args.cases);matches=[]
    for r in rows:
        text=' '.join(m.text for m in r.input.messages)
        similarity,reference=max((SequenceMatcher(None,text.casefold(),old.casefold()).ratio(),identifier) for identifier,old in known)
        matches.append({'case_id':r.case_id,'declared_novelty':r.novelty,'nearest_known':reference,'lexical_similarity':similarity,'semantic_novelty':'not_proven_by_lexical_distance'})
    required=['negation','conditional_negation','quoted_warning','multiple_speakers','multiple_transactions','ambiguous_reference','self_claim','state_update','contradictory_user_update','irrelevant_interleaving','prompt_injection_as_data']
    dump(args.out,{'known_sources':sources,'seen_input_count':len(known),'no_holdout_opened':True,'case_novelty':matches,
      'new_untrained_action_types':dict(Counter(e.attributes['action_type'] for r in rows for e in r.expected.events if e.attributes['action_type'] not in ATTRS['action_type'])),
      'coverage_gaps_by_domain':{d:sorted(set(required)-{p for r in rows if r.domain==d for p in r.phenomena}) for d in sorted({r.domain for r in rows})},
      'formal_reviewed':0,'blind_holdout':'not supplied; implementer has seen these drafts'})

if __name__=='__main__':main()
