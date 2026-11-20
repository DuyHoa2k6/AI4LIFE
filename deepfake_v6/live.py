#!/usr/bin/env python3
"""live.py — live video-call deepfake detection (CPU-only, standalone).

Samples one frame every --interval seconds from a live source and
scores it with the same detectors as check.py: the face ensemble
(DeepGuard + dima806 + prithiv v2, primary for video) and Community
Forensics on the whole frame (secondary). A rolling verdict over the
last --window scored frames is printed live, so a single odd frame
never flips the verdict.

Sources:
    webcam   the default camera (cv2.VideoCapture(0))
    screen   a region of the primary monitor (mss) — point it at the
             other person's video tile in a call. --region L,T,W,H
             (default: the whole primary monitor).
    file     a video file played at real-time speed (simulated live
             stream — for testing on this machine, which has no
             camera/display, and for checking a recorded call).

Honest limits (measured, not promised):
  - This is NEAR-real-time sampling, not 30 fps analysis. One frame
    costs ~2-4 s on a laptop CPU (MTCNN + 3 face models + CommFor),
    so --interval 3 s is the practical default. A shorter interval
    only helps if the machine keeps up; when scoring falls behind
    real time, live.py says so instead of silently lagging.
  - The verdict is the rolling mean of the face-ensemble scores over
    the last --window frames (same 0.40/0.60 bands as check.py).
    The whole-frame AI score is reported alongside and raises a
    warning when it stays high while the face score says real — it
    does NOT flip the verdict by itself (its value as a video signal
    is measured by the v5 CommFor-on-frames eval; see README).
    --verdict-mode max (verdict from the higher of the face / AI
    rolling means) is EXPERIMENTAL: on the 21-video tests23 set
    (full-video proxy, not live rolling) it changes 2 verdicts
    (recall 0.44 -> 0.50, FPR 0.14 -> 0.13) — within noise, not a
    proven gain. Default is face.
  - A face-swap keeps the source person's mouth and voice, so it
    stays in sync and looks real frame-by-frame; no frame detector
    can catch every swap. Treat the verdict as an indicator, not a
    proof (same disclaimer as check.py).

Usage:
    python live.py [--source webcam|screen|file] [--file PATH]
                   [--region L,T,W,H] [--interval SEC] [--window N]
                   [--duration SEC] [--log FILE] [--threads N]
                   [--verdict-mode face|max]
    Ctrl+C stops; a summary is printed at the end.

Examples:
    python live.py                                  # webcam, 3 s/frame
    python live.py --source screen --region 100,100,640,480
    python live.py --source file call.mp4 --duration 60
"""
import argparse
import json
import os
import sys
import time

# Thread count must be set BEFORE detector (and torch) is imported:
# detector.py defaults OMP/MKL threads to 1 via setdefault, so an
# explicit value here wins. More threads help the per-frame ViT
# forwards on a multi-core laptop; 1 thread is safest on a weak VM.
_THREADS = None


def _parse_args():
    ap = argparse.ArgumentParser(
        description="Live video-call deepfake detection (near-real-time)")
    ap.add_argument("--source", default="webcam",
                    choices=("webcam", "screen", "file"),
                    help="frame source (default: webcam)")
    ap.add_argument("--file",
                    help="video file (required with --source file)")
    ap.add_argument("--camera", type=int, default=0,
                    help="webcam device index (default 0)")
    ap.add_argument("--region", default=None,
                    help="screen region L,T,W,H (default: primary monitor)")
    ap.add_argument("--interval", type=float, default=3.0,
                    help="seconds between sampled frames (default 3.0)")
    ap.add_argument("--window", type=int, default=5,
                    help="rolling-verdict window in frames (default 5)")
    ap.add_argument("--duration", type=float, default=0,
                    help="stop after N seconds (0 = until Ctrl+C)")
    ap.add_argument("--log", default=None,
                    help="append per-frame JSON lines to FILE")
    ap.add_argument("--threads", type=int, default=2,
                    help="torch threads for the models (default 2)")
    ap.add_argument("--verdict-mode", default="face",
                    choices=("face", "max"),
                    help="face = verdict from the face rolling mean "
                         "(default); max = verdict from the higher of "
                         "the face / whole-frame rolling means")
    ap.add_argument("--no-ai-image", action="store_true",
                    help="skip the whole-frame CommFor score (faster)")
    return ap.parse_args()


def _now():
    return time.strftime("%H:%M:%S")


def _score_frame(pil_img, args, models):
    """Score one PIL frame -> dict with face/ai scores and timings.

    models is a dict of pre-loaded model objects (kept resident across
    frames — the per-call load/unload in detector.score_crops would
    re-read 2x343 MB of ViT weights for every single frame).
    Returns None when the frame has no usable face (face_score None)
    but still reports the whole-frame AI score when enabled.
    """
    import detector
    t0 = time.time()
    face_score = None
    face_ms = None
    found = detector.detect_largest_face_landmarks(pil_img)
    if found is not None:
        box, _prob, landmarks = found
        crop, reason = detector.face_crop_for_scoring(pil_img, box)
        if crop is not None:
            rec = {"timestamp": 0.0, "face_size": 0, "luminance": 0.0,
                   "frontality": None, "scores": {}}
            rec["scores"]["deepguard"] = detector.score_face_crop(
                models["deepguard"], crop)
            for name in ("dima806", "prithiv_v2"):
                model, fake_index = models[name]
                rec["scores"][name] = detector.score_crop_vit(
                    model, fake_index, crop)
            face_score = detector._frame_combined(
                rec, detector.AGGREGATION)
            face_ms = round((time.time() - t0) * 1000)
    ai_score = None
    ai_ms = None
    if not args.no_ai_image:
        t1 = time.time()
        ai_score = detector.score_image_ai(pil_img)
        ai_ms = round((time.time() - t1) * 1000)
    return {"face_score": (round(face_score, 4)
                           if face_score is not None else None),
            "face_ms": face_ms,
            "ai_score": (round(ai_score, 4)
                         if ai_score is not None else None),
            "ai_ms": ai_ms}


def _rolling_mean(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def main():
    global _THREADS
    args = _parse_args()
    os.environ["OMP_NUM_THREADS"] = str(args.threads)
    os.environ["MKL_NUM_THREADS"] = str(args.threads)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import detector

    if args.source == "file" and not args.file:
        print("ERROR: --source file needs --file PATH", file=sys.stderr)
        sys.exit(2)
    if args.source == "file" and not os.path.exists(args.file):
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    # --- open the source ---
    cap = None
    sct = None
    region = None
    if args.source == "webcam":
        import cv2
        cap = cv2.VideoCapture(args.camera)
        if not cap.isOpened():
            print(f"ERROR: cannot open webcam {args.camera}",
                  file=sys.stderr)
            sys.exit(3)
        print(f"[{_now()}] source: webcam {args.camera}")
    elif args.source == "screen":
        import mss
        sct = mss.mss()
        if args.region:
            try:
                left, top, w, h = (int(v) for v in
                                   args.region.split(","))
            except ValueError:
                print("ERROR: --region must be L,T,W,H", file=sys.stderr)
                sys.exit(2)
            region = {"left": left, "top": top, "width": w, "height": h}
        else:
            region = sct.monitors[1]
        print(f"[{_now()}] source: screen region {region}")
    else:
        import cv2
        cap = cv2.VideoCapture(args.file)
        if not cap.isOpened():
            print(f"ERROR: cannot open video: {args.file}",
                  file=sys.stderr)
            sys.exit(3)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        print(f"[{_now()}] source: file {args.file} "
              f"(simulated live, {fps:.1f} fps)")

    # --- warm up the models once (first frame pays the load cost) ---
    print(f"[{_now()}] loading models (first run downloads nothing; "
          f"weights come from weights/) ...", flush=True)
    t_load = time.time()
    models = {
        "deepguard": detector.get_deepguard(),
        "dima806": detector.get_vit_model("dima806"),
        "prithiv_v2": detector.get_vit_model("prithiv_v2"),
    }
    if not args.no_ai_image:
        detector.get_commfor()
    print(f"[{_now()}] models ready in {time.time() - t_load:.1f}s "
          f"(face ensemble: {detector.MODEL_NAME}; whole-frame: "
          f"{detector.COMMFOR_MODEL_NAME})", flush=True)
    print(f"[{_now()}] sampling every {args.interval}s, rolling window "
          f"{args.window} frames, verdict mode: {args.verdict_mode}. "
          f"Ctrl+C to stop.", flush=True)

    log_f = open(args.log, "a") if args.log else None
    from PIL import Image
    import numpy as np
    import cv2

    face_hist, ai_hist = [], []
    n_frames = n_no_face = 0
    t_start = time.time()
    next_sample_at = t_start
    behind_warned = False
    try:
        while True:
            if args.duration and time.time() - t_start >= args.duration:
                break
            # --- grab one frame ---
            frame = None
            if args.source == "webcam":
                ok, bgr = cap.read()
                if not ok:
                    print(f"[{_now()}] webcam read failed, stopping",
                          file=sys.stderr)
                    break
                frame = Image.fromarray(
                    cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            elif args.source == "screen":
                shot = sct.grab(region)
                frame = Image.fromarray(
                    np.array(shot)[:, :, :3][:, :, ::-1].copy())
                # mss gives BGRA; [:, :, ::-1] flips to RGB and the
                # copy() makes it a fresh array (no shared buffer)
            else:
                # file source: simulated live stream — seek to the
                # frame at the CURRENT video time (elapsed wall time
                # since start), so the sampled frames track real time
                # instead of crawling sequentially from frame 0 (a
                # 25 fps video would otherwise take 25x longer than
                # real time to cover). If the seek lands past the end,
                # stop.
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                target = int((time.time() - t_start) * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, target)
                ok, bgr = cap.read()
                if not ok:
                    print(f"[{_now()}] end of file", flush=True)
                    break
                frame = Image.fromarray(
                    cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            # --- score it ---
            t_frame = time.time()
            res = _score_frame(frame, args, models)
            n_frames += 1
            if res["face_score"] is None:
                n_no_face += 1
            face_hist.append(res["face_score"])
            ai_hist.append(res["ai_score"])
            face_hist = face_hist[-args.window:]
            ai_hist = ai_hist[-args.window:]
            face_roll = _rolling_mean(face_hist)
            ai_roll = _rolling_mean(ai_hist)
            if args.verdict_mode == "max":
                cands = [v for v in (face_roll, ai_roll)
                         if v is not None]
                verdict_score = max(cands) if cands else None
            else:
                verdict_score = face_roll
            verdict = detector.verdict_from_score(verdict_score)
            warn = ""
            if (face_roll is not None and ai_roll is not None
                    and ai_roll > 0.6 and face_roll < 0.4):
                warn = "  <-- WARNING: whole-frame AI signal high, " \
                       "face says real"
            line = (f"[{_now()}] #{n_frames} face="
                    f"{res['face_score'] if res['face_score'] is not None else '-'} "
                    f"(roll {face_roll:.3f})" if face_roll is not None
                    else f"[{_now()}] #{n_frames} face=- (roll -)")
            if not args.no_ai_image:
                line += (f" ai={res['ai_score']} "
                         f"(roll {ai_roll:.3f})" if ai_roll is not None
                         else f" ai={res['ai_score']} (roll -)")
            line += f" verdict={verdict}{warn}"
            face_ms_s = (f"{res['face_ms']}ms"
                         if res["face_ms"] is not None else "-")
            ai_ms_s = (f"+{res['ai_ms']}ms" if res["ai_ms"] else "")
            line += f" [{face_ms_s}{ai_ms_s}]"
            print(line, flush=True)
            if log_f:
                log_f.write(json.dumps({
                    "t": _now(), "frame": n_frames,
                    "face_score": res["face_score"],
                    "ai_score": res["ai_score"],
                    "face_roll": (round(face_roll, 4)
                                  if face_roll is not None else None),
                    "ai_roll": (round(ai_roll, 4)
                                if ai_roll is not None else None),
                    "verdict": verdict,
                    "face_ms": res["face_ms"],
                    "ai_ms": res["ai_ms"],
                }) + "\n")
                log_f.flush()
            # --- pace the next sample ---
            next_sample_at += args.interval
            wait = next_sample_at - time.time()
            if wait < -args.interval:
                if not behind_warned:
                    print(f"[{_now()}] NOTE: scoring is slower than "
                          f"real time (a frame costs more than "
                          f"{args.interval}s) — increase --interval",
                          flush=True)
                    behind_warned = True
                next_sample_at = time.time() + args.interval
                wait = args.interval
            if wait > 0:
                time.sleep(wait)
    except KeyboardInterrupt:
        print(f"\n[{_now()}] stopped by user", flush=True)
    finally:
        if cap is not None:
            cap.release()
        if sct is not None:
            sct.close()
        if log_f:
            log_f.close()
    elapsed = time.time() - t_start
    face_vals = [v for v in face_hist if v is not None]
    print(f"[{_now()}] SUMMARY: {n_frames} frames in {elapsed:.0f}s "
          f"({n_no_face} with no usable face); "
          f"mean face score "
          f"{sum(face_vals) / len(face_vals):.4f}" if face_vals else
          f"[{_now()}] SUMMARY: {n_frames} frames in {elapsed:.0f}s "
          f"({n_no_face} with no usable face); no face scored",
          flush=True)
    print(detector.DISCLAIMER, flush=True)


if __name__ == "__main__":
    main()
