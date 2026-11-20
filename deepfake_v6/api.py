#!/usr/bin/env python3
"""api.py — HTTP API for the deepfake detector (CPU-only, standalone).

Run:
    uvicorn api:app --host 127.0.0.1 --port 8001

Endpoints:
    GET  /health          -> {"status": "ok", ...}
    POST /deepfake/check  -> multipart file upload (image/video/.wav),
                             returns the same JSON object as check.py.

Models load lazily on the first request and stay in memory afterwards.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402

import detector  # noqa: E402

app = FastAPI(title="Deepfake Detector v4",
              description="Image/video deepfake check "
                          "(DeepGuard + dima806 + prithiv-v2 ensemble) "
                          "with SyncNet lip-sync flag and video-audio "
                          "spoof check, and voice-spoof check (AASIST). "
                          "CPU-only.")


@app.get("/health")
def health():
    return {"status": "ok",
            "image_video_model": detector.MODEL_NAME,
            "audio_model": detector.AUDIO_MODEL_NAME,
            "verdict_bands": {"likely_real": "< 0.40",
                              "uncertain": "0.40 - 0.60",
                              "likely_fake": "> 0.60"}}


@app.post("/deepfake/check")
async def deepfake_check(file: UploadFile = File(...),
                         max_frames: int = detector.MAX_VIDEO_FRAMES):
    ext = os.path.splitext(file.filename or "")[1].lower()
    allowed = detector.IMAGE_EXTS | detector.VIDEO_EXTS | detector.AUDIO_EXTS
    if ext not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"unsupported file type '{ext}'. Allowed: "
                   f"{sorted(allowed)}")
    suffix = ext
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
    try:
        result = detector.check_file(tmp_path, max_frames)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    result["file"] = file.filename
    return result
