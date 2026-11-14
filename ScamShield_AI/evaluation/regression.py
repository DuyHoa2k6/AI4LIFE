import argparse
from pathlib import Path
from ml.phobert.data import load as load_training
from .schema import Case
from .io import jsonl
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'evaluation/data/regression_cases.jsonl');args=parser.parse_args();rows=[]
    # These are already-read train/validation only. Do not open test_locked/holdout.
    for split in ['train','validation']:
        for s in load_training(ROOT.parent/'data/phobert/splits'/f'{split}.jsonl'):
            metadata={p.id:p for p in s.participants}
            def pid(value):return 'unknown:m1:addressee' if metadata[value].kind=='unknown' else value
            domain='relationships' if s.family_id in ('loan_coercion','extortion') else 'employment' if s.family_id=='travel_custody' else 'data_access' if s.family_id in ('auth_warning','remote_access','send_credentials') else 'finance'
            tags=[]
            if s.risk_reference=='high':
                kinds={e.attributes['action_type'] for e in s.events}
                tags=['access_loss'] if 'disclose_credentials' in kinds else ['pay_to_withdraw'] if 'withdraw' in kinds else ['threat_to_compel'] if 'threaten_disclosure' in kinds else []
            e={'participants':[{**p.model_dump(),'id':pid(p.id)} for p in s.participants],
              'spans':[v.model_dump() for v in s.spans],
              'events':[{**v.model_dump(),'description':next(x.quote for x in s.spans if x.id==v.anchor_id),'information_status':'claimed','argument_refs':[]} for v in s.events],
              'event_arguments':[{**v.model_dump(),'participant_id':pid(v.participant_id)} for v in s.event_arguments],
              'relations':[{'id':'r'+str(i),'type':v.label,'source_id':v.source,'target_id':v.target,'scope_id':'t1','evidence_refs':v.evidence_refs} for i,v in enumerate(s.relations)],
              'cases':[{'id':k,'event_refs':v,'participant_refs':[pid(p.id) for p in s.participants]} for k,v in s.transactions.items()],
              'risk_status':s.risk_reference,'rationale':'Nhãn phát triển nháp đã biết; không phải gold độc lập.','decisive_event_refs':s.risk_basis,'mechanism_tags':tags,
              'missing_information':s.missing_information,'acceptable_question_targets':['payment_purpose'] if s.risk_reference=='need_context' and any(e.attributes['action_type']=='transfer' for e in s.events) else ['requested_step'] if s.risk_reference=='need_context' else [],
              'acceptable_questions':[],'contradictions':[],'forbidden_inferences':['Người gửi chắc chắn phạm tội.','Danh tính đã được xác minh.']}
            rows.append(Case.model_validate({'case_id':'R:'+s.id,'family_id':'regression:'+s.family_id,'template_id':'regression:'+s.template_group,'source_group':'regression:'+s.source_group,'split':'regression','domain':domain,
              'provenance':{'origin':'synthetic','source_ref':'../data/phobert/splits/'+split+'.jsonl'},'novelty':'seen_development','review_status':'draft',
              'input':{'messages':[m.model_dump() for m in s.messages]},'expected':e,
              'annotation_completeness':{'spans':'partial','events':'complete','roles':'complete','relations':'complete','risk':'complete','explanation':'partial','questions':'partial'},'phenomena':['seen_training_or_validation']}))
    jsonl(args.out,[r.model_dump() for r in rows]);print(f'{len(rows)} seen regression cases; no locked data opened')

if __name__=='__main__':main()
