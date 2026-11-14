"""Strict head initialization, never reinterpret an old checkpoint label order."""
import hashlib,json
from pathlib import Path
import torch
from .schema import VERSION,SPAN_LABELS,ATTRS,ROLES,RELATIONS,RISKS

def load_heads(model,path):
    path=Path(path);labels=json.loads((path/'labels.json').read_text(encoding='utf-8'))
    expected={'schema_version':VERSION,'spans':SPAN_LABELS,'attributes':ATTRS,'roles':ROLES,'relations':RELATIONS,'risks':RISKS}
    if labels!=expected:raise ValueError('Warm-start label mapping/order differs; explicit head migration required')
    manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    data=(path/'heads.pt').read_bytes();sha=hashlib.sha256(data).hexdigest()
    if sha!=manifest['heads_sha256']:raise ValueError('Warm-start checkpoint hash mismatch')
    state=torch.load(path/'heads.pt',map_location=next(model.parameters()).device,weights_only=True)
    incompatible=model.load_state_dict(state,strict=False)
    if incompatible.unexpected_keys or any(not name.startswith('encoder.') for name in incompatible.missing_keys):raise ValueError('Warm-start heads are incomplete')
    return {'heads_sha256':sha,'parent_manifest_sha256':hashlib.sha256((path/'manifest.json').read_bytes()).hexdigest()}
