"""Download pinned Vietnamese/English data for local Tesseract.js (no user images)."""
import hashlib
import json
from pathlib import Path
import httpx

DIRECTORY=Path(__file__).resolve().parent/'ocr/models'
def main():
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    hashes={}
    for lang in ('vie','eng'):
        url=f'https://raw.githubusercontent.com/naptha/tessdata/gh-pages/4.0.0/{lang}.traineddata.gz'
        response=httpx.get(url,timeout=60,follow_redirects=False)
        response.raise_for_status()
        data=response.content
        if not data.startswith(b'\x1f\x8b') or len(data)>25_000_000:
            raise RuntimeError('Invalid OCR model download')
        (DIRECTORY/f'{lang}.traineddata.gz').write_bytes(data)
        hashes[lang]={'url':url,'sha256':hashlib.sha256(data).hexdigest()}
    (DIRECTORY/'hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print('Installed local vie+eng OCR models; hashes saved.')

if __name__=='__main__':main()
