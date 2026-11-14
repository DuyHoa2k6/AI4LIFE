# Đầu ra bước phân tích Python — 12/11/2026

Cập nhật rules-1.2: thêm kho viết tắt có điều kiện ngữ cảnh, giữ ánh xạ về nguyên bản.
Xem [dataset và nguyên tắc phân giải](../data/README_ABBREVIATIONS.md).
Chỉ dùng cho /api/observe, không đổi /api/analyze. Resolved là cách hiểu từ vựng
theo luật, không xác nhận danh tính/rủi ro. Từ đa nghĩa được giữ lại và hỏi thêm.

Cập nhật rules-1.1: segmentation.py tách mệnh đề từ dấu câu, từ nối có vị ngữ theo
sau, cụm hành động mới và mã giao dịch thay đổi. Không thêm dấu câu vào nguyên bản,
không tạo đoạn chỉ chứa dấu phẩy. Unit thêm boundary_reason,
boundary_status=observed/inferred/uncertain và limitations. Phạm vi ngữ cảnh mới
giúp tránh lan phủ định/cảnh báo sang yêu cầu tiếp theo. Cấu trúc phối hợp hoặc mệnh
đề quan hệ mơ hồ được giữ/đánh dấu chưa chắc, không ép thành lệnh mới.
[Kiểm thử tách đoạn thiếu dấu](reports/local_segmentation_20261112/README.md).

Theo phạm vi mới nhất, **POST /api/observe** trích 18 trường bằng Python, trả bằng
chứng/hành động/quan hệ và adapter tám answers. Không gọi Gemini, truy xuất, OCR,
URL hoặc quyết định mức rủi ro. **Chưa thay Gemini đầu trong /api/analyze**;
website/extension vẫn dùng luồng cũ. Đây là điểm kiểm tra đầu ra trước khi tích hợp tiếp.

## Khảo sát và tương thích

Trong backend/two_pass.py, lượt đầu cũ là InitialReviewDraft → bind metadata → verify.
Truy xuất dùng văn bản gốc/quote/action; lượt hai nhận observations/hypotheses/
uncertainties. Frontend đọc AnalyzeResponse cuối, không đọc 18 trường này.

| Cũ | Mới |
|---|---|
| AnalyzeRequest | Cùng text/messages/context/question/links/ocr_sources, cùng giới hạn |
| findings | events → adapter.findings, speaker là metadata, actor ghi riêng |
| Evidence | spans có source/provenance và offset Unicode code point; end loại trừ |
| answers | answers_18 và adapter.answers gồm đúng tám khóa cũ |
| hypotheses | [] để không biến mẫu luật thành tên thủ đoạn |
| uncertainties | follow_up_questions tối đa hai câu |
| context | source=context/provenance=user_report, không biến thành bằng chứng message |
| links/ocr_sources | Chỉ là đầu vào; không coi như kiểm tra kỹ thuật đã chạy |

Adapter ánh xạ claim←claims, claimed_identity←sender_identity,
requested_action←requested_actions, persuasion←persuasion,
assets_at_risk←assets_and_access, impersonation←contradictions_and_alternatives,
sequence←conditions_and_sequence, evidence_sufficiency←evidence_quality.
Ánh xạ impersonation có giới hạn: phủ định/mâu thuẫn không tự chứng minh mạo danh.
claimed chuyển inferred vì enum cũ chỉ có observed/inferred/unknown. Refs trong
adapter trỏ finding ID; thiếu finding tương ứng giữ unknown. Đây là phép chuyển mất
chi tiết, không nhét toàn bộ 18 trường vào tám ô. question không được coi là lời người gửi.

18 khóa theo schema.py: situation, participants, sender_identity, relationship,
communication_channel, claims, requested_actions, action_targets, stated_purpose,
assets_and_access, benefit_and_mismatch, persuasion, conditions_and_sequence,
contradictions_and_alternatives, technical_checks, evidence_quality,
missing_information, assessment. Mỗi trường có status/value/evidence_refs/
missing_information. Value Pydantic gồm statements/event_ids/participant_ids/relation_ids.
benefit_and_mismatch hiện unknown; technical_checks luôn unknown tại bước này.
Danh tính/quan hệ tự nhận dùng claimed, không suy quan hệ thật từ anh/chị/em.

## Chạy và xem kết quả

Từ workspace gốc:

```powershell
python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log
```

Mở http://127.0.0.1:8000/docs → POST /api/observe → Try it out:

```json
{"text":"Chưa thấy tiền về, nhưng cứ giao máy trước."}
```

Nhận receive_funds / negative / claim / pending và handover_asset / positive /
request / requested. Quan hệ before nói về giao trước khi xác nhận thanh toán,
không chứng minh biên lai giả, chưa phải high/suspicious.
Khi bổ sung ý nghĩa mã, gửi lại toàn bộ messages đúng ID/speaker. Endpoint stateless;
input_sha256 ràng buộc snapshot, không tự ghép request trước. Nhiều yêu cầu mã thì
chưa tự chọn một yêu cầu để nối với câu “Đó là mã đăng nhập”.

## Thành phần và dữ liệu

- backend/local_observation/text.py: chuẩn hóa cụm Unicode có ánh xạ, tách câu/mệnh đề,
  giữ URL/số tiền/lời trích. Mọi quote cắt từ nguyên bản trong request.
- rules.json: 18 mẫu kiểm soát, có ID/mô tả/context/tests. Không nạp regex từ request;
  restart sau khi sửa để xóa cache. analyzer.py điều phối và map 18 trường/adapter.
- schema.py quy định đầu ra; dataset.py quy định gán nhãn participants/spans/events/
  relations/expected_answers_18/risk_label_reference/provenance/review_status.
- Luật quan hệ nằm trong analyzer.py, chưa phải mô hình học: REL-HANDOVER-BEFORE-CONFIRMATION,
  REL-REPORTED-PAYMENT-FIRST, REL-NEGATIVE-CONDITION, REL-TIMED-UPDATE,
  REL-OPPOSITE-STATE, REL-EXPLICIT-PURPOSE, REL-STATED-REASON, REL-EXPLICIT-ORDER,
  REL-EXPLICIT-CODE-REPLY, REL-QUOTED-WARNING, REL-REPORTED-SPEECH.
  Mỗi relation ghi rule_id để có thể thay riêng bộ trích bằng mô hình tự huấn luyện.
  warning_about nối speaker tới event; reported_by nối event tới speaker.
- Ba mẫu xuất từ input dev có weak_label/rule_ids, risk_label_reference=null;
  cần người rà trước huấn luyện. Dataset gốc giữ nguyên, không đọc validation/holdout.
- Không ghi văn bản ra log/file mặc định; chỉ lệnh kiểm thử lưu dữ liệu tổng hợp chủ động.

Giữ nội dung tối đa 10.000 ký tự, context 2.000, tối đa 100 messages, body 64 KiB.
Tối đa 50 event, đạt giới hạn có thông báo phần chưa phân tích. Không khớp mẫu không
có nghĩa clear. Từ lóng/hàm ý, nhiều giao dịch ngầm, quan hệ xa, người hưởng lợi và
cú pháp phức tạp còn giới hạn. Quan hệ hai câu liền nhau có thể inferred và ghi giới hạn.
Không nối qua mã giao dịch khác nhau; “sáu số” không tự thành OTP; “tài xế đang chờ”
không tự thành yêu cầu giao hàng hoặc bằng chứng chưa thanh toán.

Từ thư mục ứng dụng có backend:

```powershell
python -m unittest discover -s tests -p test_local_observation.py -v
python local_observation_check.py --output reports/local_observation_rerun
```

Chấm trên 30 ca phát triển nhãn nháp, ghi predictions trước khi đọc expected,
khóa hash và đo xử lý thuần/ASGI. Không phải đánh giá độc lập. Precision/recall người
tham gia theo ngữ nghĩa chưa đo, chỉ kiểm tra metadata. Không đo chất lượng downstream.
[Báo cáo và từng ca](reports/local_observation_20261112/README.md).
