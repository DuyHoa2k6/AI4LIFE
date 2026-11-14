# PhoBERT cục bộ — bản nghiên cứu

Đã có mã chuẩn bị dữ liệu, validator, tách từ và ánh xạ bằng chứng, huấn luyện từng task, inference, so sánh baseline, đồ thị suy luận và tích hợp API. Đã chạy encoder PhoBERT thật trên CPU, huấn luyện head, overfit nhỏ và một bước fine-tuning encoder thật. **Chất lượng hiện chưa đủ để thay bộ phân tích mặc định.** Không gọi Gemini hoặc API mô hình ngoài.

Kết quả, lỗi và thời gian thực: [báo cáo 14/11/2026](reports/phobert_20261114/README.md). Các checkpoint đã tạo nằm ở `artifacts/phobert/`, chưa được duyệt production. Mặc định vẫn `SCAMSHIELD_REASONER=legacy`.

## Môi trường và chuẩn bị

Máy đã kiểm: Windows 11, Python 3.12.5, i5-12500H, RAM khoảng 15,70 GiB, Intel Iris Xe, CUDA không có. Dùng CPU float32, 2 thread, batch 1 và gradient accumulation. Java có sẵn để chạy RDRSegmenter. `.venv-phobert` riêng với môi trường backend cũ.

Từ thư mục ứng dụng bên trong repo:

```powershell
cd C:\AI4Life\AI4LIFE\ScamShield_AI\ScamShield_AI
.\SETUP_PHOBERT.ps1
```

Script cài PyTorch CPU, các thư viện theo `ml/phobert/requirements.txt` và backend requirements, rồi tải checkpoint `vinai/phobert-base` + VnCoreNLP vào `artifacts/phobert`. Checkpoint và segmenter khóa revision; hash từng asset trong preparation.json. [Model card](https://huggingface.co/vinai/phobert-base), [giấy phép MIT](https://github.com/VinAIResearch/PhoBERT/blob/master/LICENSE), [hướng dẫn PhoBERT và tách từ](https://github.com/VinAIResearch/PhoBERT). Không đổi sang PhoBERT base-v2 hoặc mô hình khác.

Máy hiện tại đã cài và đã có asset, không cần tải lại để chạy. Snapshot đầy đủ phiên bản pip trong `ml/phobert/environment.lock.txt`; với máy mới cần index PyTorch CPU khi cài bản `+cpu`. Checkpoint gốc khoảng 545 MB; checkpoint fine-tune stage span khoảng 548 MB; các head nghiên cứu khoảng 5,6 MB/bản. Khi di chuyển dự án, cần cả base, tokenizer, VnCoreNLP và heads, không chỉ heads.pt.

## Dữ liệu

```powershell
.\.venv-phobert\Scripts\python.exe -m ml.phobert.build_smoke_data
.\.venv-phobert\Scripts\python.exe -m ml.phobert.audit
```

Lệnh build chỉ tái tạo **bộ nháp smoke** 20 ca do agent biên soạn cùng schema/split/hash; không nhập weak_label v2 và không tự đổi thành gold. Có 12 train, 4 validation, 4 test_locked; giữ các cặp tối thiểu cùng nhóm. Builder thực hiện khử gần trùng trước chia. Không chạy build để xóa hoặc thay bộ dữ liệu đã được nhóm con người rà trong tương lai.

Validator là `ml/phobert/schema.py` và `data.py`. `load(path, supervised=True)` từ chối draft/public regression; `allow_draft=True` chỉ dành cho chẩn đoán được ghi rõ. [Hướng dẫn nhãn và rà độc lập](../data/phobert/ANNOTATION_GUIDE.md) phân biệt complete/partial/unannotated, null/unknown và hướng quan hệ. Hiện 0 ca mới được người rà độc lập; không có kết quả holdout độc lập.

## Huấn luyện và đánh giá

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
$env:PYTHONIOENCODING='utf-8'

# Các head được huấn luyện riêng từng task, encoder đóng băng để thử CPU.
.\.venv-phobert\Scripts\python.exe -m ml.phobert.train

# Kiểm tra khả năng học trên đúng 4 mẫu train, không phải validation độc lập.
.\.venv-phobert\Scripts\python.exe -m ml.phobert.train --overfit-smoke

# Một bước fine-tune encoder thật, chỉ task span; chưa đủ head cho API.
.\.venv-phobert\Scripts\python.exe -m ml.phobert.train --config ml/phobert/cpu_finetune_step.json

# Dự đoán validation trước khi đọc nhãn để chấm.
.\.venv-phobert\Scripts\python.exe -m ml.phobert.evaluate
.\.venv-phobert\Scripts\python.exe -m ml.phobert.overfit_probe
```

`cpu_smoke.json` cấu hình checkpoint, seed, learning rate, batch, accumulation, max_length, overlap, epochs, early stopping, loss weights, device và freeze_encoder. Chỉ batch_size=1 đã triển khai; giá trị khác bị từ chối, dùng accumulation thay thế. CPU dùng float32. Chọn epoch bằng validation loss; threshold 0,5 đang cố định, chưa hiệu chuẩn/tối ưu trên dữ liệu đủ lớn. Không dùng test chọn ngưỡng.

Muốn fine-tune đầy đủ sau khi có dữ liệu: dùng config riêng với `freeze_encoder=false`, đủ stage spans/attributes/roles/relations/baseline, bỏ train_sample_limit và `allow_draft_smoke=false`. Đầu vào phải được rà độc lập. Đây là fine-tuning mô hình pretrained, không phải pretraining từ đầu. Chưa chạy cấu hình đầy đủ trên bộ gold đủ lớn.

`evaluate --split test_locked` bị chặn nếu thiếu `--final-test`. Lựa chọn cuối phải khóa model/config/hash trước phép đo test; evaluator lưu test_freeze.json và từ chối đổi cấu hình sau khóa. Bốn test smoke là dữ liệu nháp công khai đã được agent biên soạn, không được gọi là holdout độc lập. Chưa chạy lệnh đánh giá test trong đợt này.

Chạy lại chuỗi smoke đã nghiệm thu:

```powershell
.\.venv-phobert\Scripts\python.exe -m ml.phobert.run_checks
```

Lệnh này tạo lại checkpoint nghiên cứu và báo cáo train/validation/API; không dùng test khóa. Để chỉ kiểm thử mã:

```powershell
.\.venv-phobert\Scripts\python.exe -m pytest tests -q
```

## Chạy API PhoBERT thử nghiệm

Đây là lựa chọn chủ động cho nghiên cứu: mô hình hiện còn false-clear và giải thích sai, không dùng để thay hệ thống đang vận hành.

```powershell
cd C:\AI4Life\AI4LIFE\ScamShield_AI\ScamShield_AI
.\RUN_PHOBERT_EXPERIMENTAL.ps1
```

Script đặt biến môi trường cho process này: mode local_rules để giữ hợp đồng API cũ, reasoner phobert, checkpoint smoke_heads, cờ cho phép nghiên cứu, model offline và tắt HTTP HEAD URL. Không sửa `backend/local_settings.py`. Nếu cổng 8000 đang có backend cũ, dừng process đó trước khi dùng cùng cổng.

Website/API vẫn là `http://127.0.0.1:8000` và `POST /api/analyze`. Public schema và bốn mức không đổi; `analysis.decision_version=phobert-structured-1.0-support`. Cùng renderer đọc display_summary/display_action, không hiển thị 18 trường hoặc debug. `/api/analyze-local` vẫn cung cấp cấu trúc để nghiên cứu.

Không có cờ cho phép nghiên cứu, checkpoint smoke bị chặn. Thiếu dependency/checkpoint/hash hoặc head chưa học không tự chuyển sang mock, luật cũ hay API ngoài. Startup nạp model một lần. Runtime một slot không hàng đợi ẩn: bận trả 503; unsupported/error không là clear hoặc need_context. Context_facts/thông tin bổ sung chưa được pipeline ML nháp hỗ trợ và trả trạng thái không xử lý được; reasoner mặc định giữ chức năng hiện tại.

Để quay lại backend cũ, mở PowerShell mới và chạy lệnh thông thường bằng Python môi trường cũ. Không chạy trong cửa sổ còn giữ biến môi trường phobert nếu muốn dùng mặc định.

## Kiến trúc và giới hạn

1. Giữ bản gốc từng message và speaker ID. RDRSegmenter tạo từ; bảng start/end ánh xạ lại Unicode code point gốc, kể cả emoji và xuống dòng. Accent normalization chỉ giúp căn chỉnh vị trí, không trở thành bằng chứng. Lỗi căn chỉnh dừng pipeline.
2. Tokenizer PhoBERT slow tạo BPE từng từ; kiểm tra thực tế không giả định offset_mapping/word_ids. Token pool theo bảng tự xây. Cửa sổ chồng lấn tối đa 256 token, chèn EOS khi đổi message, không cắt cuối im lặng. Vượt giới hạn trả lỗi; cặp xa chưa cùng cửa sổ được báo unsupported/partial.
3. Một encoder dùng các head span đa nhãn, sáu thuộc tính sự kiện, vai liên kết theo sự kiện, quan hệ đa nhãn có hướng, baseline bốn mức. Hiện decoder nghiệm thu chỉ xuất action; entity/đồng tham chiếu và span khác còn thiếu gold. Speaker metadata được giữ nguyên, không tính thành thành tích học đoán người nói.
4. Backend kiểm quote, ID, speaker, transaction và cạnh, loại dữ kiện sai rồi tính lại. Bộ graph rule có ID, đầu mút, evidence_refs, cơ chế, điều kiện, giới hạn. Nhận dạng ID đơn A/B bằng mẫu định dạng chỉ hỗ trợ binding, không là suy luận rủi ro. Classifier bốn mức ghi bất đồng, không quyết định nâng mức.
5. Tạo 18 trường từ cấu trúc có sẵn, giữ unknown cho phần chưa biết. Giải thích mẫu Python; không dùng chain-of-thought làm bằng chứng. Hợp đồng public giữ mode cũ để tương thích, không có nghĩa các head ML là luật.
6. RAG/URL enrich cũ chạy sau cấu trúc đã kiểm chứng khi cấu hình cho phép. Checkpoint/label/tokenizer/preprocessing được khóa. Runtime không lưu hội thoại ra đĩa; chỉ các script nghiệm thu chủ động ghi dữ liệu tổng hợp và ca công khai được giao kiểm thử.

Các nhiệm vụ chưa hoàn thành và số đo thực tế nằm trong báo cáo. Đặc biệt chưa có gold độc lập đủ rộng, chưa hiệu chuẩn, chưa nghiệm thu nhiều giao dịch/ngôn ngữ biến thể và chưa chứng minh PhoBERT cải thiện kết quả so với bộ luật hiện tại.
