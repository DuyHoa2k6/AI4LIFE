"""Local OCR only: bounded image upload, no URL fetching, ephemeral provenance."""
from collections import OrderedDict
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid
from PIL import Image, ImageOps, UnidentifiedImageError
from .providers import ProviderFailure

ROOT=Path(__file__).resolve().parent.parent
MAX_BYTES=4*1024*1024
MAX_PIXELS=8_000_000
_slots=threading.BoundedSemaphore(2)
_lock=threading.Lock()
_sources=OrderedDict()


def recognize(data):
    if not data or len(data)>MAX_BYTES:
        raise ProviderFailure('OCR_IMAGE_TOO_LARGE',413)
    try:
        image=Image.open(BytesIO(data))
        if image.format not in ('PNG','JPEG','WEBP') or image.width*image.height>MAX_PIXELS:
            raise ValueError()
        image=ImageOps.exif_transpose(image)
        image.load()
        rgba=image.convert('RGBA')
        background=Image.new('RGBA',rgba.size,'white');background.alpha_composite(rgba)
        image=background.convert('RGB')
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ProviderFailure('OCR_INVALID_IMAGE',422) from None
    node=shutil.which('node')
    if not node or not (ROOT/'ocr/node_modules/tesseract.js').exists() or not all(
            (ROOT/f'ocr/models/{lang}.traineddata.gz').exists() for lang in ('vie','eng')):
        raise ProviderFailure('OCR_NOT_INSTALLED',503)
    if not _slots.acquire(blocking=False):
        raise ProviderFailure('OCR_BUSY',429)
    started=time.perf_counter()
    try:
        directory=ROOT/'.ocr-tmp';directory.mkdir(exist_ok=True)
        path=directory/(uuid.uuid4().hex+'.png')
        try:
            image.save(path)
            try:
                result=subprocess.run([node,str(ROOT/'ocr/recognize.cjs'),str(path)],
                    capture_output=True,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            except subprocess.TimeoutExpired:
                raise ProviderFailure('OCR_TIMEOUT',504) from None
            if result.returncode or len(result.stdout)>2_000_000:
                raise ProviderFailure('OCR_FAILED',502)
            try: output=json.loads(result.stdout)
            except (ValueError,UnicodeError): raise ProviderFailure('OCR_FAILED',502) from None
        finally:
            path.unlink(missing_ok=True)
    finally:
        _slots.release()
    text=output['text'].strip()
    if len(text)>10000: raise ProviderFailure('OCR_TEXT_TOO_LONG',413)
    confidence=float(output.get('confidence') or 0)
    status='no_text' if sum(c.isalnum() for c in text)<3 else 'low_confidence' if confidence<60 else 'ready'
    source_id=uuid.uuid4().hex if status!='no_text' else None
    response={'source_id':source_id,'image_sha256':hashlib.sha256(data).hexdigest(),
              'text':text,'status':status,'confidence':confidence,'engine':'tesseract.js-7.0.0-vie+eng',
              'width':image.width,'height':image.height,'blocks':output.get('blocks',[])[:500],
              'ocr_ms':(time.perf_counter()-started)*1000,
              'notice':'Văn bản do OCR nhận diện, có thể sai; hãy đối chiếu ảnh trước khi phân tích.'}
    if source_id:
        with _lock:
            now=time.monotonic()
            for key in list(_sources):
                if _sources[key][0]<now: del _sources[key]
            _sources[source_id]=(now+900,response)
            while len(_sources)>128: _sources.popitem(last=False)
    return response


def validate_sources(request):
    messages={m.id:m for m in request.as_messages()}
    result=[]
    with _lock:
        for ref in request.ocr_sources:
            source=_sources.get(ref.source_id)
            if source is None or source[0]<time.monotonic():
                raise ProviderFailure('OCR_SOURCE_EXPIRED',422)
            data=source[1]
            if messages[ref.message_id].text!=data['text']:
                raise ProviderFailure('OCR_TEXT_CHANGED',422)
            result.append({'message_id':ref.message_id,'image_id':ref.source_id,
                           'origin':'image_ocr','image_sha256':data['image_sha256'],
                           'confidence':data['confidence'],'width':data['width'],'height':data['height'],
                           'blocks':data['blocks'],'verification':'matches_ocr_output_not_verified_pixels'})
    return result
