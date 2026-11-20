"""Real-time face check for the live video-call tab (web_v6.py).

Per frame: MTCNN faces + landmarks -> face-crop ensemble score
(deepguard + dima806 + prithiv_v2, models kept resident) per face.
Per session: liveness / consistency signals on the main face:
  - blink: eye-openness proxy from the 5 MTCNN landmarks (no eye
    contour available, and frames arrive ~1/s, so this is weak and only
    counts after a long run with zero blinks)
  - head movement: yaw/roll from landmarks; a perfectly frozen head
    over many frames suggests a still image / replay
  - boundary: sharpness of the face vs. the surrounding background
    (face-swap blending often leaves a blurrier face)
  - jumps: sudden score jumps or identity (geometry) jumps
Aux signals only ADD a small, capped bonus to the smoothed face score
(conservative so a normal webcam stays < 0.40).
"""
import collections
import math
import time

import numpy as np

import detector

WINDOW = 8
MAX_FACES = 2
AUX_CAP = 0.15
# bak_cam fix: boundary/jump are informational only (on real webcams and test videos they
# fired MORE on real faces than on fakes), so weight 0.
W_BOUNDARY, W_JUMP, W_STATIC, W_NOBLINK = 0.0, 0.0, 0.04, 0.03
FACE_ONLY_CAP = 0.59   # face models alone can at most say 'uncertain' in live mode
AGREE_MIN, AGREE_MID = 0.40, 0.60

LABELS = {
    "blink": "Chớp mắt tự nhiên",
    "head_motion": "Cử động đầu tự nhiên",
    "boundary": "Viền mặt mờ/khác nền",
    "jumps": "Điểm/khuôn mặt nhảy đột ngột",
    "ai_frame": "Toàn khung do AI tạo (mỗi 3 khung)",
}
AI_EVERY = 3


def new_session():
    return {"n": 0, "scores": collections.deque(maxlen=WINDOW),
            "eye": collections.deque(maxlen=60), "blinks": 0,
            "yaw": collections.deque(maxlen=WINDOW), "roll": collections.deque(maxlen=WINDOW),
            "boundary": collections.deque(maxlen=WINDOW), "jumps": collections.deque(maxlen=WINDOW),
            "last_score": None, "last_geom": None, "ai": collections.deque(maxlen=4), "permodel": collections.deque(maxlen=WINDOW), "hot": 0, "face_frames": 0, "t0": time.time(), "last_blink_t": None, "ratio": None, "motion": None}


def _models():
    out = {"deepguard": detector.get_deepguard()}
    for name in ("dima806", "prithiv_v2"):
        out[name] = detector.get_vit_model(name)
    return out


def _score_crop(models, crop):
    rec = {"scores": {"deepguard": detector.score_face_crop(models["deepguard"], crop)}}
    for name in ("dima806", "prithiv_v2"):
        m, idx = models[name]
        rec["scores"][name] = detector.score_crop_vit(m, idx, crop)
    m = rec["scores"]
    # median of the 3 models: one model alone (e.g. DeepGuard = 99% on a dim
    # laptop webcam) can no longer drive the frame score
    return float(np.median(list(m.values()))), {k: float(v) for k, v in m.items()}


def _gray(pil):
    import cv2
    return cv2.cvtColor(np.asarray(pil.convert("RGB")), cv2.COLOR_RGB2GRAY)


def _lapvar(g):
    import cv2
    if g.size < 64:
        return None
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def _eye_openness(g, lm, eye_dist):
    """Vertical-gradient energy in small patches around both eyes,
    normalised by patch contrast. Closed eye -> fewer horizontal edges."""
    import cv2
    r = max(4, int(eye_dist * 0.22))
    vals = []
    for (x, y) in lm[:2]:
        x, y = int(x), int(y)
        p = g[max(0, y - r):y + r, max(0, x - r):x + r].astype(np.float32)
        if p.size < 16:
            continue
        sy = np.abs(cv2.Sobel(p, cv2.CV_32F, 0, 1, ksize=3)).mean()
        vals.append(sy / (p.std() + 5.0))
    return float(np.mean(vals)) if vals else None


def _pose_geom(lm):
    le, re, nose, ml, mr = lm
    eye_dist = float(np.hypot(*(re - le)))
    mid = (le + re) / 2.0
    yaw = float((nose[0] - mid[0]) / max(eye_dist, 1.0))
    roll = float(math.degrees(math.atan2(re[1] - le[1], re[0] - le[0])))
    mouth_mid = (ml + mr) / 2.0
    geom = np.array([
        float(np.hypot(*(mouth_mid - mid))) / max(eye_dist, 1.0),
        float(np.hypot(*(mr - ml))) / max(eye_dist, 1.0),
    ])
    return eye_dist, yaw, roll, geom


def _boundary_signal(g, box):
    """Face-vs-background sharpness. Returns (ratio, suspicion 0..1)."""
    h, w = g.shape
    x1, y1, x2, y2 = [int(v) for v in box]
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
    bw, bh = x2 - x1, y2 - y1
    if bw < 40 or bh < 40:
        return None, None
    inner = g[y1 + bh // 5:y2 - bh // 5, x1 + bw // 5:x2 - bw // 5]
    ox1, oy1 = max(0, x1 - bw // 2), max(0, y1 - bh // 3)
    ox2, oy2 = min(w, x2 + bw // 2), min(h, y2 + bh // 3)
    ring = g[oy1:oy2, ox1:ox2].copy().astype(np.float64)
    fi = _lapvar(inner)
    import cv2
    lap = cv2.Laplacian(ring, cv2.CV_64F)
    mask = np.ones_like(lap, bool)
    mask[y1 - oy1:y2 - oy1, x1 - ox1:x2 - ox1] = False
    bg = float(lap[mask].var()) if mask.sum() > 100 else None
    if fi is None or not bg or bg < 20:   # flat background: no information
        return None, None
    ratio = fi / bg
    return round(ratio, 3), float(max(0.0, min(1.0, (0.35 - ratio) / 0.25)))


def analyze_frame(pil, st):
    t0 = time.time()
    st["n"] += 1
    W, H = pil.size
    mtcnn = detector.get_mtcnn()
    boxes, probs, lms = mtcnn.detect(pil, landmarks=True)
    faces = []
    models = None
    main = None
    if boxes is not None:
        order = sorted(range(len(boxes)), key=lambda i: -(boxes[i][2] - boxes[i][0]) * (boxes[i][3] - boxes[i][1]))
        for k, i in enumerate(order[:MAX_FACES]):
            if probs[i] is not None and probs[i] < 0.90:
                continue
            b = [float(v) for v in boxes[i]]
            crop, reason = detector.face_crop_for_scoring(pil, b)
            fs = None
            if crop is not None:
                models = models or _models()
                fs, pm = _score_crop(models, crop)
                fs = round(fs, 4)
                if main is None:
                    st["permodel"].append(pm)
            faces.append({"box_rel": [max(0, b[0]) / W, max(0, b[1]) / H, (b[2] - b[0]) / W, (b[3] - b[1]) / H],
                          "fake_score": fs, "quality_issues": [reason] if reason else []})
            if main is None:
                main = (b, lms[i] if lms is not None else None, fs)

    sig = {}
    frame_score = None
    if main is not None and main[2] is not None:
        b, lm, fs = main
        frame_score = fs
        st["face_frames"] += 1
        st["scores"].append(fs)
        g = _gray(pil)
        if lm is not None:
            lm = np.asarray(lm, float)
            eye_dist, yaw, roll, geom = _pose_geom(lm)
            st["yaw"].append(yaw); st["roll"].append(roll)
            eo = _eye_openness(g, lm, eye_dist)
            if eo is not None:
                if len(st["eye"]) >= 4:
                    med = float(np.median(st["eye"]))
                    if eo < 0.62 * med:
                        st["blinks"] += 1
                        st["last_blink_t"] = time.time()
                st["eye"].append(eo)
            ident_jump = False
            if st["last_geom"] is not None:
                ident_jump = bool(np.abs(geom - st["last_geom"]).max() > 0.40)
            st["last_geom"] = geom
        else:
            ident_jump = False
        score_jump = st["last_score"] is not None and abs(fs - st["last_score"]) > 0.35
        st["last_score"] = fs
        st["jumps"].append(1.0 if ident_jump else 0.0)  # bak_cam: score-only jumps ignored (noisy face models)
        ratio, bsus = _boundary_signal(g, b)
        if bsus is not None:
            st["boundary"].append(bsus)
            st["ratio"] = ratio
    else:
        st["last_score"] = None

    # ---- session signals (each 0..1 suspicion, None = not enough data)
    n_ff = st["face_frames"]
    noblink = None
    if len(st["eye"]) >= 20:
        noblink = 1.0 if st["blinks"] == 0 else 0.0
    static = None
    if len(st["yaw"]) >= 6:
        motion = float(np.std(st["yaw"]) * 100 + np.std(st["roll"]))
        static = float(max(0.0, min(1.0, (1.0 - motion) / 1.0)))
        st["motion"] = motion
    boundary = float(np.mean(st["boundary"])) if len(st["boundary"]) >= 3 else None
    jumps = float(np.mean(st["jumps"])) if len(st["jumps"]) >= 4 else None
    aux = 0.0
    for v, w in ((boundary, W_BOUNDARY), (jumps, W_JUMP), (static, W_STATIC), (noblink, W_NOBLINK)):
        if v is not None:
            aux += w * v
    aux = min(AUX_CAP, aux)
    # whole-frame modern AI-image detector (catches fully AI-generated
    # video such as Grok/Veo where the face ensemble sees nothing)
    if st["n"] % AI_EVERY == 1:
        try:
            st["ai"].append(detector.score_image_ai_modern(pil))
        except Exception:
            pass
    ai_mean = float(np.max(st["ai"])) if len(st["ai"]) >= 2 else None
    sc = list(st["scores"])
    base = sum(sc) / len(sc) if sc else None
    smoothed = round(min(1.0, base + aux), 4) if base is not None else None
    pmm = None
    agree = False
    if len(st["permodel"]) >= 4:
        pmm = {k: float(np.mean([d[k] for d in st["permodel"]])) for k in st["permodel"][0]}
        sv = sorted(pmm.values())
        agree = sv[0] >= AGREE_MIN and sv[1] >= AGREE_MID
    capped = False
    if smoothed is not None and not agree and smoothed > FACE_ONLY_CAP:
        smoothed, capped = FACE_ONLY_CAP, True
    if ai_mean is not None and (smoothed is None or ai_mean > smoothed):
        smoothed = round(ai_mean, 4)

    signals = [
        {"key": "blink", "label": LABELS["blink"], "suspicion": noblink,
         "detail": f"{st['blinks']} lần chớp / {len(st['eye'])} khung" if st["eye"] else "chưa đủ dữ liệu"},
        {"key": "head_motion", "label": LABELS["head_motion"], "suspicion": None if static is None else round(static, 3),
         "detail": "đầu gần như đứng yên" if (static or 0) > 0.6 else ("có cử động" if static is not None else "chưa đủ dữ liệu")},
        {"key": "boundary", "label": LABELS["boundary"], "suspicion": None if boundary is None else round(boundary, 3),
         "detail": "viền mặt khác nền rõ" if (boundary or 0) > 0.5 else ("bình thường" if boundary is not None else "chưa đủ dữ liệu")},
        {"key": "jumps", "label": LABELS["jumps"], "suspicion": None if jumps is None else round(jumps, 3),
         "detail": f"{int(sum(st['jumps']))} lần nhảy / {len(st['jumps'])} khung" if st["jumps"] else "chưa đủ dữ liệu"},
        {"key": "ai_frame", "label": LABELS["ai_frame"], "suspicion": None if ai_mean is None else round(ai_mean, 3),
         "detail": f"{len(st['ai'])} lần kiểm" if st["ai"] else "chưa đủ dữ liệu"},
    ]
    # ---- 'Lý do' list: every check with its measured value + threshold
    reasons = []
    def R(text, bad, contrib): reasons.append({"text": text, "abnormal": bool(bad), "contributing": bool(contrib)})
    pc = lambda x: "–" if x is None else f"{x * 100:.0f}%"
    if sc:
        hi = sum(1 for x in sc if x >= 0.5)
        R(f"Điểm mặt bị ghép (trung vị 3 mô hình mặt) ≥ 50% ở {hi}/{len(sc)} khung gần nhất; trung bình {pc(base)}, khung này {pc(frame_score)} (thật <40%, giả >60%)",
          base >= 0.5, base >= 0.4)
        if pmm:
            names = {"deepguard": "DeepGuard", "dima806": "dima806", "prithiv_v2": "prithiv-v2"}
            txt = ", ".join(f"{names.get(k, k)} {pc(v)}" for k, v in pmm.items())
            if agree:
                R(f"Cả 3 mô hình mặt cùng nghi (TB {len(st['permodel'])} khung: {txt}; cần cả 3 ≥ 40% và 2 mô hình ≥ 60%) → xác nhận nghi ghép mặt", True, True)
            else:
                R(f"3 mô hình mặt KHÔNG đồng thuận (TB {len(st['permodel'])} khung: {txt}; cần cả 3 ≥ 40% và 2 mô hình ≥ 60%)"
                  + (f" → điểm mặt bị giới hạn ở {pc(FACE_ONLY_CAP)} (tối đa 'Không chắc chắn') vì mô hình mặt hay báo nhầm với webcam tối/mờ" if capped else " → phần mặt chưa đủ để kết luận giả"),
                  False, capped)
    else:
        R("Chưa thấy khuôn mặt đủ rõ (cần mặt ≥ 64px, không quá mờ) → chưa chấm được phần mặt", False, False)
    elapsed = time.time() - (st["last_blink_t"] or st["t0"])
    if noblink is None:
        R(f"Chớp mắt: {st['blinks']} lần trong {len(st['eye'])} khung (cần ≥ 20 khung để đánh giá; máy nhận ~1 khung/giây nên dễ lỡ cái chớp mắt)", False, False)
    elif noblink > 0:
        R(f"Chưa thấy chớp mắt trong {elapsed:.0f} giây ({len(st['eye'])} khung) (người thật thường chớp 15–20 lần/phút)", True, True)
    else:
        R(f"Chớp mắt: thấy {st['blinks']} lần, lần gần nhất cách đây {elapsed:.0f} giây → bình thường", False, False)
    if static is None:
        R("Cử động đầu: chưa đủ 6 khung để đánh giá", False, False)
    else:
        R(f"Cử động đầu (xoay ngang/nghiêng): mức {str(round(st['motion'], 2)).replace('.', ',')} (dưới 1,00 là gần như đứng yên) → {'đầu gần như đứng yên' if static > 0.5 else 'có cử động tự nhiên'}", static > 0.5, static > 0)
    if boundary is None:
        R("Độ nét viền mặt so với nền: chưa đủ dữ liệu (cần ≥ 3 khung, nền không quá trơn)", False, False)
    else:
        rt = st["ratio"]
        rtxt = f"khung này mặt nét bằng {rt * 100:.0f}% so với nền (dưới 35% là mặt mờ hơn nền)" if rt is not None else "khung này nền quá trơn"
        R(f"Độ nét vùng mặt so với nền: {rtxt}; mức nghi trung bình {len(st['boundary'])} khung {pc(boundary)} (≥ 50% mới tính là bất thường); CHỈ THAM KHẢO, không cộng điểm (với webcam thật nền thường nét hơn mặt)", boundary >= 0.5, False)
    if jumps is None:
        R("Nhảy điểm/khuôn mặt đột ngột: chưa đủ 4 khung", False, False)
    else:
        nj = int(sum(st["jumps"]))
        R(f"Khuôn mặt đổi hình dạng đột ngột (tỉ lệ mắt–miệng lệch > 40% giữa 2 khung): {nj}/{len(st['jumps'])} khung; CHỈ THAM KHẢO, không cộng điểm (điểm mô hình mặt tự dao động mạnh giữa các khung)", jumps >= 0.5, False)
    if ai_mean is None:
        R(f"Mô hình ảnh AI đời mới trên toàn khung (mỗi 3 khung): chưa đủ 2 lần kiểm ({len(st['ai'])} lần)", False, False)
    else:
        R(f"Mô hình ảnh AI đời mới trên toàn khung: cao nhất {pc(ai_mean)} trong {len(st['ai'])} lần kiểm gần nhất (ngưỡng 50%) → {'BẤT THƯỜNG' if ai_mean >= 0.5 else 'bình thường'}",
          ai_mean >= 0.5, smoothed is not None and ai_mean >= smoothed - 1e-6 and ai_mean >= 0.4)
    if aux > 0:
        R(f"Tổng cộng thêm từ các tín hiệu sống động: +{str(round(aux * 100, 1)).replace('.', ',')}% (tối đa {AUX_CAP * 100:.0f}%)", aux >= 0.05, True)
    return {"reasons": reasons, "faces": faces, "frame_score": frame_score, "face_score_mean": None if base is None else round(base, 4),
            "aux_bonus": round(aux, 4), "smoothed_score": smoothed, "window": len(sc),
            "signals": signals, "latency_s": round(time.time() - t0, 2)}
