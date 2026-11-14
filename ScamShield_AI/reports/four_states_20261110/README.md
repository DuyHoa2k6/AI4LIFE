# Kiểm thử bốn trạng thái hiện hành — 10/11/2026

16 ca tổng hợp mới gồm dấu hiệu rõ, biến thể cần nối hành vi và ca bình thường dễ
bị hiểu sai. Bốn nhãn mục tiêu được viết riêng, mỗi nhãn 4 ca, trước khi gọi model.
Không đọc holdout, không gửi expected trong input và không sửa cấu hình/prompt/quy
tắc trong lượt này. Hai lượt chạy đã kiểm tra lại hash trước khi chấm.

## Cách chạy và phạm vi

Gemini thật, model cấu hình `gemini-3.5-flash-lite`, pipeline two_pass hiện hành;
gọi endpoint FastAPI qua ASGI TestClient và gửi HTTP thật tới provider. Không đo
website/extension, tải đồng thời hoặc cold start có kiểm soát. Nhánh nguồn chính
thống trả no_approved_sources; không phải phép đo chất lượng RAG có tài liệu thật.
Ca nhãn link khác đích dùng .invalid, được chặn trước khi gửi HTTP tới đích; quan
sát tên miền vẫn được dùng, không chứng nhận trang đích có hoạt động hay độc hại.

## Kết quả

| Chỉ tiêu | Lượt đầu | Sau kiểm tra lại riêng ca lỗi |
| --- | --- | --- |
| Số ca | 16 | Vẫn 16 ca, 4 ca được kiểm tra lại một lần |
| Có kết quả HTTP 200 | 12/16 | 15/16 |
| Lỗi | 3 lỗi provider HTTP 503, 1 EVIDENCE_INVALID | Còn 1 EVIDENCE_INVALID ở H04 |
| Khớp nhãn mục tiêu, tính trên toàn bộ ca | 8/16 = 50% | 11/16 = 68,75% |
| Khớp nhãn mục tiêu trong ca có kết quả | 8/12 = 66,67% | 11/15 = 73,33% |
| p50/p95 ca HTTP 200 | 15,41 / 35,96 giây | 15,95 / 35,96 giây |

Phân bố cuối: high 4, suspicious 1, need_context 7, clear 3; H04 không có
risk_status vì API từ chối bằng chứng. Lỗi không được coi như mức cảnh báo thứ năm.
20 lần thực thi API tổng cộng, 51 lần thử HTTP provider gồm các retry cấu hình sẵn.
Lượt đầu khoảng 273,35 giây; lượt kiểm tra lại khoảng 78,73 giây, chưa tính thời
gian rà thủ công giữa hai lượt. Không chạy lại ca lệch nhãn để chọn câu trả lời đẹp.

28/28 quote trong 15 phản hồi thành công khớp nguyên văn và không có speaker sai
trong phản hồi công bố. Điều này không chứng minh đúng ngữ nghĩa: S01 vẫn gán vai
inducement sai cho một câu nguyên văn. H04 bị từ chối trước khi công bố kết quả vì
model dùng unknown thay cho nguoi_la trong cả hai lần thử.

## Sai lệch đã rà

- **S01 high, mục tiêu suspicious:** model gắn câu không giải thích mục đích vào
  inducement và quan hệ access_required_before_benefit. Backend chấp nhận quan hệ
  có quote đúng nhưng chưa phát hiện câu không hề nêu lợi ích/điều kiện nhận lợi ích.
- **S02 need_context, mục tiêu suspicious:** regex coi đoạn chưa cung cấp nhà phát
  hành/lý do cần cài là một request cài bổ sung. Gemini coi là claim; xung đột quy tắc
  giữ backend ở need_context dù yêu cầu cài APK đã rõ.
- **N04 need_context, mục tiêu clear:** Gemini cuối không yêu cầu thêm bối cảnh;
  regex bắt “đã cài từ trước” thành request install_app, gây rule_conflicts=1.
- **S04 need_context, mục tiêu suspicious:** action other đã nhận ra nhưng mục đích
  chưa rõ. Chính sách giữ need_context cho nhóm này; đây là khác biệt ngưỡng cần
  thống nhất, không phải bằng chứng ca này chắc chắn lừa đảo.
- **H04 EVIDENCE_INVALID:** quote khớp chữ nhưng speaker model trả unknown khác
  định danh người nói của input. Cổng kiểm chứng chặn cả hai lần, không trả cảnh báo.

Các ca đúng gồm nhận ra “tiền đồng bộ” là khoản tiền phải đưa trước để nhận tiền,
đọc khoản vay bằng phương ngữ theo bối cảnh, phân biệt trích lời dụ để cảnh báo và
giữ need_context khi “cái đó”/“bước kia” chưa có đối tượng xác định.

Đây là mức khớp nhãn do người thiết kế ca chốt trước trên tập tổng hợp nhỏ, không
phải ước lượng độ chính xác độc lập hoặc cơ sở tuyên bố đạt 98% trên dữ liệu thật.

## Bàn giao

- [Nội dung, kết quả và giải thích đủ 16 ca](CASES.md).
- `live/`: lock, dự đoán đầy đủ từng ca, ma trận, số đo và lỗi lượt đầu.
- `retry_errors/`: lần kiểm tra lại N01/H02/N03/H04, giữ riêng dữ liệu lượt đầu.
- `MANUAL_REVIEW.json`, `final_summary.json`: kết quả đối chiếu cuối.
- `verification.json`: xác nhận hash hai lượt và các chỉ tiêu tổng hợp.
- `fixtures/four_states_20261110/inputs.json` và `expected.json`: input/nhãn riêng.

Lệnh từ thư mục ứng dụng (output mới phải chưa tồn tại):

```powershell
python create_four_state_checks.py
python mixed_check.py --mode two_pass --output reports/four_states_20261110/live --fixtures-dir fixtures/four_states_20261110 --pause 1 --service-error-limit 3
python mixed_check.py --mode two_pass --output reports/four_states_20261110/retry_errors --fixtures-dir fixtures/four_states_20261110 --pause 2 --service-error-limit 3 --case-ids N01 H02 N03 H04
python four_state_report.py
```

Fixture đã tồn tại thì bỏ lệnh tạo; script không ghi đè fixture cũ. Khi chạy lại cần
đổi đường dẫn output, giữ báo cáo hiện tại để đối chiếu; không tự đổi nhãn theo kết quả.
