# Chạy 10 trường hợp người dùng cung cấp — 10/11/2026

Đã gửi riêng 10 ca qua POST /api/analyze bằng ASGI TestClient, dùng Gemini thật và
cấu hình two_pass hiện hành. Không dùng nhãn mục tiêu hoặc đổi prompt/quy tắc trong
lượt chạy. Các hội thoại 4/6/7 được chuyển thành messages có ID và người nói theo
đúng nhãn trong nội dung người dùng; không gộp người nói hoặc thêm bối cảnh để ép mức.

## Kết quả thực tế

| Ca | Nội dung chính | Kết quả cuối |
| --- | --- | --- |
| 1 | Giao laptop trước khi thấy tiền vì tài xế đang chờ | need_context |
| 2 | Nhắc không làm theo lời dụ gửi OTP | clear |
| 3 | Hoàn cọc sau bước xác nhận chưa được hướng dẫn | need_context |
| 4 | Chia sẻ màn hình ngân hàng để duyệt hoàn cọc | Chưa kiểm tra được: EVIDENCE_INVALID lần đầu, PROVIDER_UNAVAILABLE lần hai |
| 5 | Đổi tài khoản nhận hóa đơn, chuyển trước rồi gọi đối chiếu sau | need_context |
| 6 | Người bán nói đã tự thấy đủ tiền trước khi giao máy | Chưa kiểm tra được: PROVIDER_UNAVAILABLE lần đầu, EVIDENCE_INVALID lần hai |
| 7 | Yêu cầu đọc sáu số dù biết đó là mã đăng nhập | Chưa kiểm tra được: EVIDENCE_INVALID cả hai lần |
| 8 | Lệnh rút chờ kiểm tra, chưa có bước tiếp theo | need_context |
| 9 | Xin hai mặt căn cước và chân dung để giữ suất hỗ trợ | high |
| 10 | Hoa hồng mồi, ứng tiền rồi nộp thêm để mở khóa | high |

Lượt đầu 5/10 ca có HTTP 200. Năm ca lỗi được kiểm tra lại đúng một lần, giữ nguyên
input và cấu hình: sau cùng 7/10 có kết quả, 3/10 vẫn lỗi. Tổng 15 lần gọi API;
không tính là 15 trường hợp khác nhau. Phân bố trong 7 kết quả: need_context 4,
clear 1, high 2, suspicious 0. Đây là số phản hồi hợp lệ, không phải độ chính xác.

Trung vị thời gian của phản hồi cuối thành công 20,68 giây; p95 58,22 giây (7 mẫu,
p95 cũng là mẫu chậm nhất). Tổng chạy khoảng 308,8 giây gồm thời gian chờ giữa các
lượt. Không đo từ nút gửi website/extension hoặc tải đồng thời. Deadline Gemini
vẫn theo cấu hình hiện có; không đổi giới hạn trong lúc kiểm thử.

## Điểm cần chú ý khi đọc kết quả

- Ca 1 và 5 có tín hiệu thực tế cần rà kỹ nhưng hệ thống vẫn giữ need_context.
  Không nên diễn giải mức này là an toàn hoặc cho phép giao máy/chuyển tiền.
  Ca 1 giữ request giao máy; ca 5 giữ request đổi tài khoản và chuyển trước, nhưng
  đều không có risk_link được chấp nhận trong phản hồi cuối.
- Các lỗi EVIDENCE_INVALID là lỗi không vượt cổng kiểm chứng bằng chứng. Phản hồi
  lỗi không chứa chi tiết đủ để khẳng định sai quote hay sai người nói; không suy
  đoán nguyên nhân cụ thể từ mã lỗi. Ca 4/6/7 không có risk_status để báo thay.
- Câu hỏi ca 3 còn chung chung về người gửi, chưa trực tiếp hỏi bước xác nhận là
  gì; các câu hỏi thực tế được ghi đầy đủ trong CASES.md, không thay bằng câu hỏi lý tưởng.
- Ca 1 chỉ nhắc đến ảnh biên lai trong văn bản. Không có ảnh thật được tải lên nên
  không chạy OCR hoặc xác minh biên lai. Tương tự, không có ảnh căn cước thật ở ca 9.
- Việc người bán nói đã thấy tiền ở ca 6 là lời khai trong nội dung, không phải
  kết quả hệ thống kết nối ngân hàng. Quote đúng chữ cũng không chứng minh lời khai đúng.

## Bàn giao

- [Đầu vào, trích dẫn, câu hỏi, thời gian và lịch sử từng ca](CASES.md).
- `inputs.json`: dữ liệu đã gửi, không có nhãn kỳ vọng.
- `predictions.json`: toàn bộ phản hồi của cả 15 lần gọi API, không xóa lỗi.
- `summary.json`: thống kê; `lock.json`: model/phiên bản hash đã khóa, không có API key.
- `verification.json`: kiểm tra hash và số trích dẫn của phản hồi thành công.

Lệnh từ thư mục ứng dụng:

```powershell
python run_user_ten_cases.py
python summarize_user_ten_cases.py
```

Đường dẫn output đã tồn tại thì script chạy API sẽ không ghi đè. Muốn tạo phiên
mới cần đổi OUT; giữ báo cáo này để đối chiếu. Không dùng các ca này làm số liệu
holdout độc lập nếu sau này chỉnh cấu hình dựa trên chúng.
