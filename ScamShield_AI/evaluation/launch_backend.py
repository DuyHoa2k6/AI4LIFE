"""Run only the research version actually selected by a recorded comparison."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from .io import digest
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--selection',type=Path,required=True);p.add_argument('--allow-experimental',action='store_true');p.add_argument('--port',type=int,default=8000);args=p.parse_args()
    choice=json.loads(args.selection.read_text(encoding='utf-8'))
    checkpoint=ROOT/choice['selected_checkpoint']
    if not args.allow_experimental or choice['selected_policy']!='baseline':raise SystemExit('Only explicitly allowed, retained baseline research policy can be launched; no candidate promotion')
    if digest(checkpoint/'heads.pt')!=choice['heads_sha256']:raise SystemExit('Selected checkpoint hash changed')
    env={**os.environ,'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'phobert','SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL':'1','SCAMSHIELD_PHOBERT_CHECKPOINT':str(checkpoint.resolve()),'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}
    subprocess.run([sys.executable,'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port',str(args.port)],cwd=ROOT,env=env,check=True)

if __name__=='__main__':main()
