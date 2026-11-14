# Explicit research mode only. Does not modify backend/local_settings.py.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:SCAMSHIELD_MODE = 'local_rules'
$env:SCAMSHIELD_REASONER = 'phobert'
$env:SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL = '1'
$env:SCAMSHIELD_PHOBERT_CHECKPOINT = Join-Path $PSScriptRoot 'artifacts/phobert/smoke_heads'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
# Fully offline experiment: domain parsing remains available, HTTP HEAD is off.
$env:SCAMSHIELD_URL_NETWORK_ENABLED = '0'
& .\.venv-phobert\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
