"""Reproduce the local smoke experiments. Does not open the locked test split."""
import json
import os
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'reports/phobert_20261114';out.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','PYTHONIOENCODING':'utf-8'}
    commands=[['-m','ml.phobert.train'],['-m','ml.phobert.train','--overfit-smoke'],
      ['-m','ml.phobert.train','--config','ml/phobert/cpu_finetune_step.json'],
      ['-m','ml.phobert.evaluate'],['-m','ml.phobert.api_smoke'],['-m','pytest','tests','-q']]
    records=[]
    for i,args in enumerate(commands):
        with (out/f'run_{i+1}.log').open('w',encoding='utf-8') as log:
            completed=subprocess.run([sys.executable,*args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        records.append({'command':[sys.executable,*args],'exit_code':completed.returncode,'log':f'run_{i+1}.log'})
        (out/'commands.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(records[-1]),flush=True)
        if completed.returncode:raise SystemExit(completed.returncode)

if __name__=='__main__':main()
