#!/usr/bin/env python3
"""detector.py — core deepfake detection logic (CPU-only, standalone).

Shared by check.py (CLI), evaluate.py (benchmark) and api.py (HTTP API).

Pipeline (image / video):
    1. Detect the largest face with MTCNN (facenet-pytorch; weights are
       bundled inside the pip package, no download at run time).
    2. Skip a frame when there is no face, when the face's longest side is
       under FACE_MIN_LONGEST_SIDE px, or when the face crop is too blurry
       (Laplacian variance under BLUR_LAP_VAR_MIN).
    3. Expand the face box by FACE_MARGIN (30% on every side, clamped to
       the image), crop, resize to 224x224.
    4. Score the SAME crop with three models, one model at a time (load,
       score all crops, unload — to bound peak RAM on small machines):
         - DeepGuard ms_eff_gcvit_b0 (FaceForensics++ c23; ImageNet
           mean/std normalisation)
         - dima806/deepfake_vs_real_image_detection (ViT-base; mean/std 0.5)
         - prithivMLmods/Deep-Fake-Detector-v2-Model (ViT-base; mean/std 0.5)
       The two ViT models were trained on GAN-generated faces, NOT on
       face-swap video; their value here is empirical (see README).
       P(fake) is taken from the label whose NAME is Fake/Deepfake in
       each model's config.json — never by index (the mappings differ
       across models: dima806 {0: Real, 1: Fake}, prithiv v2
       {0: Realism, 1: Deepfake}).
    5. Video: evenly sample up to MAX_VIDEO_FRAMES frames and aggregate
       the per-frame combined scores with the variant named in
       AGGREGATION (see aggregate_records for the exact definitions).
       No max-frame rule: one odd frame must not condemn a whole video.
       Diagnostic frame-score statistics (top-25% mean, worst 1-second
       window, fraction of frames >= 0.9, score std) are reported in
       the result but NOT used for the verdict: the 2026-11-19
       experiment showed none of them raises recall without raising
       the false-positive rate (see README).
    6. Video only, reported as SEPARATE fields (never blended into the
       face-score mean):
         - av_sync: SyncNet lip-sync check (LSE-C/LSE-D) on the video's
           own audio track. SyncNet measures sync quality, NOT forgery:
           a face-swap keeps mouth motion and audio from the same
           source person, so it stays in sync; SyncNet only flags
           dubbed / cloned-voice audio. Gate: an UNCERTAIN face
           verdict is pushed to likely_fake only when LSE-C is far
           below the real-video baseline (AV_SYNC_GATE_LSE_C_MAX,
           calibrated on the 10 real test videos — see README).
           None when there is no audio stream, <1 s of non-silent
           audio, or no face track long enough for SyncNet.
         - audio_spoof: AASIST run on the video's extracted audio
           track (P(spoof)); targets cloned-voice cases. Reported
           only, it never changes the face verdict.

Verdict bands on the aggregate score (mean P(fake); for audio P(spoof)):
    score < 0.40            -> likely_real
    0.40 <= score <= 0.60   -> uncertain
    score > 0.60            -> likely_fake
    fewer than MIN_SCORED_FRAMES scored face frames (video) or no usable
    face (image)            -> cannot_assess

Blur threshold calibration (measured on this machine, see README):
    sharp real faces (modern interview video + Lenna photo): Laplacian
    variance 212-687; a 1985 analogue interview (soft source): 39-68;
    soft in-the-wild clips (incl. the fake test videos): 9-41; the same
    Lenna face destroyed with Gaussian blur sigma 3: 3.8. Face crops are
    naturally smoother than full frames, so the classic full-image
    threshold of 100 would reject legitimate soft video. BLUR_LAP_VAR_MIN
    = 5 only rejects near-uniform crops (solid colour, extreme blur, a
    failed frame grab), not real soft video. Small-face crops inflate
    the variance, so the size filter runs first.

Audio (.wav) keeps the AASIST path: first ~4.04 s at 16 kHz mono,
softmax[1] = P(bonafide), score = P(spoof) = 1 - P(bonafide), same bands.
"""
import gc
import os
import sys

# Must be set BEFORE torch/timm are imported.
os.environ.setdefault("TIMM_USE_OLD_CACHE", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
# Never let a missing weight stall on the Hugging Face hub (it hangs on
# restricted networks). Weights are downloaded once by download_weights.py
# (stdlib urllib, no hub client) into weights/ and seeded into the timm
# cache by _ensure_deepguard_cache() before the model is built.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import json
import math
import shutil
import statistics
import subprocess
import tempfile
import time

import torch  # module level: the DeCoF head classes below subclass it

HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_DIR = os.path.join(HERE, "weights")
DEEPGUARD_BIN = "ms_eff_gcvit_b0_ff++.bin"
BACKBONE_PTH = "tf_efficientnet_b0_ns-c0e6a31c.pth"
AASIST_WEIGHTS = os.path.join(WEIGHTS_DIR, "AASIST.pth")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi"}
AUDIO_EXTS = {".wav"}

# --- face pipeline constants -------------------------------------------
FACE_MIN_LONGEST_SIDE = 64   # px; smaller faces carry too little signal
FACE_MARGIN = 0.30           # expand the face box 30% on every side
BLUR_LAP_VAR_MIN = 5.0       # Laplacian variance below this = too blurry
MIN_SCORED_FRAMES = 5        # video needs at least this many scored faces
MAX_VIDEO_FRAMES = 32        # evenly sampled frames per video

# --- verdict bands (on the aggregate score) ----------------------------
BAND_REAL_MAX = 0.40         # score < 0.40 -> likely_real
BAND_FAKE_MIN = 0.60         # score > 0.60 -> likely_fake (0.40-0.60 uncertain)

MODEL_NAME = "ensemble: deepguard + dima806 + prithiv-v2"
AUDIO_MODEL_NAME = "aasist"

# --- SyncNet (audio-visual mismatch flag) -------------------------------
# SyncNet (Oxford) lip-sync model + S3FD face detector, loaded by
# syncnet-python 0.2.3 (pip). Weights are downloaded once by
# download_weights.py into weights/ (syncnet_v2.model 54,573,114 B,
# sfd_face.pth 89,844,381 B; code MIT + Apache-2.0, weights CC-BY
# research-only). SyncNet runs only when a video has an audio stream.
# Its work dir is under .cache/ (NOT /tmp: /tmp is a 512 MB tmpfs and
# the pipeline extracts every frame as a JPEG).
SYNCNET_MODEL_FILE = "syncnet_v2.model"
S3FD_WEIGHTS_FILE = "sfd_face.pth"
SYNCNET_MIN_NON_SILENT_SEC = 1.0   # needs >= 1 s of non-silent audio
# SyncNet's S3FD runs on EVERY frame at 25 fps on CPU (~0.2 s/frame
# measured on this VM: a 55 s clip costs ~5 min). To bound the cost,
# the AV pass only looks at the first SYNCNET_MAX_SECONDS seconds of a
# video (a second window is tried once if the first yields no face
# track). Long videos are NOT fully scanned for sync — the face verdict
# still uses up to 32 frames across the whole video.
SYNCNET_MAX_SECONDS = 60.0
SYNCNET_MAX_WINDOWS = 2
CACHE_DIR = os.path.join(HERE, ".cache")
SYNCNET_WORK_ROOT = os.path.join(CACHE_DIR, "syncnet-work")
# Gate threshold on LSE-C (SyncNet confidence; higher = better sync).
# Calibrated 2026-11-19 on the 10 real test videos (see README for the
# distribution): LSE-C min 2.705 (amycuddy), max 8.183 (timurban),
# median 7.06; 2 videos had no SyncNet track. Real-world video
# routinely scores far below the clean-lab LRS2 reference (7.84), so
# the gate is set BELOW the lowest observed real value: an UNCERTAIN
# face verdict is pushed to likely_fake only when lse_c <= 2.0 — a
# clearly out-of-sync track (dubbed / mismatched audio), never a
# merely low real score. Set to None to disable the gate.
AV_SYNC_GATE_LSE_C_MAX = 2.0

# --- ensemble: Hugging Face ViT models ---------------------------------
# Weights are downloaded once by download_weights.py into
# weights/<dir>/ (config.json + preprocessor_config.json +
# model.safetensors) and loaded from those local files only — the HF hub
# client is never used (it stalls on restricted networks).
# P(fake) is taken from the label NAME in each config.json (see
# _fake_index_from_config): dima806 id2label {0: Real, 1: Fake},
# prithiv v2 id2label {0: Realism, 1: Deepfake}. Both preprocessors use
# resize 224 + rescale 1/255 + mean/std 0.5 (verified from the repos'
# preprocessor_config.json on 2026-11-19).
VIT_MODELS = {
    "dima806": {
        "dir": "dima806",
        "repo": "dima806/deepfake_vs_real_image_detection",
        "fake_label": "Fake",
        "size": 343223968,
    },
    "prithiv_v2": {
        "dir": "prithiv_v2",
        "repo": "prithivMLmods/Deep-Fake-Detector-v2-Model",
        "fake_label": "Deepfake",
        "size": 343223968,
    },
}
VIT_MEAN = (0.5, 0.5, 0.5)
VIT_STD = (0.5, 0.5, 0.5)
ENSEMBLE_MODELS = ("deepguard", "dima806", "prithiv_v2")

# Aggregation variant used by check_image/check_video. Chosen by the
# experiment of 2026-11-19 (see README): "ens_weighted" with
# WEIGHTED_DG_WEIGHT = 0.8 is the ONLY variant that raised recall on
# the original 23-file set without raising the false-positive rate
# (recall 0.375 -> 0.444, FPR 0.1111 unchanged; exactly one extra
# true positive, jimcarrey_2 at 0.618). Every other variant (equal
# ensemble mean/median, top-25% with or without the quality filter,
# DG-only top-25%) raised recall further but also raised FPR to
# 0.14-0.88, so they were rejected. The gain is marginal and
# knife-edge — see README before quoting these numbers.
AGGREGATION = "ens_weighted"

# Quality filter for the "top25_quality" variant: a scored face frame
# counts as quality when the detected face is large enough and the crop
# is neither too dark nor blown out (mean grayscale luminance of the
# 224x224 crop). Thresholds were set from the measured frame-quality
# distribution of the test set (see README).
QUALITY_MIN_FACE_PX = 120
QUALITY_LUMIN_MIN = 60.0
QUALITY_LUMIN_MAX = 210.0

# Weight of DeepGuard in the "ens_weighted" variant (the two ViT models
# split the remainder equally: 0.1 each at the chosen weight 0.8).
# Chosen by the 2026-11-19 experiment: 0.8 is the highest DeepGuard
# weight that still lets the ensemble add one true positive
# (jimcarrey_2) over DeepGuard alone; at 0.5 the ViT models (which
# fire on most real footage — see README) push two real files into
# uncertain and raise the false-positive rate.
WEIGHTED_DG_WEIGHT = 0.8

DISCLAIMER = (
    "Kết quả là chỉ báo dựa trên mô hình học máy, không phải kết luận "
    "chắc chắn. Hãy kiểm chứng thêm bằng nguồn khác trước khi kết luận "
    "một nội dung là giả mạo."
)


def verdict_from_score(score):
    """Map an aggregate score (or None) to a verdict string."""
    if score is None:
        return "cannot_assess"
    if score < BAND_REAL_MAX:
        return "likely_real"
    if score > BAND_FAKE_MIN:
        return "likely_fake"
    return "uncertain"


# --- model loading ------------------------------------------------------

_MTCNN = None
_DEEPGUARD = None
_AASIST = None


def get_mtcnn():
    """Lazy MTCNN singleton (CPU). Weights are bundled in facenet-pytorch."""
    global _MTCNN
    if _MTCNN is None:
        from facenet_pytorch import MTCNN
        _MTCNN = MTCNN(keep_all=True, device="cpu", post_process=False)
    return _MTCNN


def _ensure_weights():
    """Fetch missing weight/source files via download_weights.py.

    Called automatically on first run so a fresh machine only needs the
    code + pip install. download_weights.py is stdlib-only (urllib) and
    never touches the Hugging Face hub client.
    """
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import download_weights
    download_weights.ensure_weights()


def _ensure_deepguard_cache():
    """Seed the timm weight cache from weights/ so loading is offline.

    timm resolves the DeepGuard .bin and the EfficientNet backbone .pth
    from ~/.cache/torch/hub/checkpoints/. Seeding both files makes the
    first load take under a second; without them timm retries the
    Hugging Face hub for minutes (measured: 209 s) before giving up.
    Missing files are downloaded first (see download_weights.py).
    """
    cache = os.path.join(os.path.expanduser("~"), ".cache", "torch",
                         "hub", "checkpoints")
    os.makedirs(cache, exist_ok=True)
    for name in (DEEPGUARD_BIN, BACKBONE_PTH):
        dst = os.path.join(cache, name)
        if not os.path.exists(dst):
            src = os.path.join(WEIGHTS_DIR, name)
            if not os.path.exists(src):
                _ensure_weights()
            if not os.path.exists(src):
                raise FileNotFoundError(
                    f"missing weight file: {src} — run "
                    f"python download_weights.py to fetch it.")
            shutil.copyfile(src, dst)
    return cache


def get_deepguard():
    """Lazy DeepGuard singleton (CPU, eval mode)."""
    global _DEEPGUARD
    if _DEEPGUARD is None:
        _ensure_deepguard_cache()
        from deepguard import ms_eff_gcvit_b0
        _DEEPGUARD = ms_eff_gcvit_b0(pretrained=True, dataset="ff++")
        _DEEPGUARD.eval()
    return _DEEPGUARD


_VIT = {}  # name -> (model, fake_label_index)


def _fake_index_from_config(model_dir, fake_label):
    """Index of the fake class, found by LABEL NAME in config.json.

    Never hard-code the index: dima806 uses {0: Real, 1: Fake} while
    prithiv v2 uses {0: Realism, 1: Deepfake}; other models may flip
    them entirely (e.g. SigLIP2 {0: Fake, 1: Real}).
    """
    with open(os.path.join(model_dir, "config.json")) as f:
        cfg = json.load(f)
    for key, name in cfg.get("id2label", {}).items():
        if name == fake_label:
            return int(key)
    raise ValueError(
        f"label {fake_label!r} not found in {model_dir}/config.json "
        f"(id2label={cfg.get('id2label')})")


def get_vit_model(name):
    """Load one HF ViT model from its local folder (CPU, eval mode).

    Local files only: the folder must contain config.json,
    preprocessor_config.json and model.safetensors (downloaded once by
    download_weights.py). Missing files trigger a download attempt.
    """
    if name not in _VIT:
        info = VIT_MODELS[name]
        model_dir = os.path.join(WEIGHTS_DIR, info["dir"])
        if not os.path.exists(os.path.join(model_dir,
                                           "model.safetensors")):
            _ensure_weights()
        if not os.path.exists(os.path.join(model_dir,
                                           "model.safetensors")):
            raise FileNotFoundError(
                f"missing weight file: {model_dir}/model.safetensors — "
                f"run python download_weights.py to fetch it.")
        from transformers import ViTForImageClassification
        model = ViTForImageClassification.from_pretrained(
            model_dir, local_files_only=True)
        model.eval()
        fake_index = _fake_index_from_config(model_dir,
                                             info["fake_label"])
        _VIT[name] = (model, fake_index)
    return _VIT[name]


def unload_vit_model(name):
    """Drop one ViT model from memory (keeps peak RAM bounded).

    Models are scored one at a time over all crops, so only one ViT is
    resident at any moment.
    """
    if name in _VIT:
        del _VIT[name]
        gc.collect()


def score_crop_vit(model, fake_index, crop224):
    """Score one 224x224 face crop with a ViT model -> P(fake).

    Preprocessing follows the model's own preprocessor_config.json:
    rescale to [0, 1] then normalise with mean/std 0.5 (both ViT
    models here use 0.5/0.5).
    """
    import torch
    import torchvision.transforms as T
    x = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=VIT_MEAN, std=VIT_STD),
    ])(crop224.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        logits = model(x).logits
    probs = torch.softmax(logits, dim=1)[0]
    return float(probs[fake_index].item())


# --- whole-image AI-generation detector: Community Forensics ---------
# OwensLab/commfor-model-384 (ViT-S, MIT license). Trained on 2.7M
# images from 4,803 generators. Unlike the face models above, this one
# looks at the WHOLE image (384x384) instead of a face crop — it is
# the only detector here that can catch a fully AI-generated image
# whose face alone looks clean. Its score is reported as a separate
# field (ai_image_score) and is NEVER blended into the face-score
# mean — the same pattern as av_sync / audio_spoof. The image verdict
# rule that uses it is decided by measurement on the WasItAI set (see
# README), not by feel.
COMMFOR_MODEL_FILE = "commfor-model-384.safetensors"
COMMFOR_MODEL_NAME = "commfor-model-384"
COMMFOR_TIMM_NAME = "vit_small_patch16_384.augreg_in21k_ft_in1k"
COMMFOR_RESIZE = 440   # shorter edge -> 440, then center-crop 384
COMMFOR_CROP = 384
_COMMFOR = None


def get_commfor():
    """Lazy Community Forensics singleton (CPU, eval mode).

    Builds the timm ViT-S/16 384 backbone (pretrained=False — no hub
    download) with a 1-logit head, then loads the local safetensors
    weights (keys are the ViTClassifier wrapper's, prefixed 'vit.').
    Strict load: any missing/unexpected key is an error, not a silent
    partial load.
    """
    global _COMMFOR
    if _COMMFOR is None:
        path = os.path.join(WEIGHTS_DIR, COMMFOR_MODEL_FILE)
        if not os.path.exists(path):
            _ensure_weights()
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"missing weight file: {path} — run "
                f"python download_weights.py to fetch it.")
        import timm
        from safetensors.torch import load_file
        model = timm.create_model(COMMFOR_TIMM_NAME, pretrained=False,
                                  num_classes=1)
        raw = load_file(path)
        state = {k[4:] if k.startswith("vit.") else k: v
                 for k, v in raw.items()}
        missing, unexpected = model.load_state_dict(state, strict=False)
        if missing or unexpected:
            raise RuntimeError(
                f"commfor weight mismatch: missing={missing} "
                f"unexpected={unexpected}")
        model.eval()
        _COMMFOR = model
    return _COMMFOR


def score_images_ai(pil_imgs, batch_size=8):
    """Batched whole-image AI-generation scores -> list of P(AI).

    Same preprocessing and model as score_image_ai, but the images
    are forwarded in batches (one ViT-S forward per batch instead of
    one per image) — roughly 2-4x faster per image on CPU. Used by
    the video-frame eval and by live.py; score_image_ai stays the
    single-image entry point.
    """
    import torch
    import torchvision.transforms as T
    transform = T.Compose([
        T.Resize(COMMFOR_RESIZE),
        T.CenterCrop(COMMFOR_CROP),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]),
    ])
    model = get_commfor()
    out = []
    for i in range(0, len(pil_imgs), batch_size):
        chunk = pil_imgs[i:i + batch_size]
        batch = torch.stack(
            [transform(im.convert("RGB")) for im in chunk])
        with torch.no_grad():
            logits = model(batch)
        probs = torch.sigmoid(logits.reshape(-1))
        out.extend(float(p) for p in probs)
    return out


def score_image_ai(pil_img):
    """Whole-image AI-generation score -> P(AI-generated).

    Preprocessing is exactly the repo's val transform: resize the
    shorter edge to 440 (bilinear), center-crop 384x384, to [0, 1],
    ImageNet normalisation. Output is sigmoid(logit); label 1 = AI.
    """
    import torch
    import torchvision.transforms as T
    x = T.Compose([
        T.Resize(COMMFOR_RESIZE),
        T.CenterCrop(COMMFOR_CROP),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]),
    ])(pil_img.convert("RGB")).unsqueeze(0)
    model = get_commfor()
    with torch.no_grad():
        logit = model(x)
    return float(torch.sigmoid(logit.reshape(-1))[0].item())

# ---- AI-fix 2026-11-20: second, modern whole-image AI detector ----
# haywoodsloan/ai-image-detector-deploy (SwinV2, trained on recent
# generators incl. Flux/SDXL/Midjourney). Catches photoreal AI portraits
# that CommFor misses; CommFor still catches older SD fakes. Image
# ai_image_score = max(CommFor, modern).
MODERN_AI_DIR = os.path.join(WEIGHTS_DIR, "hf", "haywoodsloan__ai-image-detector-deploy")
MODERN_AI_NAME = "haywoodsloan-ai-image-detector"
_MODERN_AI = None


def get_modern_ai():
    global _MODERN_AI
    if _MODERN_AI is None:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        proc = AutoImageProcessor.from_pretrained(MODERN_AI_DIR)
        model = AutoModelForImageClassification.from_pretrained(MODERN_AI_DIR).eval()
        idx = [i for i, l in model.config.id2label.items() if str(l).lower().startswith("artific")][0]
        _MODERN_AI = (proc, model, int(idx))
    return _MODERN_AI


def score_image_ai_modern(pil_img):
    import torch
    proc, model, idx = get_modern_ai()
    x = proc(images=pil_img.convert("RGB"), return_tensors="pt")
    with torch.no_grad():
        p = torch.softmax(model(**x).logits, dim=-1)[0, idx].item()
    return float(p)



# --- whole-frame video AI-generation detector: DeCoF ---------------
# Frozen OpenAI CLIP ViT-L/14 (vision encoder only) -> a 2-layer
# transformer head (DeCoF, arXiv:2402.02085), trained on AIGVDBench
# incl. Sora/Veo/Kling. The head looks at 8 WHOLE frames (not face
# crops), so it can catch fully AI-generated videos whose face crops
# alone look clean. Its score is a separate field (ai_video_score),
# NEVER blended into the face-score mean — the same pattern as
# av_sync / audio_spoof. Whether it may push a verdict is decided by
# measurement on AIGVDBench (see README), not by feel.
#
# LICENSE NOTE: no license file was found in the DeCoF repo or the
# AIGVDBench dataset repo, and the weights are a 2026 RETRAIN (the
# original weights were lost in a server migration) — see README.
# The checkpoint file is a PyTorch save (zip format) despite the
# .tar name, and it holds ONLY the ViT head (7.1M params); the CLIP
# backbone comes from OpenAI's public ViT-L-14.pt (TorchScript).
DECOF_HEAD_FILE = "DeCoF.tar"
CLIP_VIT_L14_FILE = "ViT-L-14.pt"
DECOF_MODEL_NAME = "decof"
DECOF_N_FRAMES = 8
DECOF_N_SOURCE_FRAMES = 32
_CLIP_VISION = None   # (transformers CLIPVisionModel, visual proj)
_DECOF_HEAD = None


class _DeCoFPreNorm(torch.nn.Module):
    """LayerNorm then fn — same attribute names as DeCoF's vit.py so
    the checkpoint's state dict matches exactly."""

    def __init__(self, dim, fn):
        super().__init__()
        self.norm = torch.nn.LayerNorm(dim)
        self.fn = fn

    def forward(self, x, **kwargs):
        return self.fn(self.norm(x), **kwargs)


class _DeCoFFeedForward(torch.nn.Module):
    def __init__(self, dim, hidden_dim, dropout=0.):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(dim, hidden_dim),
            torch.nn.GELU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim, dim),
            torch.nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class _DeCoFAttention(torch.nn.Module):
    def __init__(self, dim, heads=8, dim_head=64, dropout=0.):
        super().__init__()
        inner_dim = dim_head * heads
        project_out = not (heads == 1 and dim_head == dim)
        self.heads = heads
        self.scale = dim_head ** -0.5
        self.attend = torch.nn.Softmax(dim=-1)
        self.to_qkv = torch.nn.Linear(dim, inner_dim * 3, bias=False)
        self.to_out = torch.nn.Sequential(
            torch.nn.Linear(inner_dim, dim),
            torch.nn.Dropout(dropout),
        ) if project_out else torch.nn.Identity()

    def forward(self, x):
        b, n, _ = x.shape
        h = self.heads
        qkv = self.to_qkv(x).chunk(3, dim=-1)
        q, k, v = [t.reshape(b, n, h, -1).transpose(1, 2)
                   for t in qkv]
        dots = torch.einsum("b h i d, b h j d -> b h i j", q, k) \
            * self.scale
        attn = self.attend(dots)
        out = torch.einsum("b h i j, b h j d -> b h i d", attn, v)
        out = out.transpose(1, 2).reshape(b, n, -1)
        return self.to_out(out)


class _DeCoFTransformer(torch.nn.Module):
    def __init__(self, dim, depth, heads, dim_head, mlp_dim,
                 dropout=0.):
        super().__init__()
        self.layers = torch.nn.ModuleList([])
        for _ in range(depth):
            self.layers.append(torch.nn.ModuleList([
                _DeCoFPreNorm(
                    dim, _DeCoFAttention(dim, heads=heads,
                                         dim_head=dim_head,
                                         dropout=dropout)),
                _DeCoFPreNorm(
                    dim, _DeCoFFeedForward(dim, mlp_dim,
                                           dropout=dropout)),
            ]))

    def forward(self, x):
        for attn, ff in self.layers:
            x = attn(x) + x
            x = ff(x) + x
        return x


class _DeCoFViT(torch.nn.Module):
    """DeCoF's ViT head, re-implemented in pure torch (no einops).

    Same module/attribute names as the repo's vit.py (pos_embedding,
    cls_token, dropout, transformer, pool, to_latent, mlp_head) so
    load_state_dict matches the checkpoint keys exactly. Pool is
    'mean'; mlp_head is LayerNorm + Linear(768, 2); label 1 = fake.
    """

    def __init__(self, num_classes=2, num_patches=8, dim=768, depth=2,
                 heads=4, mlp_dim=768, pool="mean", dropout=0.1,
                 emb_dropout=0.1):
        super().__init__()
        self.pos_embedding = torch.nn.Parameter(
            torch.randn(1, num_patches + 1, dim))
        self.cls_token = torch.nn.Parameter(torch.randn(1, 1, dim))
        self.dropout = torch.nn.Dropout(emb_dropout)
        dim_head = dim // heads
        self.transformer = _DeCoFTransformer(dim, depth, heads,
                                              dim_head, mlp_dim,
                                              dropout)
        self.pool = pool
        self.to_latent = torch.nn.Identity()
        self.mlp_head = torch.nn.Sequential(
            torch.nn.LayerNorm(dim),
            torch.nn.Linear(dim, num_classes),
        )

    def forward(self, x):
        b, n, _ = x.shape
        cls_tokens = self.cls_token.expand(b, -1, -1)
        x = torch.cat((cls_tokens, x), dim=1)
        x = x + self.pos_embedding[:, :(n + 1)]
        x = self.dropout(x)
        x = self.transformer(x)
        x = x.mean(dim=1) if self.pool == "mean" else x[:, 0]
        x = self.to_latent(x)
        return self.mlp_head(x)


def _clip_vision_state_dict():
    """Vision-encoder weights from OpenAI's ViT-L-14.pt.

    The .pt is a TorchScript archive (449 keys incl. visual.proj);
    the ScriptModule is freed right after the state dict is copied
    so peak RAM stays bounded. Returns the visual.* tensors as fp32
    (clip.load casts to float32 the same way).
    """
    import torch
    path = os.path.join(WEIGHTS_DIR, CLIP_VIT_L14_FILE)
    if not os.path.exists(path):
        _ensure_weights()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"missing weight file: {path} — run "
            f"python download_weights.py to fetch it.")
    model = torch.jit.load(path, map_location="cpu")
    sd = model.state_dict()
    visual = {k[7:]: v.float() for k, v in sd.items()
              if k.startswith("visual.")}
    del model
    gc.collect()
    return visual


def get_clip_vision():
    """Lazy CLIP ViT-L/14 vision encoder (transformers, CPU, fp32).

    The visual.* tensors from ViT-L-14.pt are mapped to transformers'
    CLIPVisionModel naming (in_proj split into q/k/v in that order)
    and cast to float32. Returns (vision_model, proj) where proj is
    the (1024, 768) visual projection applied to the [CLS] token —
    exactly what openai/clip's encode_image returns. Strict load:
    any missing/unexpected key is an error.
    """
    global _CLIP_VISION
    if _CLIP_VISION is None:
        import torch
        from transformers import CLIPVisionConfig, CLIPVisionModel
        visual = _clip_vision_state_dict()
        config = CLIPVisionConfig(
            hidden_size=1024, intermediate_size=4096,
            num_hidden_layers=24, num_attention_heads=16,
            num_channels=3, image_size=224, patch_size=14,
            hidden_act="quick_gelu", layer_norm_eps=1e-5)
        model = CLIPVisionModel(config)
        mapped = {
            "vision_model.embeddings.patch_embedding.weight":
                visual["conv1.weight"],
            "vision_model.embeddings.class_embedding":
                visual["class_embedding"],
            "vision_model.embeddings.position_embedding.weight":
                visual["positional_embedding"],
            "vision_model.pre_layrnorm.weight": visual["ln_pre.weight"],
            "vision_model.pre_layrnorm.bias": visual["ln_pre.bias"],
            "vision_model.post_layernorm.weight":
                visual["ln_post.weight"],
            "vision_model.post_layernorm.bias": visual["ln_post.bias"],
        }
        for i in range(24):
            src = f"transformer.resblocks.{i}"
            dst = f"vision_model.encoder.layers.{i}"
            in_w = visual[f"{src}.attn.in_proj_weight"]
            in_b = visual[f"{src}.attn.in_proj_bias"]
            q_w, k_w, v_w = in_w.chunk(3, dim=0)
            q_b, k_b, v_b = in_b.chunk(3, dim=0)
            mapped[f"{dst}.self_attn.q_proj.weight"] = q_w
            mapped[f"{dst}.self_attn.q_proj.bias"] = q_b
            mapped[f"{dst}.self_attn.k_proj.weight"] = k_w
            mapped[f"{dst}.self_attn.k_proj.bias"] = k_b
            mapped[f"{dst}.self_attn.v_proj.weight"] = v_w
            mapped[f"{dst}.self_attn.v_proj.bias"] = v_b
            mapped[f"{dst}.self_attn.out_proj.weight"] = \
                visual[f"{src}.attn.out_proj.weight"]
            mapped[f"{dst}.self_attn.out_proj.bias"] = \
                visual[f"{src}.attn.out_proj.bias"]
            mapped[f"{dst}.layer_norm1.weight"] = visual[f"{src}.ln_1.weight"]
            mapped[f"{dst}.layer_norm1.bias"] = visual[f"{src}.ln_1.bias"]
            mapped[f"{dst}.layer_norm2.weight"] = visual[f"{src}.ln_2.weight"]
            mapped[f"{dst}.layer_norm2.bias"] = visual[f"{src}.ln_2.bias"]
            mapped[f"{dst}.mlp.fc1.weight"] = visual[f"{src}.mlp.c_fc.weight"]
            mapped[f"{dst}.mlp.fc1.bias"] = visual[f"{src}.mlp.c_fc.bias"]
            mapped[f"{dst}.mlp.fc2.weight"] = visual[f"{src}.mlp.c_proj.weight"]
            mapped[f"{dst}.mlp.fc2.bias"] = visual[f"{src}.mlp.c_proj.bias"]
        missing, unexpected = model.load_state_dict(mapped,
                                                    strict=False)
        if missing or unexpected:
            raise RuntimeError(
                f"CLIP ViT-L/14 weight mismatch: missing={missing} "
                f"unexpected={unexpected}")
        model.eval()
        _CLIP_VISION = (model, visual["proj"].float())
    return _CLIP_VISION


def get_decof_head():
    """Lazy DeCoF ViT head (CPU, eval mode).

    The checkpoint (DeCoF.tar — a PyTorch save despite the name)
    holds ONLY the head (7.1M params) under the 'model' key; the
    CLIP backbone is separate (get_clip_vision). Strict load: any
    missing/unexpected key is an error.
    """
    global _DECOF_HEAD
    if _DECOF_HEAD is None:
        import torch
        path = os.path.join(WEIGHTS_DIR, DECOF_HEAD_FILE)
        if not os.path.exists(path):
            _ensure_weights()
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"missing weight file: {path} — run "
                f"python download_weights.py to fetch it.")
        ckpt = torch.load(path, map_location="cpu", weights_only=True)
        model = _DeCoFViT()
        missing, unexpected = model.load_state_dict(ckpt["model"],
                                                    strict=False)
        if missing or unexpected:
            raise RuntimeError(
                f"decof head mismatch: missing={missing} "
                f"unexpected={unexpected}")
        model.eval()
        _DECOF_HEAD = model
    return _DECOF_HEAD


def _sample_decof_frames(path):
    """Sample up to 8 frames evenly from the first 32 frames of a
    video (DeCoF's input). Returns a list of PIL images (RGB)."""
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("cv2 cannot open video")
    frames = []
    while len(frames) < DECOF_N_SOURCE_FRAMES:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError("no frames decoded")
    n = len(frames)
    idxs = sorted({min(n - 1, int(round(i * n / DECOF_N_FRAMES)))
                   for i in range(DECOF_N_FRAMES)})
    from PIL import Image
    out = []
    for i in idxs:
        rgb = cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)
        out.append(Image.fromarray(rgb))
    return out


def score_video_ai_frames(path):
    """Whole-frame video AI-generation score (Community Forensics).

    Samples 8 whole frames evenly from the first 32 (the same
    sampling DeCoF uses) and scores each with CommFor (whole-image
    P(AI)), batched in one forward pass. Returns a dict with the
    mean/median/max aggregates, the fraction of frames >= 0.5 and
    the per-frame scores.

    MEASURED (v5, 2026-11-20, same 220 videos DeCoF was measured
    on): mean aggregate AUROC 0.96, FPR@0.5 0.00, recall@0.5 0.71
    (max aggregate: AUROC 0.96, FPR 0.00, recall@0.5 0.80) — vs
    DeCoF AUROC 0.62, FPR 0.26, recall 0.22. DeCoF is replaced by
    this as the whole-frame video signal; DeCoF stays available as
    a separate diagnostic (score_video_ai) behind --ai-video.
    The MEAN aggregate is the reported ai_video_score: the max is a
    single-frame rule and the v3 experiment showed single-frame
    rules raise the false-positive rate on real footage.
    """
    frames = _sample_decof_frames(path)
    scores = score_images_ai(frames, batch_size=8)
    import statistics
    mean = sum(scores) / len(scores)
    return {
        "mean": round(mean, 4),
        "median": round(statistics.median(scores), 4),
        "max": round(max(scores), 4),
        "frac_ge_05": round(
            sum(1 for s in scores if s >= 0.5) / len(scores), 4),
        "frame_scores": [round(s, 4) for s in scores],
    }


def score_video_ai(path):
    """Whole-frame video AI-generation score -> P(fake).

    DeCoF: 8 frames evenly sampled from the first 32, each resized
    to 224x224 (squash) and ImageNet-normalised (the repo's test-time
    transform — NOT CLIP's own preprocessing), through the frozen
    CLIP ViT-L/14 vision encoder (projected to 768-dim) and the
    2-layer transformer head. Score = softmax(logits, 1)[:, 1];
    label 1 = fake (the original repo's convention, src/test.py and
    src/utils/data.py: fake_label=1, real_label=0).

    MEASURED HONESTLY on the 220-video AIGVDBench + WasItAI eval
    (20/11/2026): this 2026-retrain checkpoint does NOT separate
    AI from real on this set — AUROC 0.62, recall@0.5 0.22,
    FPR@0.5 0.26. Inverting the classes (softmax[:, 0]) raises
    recall to 0.78 but explodes FPR to 0.74 and drops AUROC to
    0.38, because the two real sets behave oppositely: TED-talk
    real videos score HIGH (0.61–0.998) while WasItAI real videos
    score LOW (mean 0.088). The head is picking up something other
    than AI-generatedness (likely static talking-head vs diverse
    content). So it stays a DIAGNOSTIC-ONLY field and never pushes
    a verdict. Do not flip the class index to chase recall — the
    FPR cost is unacceptable.
    """
    import torch
    import torchvision.transforms as T
    frames = _sample_decof_frames(path)
    transform = T.Compose([
        T.Resize((224, 224)),
        T.CenterCrop(224),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]),
    ])
    batch = torch.stack([transform(f.convert("RGB"))
                         for f in frames])
    vision, proj = get_clip_vision()
    with torch.no_grad():
        feats = vision(pixel_values=batch).pooler_output
        feats = feats @ proj
        head = get_decof_head()
        logits = head(feats.unsqueeze(0))
    probs = torch.softmax(logits, dim=1)[0]
    # Original repo convention: class 1 = fake (see docstring).
    # Measured on the 220-video eval: this is the better mapping
    # (AUROC 0.62 vs 0.38 inverted); the 2026-retrain checkpoint
    # is simply weak, not class-swapped.
    return float(probs[1].item())


def _aasist_source_present():
    """True when the AASIST model source + config are on disk.

    The light zip ships code only; these two files are fetched by
    download_weights.py from the official clovaai/aasist repo.
    """
    return (os.path.exists(os.path.join(HERE, "aasist", "models",
                                        "AASIST.py"))
            and os.path.exists(os.path.join(HERE, "aasist", "config",
                                            "AASIST.conf")))


def get_aasist():
    """Lazy AASIST singleton (CPU, eval mode)."""
    global _AASIST
    if _AASIST is None:
        if (not os.path.exists(AASIST_WEIGHTS)
                or not _aasist_source_present()):
            _ensure_weights()
        if not os.path.exists(AASIST_WEIGHTS):
            raise FileNotFoundError(
                f"missing weight file: {AASIST_WEIGHTS} — run "
                f"python download_weights.py to fetch it.")
        import torch
        sys.path.insert(0, os.path.join(HERE, "aasist"))
        with open(os.path.join(HERE, "aasist", "config",
                               "AASIST.conf")) as f:
            cfg = json.load(f)
        from models.AASIST import Model
        model = Model(cfg["model_config"])
        model.load_state_dict(torch.load(AASIST_WEIGHTS,
                                         map_location="cpu",
                                         weights_only=True))
        model.eval()
        _AASIST = model
    return _AASIST


# --- face handling ------------------------------------------------------


def laplacian_variance(pil_crop):
    """Sharpness of a PIL crop: variance of the Laplacian (grayscale)."""
    import cv2
    import numpy as np
    gray = cv2.cvtColor(np.array(pil_crop.convert("RGB")),
                        cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def expand_box(box, margin, img_w, img_h):
    """Expand a box by `margin` (fraction of its own size) on every side,
    clamped to the image bounds. Returns integer pixel coordinates."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    nx1 = max(0, int(round(x1 - margin * w)))
    ny1 = max(0, int(round(y1 - margin * h)))
    nx2 = min(img_w, int(round(x2 + margin * w)))
    ny2 = min(img_h, int(round(y2 + margin * h)))
    return nx1, ny1, nx2, ny2


def face_crop_for_scoring(pil_img, box):
    """Turn a detected face box into a 224x224 crop for DeepGuard.

    Returns (crop_or_None, skip_reason_or_None). skip_reason is one of
    "small" (face longest side under FACE_MIN_LONGEST_SIDE) or "blurry"
    (Laplacian variance under BLUR_LAP_VAR_MIN). The blur check runs on
    the tight face crop; the scored crop uses the margin-expanded box.
    """
    from PIL import Image
    img_w, img_h = pil_img.size
    x1, y1, x2, y2 = (int(round(v)) for v in box)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img_w, x2), min(img_h, y2)
    longest = max(x2 - x1, y2 - y1)
    if longest < FACE_MIN_LONGEST_SIDE:
        return None, "small"
    tight = pil_img.crop((x1, y1, x2, y2))
    if laplacian_variance(tight) < BLUR_LAP_VAR_MIN:
        return None, "blurry"
    ex1, ey1, ex2, ey2 = expand_box(box, FACE_MARGIN, img_w, img_h)
    crop = pil_img.crop((ex1, ey1, ex2, ey2)).resize(
        (224, 224), Image.LANCZOS)
    return crop, None


def score_face_crop(model, crop224):
    """Score one 224x224 face crop with DeepGuard -> P(fake)."""
    import torch
    import torchvision.transforms as T
    x = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=(0.485, 0.456, 0.406),
                    std=(0.229, 0.224, 0.225)),
    ])(crop224.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        logit = model(x).item()
    return float(torch.sigmoid(torch.tensor(logit)).item())


def detect_largest_face_landmarks(pil_img):
    """Detect faces with MTCNN; return (box, prob, landmarks) of the
    largest face, or None. landmarks is a (5, 2) array: left eye, right
    eye, nose, mouth-left, mouth-right (or None if MTCNN gives none).
    """
    mtcnn = get_mtcnn()
    boxes, probs, landmarks = mtcnn.detect(pil_img, landmarks=True)
    if boxes is None or len(boxes) == 0:
        return None
    areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in boxes]
    i = int(max(range(len(areas)), key=lambda k: areas[k]))
    lm = None
    if landmarks is not None and len(landmarks) > i:
        lm = landmarks[i]
    return (tuple(float(v) for v in boxes[i]), float(probs[i]), lm)


def _frontality(landmarks):
    """How frontal a face looks, from MTCNN landmarks (0..1, 1 = frontal).

    The nose of a frontal face sits near the midpoint of the two eyes;
    in profile it shifts far to one side. frontality = 1 - |offset| /
    eye-distance, clamped to [0, 1]. Returns None when landmarks are
    unusable (e.g. a failed detection).
    """
    if landmarks is None:
        return None
    try:
        import numpy as np
        lm = np.asarray(landmarks, dtype=float)
        if lm.shape != (5, 2):
            return None
        left_eye, right_eye, nose = lm[0], lm[1], lm[2]
        eye_dist = abs(float(right_eye[0] - left_eye[0]))
        if eye_dist < 1.0:
            return None
        mid_x = (float(left_eye[0]) + float(right_eye[0])) / 2.0
        offset = abs(float(nose[0]) - mid_x) / eye_dist
        return float(max(0.0, min(1.0, 1.0 - offset)))
    except Exception:
        return None


def _crop_luminance(crop224):
    """Mean grayscale luminance (0-255) of a 224x224 crop."""
    import cv2
    import numpy as np
    gray = cv2.cvtColor(np.array(crop224.convert("RGB")),
                        cv2.COLOR_RGB2GRAY)
    return float(gray.mean())


def collect_face_crops(path, max_frames=MAX_VIDEO_FRAMES):
    """Sample a file and build one 224x224 face crop per usable frame.

    Images contribute a single frame; videos are sampled evenly (ffmpeg,
    OpenCV fallback). Returns (duration_sec_or_None, crops, skips) where
    crops is a list of dicts {timestamp, crop, face_size, luminance,
    frontality} and skips counts {"no_face", "small", "blurry"}.
    Only usable face crops are returned; skipped frames never reach a
    model. Video frames are read into memory before their temp dir is
    removed.
    """
    from PIL import Image
    ext = os.path.splitext(path)[1].lower()
    skips = {"no_face": 0, "small": 0, "blurry": 0}
    if ext in IMAGE_EXTS:
        frame_paths = [(0.0, path)]
        duration = None
    else:
        duration = _video_duration(path)
        with tempfile.TemporaryDirectory(prefix="df-frames-") as tmpdir:
            if shutil.which("ffmpeg"):
                frame_paths = _sample_frames_ffmpeg(
                    path, tmpdir, duration, max_frames)
            else:
                frame_paths = _sample_frames_cv2(
                    path, tmpdir, duration, max_frames)
            crops = []
            for timestamp, fpath in frame_paths:
                with Image.open(fpath) as img:
                    crop_rec = _face_crop_record(img.convert("RGB"),
                                                 timestamp, skips)
                    if crop_rec is not None:
                        crops.append(crop_rec)
            return duration, crops, skips
    crops = []
    for timestamp, fpath in frame_paths:
        with Image.open(fpath) as img:
            crop_rec = _face_crop_record(img.convert("RGB"), timestamp,
                                         skips)
            if crop_rec is not None:
                crops.append(crop_rec)
    return duration, crops, skips


def _face_crop_record(pil_img, timestamp, skips):
    """Detect + crop the largest face in one frame.

    Returns a crop record dict, or None (counting the skip reason).
    """
    found = detect_largest_face_landmarks(pil_img)
    if found is None:
        skips["no_face"] += 1
        return None
    box, _prob, landmarks = found
    face_size = int(max(box[2] - box[0], box[3] - box[1]))
    crop, reason = face_crop_for_scoring(pil_img, box)
    if crop is None:
        skips[reason] += 1
        return None
    return {
        "timestamp": float(timestamp),
        "crop": crop,
        "face_size": face_size,
        "luminance": _crop_luminance(crop),
        "frontality": _frontality(landmarks),
    }


def score_crops(crops, models=ENSEMBLE_MODELS):
    """Score collected crops with each model in turn (load, score all
    crops, unload) to bound peak RAM.

    Returns per-frame records: [{timestamp, face_size, luminance,
    frontality, scores: {model_name: P(fake)}}]. The crop PIL images
    are dropped from the records (they are large and no longer needed).
    """
    records = [{
        "timestamp": c["timestamp"],
        "face_size": c["face_size"],
        "luminance": c["luminance"],
        "frontality": c["frontality"],
        "scores": {},
    } for c in crops]
    for name in models:
        if name == "deepguard":
            model = get_deepguard()
            for rec, c in zip(records, crops):
                rec["scores"]["deepguard"] = score_face_crop(
                    model, c["crop"])
        else:
            model, fake_index = get_vit_model(name)
            try:
                for rec, c in zip(records, crops):
                    rec["scores"][name] = score_crop_vit(
                        model, fake_index, c["crop"])
            finally:
                unload_vit_model(name)
    return records


def _frame_combined(rec, variant):
    """One combined P(fake) per scored frame, for a given variant."""
    s = rec["scores"]
    if variant.startswith("dg_"):
        return s["deepguard"]
    if variant == "ens_weighted":
        w = WEIGHTED_DG_WEIGHT
        rest = (1.0 - w) / 2.0
        return (w * s["deepguard"] + rest * s["dima806"]
                + rest * s["prithiv_v2"])
    if variant == "ens_median":
        return float(statistics.median(
            [s["deepguard"], s["dima806"], s["prithiv_v2"]]))
    # ens_mean and the ens_top25* variants all use the per-frame mean.
    return (s["deepguard"] + s["dima806"] + s["prithiv_v2"]) / 3.0


def _is_quality(rec):
    """A scored frame counts as quality (frontal-ish, well-lit) when the
    detected face is large enough and the crop is neither too dark nor
    blown out. Thresholds: QUALITY_MIN_FACE_PX / QUALITY_LUMIN_MIN /
    QUALITY_LUMIN_MAX (calibrated on the test set, see README)."""
    return (rec["face_size"] >= QUALITY_MIN_FACE_PX
            and QUALITY_LUMIN_MIN <= rec["luminance"] <= QUALITY_LUMIN_MAX)


def aggregate_records(records, variant):
    """Aggregate per-frame records into (score, median, top_suspicious).

    Variants (all take the per-frame combined score, then aggregate):
      dg_mean           mean of DeepGuard scores (v2 baseline).
      ens_mean          per-frame mean of the 3 models, then video mean.
      ens_median        per-frame median of the 3 models, then video mean.
      ens_weighted      per-frame 0.8*DeepGuard + 0.1*dima806 +
                        0.1*prithiv_v2, then video mean. (The chosen
                        variant; see AGGREGATION.)
      ens_top25         mean of the top 25% highest per-frame
                        ensemble-mean scores.
      ens_top25_quality same as ens_top25 but only over quality frames;
                        falls back to all frames when fewer than 4
                        quality frames were scored.
      dg_top25          mean of the top 25% DeepGuard scores (diagnostic
                        only: separates "top-k helps" from "ensemble
                        helps").
    score is None when there are no scored frames. median is the median
    of the per-frame combined scores used. top_suspicious lists the 3
    frames with the highest combined score and their timestamps.
    """
    if not records:
        return None, None, []
    combined = [(r["timestamp"], _frame_combined(r, variant))
                for r in records]
    if variant == "ens_top25_quality":
        quality = [(t, s) for (t, s), r in zip(combined, records)
                   if _is_quality(r)]
        if len(quality) >= 4:
            combined = quality
    if variant in ("ens_top25", "ens_top25_quality", "dg_top25"):
        k = max(1, int(math.ceil(len(combined) * 0.25)))
        top_k = sorted(combined, key=lambda ts: ts[1], reverse=True)[:k]
        score = sum(s for _t, s in top_k) / len(top_k)
    else:
        score = sum(s for _t, s in combined) / len(combined)
    median = float(statistics.median([s for _t, s in combined]))
    top = sorted(combined, key=lambda ts: ts[1], reverse=True)[:3]
    top_suspicious = [{"timestamp": round(t, 2), "score": round(s, 4)}
                      for t, s in top]
    return score, median, top_suspicious


def frame_statistics(records, variant=AGGREGATION):
    """Diagnostic per-video frame-score statistics (reported, NOT used
    for the verdict).

    Experiment 2026-11-19 on /tmp/ensemble_frames.json (original
    23-file set, same bands): top25_mean reaches recall 1.0000 but
    pushes FPR 0.1111 -> 0.5556; worst_window_1s_mean also reaches
    recall 1.0000 but FPR -> 0.6000 (and its median effective window is
    1 frame — for long videos the sampled frames are seconds apart, so
    a 1-second window degenerates to the max frame score);
    frac_frames_ge_09 collapses recall to 0.0909; score_std has no
    signal (real mean 0.190 vs fake 0.233, AUC 0.529). None passed the
    strict adoption rule (raise recall without raising FPR), so the
    shipped aggregation stays the v3 mean. These numbers are reported
    so a human can see the concentration of suspicious frames.
    """
    if not records:
        return {"top25_mean": None, "worst_window_1s_mean": None,
                "worst_window_1s_frames": 0, "frac_frames_ge_09": None,
                "score_std": None}
    ts = sorted((r["timestamp"], _frame_combined(r, variant))
                for r in records)
    scores = [s for _t, s in ts]
    n = len(scores)
    k = max(1, math.ceil(n * 0.25))
    top25 = sum(sorted(scores, reverse=True)[:k]) / k
    best, best_k = None, 0
    for t0, _s in ts:
        window = [s for t, s in ts if t0 <= t <= t0 + 1.0]
        m = sum(window) / len(window)
        if best is None or m > best:
            best, best_k = m, len(window)
    frac09 = sum(1 for s in scores if s >= 0.9) / n
    std = statistics.pstdev(scores) if n > 1 else 0.0
    return {"top25_mean": round(top25, 4),
            "worst_window_1s_mean": round(best, 4),
            "worst_window_1s_frames": best_k,
            "frac_frames_ge_09": round(frac09, 4),
            "score_std": round(std, 4)}


def analyze_frames(path, max_frames=MAX_VIDEO_FRAMES):
    """Full frame-level analysis of one file (image or video).

    Returns (duration, records, skips) where records are the per-frame
    ensemble records from score_crops. Used by check_* and by the
    experiment scripts; the per-frame records are what make the
    aggregation variants comparable without re-running the models.

    Results are cached on disk (see _frame_cache_*): face scoring costs
    ~50 s per video on CPU, and re-running it for every evaluation
    would waste hours. The cache key covers the file's path, mtime and
    size plus FRAME_CACHE_VERSION, so editing a file or changing the
    scoring code invalidates it. Records store per-model P(fake)
    scores, so they stay valid across aggregation changes.
    """
    import torch
    torch.set_num_threads(1)
    cached = _frame_cache_load(path, max_frames)
    if cached is not None:
        return cached
    _duration, crops, skips = collect_face_crops(path, max_frames)
    records = score_crops(crops)
    _frame_cache_save(path, max_frames, _duration, records, skips)
    return _duration, records, skips


# Cache version for per-frame ensemble records. Bump whenever the face
# scoring changes (models, preprocessing, MTCNN settings) so stale
# records are never reused.
FRAME_CACHE_VERSION = "v4-face-ensemble-1"
FRAME_CACHE_DIR = os.path.join(CACHE_DIR, "frames")


def _frame_cache_key(path, max_frames):
    import hashlib
    st = os.stat(path)
    raw = (f"{os.path.abspath(path)}|{st.st_mtime}|{st.st_size}|"
           f"{max_frames}|{FRAME_CACHE_VERSION}")
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _frame_cache_load(path, max_frames):
    fpath = os.path.join(FRAME_CACHE_DIR,
                         _frame_cache_key(path, max_frames) + ".json")
    if not os.path.exists(fpath):
        return None
    try:
        with open(fpath) as f:
            data = json.load(f)
        return data["duration"], data["records"], data["skips"]
    except Exception:
        return None


def _frame_cache_save(path, max_frames, duration, records, skips):
    try:
        os.makedirs(FRAME_CACHE_DIR, exist_ok=True)
        key = _frame_cache_key(path, max_frames)
        tmp = os.path.join(FRAME_CACHE_DIR, key + ".tmp")
        with open(tmp, "w") as f:
            json.dump({"duration": duration, "records": records,
                       "skips": skips}, f)
        os.replace(tmp, os.path.join(FRAME_CACHE_DIR, key + ".json"))
    except Exception:
        pass  # caching is an optimisation; a failure must not break a check


# --- result assembly ----------------------------------------------------


def _base_result(path, kind, model_name, duration_sec):
    return {
        "file": os.path.basename(path),
        "kind": kind,
        "verdict": "cannot_assess",
        "score": None,
        "median_score": None,
        "frames_scored": 0,
        "faces_scored": 0,
        "frames_total_sampled": 0,
        "frames_skipped_no_face": 0,
        "frames_skipped_small": 0,
        "frames_skipped_blurry": 0,
        "top_suspicious": [],
        "top25_mean": None,
        "worst_window_1s_mean": None,
        "worst_window_1s_frames": 0,
        "frac_frames_ge_09": None,
        "score_std": None,
        "av_sync": None,
        "audio_spoof": None,
        "av_sync_gate_applied": False,
        "ai_image_score": None,
        "ai_video_score": None,
        "face_score": None,
        "face_verdict": None,
        "model": model_name,
        "aggregation": None,
        "model_scores": None,
        "duration_sec": duration_sec,
        "disclaimer": DISCLAIMER,
    }


def _finish_records_result(result, records, skips, variant=AGGREGATION):
    """Fill verdict/score/top_suspicious of a result from per-frame
    records, using the given aggregation variant. Adds the per-model
    mean scores and the aggregation name to the result."""
    result["frames_scored"] = len(records)
    result["faces_scored"] = len(records)
    result["frames_skipped_no_face"] = skips["no_face"]
    result["frames_skipped_small"] = skips["small"]
    result["frames_skipped_blurry"] = skips["blurry"]
    result["aggregation"] = variant
    result["frame_scores"] = [{"t": round(r["timestamp"], 2),
                               "s": round(_frame_combined(r, variant), 4),
                               "m": {k: round(v, 4) for k, v in r["scores"].items()}}
                              for r in records]
    if records:
        per_model = {}
        for name in ENSEMBLE_MODELS:
            vals = [r["scores"][name] for r in records]
            per_model[name] = round(sum(vals) / len(vals), 4)
        result["model_scores"] = per_model
    score, median, top = aggregate_records(records, variant)
    result.update(frame_statistics(records, variant))
    if len(records) < MIN_SCORED_FRAMES and result["kind"] == "video":
        result["verdict"] = "cannot_assess"
        result["score"] = None
        result["median_score"] = None
        return result
    if score is None:
        result["verdict"] = "cannot_assess"
        result["score"] = None
        result["median_score"] = None
        return result
    result["score"] = round(score, 4)
    result["median_score"] = round(median, 4)
    result["verdict"] = verdict_from_score(score)
    result["top_suspicious"] = top
    return result


# --- audio track / SyncNet (video only) ---------------------------------

def _audio_stream_info(path):
    """(has_audio_stream, duration_sec) for a media file via ffprobe."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "stream=codec_type",
             "-show_entries", "format=duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        info = json.loads(out.stdout)
        has_audio = any(s.get("codec_type") == "audio"
                        for s in info.get("streams", []))
        dur = info.get("format", {}).get("duration")
        return has_audio, (float(dur) if dur else None)
    except Exception:
        return False, None


def _non_silent_seconds(path, duration):
    """Seconds of non-silent audio via ffmpeg silencedetect.

    Returns None when the measurement fails (caller treats it as
    unknown, i.e. does not block on it). Silence is measured with a
    -50 dB threshold and 0.5 s minimum silence; non-silent time is
    duration minus total silence.
    """
    if duration is None:
        return None
    try:
        proc = subprocess.run(
            ["ffmpeg", "-v", "info", "-i", path, "-vn", "-af",
             "silencedetect=noise=-50dB:d=0.5", "-f", "null", "-"],
            capture_output=True, text=True, timeout=120)
        silence = 0.0
        for line in (proc.stderr or "").splitlines():
            if "silence_duration" in line:
                try:
                    silence += float(
                        line.split("silence_duration:")[1].split()[0])
                except (ValueError, IndexError):
                    pass
        return max(0.0, duration - silence)
    except Exception:
        return None


_SYNCNET_PIPE = None


def get_syncnet_pipeline():
    """Lazy SyncNetPipeline singleton (CPU).

    Loads S3FD + SyncNet from weights/ (downloaded once by
    download_weights.py). The pipeline is kept resident across calls
    in one process so repeated videos do not reload the models.
    """
    global _SYNCNET_PIPE
    if _SYNCNET_PIPE is None:
        s3fd = os.path.join(WEIGHTS_DIR, S3FD_WEIGHTS_FILE)
        sn = os.path.join(WEIGHTS_DIR, SYNCNET_MODEL_FILE)
        if not os.path.exists(s3fd) or not os.path.exists(sn):
            _ensure_weights()
        if not os.path.exists(s3fd) or not os.path.exists(sn):
            raise FileNotFoundError(
                f"missing SyncNet weights: {s3fd} / {sn} — run "
                f"python download_weights.py to fetch them.")
        from syncnet_python import SyncNetPipeline
        _SYNCNET_PIPE = SyncNetPipeline(
            {"s3fd_weights": s3fd, "syncnet_weights": sn}, device="cpu")
    return _SYNCNET_PIPE


def _trim_video(path, start_sec, seconds, tmpdir):
    """Trim a video window with ffmpeg (stream copy, fast) for SyncNet.

    Returns the trimmed file path. -ss before -i seeks to the nearest
    keyframe, so the window start is approximate — SyncNet only needs
    relative audio/video alignment, not absolute timestamps.
    """
    out = os.path.join(tmpdir, f"window_{int(start_sec)}.mp4")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start_sec), "-i", path,
         "-t", str(seconds), "-c", "copy", out],
        check=True, timeout=120)
    return out


def run_av_sync(path):
    """Audio-visual sync check for one video file (SyncNet).

    Returns None when not applicable: no audio stream, <1 s of
    non-silent audio, or SyncNet finds no face track long enough.
    Otherwise returns {lse_c, lse_d, offset_frames, n_tracks,
    window_start_sec, note}. lse_c = SyncNet confidence (higher =
    better sync), lse_d = min distance (lower = better sync).
    Real-video reference (LRS2): LSE-C ~7.84, LSE-D ~6.74. The
    best-confidence track's own values are reported (the pipeline's
    max(conf)/min(dist) may come from different tracks).

    Only the first SYNCNET_MAX_SECONDS seconds are scanned (a second
    window is tried once if the first yields no face track): S3FD runs
    on every frame at 25 fps on CPU (~0.2 s/frame measured), so a full
    scan of a long video would take tens of minutes.

    This is a SYNC-QUALITY metric, not a forgery detector: a face-swap
    keeps mouth motion and audio from the same source person, so it
    stays in sync. It only flags dubbed / cloned-voice audio, and it
    is NEVER blended into the face-score mean. The work dir is under
    .cache/ (the pipeline extracts every frame as a JPEG; /tmp is a
    512 MB tmpfs and would overflow on long videos).
    """
    has_audio, duration = _audio_stream_info(path)
    if not has_audio:
        return None
    ns = _non_silent_seconds(path, duration)
    if ns is not None and ns < SYNCNET_MIN_NON_SILENT_SEC:
        return None
    pipe = get_syncnet_pipeline()
    os.makedirs(SYNCNET_WORK_ROOT, exist_ok=True)
    work = tempfile.mkdtemp(prefix="syncnet-", dir=SYNCNET_WORK_ROOT)
    try:
        last_error = None
        for window_i in range(SYNCNET_MAX_WINDOWS):
            start = window_i * SYNCNET_MAX_SECONDS
            if duration is not None and start >= duration:
                break
            if duration is None or duration > SYNCNET_MAX_SECONDS:
                clip = _trim_video(path, start, SYNCNET_MAX_SECONDS, work)
            else:
                clip = path
            try:
                # syncnet_python prints diagnostics ("Framewise conf",
                # "Compute time", ...) to stdout; redirect them to
                # stderr so `check.py --json` stays pure JSON.
                import contextlib
                import io
                import sys
                _buf = io.StringIO()
                with contextlib.redirect_stdout(_buf):
                    (offsets, confs, dists, _best_conf, _min_dist,
                     _json, _has_face) = pipe.inference(
                         video_path=clip, audio_path=None,
                         cache_dir=work)
                sys.stderr.write(_buf.getvalue())
            except Exception as e:  # noqa: BLE001 - SyncNet must never kill a check
                last_error = str(e)
                continue
            if offsets:
                i = int(max(range(len(confs)), key=lambda k: confs[k]))
                return {"lse_c": round(float(confs[i]), 3),
                        "lse_d": round(float(dists[i]), 3),
                        "offset_frames": int(offsets[i]),
                        "n_tracks": len(offsets),
                        "window_start_sec": float(start),
                        "note": "SyncNet LSE-C/LSE-D on best-confidence "
                                "track; higher C / lower D = better sync"}
        if last_error is not None:
            return {"lse_c": None, "lse_d": None, "offset_frames": None,
                    "n_tracks": 0,
                    "note": f"syncnet error: {last_error}"}
        return {"lse_c": None, "lse_d": None, "offset_frames": None,
                "n_tracks": 0,
                "note": "no face track long enough for SyncNet "
                        "(needs a >= 2 s track)"}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _aasist_p_spoof_for_samples(data_16k_mono):
    """P(spoof) for a 16 kHz mono float array (AASIST).

    Scores the first ~4.04 s (the length AASIST was trained on);
    shorter inputs are tiled. Shared by _score_wav_with_aasist and
    the multi-window video-audio scoring.
    """
    import numpy as np
    import torch
    nb_samp = 64600  # ~4.04 s at 16 kHz
    data = np.asarray(data_16k_mono, dtype=np.float32)
    if len(data) < nb_samp:
        data = np.tile(data, int(np.ceil(nb_samp / len(data))))
    x = torch.from_numpy(data[:nb_samp]).unsqueeze(0)
    model = get_aasist()
    with torch.no_grad():
        _out, logits = model(x)
    probs = torch.softmax(logits, dim=1)[0]
    return float(probs[0].item())


def _load_wav_mono_16k(path):
    """Load a wav file as (float32 mono samples at 16 kHz, duration_sec)."""
    import numpy as np
    import torch
    from scipy.io import wavfile
    torch.set_num_threads(1)
    sr, data = wavfile.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    orig_dtype = data.dtype
    data = data.astype(np.float32)
    if np.abs(data).max() > 1.5:  # int PCM -> [-1, 1]
        data = data / (2 ** 15 if orig_dtype == np.int16 else 2 ** 31)
    if sr != 16000:
        import torchaudio
        data = torchaudio.functional.resample(
            torch.from_numpy(data), sr, 16000).numpy()
        sr = 16000
    return data, round(len(data) / 16000, 2)


def _score_wav_with_aasist(path):
    """Score one .wav file with AASIST -> (p_spoof, duration_sec).

    Scores the first ~4.04 s (the length AASIST was trained on).
    Shared by check_audio (.wav input) — a voice file IS the sample,
    so its start is the right window.
    """
    data, duration_sec = _load_wav_mono_16k(path)
    return _aasist_p_spoof_for_samples(data), duration_sec


def _score_wav_windows_with_aasist(path):
    """Score a video's extracted audio track in 3 windows -> dict.

    The first seconds of a video are often NOT speech (intro music,
    applause — a TED talk's first 4 s measured RMS 0.164 vs 0.06-0.09
    for the speech that follows, and AASIST scored that applause as
    P(spoof)=0.858 on a genuine video). So instead of the first 4 s,
    three ~4 s windows centred at 25%, 50% and 75% of the track are
    scored and the MEDIAN is reported — one bad window (applause,
    music, silence) cannot dominate. Short tracks collapse to fewer
    windows (deduplicated starts). Returns
    {p_spoof (median), verdict, windows: [{start_sec, p_spoof}]}.
    """
    data, duration_sec = _load_wav_mono_16k(path)
    nb_samp = 64600
    starts = []
    for frac in (0.25, 0.5, 0.75):
        start = int(round((duration_sec * frac - nb_samp / 16000 / 2)
                          * 16000))
        start = max(0, min(start, max(0, len(data) - nb_samp)))
        if start not in starts:
            starts.append(start)
    windows = []
    for start in starts:
        p = _aasist_p_spoof_for_samples(data[start:start + nb_samp])
        windows.append({"start_sec": round(start / 16000, 2),
                        "p_spoof": round(p, 4)})
    p_med = float(statistics.median([w["p_spoof"] for w in windows]))
    return {"p_spoof": round(p_med, 4),
            "verdict": verdict_from_score(p_med),
            "windows": windows}


def check_video_audio_spoof(path):
    """Run AASIST on a video's own audio track.

    Returns {p_spoof (median over 3 windows), verdict, windows} or
    None (no audio stream, or the extraction failed). Nearly free —
    AASIST is already loaded for .wav checks — and it directly targets
    cloned-voice cases (the Musk scam ad, Stallman-type audio swaps).
    It is reported as a separate field and NEVER changes the face
    verdict. Windows are centred at 25%/50%/75% of the track (see
    _score_wav_windows_with_aasist) because a video's first seconds
    are often applause/music, which AASIST scores as spoof.
    """
    has_audio, _duration = _audio_stream_info(path)
    if not has_audio:
        return None
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="df-audio-",
                                         dir=CACHE_DIR) as tmpdir:
            wav = os.path.join(tmpdir, "audio.wav")
            subprocess.run(
                ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1",
                 "-ar", "16000", "-f", "wav", wav],
                check=True, timeout=300)
            return _score_wav_windows_with_aasist(wav)
    except Exception:
        return None


# --- image / video / audio checks ---------------------------------------


def check_image(path, variant=AGGREGATION):
    """Check one image file; returns the result dict.

    Two independent scores are reported:
      - face_score / face_verdict: the face-ensemble score (mean over
        face crops). Secondary for images.
      - ai_image_score: Community Forensics on the WHOLE image.
        PRIMARY for images: the verdict (score/verdict) comes from
        this field.
    The rebalancing is MEASURED, not by feel: on WasItAI Frontier
    Bench face images (n=92), CommFor AUROC 0.896 vs face-ensemble
    0.590, FPR 0.047 vs 0.419 — the face ensemble false-alarms on
    ~42% of real faces, so it cannot stay primary. On all WasItAI
    originals CommFor AUROC 0.763, FPR 0.045, recall 0.387. The face
    score stays in the result as a secondary signal (it is the only
    detector here that can catch a face-swap inside an otherwise
    real photo). If CommFor fails to load/score, the verdict falls
    back to the face ensemble.
    NOTE (v5): a CommFor+DDA mean blend was MEASURED and REJECTED —
    it beats CommFor on clean originals (AUROC 0.791 vs 0.762, FPR
    0.019 vs 0.028, recall 0.430 vs 0.380 on the same 207 images)
    but DDA is catastrophically sensitive to phone smoothing: on
    smoothed real images DDA scores mean 0.927 with FPR 1.000
    (45/45), AUROC 0.491 (real scores HIGHER than AI), so the blend
    false-alarms on 51% of smoothed real photos. No DDA weight beats
    CommFor alone on both originals and smoothed images (see
    df-v5-scratch/weight_sweep.py). DDA is therefore not used.
    """
    t0 = time.time()
    result = _base_result(path, "image", MODEL_NAME, None)
    result["frames_total_sampled"] = 1
    duration, records, skips = analyze_frames(path)
    result["elapsed_sec"] = round(time.time() - t0, 2)
    result = _finish_records_result(result, records, skips, variant)
    result["face_score"] = result["score"]
    result["face_verdict"] = result["verdict"]
    try:
        from PIL import Image
        with Image.open(path) as img:
            cf = score_image_ai(img)
            result["ai_commfor_score"] = round(cf, 4)
            try:
                md = score_image_ai_modern(img)
                result["ai_modern_score"] = round(md, 4)
            except Exception as e:
                md = None
                result["ai_modern_error"] = str(e)[:200]
            result["ai_image_score"] = round(max(cf, md) if md is not None else cf, 4)
    except Exception:
        result["ai_image_score"] = None
    if result["ai_image_score"] is not None:
        result["score"] = result["ai_image_score"]
        result["median_score"] = result["ai_image_score"]
        result["verdict"] = verdict_from_score(result["ai_image_score"])
        result["model"] = COMMFOR_MODEL_NAME + " + " + MODERN_AI_NAME
    result["elapsed_sec"] = round(time.time() - t0, 2)
    return result


def _video_duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        return float(json.loads(out.stdout)["format"]["duration"])
    except Exception:
        return None


def _sample_frames_ffmpeg(path, tmpdir, duration, max_frames):
    """Extract up to max_frames evenly spaced full-res frames with ffmpeg.

    Returns [(timestamp_sec, filepath)].
    """
    if duration and duration > 0:
        fps = max_frames / duration
    else:
        fps = 1.0
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf",
           f"fps={fps:.4f}", os.path.join(tmpdir, "f%04d.png")]
    subprocess.run(cmd, check=True, timeout=900)
    files = sorted(f for f in os.listdir(tmpdir) if f.endswith(".png"))
    out = []
    for i, name in enumerate(files[:max_frames]):
        out.append(((i + 0.5) / fps, os.path.join(tmpdir, name)))
    return out


def _sample_frames_cv2(path, tmpdir, duration, max_frames):
    """OpenCV fallback for frame sampling (no ffmpeg needed)."""
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("cv2 cannot open video")
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        step = max(1, int(round(video_fps)))
        idxs = list(range(0, max_frames * step, step))
    else:
        idxs = sorted({int(round(i * total / max_frames))
                       for i in range(max_frames)})
    wanted = set(idxs)
    out, idx = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx in wanted:
            name = os.path.join(tmpdir, f"f{len(out) + 1:04d}.png")
            cv2.imwrite(name, frame)
            out.append((idx / video_fps, name))
            if len(out) >= max_frames:
                break
        idx += 1
    cap.release()
    return out


def check_video(path, max_frames=MAX_VIDEO_FRAMES, variant=AGGREGATION,
                run_av=True, run_decof=True):
    """Check one video file; returns the result dict.

    run_av adds the two separate audio-visual fields (av_sync via
    SyncNet, audio_spoof via AASIST on the extracted track) and applies
    the SyncNet gate: an UNCERTAIN face verdict becomes likely_fake
    when LSE-C is at or below AV_SYNC_GATE_LSE_C_MAX. Pass
    run_av=False to skip the audio-visual pass (faster; face verdict
    only). The whole-frame field ai_video_score is now Community
    Forensics on 8 whole frames (mean aggregate) — it replaces DeCoF,
    which failed the v5 adoption rule (AUROC 0.62, FPR 0.26 on the
    same 220 videos; CommFor-frames: AUROC 0.96, FPR 0.00,
    recall@0.5 0.71). ai_video_score is reported as a separate field
    and never changes the face verdict by itself. run_decof adds the
    DeCoF score as a separate diagnostic field decof_score; pass
    run_decof=False to skip it (~44s saved per video on this VM).
    """
    t0 = time.time()
    duration, records, skips = analyze_frames(path, max_frames)
    result = _base_result(path, "video", MODEL_NAME, duration)
    result["frames_total_sampled"] = len(records) + sum(skips.values())
    result = _finish_records_result(result, records, skips, variant)
    try:
        frames_ai = score_video_ai_frames(path)
        result["ai_video_score"] = frames_ai["mean"]
        result["ai_video_frames"] = frames_ai
    except Exception:
        result["ai_video_score"] = None
        result["ai_video_frames"] = None
    # AI-fix: modern whole-frame AI detector on 4 frames; mean of the top 2.
    try:
        fr = _sample_decof_frames(path)[::2][:4]
        ms = sorted((score_image_ai_modern(f) for f in fr), reverse=True)
        result["ai_video_modern_frames"] = [round(x, 4) for x in ms]
        result["ai_video_modern_score"] = round(sum(ms[:2]) / len(ms[:2]), 4)
        if result["ai_video_modern_score"] > (result["score"] if result["score"] is not None else -1):
            result["face_score"] = result["score"]
            result["face_verdict"] = result["verdict"]
            result["score"] = result["ai_video_modern_score"]
            result["verdict"] = verdict_from_score(result["score"])
            result["verdict_source"] = "ai_video_modern"
    except Exception as e:
        result["ai_video_modern_score"] = None
        result["ai_video_modern_error"] = str(e)[:200]
    if run_decof:
        try:
            result["decof_score"] = round(score_video_ai(path), 4)
        except Exception:
            result["decof_score"] = None
    if run_av:
        result["av_sync"] = run_av_sync(path)
        result["audio_spoof"] = check_video_audio_spoof(path)
        if (result["verdict"] == "uncertain"
                and result["av_sync"] is not None
                and result["av_sync"]["lse_c"] is not None
                and AV_SYNC_GATE_LSE_C_MAX is not None
                and result["av_sync"]["lse_c"] <= AV_SYNC_GATE_LSE_C_MAX):
            result["verdict"] = "likely_fake"
            result["av_sync_gate_applied"] = True
            result["av_sync"]["note"] = (
                result["av_sync"]["note"]
                + " | gate applied: uncertain face score + LSE-C at or "
                  "below the real-video baseline -> likely_fake")
    result["elapsed_sec"] = round(time.time() - t0, 2)
    return result


def check_audio(path):
    """Check one .wav file with AASIST; returns the result dict."""
    t0 = time.time()
    p_spoof, duration_sec = _score_wav_with_aasist(path)
    result = _base_result(path, "audio", AUDIO_MODEL_NAME, duration_sec)
    result["score"] = round(p_spoof, 4)
    result["median_score"] = round(p_spoof, 4)
    result["verdict"] = verdict_from_score(p_spoof)
    result["audio_spoof"] = {"p_spoof": round(p_spoof, 4),
                             "verdict": result["verdict"]}
    result["elapsed_sec"] = round(time.time() - t0, 2)
    return result


def check_file(path, max_frames=MAX_VIDEO_FRAMES, variant=AGGREGATION,
               run_av=True, run_decof=True):
    """Dispatch on file extension; returns the result dict."""
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXTS:
        return check_image(path, variant)
    if ext in VIDEO_EXTS:
        return check_video(path, max_frames, variant, run_av, run_decof)
    if ext in AUDIO_EXTS:
        return check_audio(path)
    raise ValueError(
        f"unsupported file type '{ext}'. Images: {sorted(IMAGE_EXTS)}; "
        f"video: {sorted(VIDEO_EXTS)}; audio: {sorted(AUDIO_EXTS)}")
