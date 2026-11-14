"""Explicit online preparation only; runtime never downloads missing artifacts."""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'artifacts' / 'phobert'
BASE_REVISION='01daacda68afe13d83023d16ec647239e344a1e6'
VNC_REVISION='62bbc58fe5d113c898eae112656be97dcf50b3a0'

def fetch(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix(path.suffix + '.partial')
        with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        temporary.replace(path)
    return {'path': str(path.relative_to(ASSETS)), 'bytes': path.stat().st_size,
            'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest(), 'url': url}

def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    revision = BASE_REVISION
    names = ['config.json', 'vocab.txt', 'bpe.codes', 'pytorch_model.bin', 'README.md']
    files = [fetch(f'https://huggingface.co/vinai/phobert-base/resolve/{revision}/{n}', ASSETS/'base'/n) for n in names]
    files.append(fetch('https://raw.githubusercontent.com/VinAIResearch/PhoBERT/master/LICENSE', ASSETS/'base'/'LICENSE'))
    # Pin the original toolkit repository, not an unrelated word segmenter.
    vnc_revision = VNC_REVISION
    for n in ['VnCoreNLP-1.2.jar', 'models/wordsegmenter/vi-vocab', 'models/wordsegmenter/wordsegmenter.rdr']:
        files.append(fetch(f'https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/{vnc_revision}/{n}', ASSETS/'vncorenlp'/n))
    manifest = {'checkpoint': 'vinai/phobert-base', 'revision': revision, 'license': 'MIT',
                'vncorenlp_revision': vnc_revision, 'max_tokens_including_special': 256, 'files': files}
    (ASSETS/'preparation.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'checkpoint': manifest['checkpoint'], 'revision': revision, 'files': len(files)}))

if __name__ == '__main__':
    main()
