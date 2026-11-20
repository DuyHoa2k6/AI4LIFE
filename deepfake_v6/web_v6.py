"""Giao dien web cho ban v6 (dung lai giao dien cua ban truoc).
Chay: MO_GIAO_DIEN_V6.cmd -> http://127.0.0.1:8011/
"""
import asyncio, collections, os, sys, tempfile, time, uuid
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault('OMP_NUM_THREADS', '2'); os.environ.setdefault('MKL_NUM_THREADS', '2')
import detector  # noqa: E402

app = FastAPI(title="ScamShield Deepfake v6 - giao dien")
WEB = HERE / "web"
app.mount("/static", StaticFiles(directory=str(WEB)), name="static")
_sem = asyncio.Semaphore(1)
THR = 0.5

REASON = {
    "likely_fake": "Mô hình v6 thấy dấu hiệu giả mạo/AI tạo rõ (điểm > 60%).",
    "likely_real": "Mô hình v6 không thấy dấu hiệu giả mạo đáng kể (điểm < 40%).",
    "uncertain": "Điểm nằm vùng 40–60%, cần kiểm chứng thêm.",
    "cannot_assess": "Không đủ khung hình có khuôn mặt rõ để đánh giá (mặt quá nhỏ/mờ hoặc không có mặt).",
}

def vd(s):
    if s is None: return "cannot_assess"
    return detector.verdict_from_score(s)

def pc(x):
    return "–" if x is None else f"{x * 100:.0f}%"

def sec(t):
    return f"{t:.1f}".replace(".", ",")

def flag(x, thr=THR):
    return "BẤT THƯỜNG" if x is not None and x >= thr else "bình thường"

MODEL_VI = {"deepguard": "DeepGuard", "dima806": "dima806", "prithiv_v2": "prithiv-v2"}
ADVICE = ("Khuyến nghị: KHÔNG chuyển tiền hay gửi mã OTP; gọi lại qua số điện thoại quen (không dùng số/link trong tin nhắn); "
          "hỏi một câu riêng tư chỉ người thật mới biết; báo cho người thân và trình báo công an nếu bị đòi tiền.")

def build_reasons(r):
    kind, v = r.get("kind"), r.get("verdict")
    out = []  # (text, abnormal: bool)
    def add(t, bad=False): out.append({"text": t, "abnormal": bool(bad)})
    face = r.get("face_score") if kind == "image" else (r.get("face_score") if r.get("verdict_source") else r.get("score"))
    ms = r.get("model_scores") or {}
    if kind == "image":
        md, cf = r.get("ai_modern_score"), r.get("ai_commfor_score")
        if md is not None:
            add(f"Mô hình ảnh AI đời mới (haywoodsloan, nhận diện Flux/SDXL/Midjourney): {pc(md)} (ngưỡng 50%) → {flag(md)}", md >= THR)
        if cf is not None:
            add(f"Mô hình Community Forensics (ảnh AI kiểu Stable Diffusion/GAN): {pc(cf)} (ngưỡng 50%) → {flag(cf)}", cf >= THR)
        if md is not None and cf is not None and abs(md - cf) >= 0.5:
            add(f"Hai mô hình ảnh AI bất đồng ({pc(md)} so với {pc(cf)}): kết luận lấy mức cao hơn {pc(max(md, cf))}", True)
    else:
        n = r.get("frames_scored") or 0
        fsc = r.get("frame_scores") or []
        add(f"Đã lấy mẫu {r.get('frames_total_sampled', 0)} khung: chấm được {n} khung có mặt; bỏ qua {r.get('frames_skipped_no_face', 0)} khung không có mặt, "
            f"{r.get('frames_skipped_small', 0)} khung mặt quá nhỏ (<64px), {r.get('frames_skipped_blurry', 0)} khung quá mờ", n < 5)
        if n < 5:
            add(f"Chỉ {n} khung có mặt rõ (cần ít nhất 5) → không đủ để kết luận về ghép mặt", True)
        if fsc:
            hi = [f for f in fsc if f["s"] >= THR]
            add(f"Điểm ghép mặt trung bình {n} khung: {pc(face)} (thật <40%, giả >60%) → {flag(face)}", face is not None and face >= THR)
            add(f"{len(hi)}/{len(fsc)} khung ({len(hi) * 100 // len(fsc)}%) có điểm mặt ≥ 50%", len(hi) * 2 >= len(fsc))
            top = sorted(fsc, key=lambda f: -f["s"])[:3]
            add("Khung đáng ngờ nhất: " + ", ".join(f"giây {sec(f['t'])} mặt {pc(f['s'])}" for f in top), top[0]["s"] >= THR)
            low = min(fsc, key=lambda f: f["s"])
            add(f"Khung ít nghi nhất: giây {sec(low['t'])} mặt {pc(low['s'])}; độ dao động giữa các khung (độ lệch chuẩn) {pc(r.get('score_std'))}")
            if r.get("frac_frames_ge_09") is not None:
                add(f"Tỷ lệ khung có điểm mặt ≥ 90%: {pc(r.get('frac_frames_ge_09'))}", r.get("frac_frames_ge_09") >= 0.25)
        am = r.get("ai_video_modern_score")
        if am is not None:
            add(f"Mô hình ảnh AI đời mới trên {len(r.get('ai_video_modern_frames') or [])} khung toàn cảnh (video AI kiểu Grok/Veo/Sora): {pc(am)} "
                f"(các khung: {', '.join(pc(x) for x in r.get('ai_video_modern_frames') or [])}; ngưỡng 50%) → {flag(am)}", am >= THR)
        av = r.get("ai_video_score")
        if av is not None:
            add(f"Mô hình Community Forensics trên 8 khung toàn cảnh: {pc(av)} (ngưỡng 50%) → {flag(av)}", av >= THR)
        if r.get("verdict_source") == "ai_video_modern":
            add(f"Kết luận lấy theo mô hình video AI ({pc(am)}) vì cao hơn điểm ghép mặt ({pc(face)})", True)
    if kind == "image":
        if r.get("faces_scored"):
            note = ("; chỉ là tín hiệu phụ, KHÔNG dùng để kết luận ảnh vì đo trên bộ thử, phần mặt báo nhầm ~42% ảnh mặt thật"
                    if face is not None and face >= THR and v == "likely_real" else " (tín hiệu phụ)")
            add(f"Kiểm tra mặt bị ghép/chỉnh (3 mô hình mặt): {pc(face)} (ngưỡng 50%) → {flag(face)}{note}", face is not None and face >= THR)
        else:
            sk = [f"{r.get('frames_skipped_no_face', 0)} không có mặt", f"{r.get('frames_skipped_small', 0)} mặt quá nhỏ (<64px)", f"{r.get('frames_skipped_blurry', 0)} mặt quá mờ"]
            add("Không có khuôn mặt đủ rõ để kiểm tra ghép mặt (" + ", ".join(sk) + ")")
    if ms:
        vals = list(ms.values())
        txt = ", ".join(f"{MODEL_VI.get(k, k)} {pc(x)}" for k, x in ms.items())
        if max(vals) - min(vals) >= 0.4:
            add(f"Các mô hình mặt bất đồng: {txt} → độ tin cậy phần mặt thấp", True)
        else:
            add(f"Điểm từng mô hình mặt: {txt} (khá thống nhất)")
    a = r.get("av_sync")
    if a and a.get("lse_c") is not None:
        add(f"Khớp khẩu hình – giọng nói (SyncNet LSE-C): {a['lse_c']:.2f} (≤ 2,0 là đáng ngờ)", a["lse_c"] <= 2.0)
    sp = r.get("audio_spoof")
    if sp and sp.get("p_spoof") is not None:
        add(f"Giọng nói giả (AASIST): {pc(sp['p_spoof'])} (ngưỡng 50%) → {flag(sp['p_spoof'])}", sp["p_spoof"] >= THR)
    elif kind == "video":
        add("Chưa kiểm tra âm thanh/khẩu hình trong giao diện này (để xử lý nhanh)")
    s = r.get("score")
    if v == "likely_fake":
        bad = [x["text"].split(":")[0] for x in out if "BẤT THƯỜNG" in x["text"] or "Kết luận lấy" in x["text"]][:2]
        summ = f"Có dấu hiệu giả mạo: điểm tổng {pc(s)} > 60%" + (f", chủ yếu do {', '.join(bad)}." if bad else ".")
    elif v == "uncertain":
        summ = f"Chưa chắc chắn: điểm tổng {pc(s)} nằm trong vùng 40–60%, cần xác minh thêm."
    elif v == "likely_real":
        summ = f"Có vẻ thật: điểm tổng {pc(s)} < 40%; " + f"{sum(1 for x in out if not x['abnormal'])}/{len(out)} phép kiểm bình thường."
    else:
        summ = "Không đánh giá được: không đủ khung hình có khuôn mặt rõ."
    return summ, out, (ADVICE if v in ("likely_fake", "uncertain") else "")

def adapt(r):
    kind = r.get("kind")
    sig = {}
    if r.get("face_score") is not None or kind == "video":
        fsv = r.get("face_score") if (kind == "image" or r.get("verdict_source")) else r.get("score")
        sig["face_manipulation"] = {"score": fsv, "threshold": THR, "verdict": vd(fsv)}
    ai = r.get("ai_image_score") if kind == "image" else max([x for x in (r.get("ai_video_score"), r.get("ai_video_modern_score")) if x is not None], default=None)
    if ai is not None:
        sig["ai_generated"] = {"score": ai, "threshold": THR, "verdict": vd(ai)}
    fsc = r.get("frame_scores") or []
    frames = [{"t": f["t"], "fake_score": f["s"]} for f in sorted(fsc, key=lambda f: f["t"])] if kind == "video" else []
    summ, reasons, advice = build_reasons(r)
    # item 1: abnormal lines that do NOT drive the verdict are reference-only (grey info)
    for x in reasons:
        t = x["text"]
        x["info"] = bool(x["abnormal"] and (r.get("verdict") == "likely_real" or "bất đồng" in t
                         or "tín hiệu phụ" in t or "KHÔNG dùng" in t or "Chưa kiểm tra" in t))
    return {"type": kind, "verdict": r.get("verdict"), "score": r.get("score"), "threshold": THR,
            "reason": summ, "reasons": reasons, "advice": advice, "disclaimer": r.get("disclaimer", ""),
            "elapsed_s": r.get("elapsed_sec"), "model": "v6 (" + str(r.get("model")) + ")",
            "signals": sig, "frames": frames, "duration_s": r.get("duration_sec") or (frames[-1]["t"] if frames else 1),
            "most_suspicious": [], "faces": [], "raw": r}

def err(code, status, msg):
    return JSONResponse(status_code=status, content={"code": code, "message": msg, "request_id": str(uuid.uuid4())})

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(str(WEB / "index.html"))

@app.get("/api/deepfake/health")
def health():
    return {"status": "ok", "model": "v6"}

async def _run(data, ext, max_frames=detector.MAX_VIDEO_FRAMES):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / ("upload" + ext)
        p.write_bytes(data)
        async with _sem:
            return await asyncio.to_thread(detector.check_file, str(p), max_frames, detector.AGGREGATION, False, False)

@app.post("/api/deepfake/check")
async def check(file: UploadFile = File(...), thumbs: bool = Query(False)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in detector.IMAGE_EXTS | detector.VIDEO_EXTS | detector.AUDIO_EXTS:
        return err("UNSUPPORTED_TYPE", 415, f"Định dạng {ext or '?'} không hỗ trợ.")
    try:
        r = await _run(await file.read(), ext)
    except Exception as e:
        return err("BAD_MEDIA", 422, str(e))
    out = adapt(r); out["file"] = file.filename
    return out

# ---- live: kiem tra mat thoi gian thuc (live_check.py) ----
import io, threading  # noqa: E402
import live_check  # noqa: E402
ALERT_N = 3
_sessions = {}
_live_lock = threading.Lock()

def _live(data, sid):
    from PIL import Image
    img = Image.open(io.BytesIO(data)).convert("RGB")
    with _live_lock:
        st = _sessions.setdefault(sid, live_check.new_session())
        return live_check.analyze_frame(img, st), st

@app.post("/api/deepfake/frame")
async def frame(file: UploadFile = File(...), session_id: str = Query("default", max_length=64)):
    t0 = time.time()
    try:
        r, st = await asyncio.to_thread(_live, await file.read(), session_id)
    except Exception as e:
        return err("BAD_MEDIA", 422, str(e))
    sm = r["smoothed_score"]
    v = vd(sm) if sm is not None else "cannot_assess"
    st["hot"] = st["hot"] + 1 if v == "likely_fake" else 0
    r.update({"verdict": v, "threshold": THR, "alert": st["hot"] >= ALERT_N,
              "frames_received": st["n"], "latency_s": round(time.time() - t0, 2)})
    return r

@app.post("/api/deepfake/frame/reset")
def frame_reset(session_id: str = Query("default", max_length=64)):
    _sessions.pop(session_id, None)
    return {"ok": True}

# ---- item 2: 'Kiem tra chu dong' - landmark-only fast sampling ----
def _landmarks(data):
    from PIL import Image
    import numpy as np, cv2
    img = Image.open(io.BytesIO(data)).convert("RGB")
    W, H = img.size
    boxes, probs, lms = detector.get_mtcnn().detect(img, landmarks=True)
    g = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)
    if boxes is None or len(boxes) == 0:
        return {"face": False, "lum": round(float(g.mean()), 1)}
    i = int(max(range(len(boxes)), key=lambda k: (boxes[k][2] - boxes[k][0]) * (boxes[k][3] - boxes[k][1])))
    b = [float(v) for v in boxes[i]]
    out = {"face": True, "prob": round(float(probs[i]), 4), "lum": round(float(g.mean()), 1),
           "box_rel": [max(0, b[0]) / W, max(0, b[1]) / H, (b[2] - b[0]) / W, (b[3] - b[1]) / H]}
    x1, y1, x2, y2 = [int(max(0, v)) for v in b]
    out["face_lum"] = round(float(g[y1:y2, x1:x2].mean()), 1) if (y2 > y1 and x2 > x1) else None
    if lms is not None:
        lm = np.asarray(lms[i], float)
        eye_dist, yaw, roll, _geom = live_check._pose_geom(lm)
        out.update({"yaw": round(yaw, 4), "roll": round(roll, 2),
                    "eye": live_check._eye_openness(g, lm, eye_dist)})
    return out

@app.post("/api/deepfake/landmarks")
async def landmarks(file: UploadFile = File(...)):
    t0 = time.time()
    try:
        data = await file.read()
        with _live_lock:
            pass
        r = await asyncio.to_thread(_landmarks, data)
    except Exception as e:
        return err("BAD_MEDIA", 422, str(e))
    r["latency_s"] = round(time.time() - t0, 3)
    return r
