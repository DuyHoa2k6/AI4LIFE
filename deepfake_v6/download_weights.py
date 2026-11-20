#!/usr/bin/env python3
"""download_weights.py — fetch model weights (and the AASIST model source)
on first run. Stdlib only (urllib).

No Hugging Face hub client, no transformers: the HF hub client stalls on
restricted networks, while direct HTTPS downloads from the same hosts
work fine (verified on 2026-11-19).

Files fetched (total 1,967,043,794 bytes = ~1.97 GB):

    weights/ms_eff_gcvit_b0_ff++.bin
        DeepGuard ms_eff_gcvit_b0 head weights, trained on FaceForensics++
        (c23). Source: the weight registry inside the installed deepguard
        package (HanMoonSub/DeepGuard release v0.1.0).
    weights/tf_efficientnet_b0_ns-c0e6a31c.pth
        timm EfficientNet-B0 backbone (tf_efficientnet_b0.ns_jft_in1k)
        that DeepGuard's FeatExtractor loads with pretrained=True.
        Source: the URL baked into timm's efficientnet model definition.
    weights/AASIST.pth
        AASIST voice-spoof weights (clovaai/aasist repo, models/weights/).
    aasist/models/AASIST.py + aasist/config/AASIST.conf
        AASIST model source + config from the same repo. The light zip
        ships code only, so the model source is fetched here too (19 KB).
        Without these two files the .wav check cannot run; image/video
        checks do not need them.
    weights/dima806/{model.safetensors, config.json,
                      preprocessor_config.json}
        dima806/deepfake_vs_real_image_detection (ViT-base, Apache-2.0),
        trained on GAN-generated faces. 343,223,968 bytes for the weights.
    weights/prithiv_v2/{model.safetensors, config.json,
                        preprocessor_config.json}
        prithivMLmods/Deep-Fake-Detector-v2-Model (ViT-base, Apache-2.0),
        trained on GAN-generated faces. 343,223,968 bytes for the weights.
    weights/syncnet_v2.model (54,573,114 bytes) + weights/sfd_face.pth
        (89,844,381 bytes)
        SyncNet (Oxford) lip-sync model + S3FD face detector, for the
        audio-visual mismatch flag (av_sync). Weights: CC-BY, research
        purposes only. Source: Oxford VGG lipsync data page. These are
        only loaded when a video has an audio stream; they are never
        blended into the face-score mean.
    weights/commfor-model-384.safetensors (87,262,324 bytes)
        Community Forensics whole-image AI-generation detector
        (OwensLab/commfor-model-384, ViT-S, MIT license), trained on
        2.7M images from 4,803 generators. Scores the WHOLE image
        (ai_image_score) instead of a face crop. Source: Hugging Face
    weights/DeCoF.tar (56,815,450 bytes)
        DeCoF video-detection head (2 transformer layers + MLP over
        frozen CLIP ViT-L/14 frame features), retrained 2026-02-28 on
        the updated AIGVDBench dataset — the ORIGINAL weights were lost
        in a server migration, so these are NOT the arXiv paper's
        weights. NOTE: the file is a PyTorch checkpoint (zip format)
        despite the .tar name. LICENSE UNVERIFIED: no license file was
        found in the DeCoF repo or the AIGVDBench dataset repo — see
        README. The head alone is useless without the CLIP backbone
        below; it is loaded as a clearly-marked component.
    weights/ViT-L-14.pt (932,768,134 bytes)
        OpenAI CLIP ViT-L/14 (full model incl. text encoder — only the
        vision encoder is used), the frozen backbone for DeCoF.
        TorchScript archive from OpenAI's CDN. Loaded with
        torch.jit.load, cast to float32 (as clip.load does).

The two ViT models are ensemble members alongside DeepGuard (see
detector.py). Their label mappings differ and are resolved BY NAME
from each config.json at load time (dima806 {0: Real, 1: Fake},
prithiv v2 {0: Realism, 1: Deepfake}) — never hard-code an index.

Existing files with the right size are skipped. A partial download is
resumed with HTTP Range when the server allows it, otherwise restarted.
detector.py calls ensure_weights() automatically when a needed file is
missing, so plain `python check.py <file>` works on a fresh machine;
running this script directly just does the download up front.

Usage:
    python download_weights.py [--force]
"""
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# (relative path, download URL, expected size in bytes, description)
FILES = [
    ("weights/ms_eff_gcvit_b0_ff++.bin",
     "https://github.com/HanMoonSub/DeepGuard/releases/download/"
     "v0.1.0/ms_eff_gcvit_b0_ff++.bin",
     36642117,
     "DeepGuard ms_eff_gcvit_b0 head weights (FaceForensics++ c23)"),
    ("weights/tf_efficientnet_b0_ns-c0e6a31c.pth",
     "https://github.com/rwightman/pytorch-image-models/releases/"
     "download/v0.1-weights/tf_efficientnet_b0_ns-c0e6a31c.pth",
     21386709,
     "timm EfficientNet-B0 backbone (tf_efficientnet_b0.ns_jft_in1k)"),
    ("weights/AASIST.pth",
     "https://raw.githubusercontent.com/clovaai/aasist/main/"
     "models/weights/AASIST.pth",
     1281532,
     "AASIST voice-spoof weights (clovaai/aasist)"),
    ("aasist/models/AASIST.py",
     "https://raw.githubusercontent.com/clovaai/aasist/main/"
     "models/AASIST.py",
     18960,
     "AASIST model source (clovaai/aasist)"),
    ("aasist/config/AASIST.conf",
     "https://raw.githubusercontent.com/clovaai/aasist/main/"
     "config/AASIST.conf",
     997,
     "AASIST model config (clovaai/aasist)"),
    ("weights/dima806/model.safetensors",
     "https://huggingface.co/dima806/deepfake_vs_real_image_detection/"
     "resolve/main/model.safetensors",
     343223968,
     "dima806 deepfake-vs-real ViT weights (HF, Apache-2.0)"),
    ("weights/dima806/config.json",
     "https://huggingface.co/dima806/deepfake_vs_real_image_detection/"
     "resolve/main/config.json",
     726,
     "dima806 model config (label map: 0 Real, 1 Fake)"),
    ("weights/dima806/preprocessor_config.json",
     "https://huggingface.co/dima806/deepfake_vs_real_image_detection/"
     "resolve/main/preprocessor_config.json",
     325,
     "dima806 image preprocessor config (mean/std 0.5)"),
    ("weights/prithiv_v2/model.safetensors",
     "https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model/"
     "resolve/main/model.safetensors",
     343223968,
     "prithiv Deep-Fake-Detector v2 ViT weights (HF, Apache-2.0)"),
    ("weights/prithiv_v2/config.json",
     "https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model/"
     "resolve/main/config.json",
     738,
     "prithiv v2 model config (label map: 0 Realism, 1 Deepfake)"),
    ("weights/prithiv_v2/preprocessor_config.json",
     "https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model/"
     "resolve/main/preprocessor_config.json",
     351,
     "prithiv v2 image preprocessor config (mean/std 0.5)"),
    ("weights/syncnet_v2.model",
     "https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/"
     "syncnet_v2.model",
     54573114,
     "SyncNet lip-sync model (Oxford VGG, CC-BY research-only)"),
    ("weights/sfd_face.pth",
     "https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/"
     "sfd_face.pth",
     89844381,
     "S3FD face detector weights for SyncNet (Oxford VGG)"),
    ("weights/commfor-model-384.safetensors",
     "https://huggingface.co/OwensLab/commfor-model-384/"
     "resolve/main/model.safetensors",
     87262324,
     "Community Forensics whole-image AI detector (ViT-S, MIT)"),
    ("weights/DeCoF.tar",
     "https://huggingface.co/datasets/AIGVDBench/AIGVDBench/"
     "resolve/main/Weights/DeCoF.tar",
     56815450,
     "DeCoF video-detection head (2026 retrain; LICENSE UNVERIFIED)"),
    ("weights/ViT-L-14.pt",
     "https://openaipublic.azureedge.net/clip/models/"
     "b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/"
     "ViT-L-14.pt",
     932768134,
     "OpenAI CLIP ViT-L/14 (frozen backbone for DeCoF)"),
]

TOTAL_BYTES = sum(size for _p, _u, size, _d in FILES)
USER_AGENT = "deepfake-detector/3.0 (urllib)"
CHUNK = 1024 * 1024  # 1 MB reads
MAX_ATTEMPTS = 3


def _human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def _download_one(url, dest, expected_size):
    """Download url -> dest (resuming a .part file when possible).

    Returns True if the file was downloaded, False if it already existed
    with the right size. Raises on failure after MAX_ATTEMPTS attempts.
    """
    if os.path.exists(dest) and os.path.getsize(dest) == expected_size:
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        resume_from = os.path.getsize(tmp) if os.path.exists(tmp) else 0
        if resume_from >= expected_size:
            os.replace(tmp, dest)
            return True
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        if resume_from > 0:
            req.add_header("Range", f"bytes={resume_from}-")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                status = resp.status
                if status == 206:
                    mode = "ab"  # resume accepted
                elif status == 200 and resume_from > 0:
                    # Server ignored Range: restart from scratch.
                    resume_from = 0
                    mode = "wb"
                elif status == 200:
                    mode = "wb"
                else:
                    raise RuntimeError(f"HTTP {status}")
                done = resume_from
                last_pct = done * 100 // expected_size
                with open(tmp, mode) as f:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        pct = done * 100 // expected_size
                        if pct >= last_pct + 10:
                            last_pct = pct
                            print(f"  ... {pct}% ({_human(done)} / "
                                  f"{_human(expected_size)})", flush=True)
            if os.path.getsize(tmp) != expected_size:
                raise RuntimeError(
                    f"size mismatch: got {os.path.getsize(tmp)} bytes, "
                    f"expected {expected_size}")
            os.replace(tmp, dest)
            return True
        except Exception as e:
            print(f"  attempt {attempt}/{MAX_ATTEMPTS} failed: {e}",
                  flush=True)
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(
                    f"could not download {url} after {MAX_ATTEMPTS} "
                    f"attempts: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError("unreachable")


def ensure_weights(verbose=True):
    """Download every missing weight/source file. Returns (downloaded, skipped)."""
    downloaded, skipped = [], []
    for rel, url, size, desc in FILES:
        dest = os.path.join(HERE, rel)
        if verbose:
            print(f"[{rel}] {desc} ({_human(size)})")
        if os.path.exists(dest) and os.path.getsize(dest) == size:
            if verbose:
                print("  already present, skipping")
            skipped.append(rel)
            continue
        if verbose:
            print(f"  downloading from {url}")
        _download_one(url, dest, size)
        if verbose:
            print("  done")
        downloaded.append(rel)
    if verbose:
        print(f"weights ready: {len(downloaded)} downloaded, "
              f"{len(skipped)} already present "
              f"(total {_human(TOTAL_BYTES)})")
    return downloaded, skipped


def main():
    force = "--force" in sys.argv
    if force:
        for rel, _u, _s, _d in FILES:
            for suffix in ("", ".part"):
                p = os.path.join(HERE, rel + suffix)
                if os.path.exists(p):
                    os.remove(p)
        print("forced re-download of all files")
    print(f"Deepfake Detector — downloading weights "
          f"(total {_human(TOTAL_BYTES)})")
    try:
        ensure_weights()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Check your network connection and run this script again; "
              "partial downloads resume automatically.", file=sys.stderr)
        sys.exit(1)
    print("All weights present. You can now run: "
          "python check.py <image/video/.wav>")


if __name__ == "__main__":
    main()
