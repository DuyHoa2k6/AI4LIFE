# Kiểm tra đầu ra Python đầu tiên — 12/11/2026

Phạm vi theo yêu cầu mới nhất: **chỉ phân tích đầu tiên**, qua POST /api/observe.
Chưa thay Gemini đầu trong /api/analyze, chưa chạy Gemini cuối/RAG hoặc đo chất lượng
bốn mức cảnh báo. Không thay key, cấu hình provider, extension hoặc cách quyết định rủi ro.

## Kết quả cuối

- 223 unittest backend đạt, gồm 20 kiểm thử mới; một kiểm thử bảng chạy đủ 30 ca A–L
  và mở rộng. Các kiểm thử provider cũ dùng transport giả lập, không gọi live.
- 30/30 ca phát triển khớp tham chiếu nháp: **41/41 cụm động từ/loại hành động**,
  **41/41 hành động kèm phủ định/vai/trạng thái**, **15/15 quan hệ theo nhãn luật**.
  Precision/recall trên các phần này đều 1,0 trong bộ ca đã dùng phát triển.
- **137/137 quote đúng ID/offset Unicode**, 137/137 speaker metadata khớp input.
  Đây là kiểm tra liên kết metadata; **chưa đo precision/recall ngữ nghĩa actor/
  recipient/beneficiary** do chưa có nhãn đầy đủ được người độc lập rà.
- **0 lời gọi provider, 0 request mạng** ở phép thử endpoint; không đọc validation/holdout.
- API ASGI trên 30 ca: p50 **1,37 ms**, p95 **2,12 ms**. Không phải thời gian từ browser,
  chưa đo cold start/tải đồng thời. Các mẫu dài 100/1.000/10.000 ký tự đo 30 lượt mỗi loại,
  xem [TIMING.md](TIMING.md). Mẫu nhiều event bị giới hạn ở 50, không coi phần chưa đọc là an toàn.
- API website tĩnh và hợp đồng /api/analyze vẫn qua test; không chạy lại Chrome thật
  ở lượt thay đổi này vì không sửa frontend và chưa nối route mới vào UI.

Không diễn giải các con số này là hệ thống chính xác 100%/98% ngoài thực tế: dữ liệu
là tổng hợp/ca người dùng cung cấp, đã dùng sửa luật; nhãn là draft_reference,
chưa có hai người rà độc lập. Chưa có phép đo holdout, chất lượng 18 trường toàn diện,
hay phân loại rủi ro cuối. Các lỗi đã sửa khi phát triển gồm đồng/đóng, mã/màn/mặt,
phủ định của người cảnh báo lan vào lời trích, và nhãn H bỏ sót quan hệ mục đích đã có ở G.

## Dữ liệu chưa rõ và giới hạn

technical_checks và benefit_and_mismatch đều unknown trong 30 ca. Danh tính/quan hệ
chỉ tự nhận, không verified. Bộ luật chưa có suy luận người hưởng lợi hoặc mọi cấu
trúc tiếng Việt; action_targets là đối tượng ứng viên từ mệnh đề, không bảo đảm đã
phân tích đúng bổ ngữ trong câu phức. Không có câu phù hợp mẫu không có nghĩa clear.
Xem số trường unknown theo từng khóa trong [summary.json](final/summary.json).

Các quan hệ liền câu chưa có mã giao dịch được gắn inferred và giới hạn; giao dịch
ngầm phức tạp còn có thể sai. Câu bổ sung phải gửi cùng toàn bộ hội thoại, không
có lưu/ghép phiên ngầm. Mã chưa rõ loại sẽ hỏi mô tả loại mã, không xin mã thật.

## Xem mã, dataset và kết quả

- [Cách chạy, khảo sát và ánh xạ 18 → 8](../../README_PYTHON_OBSERVATION.md).
- [30 ca cùng hành động/quan hệ/câu hỏi/unknown](CASES.md).
- [Ví dụ A đầy đủ 18 trường và adapter](example_A.json).
- [Toàn bộ dự đoán](final/predictions.json), [kết quả từng ca](final/case_summary.json),
  [số liệu](final/summary.json), [hash khóa](final/hashes.json).
- [Ba mẫu dev thí điểm](final/dev_pilot.jsonl) và [schema gán nhãn](final/annotation.schema.json).
  Các mẫu là weak_label, có rule_ids, risk_label_reference=null; không phải nhãn chuẩn
  để huấn luyện/chấm chất lượng trước khi được rà. Dataset gốc không đổi.

Thư mục final là lần chấm mã cuối có provenance=user_report và câu hỏi phủ định mơ hồ.
Các JSON trực tiếp ở thư mục cha là lần chạy phát triển trước; không gộp hai lượt thành
mẫu độc lập hoặc chọn số liệu tốt hơn. Không có ca nào còn sai so với tham chiếu của
bộ phát triển này; độ phủ ngoài bộ đó chưa được chứng minh.

Từ thư mục ứng dụng có backend, dùng output mới:

```powershell
python -m unittest discover -s tests -p test_local_observation.py -v
python local_observation_check.py --output reports/local_observation_rerun
```

Script ghi dự đoán trước khi đọc expected. Runtime không đọc dữ liệu nhãn, không
ghi văn bản riêng tư mặc định; báo cáo này lưu dữ liệu tổng hợp do lệnh kiểm thử chủ động tạo.
