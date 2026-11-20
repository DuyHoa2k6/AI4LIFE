# Deepfake Detector v6 (light) — standalone, CPU-only

Phát hiện mặt giả trong ảnh/video và giọng giả trong file âm thanh, chạy
hoàn toàn trên CPU, không cần GPU, không cần tài khoản/key.

**Bản light này chỉ chứa code.** Weights (~1,97 GB) không đi kèm trong zip
mà được tải một lần ở lần chạy đầu — bằng `python download_weights.py`
hoặc tự động khi chạy `check.py` lần đầu (xem mục dưới). Mọi link tải
đều ghi rõ trong bảng mô hình.

- **Ảnh / video (mặt giả):** ensemble 3 mô hình chấm cùng một face crop
  — DeepGuard `ms_eff_gcvit_b0` (FaceForensics++ c23, trọng số 0.8) +
  **dima806/deepfake_vs_real_image_detection** và
  **prithivMLmods/Deep-Fake-Detector-v2-Model** (ViT-base, train trên
  mặt GAN, trọng số 0.1 mỗi model). Mặt được dò bằng MTCNN rồi cắt với
  biên 30% trước khi chấm — đúng kiểu dữ liệu mô hình đã được train.
  Điểm video = **trung bình** các khung (không dùng top-25% hay
  max-frame — đã thử ở v3/v4, đều tăng báo nhầm video thật; xem bảng
  so sánh). JSON trả thêm 4 thống kê chẩn đoán trên điểm từng khung
  (`top25_mean`, `worst_window_1s_mean`, `frac_frames_ge_09`,
  `score_std`) — chỉ để đọc, không đổi verdict.
- **Đồng bộ môi–tiếng (SyncNet, mới ở v4):** cờ `av_sync` riêng biệt
  (LSE-C/LSE-D) — **không bao giờ trộn vào điểm mặt**. Chỉ lật verdict
  khi mặt đang `uncertain` VÀ LSE-C ≤ 2.0 (ngưỡng hiệu chuẩn trên video
  thật, xem mục hiệu chuẩn). Face-swap thuần giữ nguyên đồng bộ
  môi–tiếng nên SyncNet không bắt được nó; cờ này chỉ bắt trường hợp
  lồng tiếng / giọng clone không khớp miệng.
- **Giọng nói (giả giọng):** AASIST (`clovaai/aasist`) — file `.wav`
  chấm trực tiếp; video được tách audio ra chấm thêm ở 3 cửa sổ
  (25%/50%/75% thời lượng, lấy trung vị) và báo ở trường
  `audio_spoof` riêng biệt, không đổi verdict mặt.
- **Ảnh tạo bởi AI (toàn ảnh, mới ở v4):** Community Forensics
  (`OwensLab/commfor-model-384`, ViT-S, MIT) chấm TOÀN ảnh 384×384,
  trả về `ai_image_score`. **Đây là verdict chính cho ảnh tĩnh**
  (đo trên WasItAI: AUROC 0.896 so với 0.590 của ensemble mặt, FPR
  0.047 so với 0.419 — xem mục kết quả). Điểm ensemble mặt giữ lại
  làm trường phụ (`face_score` / `face_verdict`).
- **Video tạo bởi AI (toàn khung, mới ở v5):** Community Forensics
  chấm 8 khung toàn cảnh (lấy đều từ 32 khung đầu, xử lý theo lô),
  trả về `ai_video_score` riêng biệt — không trộn vào điểm mặt,
  không tự đổi verdict. Đo trên cùng 220 video DeCoF từng đo:
  AUROC **0.924** so với 0.449 của DeCoF, FPR **0.000** so với 0.659,
  recall@0.5 0.603 so với 0.777 (DeCoF bắt nhiều hơn nhưng báo nhầm
  66% video thật nên không dùng được). Xem mục kết quả v5. DeCoF
  vẫn còn, nhưng chỉ làm trường chẩn đoán `decof_score` khi chạy
  với `--ai-video` (xem lưu ý giấy phép ở dưới).

## Mô hình và weights

| Mô hình | Dùng để làm gì | File | Tải từ | Dung lượng |
|---|---|---|---|---|
| DeepGuard `ms_eff_gcvit_b0` (FaceForensics++ c23) | Chấm mặt giả trong ảnh/video (trọng số 0.8 trong ensemble) | `weights/ms_eff_gcvit_b0_ff++.bin` | https://github.com/HanMoonSub/DeepGuard/releases/download/v0.1.0/ms_eff_gcvit_b0_ff++.bin | 36.642.117 byte (~35,0 MB) |
| timm EfficientNet-B0 (`tf_efficientnet_b0.ns_jft_in1k`) | Backbone mà DeepGuard dùng để trích đặc trưng | `weights/tf_efficientnet_b0_ns-c0e6a31c.pth` | https://github.com/rwightman/pytorch-image-models/releases/download/v0.1-weights/tf_efficientnet_b0_ns-c0e6a31c.pth | 21.386.709 byte (~20,4 MB) |
| AASIST | Chấm giọng giả trong file `.wav` | `weights/AASIST.pth` | https://raw.githubusercontent.com/clovaai/aasist/main/models/weights/AASIST.pth | 1.281.532 byte (~1,2 MB) |
| AASIST (mã nguồn + config) | Mã nguồn mô hình AASIST, cần để chạy file `.wav` | `aasist/models/AASIST.py`, `aasist/config/AASIST.conf` | https://github.com/clovaai/aasist (repo chính thức, nhánh `main`) | 19.957 byte |
| dima806 `deepfake_vs_real_image_detection` (ViT-base, Apache-2.0) | Chấm mặt giả trong ảnh/video (trọng số 0.1 trong ensemble); train trên mặt GAN | `weights/dima806/model.safetensors` + `config.json` + `preprocessor_config.json` | https://huggingface.co/dima806/deepfake_vs_real_image_detection/resolve/main/model.safetensors (config và preprocessor cùng đường dẫn, đổi tên file) | 343.223.968 byte (~327,3 MB) + 1.051 byte config |
| prithivMLmods `Deep-Fake-Detector-v2-Model` (ViT-base, Apache-2.0) | Chấm mặt giả trong ảnh/video (trọng số 0.1 trong ensemble); train trên mặt GAN | `weights/prithiv_v2/model.safetensors` + `config.json` + `preprocessor_config.json` | https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model/resolve/main/model.safetensors (config và preprocessor cùng đường dẫn, đổi tên file) | 343.223.968 byte (~327,3 MB) + 1.089 byte config |
| SyncNet `syncnet_v2.model` (Oxford, CC-BY research-only) | Cờ đồng bộ môi–tiếng cho video (LSE-C/LSE-D); không trộn vào điểm mặt | `weights/syncnet_v2.model` | https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model | 54.573.114 byte (~52,0 MB) |
| S3FD `sfd_face.pth` (Oxford, CC-BY research-only) | Dò mặt cho SyncNet (mô hình riêng, khác MTCNN) | `weights/sfd_face.pth` | https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/sfd_face.pth | 89.844.381 byte (~85,7 MB) |
| Community Forensics `commfor-model-384` (ViT-S, MIT) | Chấm ảnh tạo bởi AI trên TOÀN ảnh (verdict chính cho ảnh tĩnh); train trên 2,7 triệu ảnh từ 4.803 generator | `weights/commfor-model-384.safetensors` | https://huggingface.co/OwensLab/commfor-model-384/resolve/main/model.safetensors | 87.262.324 byte (~83,2 MB) |
| DeCoF head (2 lớp transformer + MLP, **giấy phép CHƯA XÁC MINH** — xem lưu ý dưới) | Chấm video tạo bởi AI trên 8 khung toàn cảnh (`ai_video_score`); train lại 2026 trên AIGVDBench (weights gốc đã mất do chuyển server) | `weights/DeCoF.tar` (thực chất là file checkpoint PyTorch dạng zip, không phải tar) | https://huggingface.co/datasets/AIGVDBench/AIGVDBench/resolve/main/Weights/DeCoF.tar | 56.815.450 byte (~54,2 MB) |
| OpenAI CLIP ViT-L/14 | Backbone đóng băng cho DeCoF (chỉ dùng vision encoder; text encoder không dùng) | `weights/ViT-L-14.pt` (TorchScript) | https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt | 932.768.134 byte (~889,6 MB) |

**Tổng tải lần đầu: 1.967.043.794 byte (~1,97 GB).** Tất cả các link trên
đã được kiểm chứng tải được bằng `curl` ngày 19–20/11/2026 (kích thước
khớp đúng với file đã dùng để đo ở bản v3/v4). Script tải dùng thư viện
chuẩn `urllib`, không dùng Hugging Face hub client hay `transformers`
tự tải — vì hub client bị treo trên mạng hạn chế, trong khi tải trực
tiếp bằng HTTPS vẫn chạy tốt. File đã có đủ kích thước thì được bỏ qua;
file tải dở sẽ tự nối tiếp bằng HTTP Range khi server cho phép.

> **Lưu ý giấy phép DeCoF — nói thẳng:** không tìm thấy file giấy phép
> trong repo DeCoF (github.com/wuwuwuyue/DeCoF) lẫn trong dataset
> AIGVDBench trên Hugging Face (chỉ có README.md 30 byte). Weights
> `DeCoF.tar` là bản **train lại ngày 28/02/2026** trên dataset cập
> nhật — theo README của repo, weights gốc của bài báo đã mất khi
> chuyển server. Vì vậy thành phần này được ghi rõ là **giấy phép chưa
> xác minh, weights là bản train lại 2026, không phải weights gốc của
> bài báo** — dùng để nghiên cứu/đánh giá, không dùng cho sản phẩm
> thương mại cho tới khi giấy phép được làm rõ. CLIP ViT-L/14 là của
> OpenAI (MIT license cho code; weights đi kèm model card của OpenAI).

> **Cẩn thận nhãn khi dùng 2 model ViT:** dima806 `id2label = {0: Real,
> 1: Fake}`; prithiv v2 `{0: Realism, 1: Deepfake}`. Code lấy P(fake)
> theo **tên label** trong từng `config.json` lúc nạp model, không
> hard-code index — model khác có thể đảo ngược (ví dụ SigLIP2
> `{0: Fake, 1: Real}`).

## Cài đặt

### Windows

1. Cài **Python 3.12** từ https://www.python.org/downloads/ — lúc cài
   tick **"Add python.exe to PATH"**. Kiểm tra: `py --version` phải ra
   `Python 3.12.x`.
2. Cài **ffmpeg** (để cắt khung hình video; nếu thiếu thì code tự dùng
   OpenCV thay thế): `winget install ffmpeg`, hoặc tải bản build của
   gyan.dev (https://www.gyan.dev/ffmpeg/builds/) rồi thêm thư mục `bin`
   vào PATH. Kiểm tra: `ffmpeg -version`.
3. Mở PowerShell trong thư mục này:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe download_weights.py
```

> Bắt buộc cài torch từ CPU index (dòng `--extra-index-url` trong
> `requirements.txt` đã lo việc này). Đừng cài `pip install torch` từ
> PyPI mặc định: đó là bản CUDA, nặng hơn và `torchvision` đi kèm cần
> file CUDA nên lỗi `torchvision::nms does not exist` trên máy không
> có GPU.

4. Cần ~5,5 GB ổ trống (venv + torch ~1,8 GB, weights ~1,97 GB, cache
   khung hình + SyncNet ~vài trăm MB). Bước `download_weights.py` có
   thể bỏ qua — `check.py` sẽ tự tải weights còn thiếu ở lần chạy đầu
   tiên — nhưng chạy trước một lần cho chắc. Lần tải đầu ~1,97 GB
   (chủ yếu là CLIP ViT-L/14 933 MB và 2 model ViT, mỗi cái 343 MB);
   mỗi lần chạy video 32 khung mất khoảng 50–65 giây chỉ riêng phần
   chấm mặt trên CPU (3 model chấm lần lượt), chậm hơn bản v2 chỉ có
   DeepGuard (~12 giây).
   **Phần SyncNet (v4) chậm hơn nhiều:** S3FD chạy trên mọi khung ở
   25 fps, đo thật ~5–10 phút cho một video ~55 giây (gấp ~6 lần thời
   lượng video) — video chỉ xét tối đa 60 giây đầu cho phần này. Muốn
   bỏ qua phần SyncNet + audio thì thêm `--no-av` cho `check.py`
   (xem dưới).

### Linux (máy đã kiểm chứng: Ubuntu, Python 3.12)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python download_weights.py
```

## Cách dùng

### CLI — kiểm tra 1 file

```bash
venv/bin/python check.py <file> [--json] [--max-frames N] [--no-av]
```

- Ảnh: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`
- Video: `.mp4`, `.webm`, `.mov`, `.avi` (mặc định tối đa 32 khung)
- Giọng: `.wav` (16 kHz mono là tốt nhất; khác tần số sẽ tự resample;
  file dài hơn ~4 giây chỉ xét 4 giây đầu, file ngắn hơn sẽ lặp lại)
- `--no-av`: bỏ qua phần SyncNet + tách audio (chỉ chấm mặt) — nhanh
  hơn nhiều, dùng khi chỉ cần verdict mặt hoặc máy yếu.

Ví dụ:

```bash
venv/bin/python check.py video_nghi_ngo.mp4 --json
venv/bin/python check.py anh_mat.jpg
venv/bin/python check.py giong_noi.wav --json
```

`--json` chỉ in đối tượng JSON. Không có `--json` thì in thêm 1 bản
tóm tắt ngắn rồi mới in JSON.

### Kết quả JSON

```json
{
  "file": "test_video.mp4",
  "kind": "video",
  "verdict": "likely_real",
  "score": 0.1642,
  "median_score": 0.1658,
  "frames_scored": 9,
  "faces_scored": 9,
  "frames_total_sampled": 32,
  "frames_skipped_no_face": 7,
  "frames_skipped_small": 16,
  "frames_skipped_blurry": 0,
  "top_suspicious": [{"timestamp": 58.34, "score": 0.2198},
                     {"timestamp": 259.86, "score": 0.1769},
                     {"timestamp": 79.55, "score": 0.1743}],
  "top25_mean": 0.1932,
  "worst_window_1s_mean": 0.2198,
  "worst_window_1s_frames": 2,
  "frac_frames_ge_09": 0.0,
  "score_std": 0.0451,
  "av_sync": {"lse_c": 6.372, "lse_d": 8.107, "offset_frames": 2,
              "n_tracks": 7, "window_start_sec": 0.0,
              "note": "SyncNet LSE-C/LSE-D on best-confidence track; higher C / lower D = better sync"},
  "audio_spoof": {"p_spoof": 0.4165, "verdict": "uncertain",
                  "windows": [{"start_sec": 84.85, "p_spoof": 0.41},
                              {"start_sec": 169.7, "p_spoof": 0.42},
                              {"start_sec": 254.55, "p_spoof": 0.43}]},
  "av_sync_gate_applied": false,
  "ai_video_score": 0.0014,
  "model": "ensemble: deepguard + dima806 + prithiv-v2",
  "aggregation": "ens_weighted",
  "model_scores": {"deepguard": 0.0219, "dima806": 0.8904,
                   "prithiv_v2": 0.5759},
  "duration_sec": 339.4,
  "disclaimer": "Kết quả là chỉ báo dựa trên mô hình học máy, không phải kết luận chắc chắn. Hãy kiểm chứng thêm bằng nguồn khác trước khi kết luận một nội dung là giả mạo."
}
```

- `verdict`: `likely_fake` / `likely_real` / `uncertain` /
  `cannot_assess`. `score` là P(fake) với ảnh/video, P(spoof) với
  audio; `null` khi `cannot_assess`.
- `top_suspicious`: mốc thời gian (giây) của 3 khung đáng ngờ nhất.
- `aggregation`: luật gộp điểm đã dùng (`ens_weighted`); `model_scores`:
  điểm trung bình của từng model riêng (DeepGuard / dima806 / prithiv v2)
  trên các khung đã chấm — xem để biết model nào đang kéo điểm lên hay
  xuống (ví dụ ở video trên, dima806 cho 0.89 trên video thật trong khi
  DeepGuard chỉ 0.02).
- `top25_mean` / `worst_window_1s_mean` / `frac_frames_ge_09` /
  `score_std` (mới ở v4): thống kê chẩn đoán trên điểm từng khung —
  trung bình top 25% khung, trung bình cửa sổ 1 giây cao nhất, tỉ lệ
  khung ≥ 0.9, độ lệch chuẩn. **Chỉ để đọc, không đổi verdict** (đã
  thử dùng làm luật gộp ở v3/v4: recall lên nhưng báo nhầm video thật
  tăng mạnh — xem bảng so sánh).
- `av_sync` (mới ở v4, chỉ video): SyncNet LSE-C (cao = đồng bộ tốt)
  và LSE-D (thấp = đồng bộ tốt) trên track có độ tin cậy cao nhất,
  cùng số track tìm được và cửa sổ giây đã xét (tối đa 60 giây đầu;
  cửa sổ thứ hai 60–120 giây chỉ thử khi cửa sổ đầu không có track).
  `null` khi video không có audio, audio gần như câm, hoặc không có
  track mặt đủ dài (≥ 2 giây) — clip ngắn hay mặt nhỏ thường ra
  `null`. **Không bao giờ trộn vào điểm mặt.**
- `audio_spoof` (mới ở v4, chỉ video): AASIST chấm audio tách từ
  video ở 3 cửa sổ (25%/50%/75% thời lượng), `p_spoof` là trung vị 3
  cửa sổ; `windows` ghi từng cửa sổ. `null` khi không có audio.
  **Không đổi verdict mặt** — đo thật cho thấy AASIST báo nhầm cao
  trên audio video (xem mục giới hạn).
- `av_sync_gate_applied` (mới ở v4): `true` chỉ khi verdict
  `uncertain` đã bị SyncNet lật thành `likely_fake` (LSE-C ≤ 2.0).
- `ai_video_score` (mới ở v4, chỉ video): DeCoF chấm 8 khung toàn
  cảnh, P(fake). **Chỉ để đọc, không đổi verdict mặt** — xem mục kết
  quả DeCoF.
- Với ảnh tĩnh, verdict chính lấy từ CommFor: `score` là
  `ai_image_score` (P(AI) trên toàn ảnh), `model` là
  `"commfor-model-384"`; điểm ensemble mặt giữ ở `face_score` /
  `face_verdict`. Với audio, các trường khung hình bằng 0 và `model`
  là `"aasist"`. Với ảnh, `av_sync` và `audio_spoof` đều là `null`.

### API

```bash
venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8001
```

- `GET /health` — trạng thái và tên mô hình.
- `POST /deepfake/check` — upload 1 file (multipart, field `file`),
  trả về đúng JSON như `check.py`. Tham số query `max_frames` đổi số
  khung tối đa của video.

```bash
curl -F "file=@anh_mat.jpg" http://127.0.0.1:8001/deepfake/check
```

### Benchmark — đánh giá trên 2 thư mục mẫu

```bash
venv/bin/python evaluate.py <thu_muc_that> <thu_muc_gia> [--max-frames N] [--jobs N] [--out results.json] [--no-av]
```

In ra accuracy, precision, recall, F1, AUC, confusion matrix
(TP/FP/TN/FN), tỉ lệ báo nhầm file thật, thời gian trung bình mỗi file
và bảng từng file. File `uncertain` / `cannot_assess` không tính đúng
hay sai — số lượng của chúng được báo riêng, các chỉ số chỉ tính trên
file đã kết luận được. `--jobs N` chạy song song N tiến trình (mỗi
tiến trình nạp model riêng — máy ít RAM thì để 1). `--out` ghi kết
quả đầy đủ ra JSON (kèm LSE-C, `audio_spoof`, cờ gate, thời gian từng
file). `--no-av` bỏ qua phần SyncNet + audio (nhanh hơn nhiều).
**Lưu ý:** lần chạy đầu chậm vì phải chấm mặt; các lần sau dùng cache
khung hình (`.cache/frames/`, khóa theo đường dẫn + mtime + kích
thước + phiên bản code chấm) nên chỉ còn phần SyncNet là chậm.

## Cách hoạt động

1. **Dò mặt (MTCNN, facenet-pytorch):** weights `pnet/rnet/onet` nằm
   sẵn trong gói pip, không tải gì lúc chạy. Mỗi khung lấy mặt lớn
   nhất. Không có mặt → bỏ qua khung.
2. **Lọc:** mặt có cạnh dài nhất dưới 64 px → bỏ qua; mặt quá mờ
   (phương sai Laplacian của vùng mặt dưới 5.0 — xem mục hiệu chuẩn
   bên dưới) → bỏ qua. Khung bị bỏ qua không được chấm và không tính
   vào số khung đã chấm.
3. **Cắt mặt:** mở rộng khung mặt 30% mỗi phía (giới hạn trong ảnh),
   cắt ra, resize 224×224, rồi chấm **cùng một crop bằng 3 mô hình,
   lần lượt từng model** (nạp, chấm hết các khung, gỡ khỏi RAM — để
   máy ít RAM vẫn chạy được): DeepGuard (chuẩn hoá mean/std ImageNet),
   dima806 và prithiv v2 (chuẩn hoá mean/std 0.5). P(fake) của mỗi model
   ViT lấy theo **tên label** trong `config.json` của chính model đó.
   Ảnh tĩnh dùng đúng pipeline này với mặt lớn nhất.
4. **Video:** lấy mẫu đều tối đa 32 khung khắp video (ffmpeg, dự phòng
   OpenCV). Gộp điểm mỗi khung bằng **0.8×DeepGuard + 0.1×dima806 +
   0.1×prithiv v2**, rồi lấy **trung bình** các khung có mặt (điểm chính)
   và **trung vị**. Không dùng luật "một khung giả là cả video giả":
   video thật cũng có vài khung cho điểm cao (xem mục giới hạn). Luật
   gộp này là kết quả thực nghiệm v3 — xem bảng so sánh ở mục kết quả.
5. **Kết luận** theo điểm gộp (ảnh/video: P(fake); audio: P(spoof)):
   `< 0.40` likely_real, `0.40–0.60` uncertain, `> 0.60` likely_fake.
   Video dưới 5 khung có mặt → `cannot_assess`.
6. **Audio:** AASIST đọc ~4 giây đầu ở 16 kHz mono, `P(spoof) =
   1 − P(bonafide)`, cùng dải kết luận như trên.
7. **Video — cờ SyncNet + audio (mới ở v4, bỏ qua với `--no-av`):**
   sau khi chấm mặt, tách audio của video ra: (a) chạy SyncNet trên
   tối đa 60 giây đầu (cửa sổ thứ hai 60–120 giây chỉ khi cửa sổ đầu
   không có track mặt ≥ 2 giây) để lấy LSE-C/LSE-D — ghi vào
   `av_sync`, không trộn vào điểm mặt; (b) chạy AASIST trên 3 cửa sổ
   audio (25%/50%/75% thời lượng, lấy trung vị) — ghi vào
   `audio_spoof`, không đổi verdict. **Cổng duy nhất từ SyncNet vào
   verdict:** nếu mặt đang `uncertain` VÀ `lse_c ≤ 2.0` thì verdict
   thành `likely_fake` và `av_sync_gate_applied = true`. Ngưỡng 2.0
   hiệu chuẩn trên 10 video thật (thấp nhất đo được 2.705 — xem mục
   hiệu chuẩn SyncNet). Face-swap thuần vẫn đồng bộ môi–tiếng nên
   cổng này gần như không bao giờ mở trên clip face-swap — đó là kết
   quả đo được, không phải lỗi cài đặt.

## Kết quả đo thật (bản v3, 19/11/2026)

Đo trên cùng tập test 23 file của bản v2 (12 thật / 11 giả: phỏng vấn
và TED trên YouTube + clip deepfake trên archive.org, mỗi clip giả đã
kiểm tra bằng mắt qua 3 khung hình; chi tiết xem `tests/` trong bản
đầy đủ — bản light này **không kèm file test**, các số dưới đây là kết
quả đo của cùng bộ code này trên tập đó). Các chỉ số chỉ tính trên file
đã kết luận được. Chạy `evaluate.py` trên đúng 3 tập này cho ra các số
sau (log đầy đủ xem `tests/EVAL_2026-11-19.md`).

### Trước / sau: v2 (chỉ DeepGuard) → v3 (ensemble 0.8/0.1/0.1)

| Tập | | Accuracy | Precision | Recall | F1 | AUC | Báo nhầm thật |
|---|---|---|---|---|---|---|---|
| Gốc (23 file) | v2 | 0.6471 | 0.7500 | 0.3750 | 0.5000 | 0.7500 | 0.1111 (1/9) |
| Gốc (23 file) | **v3** | **0.6667** | **0.8000** | **0.4444** | **0.5714** | **0.7778** | **0.1111 (1/9)** |
| Nén nặng (8 file) | v2 | 0.5714 | — (0 TP) | 0.0000 | — | 0.6667 | 0.0000 |
| Nén nặng (8 file) | **v3** | **0.5714** | **— (0 TP)** | **0.0000** | **—** | **0.6667** | **0.0000** |
| Giả lập quay màn hình (4 file) | v2 | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 1.0000 | 0.0000 |
| Giả lập quay màn hình (4 file) | **v3** | **0.7500** | **1.0000** | **0.5000** | **0.6667** | **1.0000** | **0.0000** |

Confusion tập gốc v3: TP 4 / FN 5 / TN 8 / FP 1; 18 file kết luận được,
5 không kết luận (4 uncertain + 1 cannot_assess). Thời gian trung bình
~50–65 giây/file video (3 model chấm lần lượt), chậm hơn v2 (~12 giây).

### Bảng so sánh các luật gộp đã thử (tập gốc, 23 file)

Tất cả các luật đều chấm trên **cùng** các khung mặt đã cắt và cùng
điểm từng model (chỉ khác cách gộp), nên bảng này so sánh công bằng.
Quy tắc chọn đã định trước: chỉ giữ luật nào **tăng recall mà không
tăng tỉ lệ báo nhầm video thật** so với v2 (recall 0.3750, FPR 0.1111).

| Luật gộp | Accuracy | Precision | Recall | F1 | AUC | Báo nhầm thật | Kết luận |
|---|---|---|---|---|---|---|---|
| `dg_mean` (v2, chỉ DeepGuard) | 0.6471 | 0.7500 | 0.3750 | 0.5000 | 0.7500 | 0.1111 (1/9) | baseline |
| `ens_mean` (trung bình 3 model) | 0.7500 | 0.6667 | 1.0000 | 0.8000 | 1.0000 | 0.5000 (2/4) | LOẠI — báo nhầm tăng |
| `ens_median` (trung vị 3 model) | 0.6429 | 0.7143 | 0.6250 | 0.6667 | 0.8542 | 0.3333 (2/6) | LOẠI — báo nhầm tăng |
| `ens_weighted` 0.5/0.25/0.25 | 0.8333 | 0.8000 | 0.8000 | 0.8000 | 0.9143 | 0.1429 (1/7) | LOẠI — báo nhầm tăng |
| `ens_top25` (trung bình top 25% khung) | 0.6316 | 0.6111 | 1.0000 | 0.7586 | 0.6023 | 0.8750 (7/8) | LOẠI — báo nhầm tăng mạnh |
| `ens_top25_quality` (top 25% khung chất lượng) | 0.6667 | 0.6471 | 1.0000 | 0.7857 | 0.6883 | 0.8571 (6/7) | LOẠI — lọc chất lượng không cứu được |
| `dg_top25` (top 25% chỉ DeepGuard) | 0.7778 | 0.7143 | 1.0000 | 0.8333 | 0.7250 | 0.5000 (4/8) | LOẠI — báo nhầm tăng |
| **`ens_weighted` 0.8/0.1/0.1 (v3, đã chọn)** | **0.6667** | **0.8000** | **0.4444** | **0.5714** | **0.7778** | **0.1111 (1/9)** | **GIỮ — luật duy nhất đạt quy tắc chọn** |

Lưới lọc chất lượng cho `ens_top25_quality` (mặt ≥80/100/120/150 px ×
độ sáng 40–230 / 60–210 / 80–200) cũng đã thử đủ 12 tổ hợp: recall
luôn 1.0000 nhưng báo nhầm luôn 0.85–0.88 — lọc chất lượng không tách
được hai phía. Chỉ số frontality từ landmark MTCNN cũng vô dụng (trung
vị 1.0 trên mọi tập — gần như khung nào nó cũng cho là chính diện).

### Đọc đúng các con số này — nói thẳng

- **Ensemble KHÔNG sửa được vấn đề recall.** Điểm tăng duy nhất của
  v3 so với v2 là **đúng 1 file**: `fake_jimcarrey_2` từ 0.586
  (uncertain) lên 0.618 (likely_fake, vừa chạm qua ngưỡng 0.60).
  Recall vẫn dưới 0.5 — trên clip giả ngoài đời thực, công cụ vẫn bỏ
  sót hơn một nửa.
- **2 model ViT mới gần như không phân biệt được thật/giả trên tập
  này.** Điểm trung bình từng model trên từng file (tập gốc):
  dima806 cho 0.89–0.98 trên video **thật** (phỏng vấn Straley 0.982,
  test_video 0.890, Tim Urban 0.969) lẫn giả (0.87–0.99); prithiv v2
  cho 0.61–0.83 trên video thật (Simon Sinek 0.828, Ken Robinson
  0.770, Amy Cuddy 0.719, Lenna 0.679) và 0.22–0.68 trên clip giả.
  Đứng một mình: dima806 accuracy 0.63, báo nhầm thật 0.625; prithiv
  v2 accuracy 0.40, báo nhầm thật 0.625. Chỉ DeepGuard là có tín hiệu
  phân biệt thật (video thật 0.02–0.49, trừ Duckworth 0.719; clip giả
  0.17–0.96) — đó là lý do trọng số DeepGuard phải lên tới 0.8 thì
  ensemble mới không phá tỉ lệ báo nhầm.
- **Các điểm v3 đều nằm sát biên.** Lenna 0.382 và Brené Brown 0.400
  chỉ cách ngưỡng uncertain 0.40 một chút; jimcarrey_2 0.618 chỉ cách
  ngưỡng likely_fake 0.60 một chút. Đổi một file test khác là các số
  này có thể đổi chiều — đừng trích recall 0.44 như độ đúng tổng quát.
- **Mean dilution vẫn còn nguyên:** mọi clip giả bị sót đều có khung
  riêng lẻ đạt 0.95–1.0 nhưng đa số khung gần 0 nên trung bình chỉ còn
  0.17–0.27. Luật top-25% lật được cả 5 clip giả bị sót (recall 1.0)
  nhưng đồng thời lật 4–7 video thật sang giả — không dùng được.
- **Nén mạnh (360p, crf 32) làm recall về 0 ở cả v2 lẫn v3** — nén xoá
  sạch tín hiệu giả. Không dùng một mình công cụ này để kết luận trước
  công chúng.
- **Clip Stallman:** video là cảnh quay thật nên video đúng là thật;
  phần giả nằm ở giọng — tách audio ra chấm bằng AASIST cho ra
  likely_fake, P(spoof)=0.9945. Hai kênh bắt hai loại giả khác nhau.
- Tập test còn nhỏ (21 video gốc) nên các chỉ số mang tính tham khảo,
  không phải độ đúng tổng quát; một file đổi verdict làm recall lệch
  ~12 điểm. Kết quả của công cụ là chỉ báo, không phải kết luận chắc
  chắn — câu này cũng in trong mọi kết quả JSON.

## Hiệu chuẩn ngưỡng mờ (đo thật)

Phương sai Laplacian đo trên vùng mặt (không phải cả khung hình — mặt
người vốn mịn hơn nền):

| mẫu | phương sai Laplacian |
|---|---|
| mặt thật sắc nét (phỏng vấn hiện đại, ảnh Lenna) | 212–687 |
| phỏng vấn analog 1985 (nguồn mềm) | 39–68 |
| clip ngoài đời thực (cả thật lẫn giả, nguồn mềm) | 9–41 |
| mặt Lenna làm mờ Gaussian sigma 3 | 3.8 |

Ngưỡng `BLUR_LAP_VAR_MIN = 5.0` chỉ loại vùng gần như đồng màu (mờ nát,
khung lỗi), không loại video mềm bình thường. Ngưỡng 100 kiểu cổ điển
(cho cả khung hình) đã thử và loại sai gần hết clip test. Vì vùng mặt
nhỏ làm phương sai tăng giả nên bộ lọc kích thước (≥64 px) chạy trước
bộ lọc mờ.

## Hiệu chuẩn SyncNet (đo thật, v4, 19/11/2026)

Chạy SyncNet trên 10 video thật của tập test (phỏng vấn + TED trên
YouTube; mỗi video xét tối đa 60 giây đầu). Tham chiếu lab LRS2:
LSE-C ~7.84, LSE-D ~6.74 — **video thật ngoài đời thấp hơn và phân
tán hơn nhiều**, nên ngưỡng gate phải đặt dưới giá trị thật thấp nhất
chứ không lấy theo LRS2.

| Video thật | LSE-C | LSE-D | Track | Thời gian SyncNet |
|---|---|---|---|---|
| Phỏng vấn Straley 1985 (60 giây) | 2.749 | 8.162 | 1 | 620,9 giây |
| TED Amy Cuddy (~55 giây) | 2.705 | 12.207 | 1 | 382,6 giây |
| TED Brené Brown (~55 giây) | 6.834 | 6.792 | 1 | 333,2 giây |
| TED Dan Gilbert (~55 giây) | — (không có track) | — | 0 | 185,7 giây |
| TED Angela Duckworth (~55 giây) | 7.866 | 6.891 | 1 | 240,9 giây |
| TED Ken Robinson (~55 giây) | 7.525 | 6.582 | 2 | 347,8 giây |
| TED Tim Urban (~55 giây) | 8.183 | 5.677 | 1 | 315,6 giây |
| TED Robert Waldinger (~55 giây) | — (không có track) | — | 0 | 309,4 giây |
| Phỏng vấn Sunil Gupta (339 giây, xét 60 giây đầu) | 6.372 | 8.107 | 7 | 402,7 giây |
| TED Simon Sinek (~55 giây) | 7.293 | 7.417 | 2 | 291,6 giây |

LSE-C trên 8 video có track: thấp nhất **2.705**, cao nhất **8.183**,
trung vị **7.06**, trung bình 6.19. Hai video không có track mặt đủ
dài (≥ 2 giây) cho SyncNet — Dan Gilbert và Waldinger (mặt nhỏ / quay
rộng, Waldinger cũng là file `cannot_assess` ở phần mặt). **Ngưỡng
gate `AV_SYNC_GATE_LSE_C_MAX = 2.0`**: dưới giá trị thật thấp nhất
(2.705) với biên ~0.7 — cổng chỉ mở khi track rõ ràng lệch đồng bộ
(lồng tiếng / audio không khớp), và chỉ áp cho verdict đang
`uncertain`. Thời gian SyncNet trung bình ~350 giây/video ~55 giây
(gấp ~6 lần thời lượng) — S3FD chạy trên mọi khung ở 25 fps là nút
cổ chai; dùng `--no-av` để bỏ qua.

**Cẩn thận khi đọc LSE-C:** video thật cũng có thể cho LSE-C ~2.7
(Straley 1985, Amy Cuddy) — quay cũ, cắt cảnh nhiều, mặt hay ở góc
nghiêng hoặc xa. LSE-C thấp một mình không có nghĩa là giả; nó chỉ
có ý nghĩa khi kết hợp với verdict mặt đang `uncertain` và ngưỡng
2.0 đã hiệu chuẩn.

## Kết quả đo thật (bản v4, 19/11/2026)

### Đợt 2a — thống kê điểm từng khung (không model mới)

Bốn thống kê tính từ điểm ensemble từng khung đã thử làm luật gộp
thay thế trên tập gốc 23 file. **Không luật nào được giữ** — tất cả
đều đánh đổi báo nhầm lấy recall:

| Luật gộp thay thế | Recall | Báo nhầm thật | AUC | Kết luận |
|---|---|---|---|---|
| mean (v3, giữ nguyên) | 0.4444 | 0.1111 (1/9) | 0.7778 | baseline |
| top25_mean (trung bình 25% khung cao nhất) | 1.0000 | 0.5556 (5/9) | — | LOẠI |
| worst_window_1s_mean (cửa sổ 1 giây cao nhất) | 1.0000 | 0.6000 (6/10) | 0.51 | LOẠI — suy biến thành max-frame trên video dài |
| frac_frames_ge_09 (tỉ lệ khung ≥ 0.9) | 0.0909 | — | — | LOẠI — recall sụp |
| score_std (độ lệch chuẩn điểm khung) | — | — | 0.529 | LOẠI — không có tín hiệu (thật 0.190 vs giả 0.233) |

Bốn số này vẫn có trong JSON kết quả dưới dạng chẩn đoán
(`top25_mean`, `worst_window_1s_mean`, `frac_frames_ge_09`,
`score_std`) nhưng không đổi verdict.

### Đợt 2b — SyncNet + AASIST trên audio tách từ video

Trước / sau: v3 (ensemble mặt) → v4 (thêm cổng SyncNet + trường
`audio_spoof` tham khảo). Chạy `evaluate.py` với `--jobs 2` trên cả
3 tập.

| Tập | | Accuracy | Precision | Recall | F1 | AUC | Báo nhầm thật |
|---|---|---|---|---|---|---|---|
| Gốc (23 file) | v3 | 0.6667 | 0.8000 | 0.4444 | 0.5714 | 0.7778 | 0.1111 (1/9) |
| Gốc (23 file) | **v4** | **0.6842** | **0.8333** | **0.5000** | **0.6250** | **0.7889** | **0.1111 (1/9)** |
| Nén nặng (8 file) | v3 | 0.5714 | — (0 TP) | 0.0000 | — | 0.6667 | 0.0000 |
| Nén nặng (8 file) | **v4** | **0.5714** | **— (0 TP)** | **0.0000** | **—** | **0.6667** | **0.0000** |
| Giả lập quay màn hình (4 file) | v3 | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 1.0000 | 0.0000 |
| Giả lập quay màn hình (4 file) | **v4** | **0.7500** | **1.0000** | **0.5000** | **0.6667** | **1.0000** | **0.0000** |

Confusion tập gốc v4: TP 5 / FN 5 / TN 8 / FP 1; 19 file kết luận
được, 4 không kết luận. Thời gian trung bình **263 giây/file** (v3:
~50–65 giây) — SyncNet là nút cổ chai.

**Cổng SyncNet chỉ mở đúng 1 lần trên cả 3 tập:**
`fake_simoncowell_5` — điểm mặt 0.5104 (uncertain) + LSE-C 0.418
(≤ 2.0) → likely_fake. Đó là toàn bộ mức tăng recall v3→v4
(TP 4→5). Mọi file uncertain khác đều có LSE-C cao (Ken Robinson
7.525, Tim Urban 8.183) hoặc không có track (Keanu Reeves clip 3
giây, Waldinger).

**Vì sao cổng chỉ áp cho verdict `uncertain`:** video **thật**
nén nặng Straley cho LSE-C **1.976 — dưới ngưỡng 2.0**. Nếu cổng áp
cả cho verdict `likely_real` thì file thật này đã thành báo nhầm.
Ngược lại, 3 clip giả có LSE-C rất thấp nhưng điểm mặt tự tin
`likely_real` (Pattinson 0.605, Simon Cowell 1: 0.47, Tom Cruise
0.916; Pattinson bản quay màn hình 0.42) vẫn bị sót — cổng không cứu
được chúng theo luật hiện tại. Mở rộng cổng sang `likely_real` là
đề xuất cho đợt sau, cần thêm dữ liệu video thật để hiệu chuẩn lại
ngưỡng, không tự ý đổi ở bản này.

**`audio_spoof` trên audio tách từ video không phân biệt được thật
giả** — trung vị 3 cửa sổ (25% / 50% / 75% thời lượng) trên video
thật ~0.95, trên clip giả ~0.98; 7/10 video thật cho trên 0.5.
Trường này chỉ tham khảo, không bao giờ đổi verdict (xem mục Giới
hạn). Riêng file `.wav` giọng thật sạch vẫn đúng (0.054) và giọng
giả Stallman 0.9945.

### Đọc đúng các con số v4 — nói thẳng

- **SyncNet giúp đúng 1 file.** Face-swap thuần vẫn đồng bộ
  (Obama LSE-C 8.298, Jim Carrey 2.564, Cage 2.063, RDJ 2.751) nên
  SyncNet không bắt được chúng; nó chỉ bắt trường hợp lồng tiếng /
  giọng clone không khớp miệng.
- **Nén mạnh vẫn làm recall về 0** ở cả v3 lẫn v4 — nén xoá sạch
  tín hiệu giả lẫn tín hiệu đồng bộ.
- **Giá phải trả là thời gian:** 263 giây/file trung bình (chậm nhất
  Straley 625 giây, nhanh nhất clip ngắn Keanu Reeves 24 giây). Dùng
  `--no-av` khi chỉ cần verdict mặt (~50–65 giây/file).
- Tập test còn nhỏ (23 file gốc) — một file đổi verdict làm recall
  lệch ~5–12 điểm. Các số trên là chỉ báo, không phải độ đúng tổng
  quát.

## Kết quả đo thật — Community Forensics (ảnh tĩnh, v4, 20/11/2026)

**Vấn đề gốc:** ảnh selfie thật của người dùng (chế độ chân dung,
bokeh, làm mịn da) bị ensemble mặt v3 chấm 0.8335 likely_fake
(DeepGuard 0.9868); ảnh AI tạo hoàn toàn bị sót 0.0664 likely_real.
Cả ba model mặt đều chỉ nhìn face crop — không model nào nhìn toàn
ảnh. Community Forensics (OwensLab/commfor-model-384, ViT-S, MIT,
train trên 2,7 triệu ảnh từ 4.803 generator) chấm TOÀN ảnh 384×384,
trả về trường riêng `ai_image_score` (P(AI), sigmoid của 1 logit).

**Tập đo:** WasItAI Frontier Bench 10/2026 (bản public, HF
`wasitaigeneratedcom/frontier-image-video-bench-2026-10`) — 747 ảnh
gốc duy nhất (486 thật + 261 AI từ 19 generator) + 2.229 bản sao qua
WhatsApp/Instagram/reshare (mô phỏng pipeline điện thoại + nén lại
qua Zalo/Facebook). Tổng 2.976 ảnh. Đo bằng `eval_commfor_wasitai.py`
(CommFor, ~0,8 giây/ảnh).

| Tập | AUROC | Recall @1% FPR | FPR @0.5 | Recall @0.5 |
|---|---|---|---|---|
| Ảnh gốc (747) | 0.7628 | 0.2874 | 0.0453 (22/486) | 0.3870 |
| Qua WhatsApp/IG/reshare (2.229) | 0.6740 | 0.1507 | 0.0062 (9/1.446) | 0.1315 |
| Tất cả (2.976) | 0.6925 | 0.1590 | 0.0160 (31/1.932) | 0.1954 |

Recall @0.5 trên ảnh gốc theo từng generator (n): hidream-o1-image
1.000 (16), flux-2 0.923 (13), krea-2/turbo 0.875 (16),
kling-image/v3 0.700 (10), qwen-image-2512 0.600 (10), z-image/turbo
0.545 (11), nano-banana-2.1 0.500 (14), ideogram/v4.5 0.412 (17),
luma 0.308 (13), qwen-image-3 0.267 (15), mai-image-2.5 0.250 (12),
nano-banana-pro 0.250 (20), gpt-image-2 0.250 (12), flux-2-pro 0.176
(17), flux-3 0.091 (11), muse-image 0.083 (12), seedream/v5/pro
0.071 (14), recraft/v4.1 0.062 (16), **grok-imagine-image/v2.0 0.000
(12)**. CommFor bắt tốt generator cũ/gần dữ liệu train, gần như mù
trước generator frontier mới nhất (Grok Imagine, Muse, Recraft,
Seedream). Ảnh qua WhatsApp/Instagram/reshare mất gần hết tín hiệu
AI (recall 0.387 → 0.132) nhưng đồng thời cũng ít báo nhầm ảnh thật
hơn (FPR 0.045 → 0.006).

**So sánh với baseline (ensemble mặt v3) trên cùng 92 ảnh có mặt
(49 AI + 43 thật, đo bằng `eval_face_subset.py`):**

| Detector | AUROC | Recall @0.5 | FPR @0.5 |
|---|---|---|---|
| Ensemble mặt v3 (baseline) | 0.5899 | 0.5306 | **0.4186** |
| **Community Forensics** | **0.8958** | 0.4694 | **0.0465** |

Quy tắc chọn (định trước, giống v3): chỉ giữ detector mới nếu AUROC
tăng VÀ FPR trên ảnh thật không tăng. **CommFor ĐẠT cả hai, rõ rệt:**
AUROC 0.590 → 0.896, FPR 0.419 → 0.047. Ensemble mặt báo nhầm ~42%
ảnh mặt thật (dima806/prithiv cho điểm cao trên mặt thật — đã biết
từ v3) nên không thể giữ làm verdict chính cho ảnh tĩnh.

**Quyết định:** từ v4, **verdict ảnh tĩnh lấy từ `ai_image_score`
(CommFor)**; điểm ensemble mặt giữ lại làm trường phụ (`face_score` /
`face_verdict`) vì nó là detector duy nhất ở đây bắt được face-swap
trong một ảnh vốn là thật. Nếu CommFor lỗi, verdict rơi về ensemble
mặt.

**Kiểm tra hồi quy (2 ảnh người dùng gửi, KHÔNG dùng làm tiêu chí
chọn — chỉ báo cáo):**

| Ảnh | v3 (ensemble mặt) | v4 (CommFor) |
|---|---|---|
| Selfie thật (chân dung, bokeh, làm mịn) | 0.8335 likely_fake (SAI) | **0.0227 likely_real (ĐÚNG)** |
| Ảnh AI tạo hoàn toàn (generator mới) | 0.0664 likely_real (SAI) | 0.1098 likely_real (vẫn SAI, nhưng cao hơn) |

Selfie đã sửa. Ảnh AI vẫn sót ở cả hai bản — CommFor mù trước
generator frontier mới nhất, đúng như số liệu WasItAI ở trên
(grok-imagine 0.000, muse 0.083). Đây là giới hạn thật của detector
mở hiện tại, không phải lỗi cài đặt (đã kiểm chứng preprocessing và
sigmoid khớp đúng code gốc của repo Community Forensics).

## Kết quả đo thật — DeCoF (video toàn khung, v4, 20/11/2026)

**Mô hình:** DeCoF — CLIP ViT-L/14 đóng băng + đầu transformer 2
lớp, chấm 8 khung toàn cảnh lấy đều từ 32 khung đầu, trả về trường
riêng `ai_video_score`. Weights là bản **train lại 28/02/2026** trên
dataset cập nhật (weights gốc của bài báo đã mất khi chuyển server);
**không tìm thấy giấy phép** trong repo DeCoF lẫn dataset
AIGVDBench — xem lưu ý giấy phép ở mục mô hình.

**Tập đo:** AIGVDBench test split — 25 video/generator × 6 generator
(Sora, Pika, Luma, Vidu, Kling, SVD = 150) + WasItAI video gốc
(grok-video-1.5 12, kling-v3 12, veo3-fast 4, thật 25 = 53) + 10
video thật có sẵn (TED talks) + 8 bản nén/screenrec + clip Grok
Imagine của người dùng. Tổng **220 video**, đo bằng
`eval_decof_aigvd.py` (--jobs 2), ~44 giây/video. Đã kiểm chứng
parity đặc trưng CLIP khớp đúng 0.000000 với `openai/clip`
encode_image, và preprocessing (Resize 224 squash + ImageNet norm)
khớp đúng code gốc.

**Kết quả (ngưỡng 0.5, bản gốc — không tính bản nén/screenrec):**

| | AUROC | Recall @0.5 | FPR @0.5 |
|---|---|---|---|
| Tất cả (179 AI, 35 thật) | **0.6180** | **0.2235** | **0.2571 (9/35)** |

Recall @0.5 theo từng generator (n): svd 0.520 (25), luma 0.280
(25), pika 0.240 (25), vidu 0.200 (25), kling 0.200 (25), sora
0.120 (25), grok-video-1.5 0.083 (12), kling-v3 0.000 (12),
veo3-fast 0.000 (4), **clip Grok Imagine của người dùng 0.000
(P(fake) = 0.0001 — sót hoàn toàn)**. AUROC theo từng generator
0.36–0.74, trung bình 0.5276 — gần như ngẫu nhiên.

**Kết luận: DeCoF (bản train lại 2026) KHÔNG ĐẠT quy tắc chọn.**
Nó không tách được video AI khỏi video thật trên tập này, và KHÔNG
được dùng để đổi verdict — chỉ giữ làm trường chẩn đoán
(`ai_video_score`). Hai bằng chứng:

1. **Recall quá thấp ở ngưỡng 0.5** (0.22) — thấp hơn nhiều so với
   ~92 AUC mà bài báo cáo (đó là với weights gốc, nay đã mất).
   Đặc biệt, nó sót hoàn toàn clip Grok Imagine của người dùng và
   gần như toàn bộ video Grok/Kling/Veo3 của WasItAI — đúng các
   generator mới nhất mà người dùng cần bắt.
2. **Hai tập video thật hành xử ngược nhau** — video TED talks thật
   chấm CAO (0.61–0.998, 7/10 báo nhầm), trong khi video thật
   WasItAI chấm THẤP (trung bình 0.088, 2/25 báo nhầm). Đảo ngược
   thứ tự class (softmax[:, 0] thay vì [:, 1]) thì recall lên 0.78
   nhưng FPR nổ lên 0.74 và AUROC rớt xuống 0.38 — vì đảo ngược sửa
   được TED talks nhưng phá hỏng WasItAI thật. Đầu này không bắt
   "AI hay thật" mà bắt một đặc tính khác (nhiều khả năng là
   talking-head tĩnh so với cảnh đa dạng). Đã kiểm chứng: thứ tự
   class trong code giữ đúng như repo gốc (label 1 = fake,
   `init_ff` ghi rõ fake=1, real=0); vấn đề nằm ở weights train
   lại, không phải code.

**Hệ quả thực tế:** verdict video vẫn lấy từ ensemble mặt (+ cổng
SyncNet) như v3/v4; `ai_video_score` chỉ để tham khảo. Muốn bắt
video AI thế hệ mới cần một detector khác (xem mục v5).

## Kết quả đo thật — v5 (20/11/2026)

### Video toàn khung: Community Forensics thay DeCoF

**Thay đổi:** `ai_video_score` giờ là Community Forensics chấm 8
khung toàn cảnh (cùng cách lấy mẫu với DeCoF: 8 khung đều từ 32
khung đầu, xử lý theo lô ~14 giây/video thay vì ~44 giây của DeCoF).
DeCoF chuyển thành trường chẩn đoán riêng `decof_score`, chỉ tính
khi chạy `--ai-video`.

**Tập đo:** đúng 220 video DeCoF từng đo ở v4 (AIGVDBench 150 +
WasItAI 53 + 10 video thật TED + clip Grok Imagine của người dùng
+ 6 video thật khác). Đo bằng `eval_commfor_video.py` (CommFor
theo lô, batch 8).

| | AUROC | Recall @0.5 | FPR @0.5 |
|---|---|---|---|
| **CommFor-frames (mean)** | **0.9239** | **0.6034** | **0.0000 (0/41)** |
| CommFor-frames (max) | 0.9254 | 0.7151 | 0.0488 (2/41) |
| CommFor-frames (median) | 0.9161 | 0.6034 | 0.0000 (0/41) |
| DeCoF (v4, cùng 220 video) | 0.4488 | 0.7765 | 0.6585 (27/41) |

Recall @0.5 theo từng generator (mean, n): svd 1.000 (25), luma
0.920 (25), pika 0.800 (25), kling 0.560 (25), sora 0.520 (25),
vidu 0.440 (25), grok-video-1.5 0.083 (12), kling-v3 0.083 (12),
veo3-fast 0.000 (4), **clip Grok Imagine của người dùng 0.000
(n=1 — nhưng ensemble mặt bắt được nó ở 0.8436)**. Max aggregate
bắt nhiều hơn (recall 0.715) nhưng là quy tắc 1-khung-đơn-lẻ, và
v3 đã chứng minh quy tắc đó tăng báo nhầm video thật — nên
**mean** là số báo cáo (`ai_video_score`), max chỉ là trường chẩn
đoán (`ai_video_frames.max`).

**Giới hạn quan trọng:** CommFor-frames chấm **0/11 video
face-swap** ở tập tests23 (điểm 0.000–0.483) — đúng như dự kiến:
face-swap là khung hình camera thật, chỉ mặt bị đổi, nên detector
toàn ảnh không thấy gì. Hai detector bắt hai loại giả khác nhau:
CommFor-frames bắt video AI tạo toàn cảnh (Sora/Kling/Pika/Luma/
SVD), ensemble mặt bắt face-swap. Quy tắc gộp đã thử (mặt
`uncertain`/`cannot_assess` + `ai_video_score` ≥ 0.6 → likely_fake)
**không đổi gì** trên tests23 (TP 5, FPR 0.143, y hệt chỉ dùng
mặt) nên **không áp dụng** — `ai_video_score` giữ làm trường
riêng, người đọc tự kết hợp với verdict mặt.

### Ảnh tĩnh: DDA đã đo và BỊ LOẠI (không dùng)

**Thử:** DDA (Dual Data Alignment, NeurIPS 2025, DINOv2-large +
LoRA rank 8, Apache-2.0) làm detector ảnh thứ hai, blend trung
bình với Community Forensics. Checkpoint đã tải và đo thật
(1.255.621.296 byte).

**Trên ảnh gốc (WasItAI, cùng 207 ảnh):**

| | AUROC | FPR @0.5 | Recall @0.5 |
|---|---|---|---|
| CommFor | 0.7620 | 0.0280 (3/107) | 0.3800 (38/100) |
| DDA | 0.7337 | 0.2617 (28/107) | 0.6700 (67/100) |
| **Blend trung bình** | **0.7914** | **0.0187 (2/107)** | **0.4300 (43/100)** |

Blend thắng trên ảnh gốc ở mọi chỉ số. Nhưng **DDA sụp đổ hoàn
toàn trên ảnh đã qua xử lý điện thoại** (làm mịn da): trên 45 ảnh
thật đã làm mịn, DDA chấm trung bình **0.927**, FPR **1.000
(45/45)** — ảnh thật chấm CAO HƠN ảnh AI (0.859), AUROC **0.491**
(tệ hơn ngẫu nhiên). DDA đọc \"không còn texture tự nhiên\" thành
\"giả\", nên mọi ảnh làm mịn da đều bị nó kết luận là giả. Hậu quả
cho blend: ở trọng số DDA 0.5, FPR trên ảnh làm mịn là **0.511**;
trọng số 0.3 → 0.267; 0.2 → 0.178; 0.1 → 0.133 (bằng CommFor)
nhưng lúc đó blend chỉ còn là \"CommFor + một nhúm DDA\" (AUROC
gốc +0.020, recall gốc −2 ảnh) — không đáng +1,26 GB và ~10
giây/ảnh. **Kết luận: DDA không được dùng trong v5.** Code và
checkpoint không ship; toàn bộ số đo giữ trong `df-v5-scratch/`
(`eval_dda.py`, `weight_sweep.py`).

### Ảnh tĩnh: làm nét / thêm nhiễu (test-time) đã đo và BỊ LOẠI

**Thử:** chấm CommFor trên ảnh đã làm nét (unsharp mask) hoặc thêm
nhiễu Gaussian, hy vọng khôi phục texture cho ảnh thật đã làm mịn.
Đo trên 80 ảnh thật đã làm mịn + 16 ảnh AI gốc:

| Biến thể | FPR ảnh thật làm mịn | Recall ảnh AI |
|---|---|---|
| Gốc (asis) | 0.225 (18/80) | 0.188 (3/16) |
| Unsharp 1.0 | 0.188 (15/80) | **0.000 (0/16)** |
| Unsharp 2.0 | 0.175 (14/80) | **0.000 (0/16)** |
| Nhiễu σ=5 | 0.438 (35/80) | 0.000 (0/16) |

Làm nét giảm báo nhầm thật một chút (18→14/80) nhưng **xóa sạch
recall AI** (3→0/16) — vì nó thêm texture giả vào ảnh AI, che mất
tín hiệu \"quá mịn\" mà CommFor dùng để bắt AI. Thêm nhiễu còn tệ
hơn: báo nhầm thật tăng gấp đôi. **Kết luận: không dùng biến thể
test-time nào.** (Số đo đầy đủ trong `df-v5-scratch/`
`eval_sharpen.jsonl`.)

### Tập đo mới: ảnh đã qua xử lý điện thoại (phoneproc)

Đã tạo **2.988 biến thể** từ 747 ảnh gốc WasItAI (mỗi ảnh × 4):
`jpeg75` (nén lại q75), `smooth` (làm mịn da bilateral + q85),
`bokeh` (mô phỏng chụp chân dung: mặt nét, nền mờ), `downscale`
(thu về cạnh dài 1080 + q70, mô phỏng Zalo/Facebook). CommFor
FPR @0.5 trên ảnh thật (n=280/biến thể): jpeg75 **0.007**, smooth
**0.193**, bokeh **0.029**, downscale **0.007**; ảnh gốc 0.045.
**Làm mịn da là thủ phạm chính gây báo nhầm** (19,3% ảnh thật đã
làm mịn bị chấm ≥ 0.5), không phải nén hay thu nhỏ. Tập này giữ
lại làm thước đo chuẩn cho v6 (file + manifest trong
`df-v5-scratch/phoneproc/`).

## Chế độ trực tiếp — live.py (mới ở v6, 20/11/2026)

`live.py` chấm một khung hình mỗi `--interval` giây từ nguồn trực
tiếp và in verdict lăn (rolling mean 5 khung gần nhất) ngay khi đang
chạy — để dùng trong lúc gọi video, thay vì chấm file sau khi quay
xong. Đây là **lấy mẫu gần-thời-gian-thực, không phải phân tích 30
fps**: một khung tốn ~2–3 giây trên CPU (MTCNN + 3 model mặt +
CommFor), nên `--interval 3.0` là mặc định thực tế; máy khỏe hơn có
thể giảm interval, máy yếu phải tăng lên. Khi chấm chậm hơn thời gian
thật, chương trình báo rõ thay vì lặng lẽ tụt lại phía sau.

**Nguồn:**
- `webcam` (mặc định): camera mặc định (`cv2.VideoCapture(0)`).
- `screen`: một vùng màn hình chính (mss) — chỉ vào ô video của
  người đối diện trong cuộc gọi. `--region L,T,W,H` (mặc định: cả
  màn hình chính). Cần `mss` (đã có trong requirements.txt).
- `file`: một file video phát theo đúng tốc độ thời gian thật
  (mô phỏng luồng trực tiếp — để test trên máy không có camera/màn
  hình, và để kiểm tra lại một cuộc gọi đã ghi). File mode tự seek
  tới khung ở thời điểm hiện tại, không bò lần lượt từ khung 0.

**Verdict:** rolling mean của điểm ensemble mặt trên `--window`
khung gần nhất (cùng ngưỡng 0.40/0.60 như check.py) — một khung lẻ
không bao giờ lật verdict. Điểm CommFor toàn khung báo kèm, và cảnh
báo khi nó cao trong khi mặt bảo thật; nó KHÔNG tự đổi verdict.
`--verdict-mode max` (lấy max của hai rolling mean) là THỬ NGHIỆM:
trên 21 video tests23 (proxy toàn video, không phải rolling trực
tiếp) nó đổi 2 verdict (recall 0.44 → 0.50, FPR 0.14 → 0.13) —
trong khoảng nhiễu, chưa chứng minh được hơn. Mặc định là `face`.

**Cách dùng:**

```
python live.py                                  # webcam, 3 giây/khung
python live.py --source screen --region 100,100,640,480
python live.py --source file call.mp4 --duration 60
python live.py --source file call.mp4 --interval 2 --log live.jsonl
```

**Đo thật trên máy ảo (file mode, `--threads 2` mặc định):**

| Nguồn | Kết quả |
|---|---|
| Clip Grok Imagine 8 s (giả), interval 2 s, 9 s | 4 khung, mặt 0.877 / 0.136 / 0.843 / 0.874 (trung bình 0.682), verdict lăn likely_fake → uncertain → likely_fake → likely_fake. Nạp model 40 s. Mỗi khung ~2,0–2,7 s (mặt 1,5–2,2 s + CommFor 0,5–0,6 s). |
| test_video thật 339 s, interval 3 s, 30 s | 10 khung (7 khung không có mặt — đoạn B-roll đầu video), mặt khi có: 0.155 / 0.158 / 0.122 (trung bình 0.140), verdict lăn likely_real suốt, không báo nhầm. Nạp model 29 s. |

**Giới hạn:** webcam và screen **chưa test được trên máy ảo này**
(không có camera/màn hình) — chỉ test file mode; người dùng cần tự
chạy `python live.py` trên laptop để kiểm chứng webcam/screen.
Nạp model lần đầu tốn ~30–40 giây (sau đó mới bắt đầu chấm). Face-
swap giữ nguyên miệng + giọng của người nguồn nên vẫn đồng bộ và
trông thật từng khung — không detector khung nào bắt được mọi trường
hợp; verdict là chỉ báo, không phải kết luận (cùng disclaimer như
check.py).


## Tốc độ đo thật (v5, 20/11/2026)

Đo trên máy ảo test (1,5 CPU chia sẻ, bị throttle — chậm hơn laptop
thật), máy rảnh, mỗi trường hợp chạy subprocess mới (nạp model lạnh).
Mục tiêu người dùng: **< 30 giây/video trên CPU laptop**.

| Chế độ | File | Thời gian wall (VM) | Verdict |
|---|---|---|---|
| Mặc định (mặt + CommFor-frames + SyncNet/AASIST) | Clip Grok Imagine 8s | **99,9 giây** | likely_fake 0.8436 |
| Mặc định + `--ai-video` (thêm DeCoF) | Clip Grok Imagine 8s | **173,1 giây** | likely_fake 0.8436 |
| `--no-av` (mặt + CommFor-frames) | Clip Grok Imagine 8s | **27,4 giây** | likely_fake 0.8436 |
| `--no-av --threads 2` | Clip Grok Imagine 8s | **12,5 giây** | likely_fake 0.8436 |
| `--no-av --threads 4` | Clip Grok Imagine 8s | **11,1 giây** | likely_fake 0.8436 |
| `--no-av` | test_video thật 339s | **10,6 giây** | likely_real 0.1642 |
| Ảnh tĩnh | Selfie thật | **5,3 giây** | likely_real 0.0227 |
| Ảnh tĩnh | Ảnh AI | **5,3 giây** | likely_real 0.1098 (sót) |
| Ảnh tĩnh | lenna.png | **5,3 giây** | likely_real 0.0003 |

**So với v4:** `--no-av` trên clip Grok từ 58 giây → **27,4 giây**
(nhanh 2,1 lần) — vì CommFor-frames (~14 giây/video, xử lý theo lô)
thay DeCoF (~44 giây/video + nạp CLIP 933 MB). `--threads 2` còn
đưa xuống **12,5 giây**. Pipeline đầy đủ từ 112 → 99,9 giây (vẫn
chậm vì SyncNet chiếm ~60–70%). **Mục tiêu < 30 giây/video trên
laptop giờ ĐẠT cả trên máy ảo chậm này ở chế độ `--no-av`** (27,4
giây), và đạt thoải mái với `--threads 2` (12,5 giây). Trên laptop
4–8 nhân thật sẽ còn nhanh hơn. Dùng `--no-av` (thêm `--threads 2`
nếu máy nhiều nhân) khi cần nhanh; chỉ chạy đầy đủ khi cần cờ
SyncNet (nghi lồng tiếng/giọng clone). `--ai-video` (DeCoF) chỉ
dùng khi cần đối chiếu chẩn đoán — nó tốn thêm ~73 giây và không
đổi verdict.

**Nút thắt còn lại:** SyncNet (S3FD chạy trên mọi khung ở 25 fps)
chiếm ~60–70% thời gian pipeline đầy đủ; phần còn lại là nạp model
(~8 giây wall) + ensemble mặt + CommFor-frames. Ảnh tĩnh đã nhanh
(5,3 giây) nhờ CommFor chỉ ~1 giây/ảnh. Đã thử chế độ `--fast`
(8 khung thay vì 32): không nhanh hơn `--no-av` và cho
`cannot_assess` trên video dài — đã gỡ từ v4, không ship.

## Giới hạn cần nhớ (đừng ghi số liệu quá lời vào báo cáo)

- Mô hình ảnh/video chính train trên FaceForensics++ (c23) — dữ liệu
  phòng lab. Trên clip giả ngoài đời thực, độ nhạy chỉ ~0.50 ở tập test
  nhỏ này (v4/v5); clip giả làm tốt hoặc nén mạnh có thể lọt. Hai model
  ViT gộp thêm train trên mặt GAN, không phải face-swap video — đo
  thật cho thấy chúng gần như không phân biệt được thật/giả trên tập
  này (dima806 báo nhầm thật 0.625, prithiv v2 0.625 khi đứng một
  mình); ensemble chỉ giữ lại được nhờ trọng số DeepGuard 0.8.
  **Video AI tạo toàn cảnh** (không phải face-swap) giờ được bắt
  thêm bởi CommFor-frames (`ai_video_score`, v5: AUROC 0.924 trên 220
  video) — nhưng các generator mới nhất (Grok Imagine, Veo 3,
  Kling v3) vẫn sót nhiều (recall 0.00–0.08).
- Video thật vẫn có khung cho điểm P(fake) rất cao (phỏng vấn 1985:
  5/32 khung đạt 0.78–1.0; TED cũ: khung đạt 1.0) — đó là lý do không
  dùng luật max-frame hay top-25%. Và vì cùng hiện tượng này, chỉnh
  ngưỡng hay luật gộp điểm không tách được clip giả sạch khỏi footage
  thật cũ.
- Cả ba mô hình train trên dữ liệu tiếng Anh/chung, chưa có dữ liệu
  tiếng Việt; file nén qua Zalo/Facebook làm độ đúng tụt mạnh.
- Bản "quay màn hình" trong tập test v2 là **giả lập** (nghiêng phối
  cảnh + nhiễu + 24fps), chưa phải clip quay thật từ điện thoại.
  **Ảnh thật đã làm mịn da (portrait/bộ lọc) vẫn báo nhầm nhiều:**
  CommFor FPR @0.5 là 0.193–0.200 trên ảnh thật đã làm mịn (n=280–505)
  so với 0.045 trên ảnh gốc — đây là thủ phạm báo nhầm chính ở v5,
  hai cách đã thử (blend DDA, làm nét/thêm nhiễu test-time) đều bị
  loại sau khi đo (xem mục kết quả v5). Cần ảnh thật quay bằng điện
  thoại (chưa có) để đo FPR thực tế.
- Audio tách từ video xét 3 cửa sổ (25% / 50% / 75% thời lượng, lấy
  trung vị); video dài xử lý chậm hơn (khoảng 50–65 giây cho 32 khung
  trên CPU vì chấm 3 model lần lượt, cộng ~6 lần thời lượng nếu chạy
  SyncNet).
- **AASIST trên audio tách từ video báo nhầm rất cao — đừng dùng làm
  verdict.** Đo thật: P(spoof) ở 4 giây đầu trên 9 video thật là
  0.004–0.9997, trung vị 0.54 (5/9 trên 0.5); trung vị 3 cửa sổ trên
  giọng TED thật (Ken Robinson) là 0.995. Trong khi file `.wav` giọng
  thật sạch cho 0.054. Đã loại trừ nguyên nhân: nén Opus 98k/AAC
  128k trên giọng sạch vẫn 0.045–0.05; thêm vang nhân tạo vẫn 0.023;
  kênh trái/phải/trộn trên audio TED đều 0.9958. Cơ chế gây nhầm chưa
  xác định (nghi do thu âm hội trường + xử lý phát sóng, chưa chứng
  minh) — vì vậy `audio_spoof` chỉ là trường tham khảo, không bao giờ
  đổi verdict. AASIST vẫn phân biệt tốt trên file `.wav` sạch (giọng
  thật 0.054; giọng giả Stallman 0.9945).
- **SyncNet không bắt được face-swap thuần** — miệng và tiếng cùng
  lấy từ người nguồn nên clip vẫn đồng bộ; nó chỉ bắt trường hợp lồng
  tiếng / giọng clone không khớp miệng. LSE-C trên video thật dao động
  2.7–8.2 (không phải lúc nào cũng ~7.8 như dữ liệu lab LRS2); clip
  ngắn (< ~6 giây) hay mặt nhỏ thường không có track SyncNet
  (`av_sync: null`). Chạy SyncNet tốn ~6 lần thời lượng video trên
  CPU — dùng `--no-av` khi không cần.
- **Community Forensics mù trước generator ảnh frontier mới nhất.**
  Đo trên WasItAI: recall @0.5 trên ảnh gốc là 0.000 với
  grok-imagine-image/v2.0 (12), 0.083 muse-image (12), 0.062
  recraft/v4.1 (16), 0.071 seedream/v5/pro (14) — trong khi bắt tốt
  generator cũ (hidream 1.000, flux-2 0.923). Ảnh qua WhatsApp /
  Instagram / reshare mất gần hết tín hiệu AI (recall 0.387 → 0.132).
  Đây là giới hạn của detector mở hiện tại, không phải lỗi cài đặt.
- **DeCoF (bản train lại 2026) KHÔNG tách được video AI khỏi video
  thật trên tập đo** (AUROC 0.618, recall @0.5 0.224, FPR @0.5 0.257;
  sót hoàn toàn clip Grok Imagine và gần như toàn bộ video Grok /
  Kling / Veo3 của WasItAI). Nó chỉ là trường chẩn đoán
  (`ai_video_score`), không bao giờ đổi verdict. Weights là bản train
  lại 2026, **giấy phép chưa xác minh** — không dùng cho sản phẩm
  thương mại.
- Mỗi lần chạy chỉ nạp một model tại một thời điểm để nhẹ RAM (máy
  kiểm chứng có ~800 MB RAM trống khi chạy; một model ViT chiếm
  ~350 MB).

## AI ngoài — có nên dùng thêm? (nghiên cứu 19/11/2026)

Muốn tăng độ đúng thì có 2 hướng: (1) thêm detector chuyên biệt chạy
local, (2) hỏi mô hình thị giác đa dụng (VLM) qua API cho các ca
`uncertain`. Nói thẳng: **VLM không phải phép màu tăng accuracy** — nó
chỉ nhìn artifact thấy được và dễ bị face-swap làm kỹ qua mặt; detector
chuyên biệt thứ hai giúp nhiều hơn, nhưng bắt buộc phải chạy lại
`evaluate.py` trên tập test trước khi tin (số accuracy tự báo trên
trang model là trong phân phối train, không phải ngoài đời thực).

**Phát hiện kỹ thuật quan trọng:** Hugging Face hub client bị treo,
nhưng tải trực tiếp bằng `curl -L
https://huggingface.co/<repo>/resolve/main/<file>` **chạy được** (đã đo:
file 343 MB tải đủ trong 13–35 giây, ~26 MB/s). Nghĩa là ensemble local
tải được ngay, không cần tải tay — chỉ cần tránh `hf_hub_download` /
transformers tự tải, hoặc đặt `HF_HUB_ENABLE_HF_TRANSFER=0`.

### Bảng khuyến nghị (theo thứ tự ưu tiên)

| Ưu tiên | Cần key gì | Dùng để làm gì | Lợi ích thực tế | Làm ngay hay sau | Chi phí/check |
|---|---|---|---|---|---|
| 1 — **ĐÃ LÀM ở v3 (19/11/2026)** | **Không cần key** | Ensemble local: thêm **dima806/deepfake_vs_real_image_detection** + **prithivMLmods/Deep-Fake-Detector-v2-Model** (ViT, 343 MB mỗi model, Apache-2.0) chấm cùng face crop, gộp điểm với DeepGuard | **Kết quả đo thật: gần như không giúp.** Luật tốt nhất (0.8 DeepGuard + 0.1 + 0.1) chỉ tăng recall 0.375 → 0.444 (đúng 1 file) mà không tăng báo nhầm; mọi luật khác đều tăng báo nhầm. Đứng một mình, dima806 báo nhầm thật 0.625, prithiv v2 0.625 — cả hai đều train trên mặt GAN, không phải face-swap video. Chi tiết xem bảng so sánh ở mục kết quả. | — | $0 |
| 2 — NGAY | **Không cần key** | Ensemble audio: thêm **mo-thecreator/Deepfake-audio-detection** (Wav2Vec2, Apache-2.0) chấm cùng file `.wav` với AASIST | Giọng giả có thêm phiếu phụ; rẻ và dễ | NGAY | $0 |
| 3 — NGAY | **Gemini API key (`GEMINI_API_KEY`)** — tạo tại https://aistudio.google.com/api-keys | Ý kiến thứ hai **chỉ cho ca uncertain (0.4–0.6)**: gửi 2–3 face crop + prompt JSON cố định, model **`gemini-2.5-flash-lite`** (hoặc `gemini-3.5-flash-lite`) | Giúp được một phần nhỏ ca uncertain; không dùng làm verdict chính, không dùng cho mọi file | NGAY (free tier) | $0 (free tier); trả phí ~$0.0002/check (Flash-Lite) / ~$0.0007/check (3.5 Flash-Lite) — ước tính |
| 4 — SAU | **OpenAI API key (`OPENAI_API_KEY`)** — https://platform.openai.com/api-keys | Dự phòng thay Gemini: **`gpt-6-luna`** (GPT-4o đã deprecated, tắt 14/01/2027 — đừng tích hợp mới vào GPT-4o) | Tương đương Gemini, rẻ ngang Flash-Lite, nhưng phải nạp tiền trước; không có bằng chứng tốt hơn Gemini | SAU (chỉ khi cần) | ~$0.0003/check (ước tính) |
| 5 — SAU / có thể bỏ | **Groq API key (`GROQ_API_KEY`)** — https://console.groq.com/keys | Ý kiến thứ hai bằng **Qwen `qwen/qwen3.8-27b` (preview)** | Yếu nhất: Llama 4 đã chết trên Groq (Scout/Maverick deprecated), Qwen còn preview, đắt nhất/check (~$0.006), vision chưa kiểm chứng chắc chắn | SAU, chỉ nếu đã có sẵn key Groq | ~$0.006/check (ước tính) |
| KHÔNG làm | — | DeepClip b0 (gated + cùng backbone DeepGuard, Celeb-DF AUC chỉ 0.68), Organika/sdxl-detector (chỉ ảnh diffusion, CC-BY-NC), CViT (repo chết), GPT-4o, Llama 4 trên Groq | Không thêm giá trị hoặc đã hết hạn | — | — |

**Giá đã kiểm chứng (trang chính thức, đọc 19/11/2026):** Gemini
https://ai.google.dev/gemini-api/docs/pricing — 2.5 Flash-Lite $0.10
input / $0.40 output, 3.5 Flash-Lite $0.30 / $2.50 per 1M token; 2.5
Flash deprecated, từ 01/12/2026 tự route sang 3.5 Flash-Lite. Groq
https://console.groq.com/docs/models — Qwen qwen3.8-27b $0.80 / $4.00.
OpenAI GPT-6 Luna $0.10 / $0.50 (nguồn thứ cấp thống nhất, chưa đối
chiếu trực tiếp platform.openai.com). Mọi "chi phí/check" là ước tính
từ giả định token (Gemini ~258 token/ảnh ≤384px; Groq 2.048 token/ảnh;
OpenAI ~765 token/ảnh) — không hãng nào niêm yết giá theo check.

**Cẩn thận khi code ensemble:** dima806 `id2label = {0: Real, 1: Fake}`;
prithiv v2 `{0: Realism, 1: Deepfake}`; nhưng Siglip2 ngược
`{0: Fake, 1: Real}`; audio mo-thecreator `{0: fake, 1: real}` — map
theo **tên label, không theo index**. Cho cùng face crop MTCNN 224×224
vào từng model rồi mới gộp điểm.

**Riêng tư:** ensemble HF local — video không rời khỏi laptop. Gemini /
Groq / OpenAI — **frame ảnh gửi lên hãng**; free tier Gemini ghi rõ nội
dung có thể dùng để cải thiện sản phẩm, paid tier thì không.

## Xử lý sự cố

- **Lần chạy đầu tải weights lâu hoặc lỗi mạng:** chạy lại
  `python download_weights.py` — file tải dở sẽ tự nối tiếp (HTTP
  Range). Nếu một link chết hẳn, tải tay file đó theo bảng mô hình ở
  trên rồi đặt vào đúng đường dẫn trong bảng.
- **Lần chạy đầu bị treo ở bước nạp mô hình:** không xảy ra nếu weights
  đã đủ — code tự đưa weights vào cache của torch trước khi nạp mô
  hình, đồng thời bật chế độ offline của Hugging Face hub để không chờ
  mạng. Nếu thiếu file weights, chương trình báo lỗi ngay thay vì treo.
- **Lỗi thiếu `transformers` hoặc model ViT không nạp được:** cài lại
  từ `requirements.txt` (đã ghim `transformers==4.57.1`). Hai model
  ViT được nạp từ thư mục local `weights/dima806/` và
  `weights/prithiv_v2/` bằng `local_files_only=True` — code không bao
  giờ tải model qua hub client. Nếu thiếu `model.safetensors` trong
  các thư mục đó, chạy `python download_weights.py`.
- **Máy hết RAM khi chạy video:** code đã chấm từng model một (nạp,
  chấm hết các khung, gỡ) để giữ RAM đỉnh thấp, nhưng một model ViT
  vẫn chiếm ~350 MB; máy cần ít nhất ~1,5 GB RAM trống. Giảm
  `--max-frames` (ví dụ 16) để chạy nhanh và nhẹ hơn.
- **Không có ffmpeg:** code tự dùng OpenCV để cắt khung hình.
- **`torchvision::nms does not exist`:** torch bản CUDA đã được cài
  đè lên bản CPU — xoá venv, cài lại từ `requirements.txt` (xem mục
  cài đặt).
- **Check `.wav` báo thiếu file `aasist/...`:** chạy
  `python download_weights.py` để tải mã nguồn AASIST; kiểm tra ảnh /
  video không cần các file này.

## Cấu trúc

```
check.py              CLI kiểm tra 1 file
detector.py           logic chung: dò mặt, cắt mặt, chấm điểm, gộp điểm
download_weights.py   tải weights + mã nguồn AASIST lần đầu (urllib, không cần key)
evaluate.py           benchmark trên 2 thư mục real/ và fake/
api.py                FastAPI: POST /deepfake/check, GET /health
requirements.txt      dependencies đã ghim phiên bản (CPU-only)
README.md             tài liệu này
weights/              (tạo ở lần chạy đầu) DeepGuard .bin + backbone .pth + AASIST .pth + dima806/ + prithiv_v2/ (mỗi thư mục: model.safetensors + config.json + preprocessor_config.json)
aasist/               (tạo ở lần chạy đầu) mã nguồn + config mô hình AASIST
```

Bản đầy đủ kèm file test (`tests/`, 23 file mẫu + bản nén + bản giả
lập quay màn hình) là file zip v2/v3 đầy đủ; bản light này chỉ khác ở
chỗ không kèm weights và file test — code và kết quả đo là như nhau.
