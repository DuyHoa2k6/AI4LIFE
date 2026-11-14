"""Hardware/software and canonical-data audit; never opens holdout or secrets."""
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
from collections import Counter
from pathlib import Path
import psutil
import torch

ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'reports/phobert_20261114';out.mkdir(parents=True,exist_ok=True)
    command='[ordered]@{cpu=@(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors); gpu=@(Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM)} | ConvertTo-Json -Depth 4 -Compress'
    query=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,timeout=30)
    hardware={'python':platform.python_version(),'os':platform.platform(),'logical_cpus':os.cpu_count(),
      'ram_total_bytes':psutil.virtual_memory().total,'ram_available_bytes':psutil.virtual_memory().available,
      'disk':dict(zip(['total','used','free'],shutil.disk_usage(ROOT))),
      'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),'cuda_device_count':torch.cuda.device_count(),
      'cuda_version':torch.version.cuda,'gpu_vram_bytes':torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else None,
      'windows_cim':json.loads(query.stdout) if query.returncode==0 and query.stdout.strip().startswith('{') else {'unavailable':True},
      'versions':{name:importlib.metadata.version(name) for name in ['transformers','tokenizers','numpy','psutil','torch']}}
    manifest=json.loads((ROOT.parent/'data/v2/manifest.json').read_text(encoding='utf-8'))
    canonical=ROOT.parent/'data/v2'/manifest['canonical_pilot'];rows=[json.loads(x) for x in canonical.read_text(encoding='utf-8').splitlines() if x.strip()]
    data={'canonical':str(canonical),'sha256':hashlib.sha256(canonical.read_bytes()).hexdigest(),'samples':len(rows),
      'review_status':dict(Counter(x['metadata']['review_status'] for x in rows)),
      'span_review':dict(Counter(s['review_status'] for x in rows for s in x['annotations']['spans'])),
      'training_eligible_from_manifest':manifest.get('training_eligible'),'old_holdout':'not opened',
      'archives':'not merged or counted as new independent data'}
    (out/'hardware.json').write_text(json.dumps(hardware,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'existing_data_audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ram_bytes':hardware['ram_total_bytes'],'cuda':hardware['cuda_available'],'existing_data':data},ensure_ascii=False))

if __name__=='__main__':main()
