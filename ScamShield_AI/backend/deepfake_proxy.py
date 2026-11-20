"""Proxy mo-dun deepfake v6 (tien trinh rieng cong 8011) vao backend nhom.

Khong import torch/transformers cua v6, tranh xung dot dependency.
Giao dien tai /deepfake dung web cua deepfake_v6 (fallback muse_v6_light).
"""
import os
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

V6_DEFAULT = "http://127.0.0.1:8011"
DEEPFAKE_MAX_BYTES = 100 * 1024 * 1024
HOP = {
    "host", "content-length", "connection", "transfer-encoding", "keep-alive",
    "proxy-authenticate", "proxy-authorization", "te", "trailers", "upgrade",
}
router = APIRouter()


def v6_base() -> str:
    return os.environ.get("SCAMSHIELD_DEEPFAKE_URL", V6_DEFAULT).rstrip("/")


def ui_dir() -> Path:
    env = os.environ.get("SCAMSHIELD_DEEPFAKE_UI")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    # Prefer in-repo deepfake_v6/web; fall back to sibling muse_v6_light/web.
    for cand in (
        here.parents[2] / "deepfake_v6" / "web",
        here.parents[3] / "muse_v6_light" / "web",
    ):
        if cand.is_dir():
            return cand
    return here.parents[2] / "deepfake_v6" / "web"


def _offline(status=503, code="DEEPFAKE_OFFLINE", message=None):
    return JSONResponse(status_code=status, content={
        "code": code,
        "message": message or (
            "Chua ket noi duoc mo-dun deepfake v6 (cong 8011). "
            "Hay chay CHAY_TAT_CA.cmd hoac MO_GIAO_DIEN_V6.cmd roi thu lai."
        ),
        "request_id": str(uuid.uuid4()),
    })


@router.get("/deepfake", include_in_schema=False)
@router.get("/deepfake/", include_in_schema=False)
async def deepfake_page():
    src = ui_dir() / "index.html"
    if not src.is_file():
        return HTMLResponse(
            "<!doctype html><meta charset=\"utf-8\"><title>Deepfake</title>"
            "<p>Khong tim thay giao dien v6 tai muse_v6_light/web. "
            "Dat SCAMSHIELD_DEEPFAKE_UI neu doi thu muc.</p>",
            status_code=503,
        )
    html = src.read_text(encoding="utf-8")
    html = html.replace("href=\"/static/", "href=\"/deepfake-static/")
    html = html.replace("src=\"/static/", "src=\"/deepfake-static/")
    html = html.replace(
        "<title>AI4LIFE – Kiểm tra Deepfake</title>",
        "<title>ScamShield AI · Deepfake / Ảnh-Video</title>",
    )
    link = (
        "<a href=\"/\" style=\"color:#e6edf3;margin-right:12px;text-decoration:none\">"
        "← Kiểm tra tin nhắn</a>"
    )
    if "<nav>" in html:
        html = html.replace("<nav>", "<nav>" + link, 1)
    else:
        html = html.replace("<header>", "<header>" + link, 1)
    return HTMLResponse(html)


@router.api_route("/api/deepfake/{path:path}", methods=["GET", "POST"])
async def proxy_deepfake(path: str, request: Request):
    url = f"{v6_base()}/api/deepfake/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP}
    body = await request.body() if request.method != "GET" else None
    timeout = httpx.Timeout(180.0, connect=3.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.request(
                request.method, url, params=request.query_params,
                content=body, headers=headers,
            )
    except httpx.ConnectError:
        return _offline()
    except httpx.TimeoutException:
        return _offline(
            504, "DEEPFAKE_TIMEOUT",
            "Mo-dun deepfake v6 xu ly qua lau. Thu lai voi tep ngan hon, "
            "hoac doi may boi vi video co the mat hang chuc giay.",
        )
    media = r.headers.get("content-type")
    return Response(content=r.content, status_code=r.status_code, media_type=media)


def mount_deepfake(app: FastAPI) -> None:
    folder = ui_dir()
    if folder.is_dir():
        app.mount("/deepfake-static", StaticFiles(directory=str(folder)), name="deepfake-static")
    app.include_router(router)
