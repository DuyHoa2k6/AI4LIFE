$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m venv .venv-phobert
if ($LASTEXITCODE -ne 0) { throw 'Cannot create ML environment' }
& .\.venv-phobert\Scripts\python.exe -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'Cannot install CPU PyTorch' }
& .\.venv-phobert\Scripts\python.exe -m pip install -r ml/phobert/requirements.txt -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Cannot install ML/backend dependencies' }
& .\.venv-phobert\Scripts\python.exe -m ml.phobert.prepare
if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare official model/segmenter assets' }
