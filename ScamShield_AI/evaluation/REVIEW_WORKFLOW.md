# Rà soát dữ liệu trước khi huấn luyện lại

Gói thực tế: [public_20261114](review_packs/public_20261114/INSTRUCTIONS.md), **35 ca, chưa có bản rà soát thực tế**. Gói không chứa nhãn draft, dự đoán, family/template/source group có thể tiết lộ mức cảnh báo. Đây vẫn là dữ liệu công khai đã được agent đọc, không phải holdout độc lập.

Công cụ không gọi mô hình, không tự gán nhãn, không sửa dataset gốc và không khởi động huấn luyện. Kết quả kiểm thử bằng danh tính `unit-fixture-*` chỉ nằm trong thư mục tạm của pytest; chúng không được tính là người rà thật.

## 1. Chuẩn bị

Chạy lệnh từ thư mục ứng dụng có `backend`, `evaluation`, `.venv-phobert`:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv-phobert\Scripts\python.exe -m evaluation.review --help
```

Gói 35 ca đã được tạo bằng lệnh sau. Để tạo đợt khác, dùng tên thư mục mới; không ghi đè gói đang có người rà:

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.review export --source evaluation/data/novel_cases.jsonl --out evaluation/review_packs/public_20261114
```

Mỗi người rà nhận bản sao riêng của gói. Họ chỉ xem `inputs.jsonl`, schema, ontology và hướng dẫn gán nhãn. Không gửi prediction hoặc nhãn draft để họ chép lại. Hai người phải rà độc lập trước khi đối chiếu.

## 2. Điền bản gán nhãn

Sao chép `annotations_blank.jsonl` sang file riêng ở ngoài gói, chẳng hạn `evaluation/reviews/reviewer_a.jsonl`. Có thể chỉ nộp một số dòng đã rà; không bắt buộc nộp hết 35 ca.

- Giữ nguyên `case_id`, `input_sha256` và bản văn gốc.
- Điền `expected` đúng [expected.schema.json](review_packs/public_20261114/expected.schema.json), gồm spans, events, participants, roles, relations, cases, mức cảnh báo, căn cứ, giới hạn và câu hỏi.
- Xem [annotation_guide.md](annotation_guide.md). Offset tính trên Unicode code point của bản gốc, `end` loại trừ; quote phải khớp chính xác.
- Đánh dấu độ hoàn thiện của cả bảy task. Thuộc tính event còn `null` không được đánh dấu events complete.
- Ghi bất định hoặc bất đồng vào `issues`; không chọn mức theo dự đoán mô hình.
- Nếu chưa thể gán đầy đủ, giữ `expected=null`, ghi dữ kiện đã rà trong `partial_annotations` như `spans` và `risk_status`. `risk_status=null` được phép; không cần đoán để điền đủ. Bản partial chỉ ghi nhận công việc, không được xuất thành mẫu đã duyệt.

Định nghĩa schema không có nghĩa là mọi nhãn đều đã được checkpoint học. Công cụ training kiểm tra label mapping riêng.

Mỗi người tạo file attestation riêng, điền reference công việc thật của mình. Không cần tên thật hoặc thông tin cá nhân. Mẫu sau cố ý chưa xác nhận đã rà; chỉ đổi các cờ sau khi công việc tương ứng thực sự đã làm:

```json
{
  "reviewer_reference": "<ma-cong-viec-nguoi-ra>",
  "human_review_performed": false,
  "independent_of_other_reviewer": false,
  "used_model_generated_annotations": false
}
```

## 3. Nhận bản rà và đối chiếu

Sau khi người rà xác nhận đã làm độc lập, `human_review_performed` và `independent_of_other_reviewer` phải là true, `used_model_generated_annotations` là false. Reference placeholder bị từ chối.

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.review submit --pack evaluation/review_packs/public_20261114 --source evaluation/data/novel_cases.jsonl --annotations evaluation/reviews/reviewer_a.jsonl --attestation evaluation/reviews/reviewer_a_attestation.json

# Lặp submit với bản gán nhãn và attestation riêng của người thứ hai.

.\.venv-phobert\Scripts\python.exe -m evaluation.review reconcile --pack evaluation/review_packs/public_20261114 --source evaluation/data/novel_cases.jsonl --out evaluation/reports/review_tooling_20261114/review_status.jsonl
```

Tool kiểm hash đầu vào/dataset, offset và tham chiếu, ghi nhận người rà, không cho một reference nộp lại cùng ca để tính thành hai người. Bản ghi có hash để phát hiện chỉnh sửa ngoài quy trình. Nếu cần sửa bản đã nộp hoặc hoàn thiện partial, tạo chu kỳ review mới với thư mục mới và nộp lại các bản hiện hành; công cụ không âm thầm ghi đè lịch sử.

`reconcile` có bốn kết quả chính: thiếu hai bản rà, còn partial, bất đồng cấu trúc, hoặc đồng thuận cấu trúc chờ người quyết định. So sánh bỏ qua cách đặt ID graph và cách viết lời giải thích; có so hành động, thuộc tính, vai, quan hệ, phạm vi, mức cảnh báo và sự kiện chủ chốt. Đồng thuận cấu trúc vẫn **không** chứng minh lời giải thích đúng nghĩa.

## 4. Người phụ trách giải quyết và duyệt

Người phụ trách đọc hai bản rà, giải quyết bất đồng và kiểm tra cả lời giải thích/câu hỏi. Tạo `resolutions.jsonl` bên ngoài gói, mỗi dòng có cùng trường với một annotation đầy đủ và thêm:

```json
{
  "adjudicator_reference": "<ma-cong-viec-nguoi-quyet-dinh>",
  "human_resolution_performed": false,
  "approved_for_training": false,
  "reason": "Ghi căn cứ giải quyết sau khi thực sự rà soát."
}
```

Đây chỉ là các trường bổ sung, không phải một dòng resolution đầy đủ. Phải có `case_id`, input hash, `expected`, completeness và `issues`. Sau khi thật sự giải quyết xong, điền reference thật, bật hai cờ và để `issues=[]`. Công cụ yêu cầu hai bản rà đầy đủ trước khi xuất.

```powershell
.\.venv-phobert\Scripts\python.exe -m evaluation.review approve --pack evaluation/review_packs/public_20261114 --source evaluation/data/novel_cases.jsonl --resolutions evaluation/reviews/resolutions.jsonl --out evaluation/training/reviewed_errors_v1.jsonl
```

Lệnh xuất file mới kèm manifest, reference, lý do, hash, split/family gốc; không sửa dataset nguồn. Bất đồng đã giải quyết được ghi `adjudicated`, đồng thuận được ghi `human_verified`. File xuất chưa có nghĩa là training đã chạy. Phần mềm chỉ ghi nhận lời xác nhận, không tự chứng minh hai reference là hai người hay họ thực sự đã rà độc lập.

## 5. Điều kiện còn lại trước fine-tune

- Ca thuộc validation/locked không được tự chuyển sang train: cần đợt phiên bản mới, chuyển cả family có lịch sử và validation thay thế. Training gate hiện chặn chuyển ngầm.
- Cần replay cũ và validation được duyệt, không trùng family/template/source với train.
- Nhãn ngoài mapping checkpoint cần thiết kế migration head và mapping có phiên bản; không nạp trọng số cũ vào head đổi kích thước.
- Chỉ chạy fine-tune sau khi gate hợp lệ; giữ checkpoint baseline, đo regression và validation, không tự đổi production.

Xem quy trình training và đánh giá tại [README.md](README.md). Hiện chưa có người rà thật nên chưa xuất `reviewed_errors_v1.jsonl` hoặc chạy huấn luyện mới.
