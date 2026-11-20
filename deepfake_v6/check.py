#!/usr/bin/env python3
"""check.py — deepfake detector CLI (CPU-only, standalone).

Usage:
    python check.py <file> [--json] [--max-frames N] [--no-av]
                    [--ai-video] [--threads N]

    <file>.png/.jpg/.jpeg/.webp/.bmp  -> ensemble on the largest face crop
    <file>.mp4/.webm/.mov/.avi        -> ensemble on up to 32 sampled frames
    <file>.wav                          -> AASIST voice-spoof check

Image/video: the largest face in each frame is cropped with a 30% margin
and scored by an ensemble of three models on the SAME crop — DeepGuard
ms_eff_gcvit_b0 (FaceForensics++ c23) with weight 0.8, plus
dima806/deepfake_vs_real_image_detection and
prithivMLmods/Deep-Fake-Detector-v2-Model (ViT-base, GAN faces) with
weight 0.1 each (see detector.py AGGREGATION). Frames with no face, a
face under 64 px, or a blurry face are skipped, never scored. Video
verdicts use the weighted per-frame ensemble score averaged over
scored face frames (<0.40 likely_real, 0.40-0.60 uncertain, >0.60
likely_fake); fewer than 5 scored face frames gives cannot_assess.
Audio verdicts use the same bands on P(spoof) from AASIST.

Videos also get two SEPARATE audio-visual fields (never blended into
the face score): av_sync (SyncNet LSE-C/LSE-D lip-sync check — only
flags dubbed/cloned voice, not face-swaps) and audio_spoof (AASIST
run on the video's own audio track). An UNCERTAIN face verdict is
pushed to likely_fake only when SyncNet LSE-C is at or below the
calibrated real-video baseline (see detector.py). --no-av skips the
audio-visual pass (faster; face verdict only). Videos also get the
separate whole-frame field ai_video_score (Community Forensics
P(AI-generated) on 8 whole frames, mean aggregate — always on; it
replaced DeCoF in v5: same 220 videos, AUROC 0.96 vs 0.62, FPR 0.00
vs 0.26, recall@0.5 0.71 vs 0.22; separate field, never changes the
face verdict by itself). --ai-video adds the DeCoF score as a further
diagnostic field decof_score (off by default because it costs
~44s/video plus a 933 MB CLIP load and the 2026-retrain checkpoint
does not separate AI from real video).

Still images also get a SEPARATE whole-image field, ai_image_score
(Community Forensics P(AI-generated) on the full 384x384 image —
never blended into the face score). For STILL IMAGES the verdict
comes from ai_image_score (the whole-image detector is primary —
measured on WasItAI: AUROC 0.896 vs 0.590, FPR 0.047 vs 0.419 for the
face ensemble on face images; see README); the face-ensemble score is
kept as a secondary field (face_score / face_verdict) because it is
the only detector here that can catch a face-swap inside an otherwise
real photo.

--json prints only the JSON result object. Without it, a short human
summary is printed, then the JSON object.
"""
import argparse
import json
import os
import sys

# --threads must be honoured BEFORE detector (and torch) is imported:
# detector.py defaults OMP/MKL threads to 1 via setdefault, so an
# explicit value on the command line wins. Parse it out of sys.argv
# here, before the import below.
def _threads_from_argv():
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--threads" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--threads="):
            return a.split("=", 1)[1]
    return None


_threads = _threads_from_argv()
if _threads is not None:
    os.environ["OMP_NUM_THREADS"] = _threads
    os.environ["MKL_NUM_THREADS"] = _threads

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import detector  # noqa: E402


def _human_summary(res):
    lines = [
        f"file: {res['file']} ({res['kind']}, model: {res['model']})",
    ]
    if res["kind"] in ("image", "video"):
        lines.append(
            f"frames: sampled {res['frames_total_sampled']}, "
            f"scored {res['frames_scored']}, skipped "
            f"no-face {res['frames_skipped_no_face']} / "
            f"small {res['frames_skipped_small']} / "
            f"blurry {res['frames_skipped_blurry']}")
    if res["score"] is None:
        lines.append("verdict: cannot_assess "
                     "(not enough usable face frames)")
    else:
        lines.append(
            f"score P(fake) = {res['score']:.4f} "
            f"(median {res['median_score']:.4f})  "
            f"verdict: {res['verdict']}")
    if res["top_suspicious"]:
        top = ", ".join(
            f"{t['timestamp']}s: {t['score']:.2f}"
            for t in res["top_suspicious"])
        lines.append(f"most suspicious frames: {top}")
    if res.get("ai_image_score") is not None:
        lines.append(
            f"ai_image_score: P(AI-generated, whole image) = "
            f"{res['ai_image_score']:.4f} "
            f"(verdict: "
            f"{detector.verdict_from_score(res['ai_image_score'])})")
    if res.get("face_score") is not None and res["kind"] == "image":
        lines.append(
            f"face_score (secondary): P(fake, face crop) = "
            f"{res['face_score']:.4f} "
            f"(verdict: {res.get('face_verdict')})")
    if res.get("ai_video_score") is not None:
        lines.append(
            f"ai_video_score: P(AI-generated, whole frames, "
            f"Community Forensics) = "
            f"{res['ai_video_score']:.4f} "
            f"(verdict: "
            f"{detector.verdict_from_score(res['ai_video_score'])}) "
            f"[separate field — does not change the face verdict]")
    if res.get("decof_score") is not None:
        lines.append(
            f"decof_score: P(fake, whole frames, DeCoF) = "
            f"{res['decof_score']:.4f} "
            f"[diagnostic only — DeCoF failed the adoption rule "
            f"(AUROC 0.62, FPR 0.26) and never changes the verdict]")
    if res.get("av_sync") is not None:
        av = res["av_sync"]
        lines.append(
            f"av_sync: LSE-C={av['lse_c']} LSE-D={av['lse_d']} "
            f"offset={av['offset_frames']} frames tracks={av['n_tracks']}"
            + (" [gate applied]" if res.get("av_sync_gate_applied")
               else ""))
    if res.get("audio_spoof") is not None:
        au = res["audio_spoof"]
        lines.append(
            f"audio_spoof: P(spoof)={au['p_spoof']:.4f} "
            f"verdict: {au['verdict']}")
    if res.get("duration_sec"):
        lines.append(f"duration: {res['duration_sec']}s, "
                     f"elapsed: {res.get('elapsed_sec')}s")
    lines.append(res["disclaimer"])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="Deepfake check: image/video (DeepGuard) or WAV (AASIST)")
    ap.add_argument("file", help="image, video or .wav file to check")
    ap.add_argument("--json", action="store_true",
                    help="print only the JSON result object")
    ap.add_argument("--max-frames", type=int,
                    default=detector.MAX_VIDEO_FRAMES,
                    help="max frames scored per video (default 32)")
    ap.add_argument("--no-av", action="store_true",
                    help="skip the SyncNet + audio-spoof pass on videos "
                         "(faster; face verdict only)")
    ap.add_argument("--ai-video", action="store_true",
                    help="also run DeCoF (whole-frame video AI score, "
                         "diagnostic only — it never changes the verdict; "
                         "off by default: it costs ~44s/video plus a "
                         "933 MB CLIP load and the 2026-retrain "
                         "checkpoint does not separate AI from real "
                         "video, see README)")
    ap.add_argument("--threads", type=int, default=None,
                    help="torch threads for the models (default 1; "
                         "2-4 can speed up the ViT forwards on a "
                         "multi-core laptop)")
    args = ap.parse_args()
    if not os.path.exists(args.file):
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)
    try:
        res = detector.check_file(args.file, args.max_frames,
                                  run_av=not args.no_av,
                                  run_decof=args.ai_video)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)
    if args.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        print(_human_summary(res))
        print(json.dumps(res, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
