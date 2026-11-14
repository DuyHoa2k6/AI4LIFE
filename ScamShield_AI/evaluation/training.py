"""Human-reviewed gate, replay and warm-start configuration; no self-training."""
import argparse,json,subprocess,sys
from pathlib import Path
from collections import Counter
from ml.phobert.schema import Sample,ATTRS,SPAN_LABELS
from ml.phobert.data import load as load_samples
from .io import load,dump,jsonl,digest,validate_splits
ROOT=Path(__file__).resolve().parents[1]

def prepare(cases,replay,validation,checkpoint,out,replay_ratio=.5):
    reviewed=[r for r in cases if r.review_status in ('human_verified','adjudicated') and len(set(r.reviewer_reference))>=2 and not r.annotation_ambiguity]
    result={'supplied':len(cases),'reviewed_new':len(reviewed),'replay_ratio':replay_ratio,'checkpoint':str(checkpoint),'status':'blocked','weights_changed':False}
    out.mkdir(parents=True,exist_ok=True)
    if not reviewed:result['reason']='No independently reviewed, unambiguous new examples. Draft/predicted labels are not eligible.';dump(out/'training_gate.json',result);return result
    frozen_families=sorted({r.family_id for r in reviewed if r.split in ('validation','locked')})
    if frozen_families:
        result['reason']='Validation/locked families require an explicit versioned promotion to development/train and replacement validation before training.'
        result['family_promotion_required']=frozen_families;dump(out/'training_gate.json',result);return result
    if not replay or not validation:result['reason']='Reviewed replay and reviewed validation files are required.';dump(out/'training_gate.json',result);return result
    old=load_samples(replay,supervised=True);val=load_samples(validation,supervised=True)
    if not 0<replay_ratio<1:raise ValueError('replay ratio must be between 0 and 1')
    converted=[];unknown=[]
    for row in reviewed:
        for e in row.expected.events:
            unknown += [(k,v) for k,v in e.attributes.items() if v is not None and v not in ATTRS[k]]
        if unknown:continue
        e=row.expected
        converted.append(Sample.model_validate({'id':row.case_id,'family_id':row.family_id,'conversation_group':row.family_id,'template_group':row.template_id,
          'source_group':row.source_group,'source':'consented_real' if row.provenance['origin']=='consented_real' else 'synthetic','review_status':'adjudicated' if row.review_status=='adjudicated' else 'independently_reviewed','reviewers':row.reviewer_reference,
          'messages':[m.model_dump() for m in row.input.messages],'participants':[p.model_dump() for p in e.participants],
          'spans':[s.model_dump() for s in e.spans],'span_label_status':{k:'complete' if row.annotation_completeness['spans']=='complete' else 'partial' if any(s.label==k for s in e.spans) else 'unannotated' for k in SPAN_LABELS},
          'events':[{'id':v.id,'anchor_id':v.anchor_id,'attributes':v.attributes,'transaction_id':v.transaction_id} for v in e.events],
          'event_arguments':[a.model_dump() for a in e.event_arguments],
          'relations':[{'source':r.source_id,'target':r.target_id,'label':r.type,'evidence_refs':r.evidence_refs} for r in e.relations],
          'transactions':{s.id:s.event_refs for s in e.cases},'risk_reference':e.risk_status,'risk_basis':e.decisive_event_refs,'missing_information':e.missing_information,
          'task_status':{'spans':row.annotation_completeness['spans'],'attributes':row.annotation_completeness['events'],'roles':row.annotation_completeness['roles'],'relations':row.annotation_completeness['relations'],'risk':row.annotation_completeness['risk']}}))
    if unknown:result['reason']='New semantic labels require explicit versioned head/mapping migration; old checkpoint will not be loaded against a resized mapping.';result['untrained_labels']=sorted(set(unknown));dump(out/'training_gate.json',result);return result
    minimum=int(__import__('math').ceil(len(converted)*replay_ratio/(1-replay_ratio)))
    if len(old)<minimum:result['reason']='Insufficient distinct reviewed replay examples; do not duplicate rows to meet ratio.';dump(out/'training_gate.json',result);return result
    train=converted+old
    for key in ['family_id','conversation_group','template_group','source_group']:
        if {getattr(x,key) for x in train}&{getattr(x,key) for x in val}:raise ValueError('Training/validation family leakage')
    jsonl(out/'reviewed_error_samples.jsonl',[s.model_dump() for s in converted]);jsonl(out/'mixed_train.jsonl',[s.model_dump() for s in train]);jsonl(out/'validation.jsonl',[s.model_dump() for s in val])
    manifest=json.loads((checkpoint/'manifest.json').read_text(encoding='utf-8'))
    config={**manifest['config'],'checkpoint':str(checkpoint/manifest['encoder_directory']) if manifest.get('encoder_directory') else manifest['base_checkpoint'],
      'warm_start':str(checkpoint),'train':str((out/'mixed_train.jsonl').resolve()),'validation':str((out/'validation.jsonl').resolve()),
      'output':str((out/'candidate_checkpoint').resolve()),'freeze_encoder':False,'learning_rate':2e-5,'encoder_learning_rate':2e-5,
      'epochs':3,'early_stopping':2,'batch_size':1,'gradient_accumulation':2,'device':'cpu','allow_draft_smoke':False,'replay_ratio':len(old)/len(train)}
    config.pop('overfit_smoke',None);config.pop('train_sample_limit',None)
    dump(out/'training_config.json',config);result.update(status='ready_for_explicit_training',reason=None,config=str(out/'training_config.json'),train_n=len(train),validation_n=len(val),parent_heads_sha256=digest(checkpoint/'heads.pt'))
    dump(out/'training_gate.json',result);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',type=Path,required=True);p.add_argument('--replay',type=Path);p.add_argument('--validation',type=Path);p.add_argument('--checkpoint',type=Path,default=ROOT/'artifacts/phobert/smoke_heads');p.add_argument('--out',type=Path,required=True);p.add_argument('--run',action='store_true');args=p.parse_args()
    result=prepare(load(args.cases),args.replay,args.validation,args.checkpoint,args.out);print(json.dumps(result,ensure_ascii=False))
    if result['status']=='blocked':raise SystemExit(3)
    if args.run:subprocess.run([sys.executable,'-m','ml.phobert.train','--config',result['config']],cwd=ROOT,check=True)

if __name__=='__main__':main()
