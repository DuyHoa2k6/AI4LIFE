#!/usr/bin/env python3
"""evaluate.py — benchmark the detector on two folders of samples.

Usage:
    python evaluate.py <real_dir> <fake_dir> [--max-frames N]
                       [--jobs N] [--out results.json] [--no-av]

Every video/image/audio file in <real_dir> is labelled real (negative)
and every file in <fake_dir> is labelled fake (positive). Each file is
checked with the same logic as check.py (face ensemble + SyncNet AV
flag + audio spoof on the video's own track, unless --no-av).

Verdict mapping for the metrics:
    likely_fake -> positive prediction, likely_real -> negative prediction.
    uncertain and cannot_assess are NOT counted as right or wrong: their
    counts are reported separately, and accuracy/precision/recall/F1/AUC
    are computed only on the decided files. AUC uses the raw score of the
    decided files (sklearn roc_auc_score); it is reported as n/a when a
    class has no decided files.

Also printed: confusion matrix (TP/FP/TN/FN), false-positive rate on
real files (FP / decided real files), average time per file, and a
per-file table (file, true label, verdict, score, frames scored,
SyncNet LSE-C, audio P(spoof), SyncNet gate applied).

--jobs runs files in parallel worker processes (spawn; each worker
imports the models fresh). Use it for the SyncNet pass, which costs
roughly 2-4x video duration on CPU. --out saves every per-file result
dict to a JSON file (same content as check.py --json, plus true_label).
"""
import argparse
import glob
import json
import os
import sys
import time
from multiprocessing import get_context

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import detector  # noqa: E402

EXTS = detector.IMAGE_EXTS | detector.VIDEO_EXTS | detector.AUDIO_EXTS


def _collect(folder):
    files = []
    for ext in sorted(EXTS):
        files.extend(glob.glob(os.path.join(folder, "*" + ext)))
        files.extend(glob.glob(os.path.join(folder, "*" + ext.upper())))
    return sorted(set(files))


def _check_one(job):
    """Worker entry point: (path, label, max_frames, run_av) -> result dict.

    Top-level (picklable) so multiprocessing spawn workers can call it.
    Each worker imports detector fresh, so models load once per worker.
    """
    path, label, max_frames, run_av = job
    t0 = time.time()
    try:
        res = detector.check_file(path, max_frames, run_av=run_av)
    except Exception as e:  # noqa: BLE001 - one bad file must not kill the run
        res = {"file": os.path.basename(path), "verdict": "error",
               "score": None, "frames_scored": 0, "av_sync": None,
               "audio_spoof": None, "av_sync_gate_applied": False,
               "error": str(e)}
    res["true_label"] = label
    res["elapsed_sec"] = round(time.time() - t0, 2)
    return res


def compute_metrics(rows):
    """rows: list of result dicts with true_label/verdict/score.

    Returns a dict with accuracy/precision/recall/F1/AUC (decided files
    only), confusion counts, FPR on real files, undecided/error counts
    and average time. Mirrors the printed report exactly.
    """
    decided = [r for r in rows
               if r["verdict"] in ("likely_fake", "likely_real")]
    undecided = [r for r in rows
                 if r["verdict"] in ("uncertain", "cannot_assess")]
    errors = [r for r in rows if r["verdict"] == "error"]
    tp = sum(1 for r in decided
             if r["true_label"] == 1 and r["verdict"] == "likely_fake")
    fn = sum(1 for r in decided
             if r["true_label"] == 1 and r["verdict"] == "likely_real")
    tn = sum(1 for r in decided
             if r["true_label"] == 0 and r["verdict"] == "likely_real")
    fp = sum(1 for r in decided
             if r["true_label"] == 0 and r["verdict"] == "likely_fake")
    n_decided = len(decided)
    acc = (tp + tn) / n_decided if n_decided else None
    prec = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * prec * rec / (prec + rec)
          if prec is not None and rec is not None and (prec + rec) else None)
    auc = None
    if len({r["true_label"] for r in decided}) == 2:
        from sklearn.metrics import roc_auc_score
        auc = float(roc_auc_score([r["true_label"] for r in decided],
                                  [r["score"] for r in decided]))
    real_decided = [r for r in decided if r["true_label"] == 0]
    fpr = (fp / len(real_decided)) if real_decided else None
    avg_time = (sum(r.get("elapsed_sec", 0) for r in rows) / len(rows)
                if rows else None)
    return {"n_real": sum(1 for r in rows if r["true_label"] == 0),
            "n_fake": sum(1 for r in rows if r["true_label"] == 1),
            "n_total": len(rows), "decided": n_decided,
            "undecided": len(undecided), "errors": len(errors),
            "accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
            "auc": auc, "tp": tp, "fn": fn, "tn": tn, "fp": fp,
            "fpr": fpr, "avg_time_sec": avg_time,
            "undecided_files": [(r["file"], r["true_label"],
                                 r["verdict"], r["score"])
                                for r in undecided]}


def main():
    ap = argparse.ArgumentParser(
        description="Benchmark the deepfake detector on real/ vs fake/ folders")
    ap.add_argument("real_dir", help="folder of genuine (real) samples")
    ap.add_argument("fake_dir", help="folder of deepfake samples")
    ap.add_argument("--max-frames", type=int,
                    default=detector.MAX_VIDEO_FRAMES,
                    help="max frames scored per video (default 32)")
    ap.add_argument("--jobs", type=int, default=1,
                    help="parallel worker processes (default 1)")
    ap.add_argument("--out",
                    help="save every per-file result dict to this JSON file")
    ap.add_argument("--no-av", action="store_true",
                    help="skip the SyncNet + audio-spoof pass "
                         "(faster; face verdict only)")
    args = ap.parse_args()
    for d in (args.real_dir, args.fake_dir):
        if not os.path.isdir(d):
            print(f"ERROR: not a directory: {d}", file=sys.stderr)
            sys.exit(2)

    jobs = []
    for label, folder in ((0, args.real_dir), (1, args.fake_dir)):
        for path in _collect(folder):
            jobs.append((path, label, args.max_frames, not args.no_av))
    print(f"files: {len(jobs)} (jobs={args.jobs}, "
          f"av={'off' if args.no_av else 'on'})", flush=True)

    if args.jobs > 1:
        ctx = get_context("spawn")
        with ctx.Pool(args.jobs) as pool:
            results = pool.map(_check_one, jobs)
    else:
        results = [_check_one(j) for j in jobs]

    for res in results:
        av = res.get("av_sync") or {}
        au = res.get("audio_spoof") or {}
        print(f"  {res['file']:38s} "
              f"true={'fake' if res['true_label'] else 'real':4s} "
              f"verdict={res['verdict']:14s} score={res['score']} "
              f"frames={res['frames_scored']} "
              f"lse_c={av.get('lse_c')} "
              f"audio_spoof={au.get('p_spoof')} "
              f"gate={res.get('av_sync_gate_applied')} "
              f"{res.get('elapsed_sec', 0):.1f}s", flush=True)
        if res["verdict"] == "error":
            print(f"    ! ERROR {res.get('error')}", file=sys.stderr)

    m = compute_metrics(results)

    def _fmt(v, nd=4):
        return f"{v:.{nd}f}" if v is not None else "n/a"

    print()
    print(f"files: real={m['n_real']} fake={m['n_fake']} "
          f"total={m['n_total']} | decided={m['decided']} "
          f"undecided={m['undecided']} (uncertain/cannot_assess) "
          f"errors={m['errors']}")
    print("=== metrics (decided files only) ===")
    print(f"accuracy : {_fmt(m['accuracy'])}")
    print(f"precision: {_fmt(m['precision'])}")
    print(f"recall   : {_fmt(m['recall'])}")
    print(f"F1       : {_fmt(m['f1'])}")
    print(f"AUC      : {_fmt(m['auc'])}")
    print("=== confusion matrix (decided files only) ===")
    print(f"TP (fake called fake)   : {m['tp']}")
    print(f"FN (fake called real)   : {m['fn']}")
    print(f"TN (real called real)   : {m['tn']}")
    print(f"FP (real called fake)   : {m['fp']}")
    print(f"false-positive rate on real files: {_fmt(m['fpr'])}")
    print(f"average time per file: "
          f"{m['avg_time_sec']:.1f}s" if m['avg_time_sec'] is not None
          else "n/a")
    if m["undecided_files"]:
        print("undecided files (not counted as right or wrong):")
        for f, y, v, s in m["undecided_files"]:
            print(f"  {f} (true {'fake' if y else 'real'}): "
                  f"{v}, score={s}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"metrics": m, "results": results}, f, indent=1)
        print(f"results saved to {args.out}")


if __name__ == "__main__":
    main()
