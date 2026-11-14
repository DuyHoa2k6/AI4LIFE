import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse, OcrInputSource, OcrResponse
from .providers import get_provider, ProviderFailure, MockProvider
from .engine import decide
from .settings import get_setting, LocalConfigError, response_timeouts_disabled
from .ocr import recognize, validate_sources, MAX_BYTES
from .urls import apply_url_evidence
from .url_network import inspect_urls


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            event = await receive()
            if event['type'] == 'http.disconnect':
                return
            chunk = event.get('body', b'')
            size += len(chunk)
            if size > (MAX_BYTES if scope.get('path')=='/api/ocr' else 65536):
                response = JSONResponse(status_code=413, content={'code': 'BODY_TOO_LARGE',
                    'message': 'Nội dung gửi vượt giới hạn.', 'request_id': str(uuid.uuid4())})
                return await response(scope, receive, send)
            chunks.append(chunk)
            if not event.get('more_body', False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': b''.join(chunks), 'more_body': False}
            return await receive()
        await self.app(scope, replay, send)


@asynccontextmanager
async def lifespan(app):
    if get_setting('SCAMSHIELD_REASONER','legacy')=='phobert':
        from .local_reasoning.phobert_adapter import get_runtime
        await asyncio.to_thread(get_runtime)
    yield

app = FastAPI(title='ScamShield AI', version='0.1.0', lifespan=lifespan)
ROOT = Path(__file__).resolve().parent.parent

app.mount('/assets', StaticFiles(directory=ROOT / 'web'), name='web-assets')
app.add_middleware(BodyLimit)
app.add_middleware(CORSMiddleware, allow_origins=get_setting('SCAMSHIELD_ALLOWED_ORIGINS', 'http://localhost:5173').split(','),
                   allow_methods=['POST', 'GET'], allow_headers=['Content-Type'])


def error(code, status, diagnostic=None):
    return JSONResponse(status_code=status, content=ErrorResponse(code=code,
        message=('Nhánh phân tích mô hình bên ngoài đã được gỡ. Hãy đặt SCAMSHIELD_MODE=local_rules.'
                 if code == 'EXTERNAL_MODEL_REMOVED' else
                 'Chưa kiểm tra được. Vui lòng kiểm tra dữ liệu hoặc thử lại.'),
        request_id=str(uuid.uuid4()), diagnostic=diagnostic).model_dump(exclude_none=True))


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    # Return schema locations only: never echo input, URLs, arbitrary keys or ValueError text.
    fields={'body','text','messages','context','question','ocr_sources','links','id',
            'message_id','url','display_text','start','end','origin','speaker','source_id'}
    issues=[{'path':[p if isinstance(p,int) or p in fields else 'field' for p in e['loc']],
             'type':e['type']} for e in exc.errors()[:5]]
    return error('INVALID_INPUT', 422, {'stage':'request_validation','issues':issues})


@app.exception_handler(ProviderFailure)
async def provider_failure(request, exc):
    return error(exc.code, exc.status, exc.diagnostic)


@app.exception_handler(LocalConfigError)
async def private_configuration_error(request, exc):
    return error('PROVIDER_CONFIG_INVALID', 503)


@app.get('/health')
async def health():
    return {'status': 'ok', 'mode': get_setting('SCAMSHIELD_MODE', 'local_rules')}


@app.get('/', include_in_schema=False)
async def website():
    return FileResponse(ROOT / 'web/index.html')


@app.get('/shared.js', include_in_schema=False)
async def shared_ui():
    return FileResponse(ROOT / 'extension/shared.js', media_type='text/javascript')


@app.get('/result-view.js', include_in_schema=False)
async def result_view_ui():
    return FileResponse(ROOT / 'extension/result_view.js', media_type='text/javascript')


@app.get('/fixture', include_in_schema=False)
async def extension_fixture():
    return FileResponse(ROOT / 'web/fixture.html')


@app.get('/client-config')
async def client_config():
    provider = get_provider()
    local = getattr(provider, 'pipeline', None) == 'local_rules'
    network = local and get_setting('SCAMSHIELD_URL_NETWORK_ENABLED','1')=='1'
    return {'mode': 'local_rules' if local else 'mock', 'url_network_enabled': network,
            'url_network_notice': ('Backend gửi HTTP HEAD tới tối đa 3 liên kết, theo tối đa 3 chuyển hướng; máy chủ đích có thể ghi nhận yêu cầu. Không đọc nội dung trang. Không gửi liên kết chứa mã riêng tư.' if network else 'Kiểm tra mạng URL đang tắt; vẫn đối chiếu cấu trúc tên miền, chưa có kết quả không đồng nghĩa liên kết an toàn.'),
            'processing_notice': ('Nội dung được xử lý bằng PhoBERT cục bộ và quy tắc trên dữ kiện dự đoán; đây là chế độ nghiên cứu chưa được kiểm chứng chất lượng. Không gửi tới API mô hình ngoài.' if get_setting('SCAMSHIELD_REASONER','legacy')=='phobert' else 'Nội dung được xử lý bằng Python và quy tắc tại backend, không gửi tới Gemini hoặc mô hình bên ngoài. Phạm vi nhận diện còn giới hạn.')}



@app.post('/api/analyze', response_model=AnalyzeResponse,
          responses={c: {'model': ErrorResponse} for c in (413, 422, 502, 503, 504)})
async def analyze(body: AnalyzeRequest, provider=Depends(get_provider)):
    request_id=str(uuid.uuid4())
    from .clarifications import prepare,finish
    local=getattr(provider,'pipeline',None)=='local_rules'
    pending=None
    if local:
        body,pending,cached=prepare(body)
        if cached is not None:return finish(body,cached,pending=pending)
    sources=validate_sources(body)
    try:
        budget = float(get_setting('SCAMSHIELD_TIMEOUT', '20'))
        # Temporary diagnostic switch: retain the deadline for easy restoration.
        extracted = await asyncio.wait_for(provider.extract(body),
            timeout=None if response_timeouts_disabled() else budget)
    except (asyncio.TimeoutError, TimeoutError):
        raise ProviderFailure('PROVIDER_TIMEOUT', 504) from None
    local=getattr(provider,'pipeline',None)=='local_rules'
    if local:
        from .local_reasoning.adapter import to_public
        result=to_public(extracted,body)
    else:
        result=decide(extracted, body, 'mock')
    if not local:
        result=apply_url_evidence(result,None,await inspect_urls(body,network=not isinstance(provider,MockProvider)),body)
    if sources:
        if result.schema_version not in ('1.9','2.0'):result.schema_version='1.8' if result.url_analysis else '1.6'
        result.input_sources=[OcrInputSource.model_validate(s) for s in sources]
        result.input_warnings+=['Quote khớp văn bản OCR chưa chứng minh OCR đọc đúng ảnh. Hãy đối chiếu ảnh gốc.']
        if any(s['confidence']<60 for s in sources):
            result.input_warnings.append('OCR có điểm chất lượng thấp; hãy dùng ảnh rõ hơn hoặc kiểm tra lại từng chữ trước khi làm theo kết quả.')
    if local:result=finish(body,result,extracted,pending)
    result.request_id=request_id
    from .diagnostics import record
    record(request_id,extracted,result)
    return result


# First-stage inspection only. This route never resolves get_provider, OCR, URL
# networking, retrieval or final risk decisions. Existing clients keep /analyze.
from .local_observation.schema import Observation


@app.post('/api/observe', response_model=Observation,
          responses={c: {'model': ErrorResponse} for c in (413, 422)})
async def observe(body: AnalyzeRequest):
    from .local_observation.analyzer import analyze as observe_local
    return await asyncio.to_thread(observe_local, body)


@app.post('/api/ocr',response_model=OcrResponse)
async def image_ocr(request: Request):
    if request.headers.get('content-type','').split(';')[0] not in ('image/png','image/jpeg','image/webp'):
        return error('OCR_UNSUPPORTED_TYPE',415)
    return await asyncio.to_thread(recognize,await request.body())


from .local_reasoning.schema import CaseInput, LocalResult


@app.post('/api/analyze-local',response_model=LocalResult,responses={503:{'model':LocalResult}})
async def analyze_local_case(body: CaseInput):
    from .local_reasoning.engine import analyze_local
    from .local_reasoning.support import enrich
    result=await asyncio.to_thread(analyze_local,body)
    result=await enrich(result,body.legacy())
    if result.analysis_status=='error':
        return JSONResponse(status_code=503,content=result.model_dump(mode='json'))
    return result


@app.get('/local',include_in_schema=False)
async def local_demo():
    return FileResponse(ROOT/'web/local.html')
