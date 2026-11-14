"""Fetch versioned Unicode reference data at setup, never fetch user URLs."""
import hashlib,json
from pathlib import Path
import httpx

def main():
    root=Path(__file__).resolve().parent/'knowledge/url'
    root.mkdir(parents=True,exist_ok=True)
    url='https://unicode.org/Public/17.0.0/security/confusables.txt'
    r=httpx.get(url,timeout=60,follow_redirects=False);r.raise_for_status()
    if len(r.content)>2_000_000 or '# Version: 17.0.0' not in r.text:raise RuntimeError('Unexpected Unicode data')
    (root/'confusables.txt').write_bytes(r.content)
    (root/'unicode_manifest.json').write_text(json.dumps({'version':'17.0.0','url':url,'sha256':hashlib.sha256(r.content).hexdigest(),'license':'https://www.unicode.org/terms_of_use.html'},indent=2)+'\n',encoding='utf-8')
    print('Installed Unicode 17.0.0 confusable mappings; URL analysis remains offline.')

if __name__=='__main__':main()
