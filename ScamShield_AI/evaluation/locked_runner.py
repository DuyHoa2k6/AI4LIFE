"""Custodian workflow. Prediction phase never receives or opens reference labels."""
import argparse,json,copy
from pathlib import Path
from datetime import datetime,timezone
from ml.phobert.schema import Message
from ml.phobert.inference import Runtime
from .io import digest,dump,jsonl,load
from .metrics import diagnose,aggregate

def predict(args):
    if (args.out/'seal.json').exists():raise ValueError('sealed run already exists')
    entries=[json.loads(x) for x in args.inputs.read_text(encoding='utf-8').splitlines() if x.strip()]
    if not entries:raise ValueError('locked input file is empty')
    if len({x.get('case_id') for x in entries})!=len(entries):raise ValueError('duplicate IDs')
    for row in entries:
        if set(row)!={'case_id','input'} or set(row['input'])!={'messages'}:raise ValueError('Locked prediction accepts IDs/messages only; no expected/family/risk fields')
        row['input']['messages']=[Message.model_validate(m).model_dump() for m in row['input']['messages']]
    runtime=Runtime(args.checkpoint,allow_experimental=args.allow_experimental)
    args.out.mkdir(parents=True,exist_ok=True)
    results=[]
    for row in entries:
        try:r=runtime.predict(row['input'],include_debug=True)
        except Exception as exc:r={'analysis_status':'error','assessment':{'risk_status':None},'graph':{'spans':[],'events':[],'relations':[]},'error_type':type(exc).__name__}
        results.append({'case_id':row['case_id'],'prediction':r})
        jsonl(args.out/'predictions.jsonl',results)
    dump(args.out/'seal.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'inputs_sha256':digest(args.inputs),'predictions_sha256':digest(args.out/'predictions.jsonl'),
      'checkpoint_sha256':digest(args.checkpoint/'heads.pt'),'model_manifest_sha256':digest(args.checkpoint/'manifest.json'),'labels_opened':False,'n':len(results),
      'independence':'not established; custodian attestation required at scoring'})

def score(args):
    if not args.allow_private_labels:raise ValueError('Scoring needs explicit --allow-private-labels; run on the independent reviewer machine')
    if (args.out/'consumed.json').exists():raise ValueError('Locked run already consumed; do not reuse it after improvements')
    seal=json.loads((args.out/'seal.json').read_text());predpath=args.out/'predictions.jsonl'
    if seal['predictions_sha256']!=digest(predpath):raise ValueError('Predictions changed after sealing')
    attestation=json.loads(args.attestation.read_text())
    if not attestation.get('custodian_reference') or not attestation.get('not_seen_by_implementer') or not attestation.get('labels_independently_reviewed'):raise ValueError('Missing independent-custodian attestation')
    rows=load(args.private_labels)
    if any(r.split!='locked' or r.review_status=='draft' or len(set(r.reviewer_reference))<2 for r in rows):raise ValueError('Independent final labels must be reviewed and locked')
    predictions={x['case_id']:x['prediction'] for x in [json.loads(line) for line in predpath.read_text(encoding='utf-8').splitlines()]}
    if set(predictions)!={r.case_id for r in rows}:raise ValueError('Locked input/reference ID mismatch')
    if args.seen_manifest:
        seen=json.loads(args.seen_manifest.read_text());seen_families={f for values in seen['split_families'].values() for f in values}
        if seen_families&{r.family_id for r in rows}:raise ValueError('Known family cannot be independent holdout')
    metrics=aggregate([diagnose(r,predictions[r.case_id]) for r in rows]);dump(args.out/'metrics.json',metrics)
    dump(args.out/'consumed.json',{'private_labels_sha256':digest(args.private_labels),'attestation':attestation,'warning':'If used to improve, reclassify these families as development and obtain a new independent set.'})

def main():
    parser=argparse.ArgumentParser();subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('predict');p.add_argument('--inputs',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--allow-experimental',action='store_true')
    p=subs.add_parser('score');p.add_argument('--out',type=Path,required=True);p.add_argument('--private-labels',type=Path,required=True);p.add_argument('--attestation',type=Path,required=True);p.add_argument('--seen-manifest',type=Path);p.add_argument('--allow-private-labels',action='store_true')
    args=parser.parse_args()
    try:predict(args) if args.command=='predict' else score(args)
    except (ValueError,OSError,RuntimeError) as exc:print(json.dumps({'error':str(exc)},ensure_ascii=False));raise SystemExit(2)

if __name__=='__main__':main()
