# Đánh giá và cải tiến PhoBERT có kiểm soát

Đã chạy mô hình cục bộ thật trên **35 ca draft đa lĩnh vực + 16 regression đã biết**, khóa baseline và thử một candidate policy. Candidate bị từ chối vì không tăng số ca vừa đúng mức vừa đủ căn cứ cấu trúc và làm giảm coverage. Không có dữ liệu mới được người rà duyệt, nên không huấn luyện lại hoặc đổi nhãn thành dự đoán. Backend production mặc định `legacy` giữ nguyên.

**A: pipeline và smoke đã chạy. B: chưa fine-tune trên nhãn mới được rà. C: chưa có holdout độc lập.** Báo cáo chính: [final_report.md](reports/20261114_rounds/final_report.md).

Đã bổ sung [quy trình nhận hai bản rà soát độc lập](REVIEW_WORKFLOW.md), gói 35 ca chỉ có đầu vào và công cụ ghi bất đồng/duyệt có lịch sử. Hiện 0 bản rà thực tế; các test mô phỏng không được tính là nhãn được con người duyệt. Công cụ không tự train hoặc chuyển validation thành train.

## Thành phần thực tế

- PhoBERT base checkpoint thật cùng head span/thuộc tính/vai/quan hệ/baseline bốn mức đã học trong đợt trước, encoder đóng băng: `artifacts/phobert/smoke_heads`.
- Checkpoint fine-tune encoder một bước trước đó chỉ học task span, không dùng như pipeline đã học đủ head.
- Suy luận rủi ro bằng quy tắc Python trên graph kiểm chứng; quy tắc không phải mô hình được học. Candidate `ml/phobert/policy_v2.py` chưa được chọn, không tự động dùng trong API.
- `ml/phobert/inference.py` chỉ thêm tùy chọn debug cho harness để đo graph trước/sau verifier. API không nhận expected và không xuất debug mặc định.
- Không gọi Gemini/API mô hình ngoài, không tải thư viện hoặc model mới trong đợt này. Các mẫu và chỉ thị nhúng chỉ là dữ liệu, không thực thi hoặc mở liên kết.

## Môi trường chạy

Các lệnh dưới đây chạy từ thư mục ứng dụng bên trong repo, dùng môi trường ML đã chuẩn bị:

```powershell
cd ScamShield_AI
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
$env:PYTHONIOENCODING='utf-8'
```

Nếu đã đứng trong thư mục có `backend`, `ml`, `evaluation` và `.venv-phobert`, bỏ lệnh `cd`. Chuẩn bị máy mới theo [README_PHOBERT.md](../README_PHOBERT.md); pipeline cần PyTorch CPU, Transformers, PyYAML, Java/RDRSegmenter và checkpoint đã khóa. Không cần API key. Source dùng ROOT tương đối và các CLI nhận đường dẫn; đường dẫn tuyệt đối trong report chỉ là metadata lần chạy.

## Dữ liệu và chống rò rỉ

`data/novel_cases.jsonl` có 35 draft: bảy nhóm × bốn mức tự nhiên và bảy biến thể. Năm ca giáo dục/biến thể dựa trên ví dụ đã có trong prompt được đánh dấu `seen_development`; 30 nhánh còn lại là draft công khai mới biên soạn. Tất cả đã được agent đọc, không là blind holdout. Mục tiêu biên soạn 84 chưa đạt: ưu tiên cấu trúc và chờ rà soát, không nhân bản theo tên/số tiền.

`data/regression_cases.jsonl` có 16 mẫu train/validation cũ đã thấy. Không mở file test_locked hoặc holdout cũ. Có 25 diagnostic, 10 validation, 16 regression; cùng family/template/source giữ trong một split. **0 human_verified**, không tạo tên người rà giả.

Mỗi ca có expected spans/events/roles/relations/cases, risk, rationale, điều còn thiếu, câu hỏi chấp nhận và kết luận bị cấm. Tham chiếu là draft, không phải nhãn chuẩn độc lập. Một ca cập nhật quyền khiếu nại N33 được đánh dấu mơ hồ và giữ chờ người rà, không sửa label để hợp với candidate.

Schema `evaluation-case-1.0` tái sử dụng kiểu Message/Span/Participant/Argument của repo. Ontology policy rộng hơn label map head đã học và được tách riêng: **không đổi thứ tự/kích thước head cũ**. Số ca nằm ngoài vocabulary checkpoint được báo riêng, không biến giới hạn schema thành kết luận encoder chắc chắn không hiểu ngôn ngữ.

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.validate_dataset --cases evaluation/data/novel_cases.jsonl --cases evaluation/data/regression_cases.jsonl --out evaluation/reports/data_audit.json
```

Validator kiểm offset Unicode code point, quote, ID, actor refs, scope, nhãn, source/review và family/near-duplicate qua split. Input Runtime chỉ có messages; expected/family/rationale không được gửi vào mô hình. Không dùng nhãn chưa gán làm negative. Các loại quan hệ có hướng/đối xứng giữ hợp đồng trong repo. Kiểm đúng hướng ngữ nghĩa vẫn cần người rà, không suy ra đã đúng chỉ vì có cạnh.

Builder `python -m evaluation.build_cases` và adapter `python -m evaluation.regression` tái tạo đúng bộ công khai để nghiên cứu; không dùng chúng để ghi đè dữ liệu đã được người rà trong tương lai.

## Khóa baseline và chạy inference

Đã lưu baseline tại `reports/20261114_rounds/baseline`. Không chạy ghi đè report có prediction; chọn run ID mới khi nghiên cứu lại.

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.freeze --out evaluation/reports/my_rounds

.\.venv-phobert\Scripts\python.exe -m evaluation.run_evaluation --cases evaluation/data/novel_cases.jsonl --cases evaluation/data/regression_cases.jsonl --out evaluation/reports/my_rounds/baseline --baseline-policy evaluation/reports/my_rounds/baseline_policy.py --oracle-spans
```

Chạy real Runtime, lưu toàn bộ `predictions.jsonl` trước khi đối chiếu labels. Sau đó chạy riêng:

- Văn bản → PhoBERT → graph → policy: E2E.
- Span tham chiếu → model head phía sau → policy: oracle/debug cho lỗi lan truyền, có ghi số anchor bị skip do không căn chỉnh được.
- Annotation tham chiếu → verifier → policy: oracle toàn graph, không là fallback sản phẩm.

`run_manifest.json` khóa checkpoint/hash, mapping, preprocessing, dữ liệu, policy, seed và acceptance. `metrics.json` tách domain/split, scope vocabulary, confusion matrix, precision/recall/F1 với `null` khi mẫu số 0, coverage và mọi trạng thái xử lý. Evidence có mẫu số trước/sau verifier. Diễn giải ngữ nghĩa bằng người chưa thực hiện; tự động so tag/sự kiện/quan hệ chỉ là proxy cấu trúc.

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.baselines --cases evaluation/data/novel_cases.jsonl --cases evaluation/data/regression_cases.jsonl --run evaluation/reports/my_rounds/baseline
.\.venv-phobert\Scripts\python.exe -m evaluation.analyze_errors --run evaluation/reports/my_rounds/baseline --out evaluation/reports/my_rounds/review
```

Comparator gồm core rulebook cũ và head phân loại bốn mức đã huấn luyện. Chúng chỉ được tính điểm risk, không nhận công cho graph/explanation của pipeline. Error log có expected/predicted từng tầng, quote, module, severity, confirmed/suspected và review state. Một mức đúng với action/role/cơ chế sai không được tính là thành công đầy đủ.

## Vòng cải tiến và giới hạn

`configs/acceptance.yaml` đã đóng băng trước cải tiến: metric chính là tỷ lệ đúng mức + đủ căn cứ cấu trúc, tối thiểu tăng 0,05; bảo vệ clear/high/coverage; p95 ≤5 giây, RSS ≤4 GiB; tối đa 3 vòng gồm baseline, 2 cấu hình, 500 lượt model, 1200 giây. Đây là tiêu chí thử nghiệm, không phải chuẩn sản phẩm. Runner kiểm ngân sách tích lũy trong cùng thư mục đợt.

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.run_evaluation --cases evaluation/data/novel_cases.jsonl --cases evaluation/data/regression_cases.jsonl --out evaluation/reports/my_rounds/candidate_01 --baseline-policy evaluation/reports/my_rounds/baseline_policy.py --policy candidate --oracle-spans

.\.venv-phobert\Scripts\python.exe -m evaluation.compare_runs --baseline evaluation/reports/my_rounds/baseline --candidate evaluation/reports/my_rounds/candidate_01 --acceptance evaluation/configs/acceptance.yaml --out evaluation/reports/my_rounds/comparison.json
```

Compare trả **exit 2** nếu không đạt hoặc điều kiện chưa xác định; không tự cho reviewed/holdout còn thiếu qua. Per-domain áp cùng các ràng buộc bảo vệ đã chốt. Trong đợt đã chạy, dừng sau baseline + một candidate vì không có cải thiện chính, coverage giảm, và không có nhãn được duyệt để sửa model. Các sửa typed policy chỉ dùng cấu trúc, không nhận domain/case_id/câu gốc để khớp riêng.

## Chuẩn bị và fine-tune từ dữ liệu đã duyệt

```powershell
# Với dữ liệu hiện có, lệnh này cố ý trả exit 3: chưa có ca human-reviewed.
.\.venv-phobert\Scripts\python.exe -m evaluation.training --cases evaluation/data/novel_cases.jsonl --out evaluation/training --checkpoint artifacts/phobert/smoke_heads
```

Sau khi người rà thật cung cấp nhãn được duyệt, replay cũ được duyệt và validation không chồng family:

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.training --cases PATH_TO_REVIEWED_CASES.jsonl --replay PATH_TO_REVIEWED_REPLAY.jsonl --validation PATH_TO_REVIEWED_VALIDATION.jsonl --checkpoint artifacts/phobert/smoke_heads --out evaluation/training/reviewed_candidate --run
```

Tool giữ reviewer reference, bỏ ca còn tranh cãi, không lấy prediction làm label; yêu cầu replay ≥50% và không nhân bản để đủ tỷ lệ. Nó tạo Sample 1.0 cho trainer hiện có, cấu hình CPU/batch1/accumulation2/epochs3/early stopping2, warm-start head từ checkpoint thực. Warm-start kiểm nguyên thứ tự mapping/hash/shape; có nhãn mới chưa nằm trong head thì chặn và báo cần migration có version, không gộp vào `other` hoặc âm thầm nạp trọng số sai kích thước. Chưa thực hiện migration/fine-tune trên ontology mở rộng vì chưa có nhãn duyệt.

Nếu một family validation được dùng sửa luật hoặc chuyển vào train, phải ghi lịch sử và chuyển cả family sang development/regression, rồi bổ sung validation không chồng lặp. Không đổi nhãn tham chiếu để làm đẹp điểm. Không online learning từ báo cáo người dùng.

## Tập khóa do người rà độc lập quản lý

Không có tập độc lập trong lần chạy này. Input khóa phải được người rà quản lý ở ngoài thư mục public, chỉ gồm case_id và input.messages. Pha predict không nhận đường dẫn labels:

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.locked_runner predict --inputs PATH_TO_LOCKED_INPUTS.jsonl --checkpoint evaluation/models/rollback_baseline --out PATH_TO_SEALED_RUN --allow-experimental
```

Trên máy người rà, sau khi prediction đã được seal:

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.locked_runner score --out PATH_TO_SEALED_RUN --private-labels PATH_TO_PRIVATE_LABELS.jsonl --attestation PATH_TO_CUSTODIAN_ATTESTATION.json --seen-manifest evaluation/data/split_manifest.json --allow-private-labels
```

Attestation cần `custodian_reference`, `not_seen_by_implementer=true`, `labels_independently_reviewed=true`; đây phải là xác nhận thật, không tạo bởi agent. Labels là schema Case với split locked và hai reviewer reference có thật. Tool kiểm seal/hash/ID/family, từ chối score lại sau consumed. Công cụ không thể tự chứng minh người rà độc lập; tên thư mục không là bằng chứng. Dùng kết quả khóa để sửa thì chuyển thành development và lấy tập độc lập mới. Không chạy score mù nào trong đợt này.

## Chạy bản được giữ và rollback

`models/model_manifest.json` chỉ tới checkpoint rollback thật có hash đúng baseline. Candidate không được chọn. Muốn mở backend nghiên cứu với đúng bản được giữ:

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.launch_backend --selection evaluation/models/model_manifest.json --allow-experimental --port 8000
```

Lệnh đặt biến môi trường trong process con, không đổi local_settings.py; model offline, HTTP HEAD URL tắt. Dừng backend cũ nếu đang chiếm cùng cổng. API text/messages vẫn dùng hợp đồng cũ. Muốn dùng production/default cũ, mở shell mới và chạy uvicorn thông thường theo README chính; mặc định legacy không thay đổi. Không tự publish model chỉ vì một số điểm tăng.

## Kiểm thử và số đo đã chạy

```powershell
.\.venv-phobert\Scripts\python.exe -m pytest tests -q
node tests/popup_version.mjs
node tests/worker_security.mjs
node tests/ocr_worker.mjs
```

Đã kiểm real API không key/chặn mạng ngoài, text/messages tương đương, input quá dài, timeout/busy không thành risk; thiếu checkpoint/mapping được kiểm bởi suite PhoBERT có sẵn. Có test validator/quote/refs, scoped unknown, state update sai hướng/sai giao dịch, lời cảnh báo, nhãn đúng nhưng sai căn cứ, review gate, cumulative budget, khóa input không được lẫn expected và warm-start trọng số thật.

Report có số đo sequential local, không phải latency từ browser/extension. RAM/VRAM, độ dài input, số gọi và cold load tách riêng. Chưa đo tải đồng thời của cả evaluator mới, stress dài hoặc chất lượng người rà độc lập. Nhiều ô phenomenon/domain còn thiếu; xem inventory.json. Không tuyên bố mục tiêu 98% hay chất lượng thực tế từ tập draft này.
