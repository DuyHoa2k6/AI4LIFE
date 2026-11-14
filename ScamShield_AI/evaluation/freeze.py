"""Freeze baseline source/checkpoint/config before inference or policy changes."""
import argparse,json,shutil
from pathlib import Path
from datetime import datetime,timezone
from .io import dump,digest
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--checkpoint',type=Path,default=ROOT/'artifacts/phobert/smoke_heads');args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if (args.out/'baseline_lock.json').exists():raise SystemExit('Baseline already frozen; use a new run directory')
    policy=ROOT/'ml/phobert/decision.py';shutil.copyfile(policy,args.out/'baseline_policy.py')
    ck=args.checkpoint.resolve();manifest=json.loads((ck/'manifest.json').read_text(encoding='utf-8'))
    sources=[*sorted((ROOT/'ml/phobert').glob('*.py')),ROOT/'backend/local_reasoning/phobert_adapter.py',ROOT/'evaluation/configs/acceptance.yaml']
    dump(args.out/'baseline_lock.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),'checkpoint':str(ck),'heads_sha256':digest(ck/'heads.pt'),
      'manifest_sha256':digest(ck/'manifest.json'),'labels_sha256':digest(ck/'labels.json'),'trained_tasks':manifest['config']['stages'],
      'training_scope':manifest['training_scope'],'checkpoint_status':manifest['status'],'baseline_policy_sha256':digest(policy),
      'files':{str(f.relative_to(ROOT)):digest(f) for f in sources},'previous_reports':'reports/phobert_20261114; public and already seen',
      'training_gate':'No independently reviewed new annotations available; no new training is authorized by the data gate.'})
    print(str(args.out/'baseline_lock.json'))

if __name__=='__main__':main()
