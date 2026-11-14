# Kiểm tra lỗi INVALID_INPUT — 10/11/2026

Ảnh báo lỗi ở tin nhắn giả mạo hỗ trợ sinh viên: gây áp lực khóa tài khoản,
yêu cầu nhập mật khẩu và dãy sáu số vào tên miền `.invalid`. Không mở tên miền.

## Kết quả thực tế

- `python tests/check_student_phishing.py`: HTTP API đang chạy ở cổng 8000,
  chế độ `two_pass`, Gemini thật; HTTP 200, `high`, 14,3949 giây.
  Đầu vào và toàn bộ phản hồi ở `input.json`, `live.json`. Đây là một ca tái hiện,
  không phải đánh giá độ chính xác trên tập độc lập. Chạy trước sửa chẩn đoán lỗi;
  không thay đổi quy tắc phân loại hoặc prompt để ép ca này thành high.
- `python -m unittest discover -s tests`: 140/140 đạt sau sửa, gồm kiểm tra
  giữ nguyên chặn sai offset và không lộ nội dung/tên trường ngoài schema.
- `node tests/worker_security.mjs`: 13/13 đạt, gồm chuyển nguyên payload có link,
  cố định API origin, chẩn đoán 422 an toàn và giao thức cấu hình.
- `node tests/popup_version.mjs`: 4/4 đạt, chặn script cũ còn trong tab.
- `node tests/browser_url.mjs`: 10/10 đạt trên Chrome 157, extension thật và
  backend mock. Ca sinh viên gửi cả văn bản/link, không OCR, hiển thị kết quả.
  Chi tiết và ảnh ở `../urls/browser/`. Phép thử Chrome này không dùng Gemini.

## Chẩn đoán và thay đổi

Không thu được request lỗi từ tab người dùng nên chưa chứng minh trường cụ thể
gây INVALID_INPUT. Nội dung tái hiện hợp lệ với backend hiện tại. Worker trước sửa
trong repo chuyển lỗi 422 thành HTTP_422, khác thông báo trong ảnh; có dấu hiệu
thành phần extension cũ đang chạy. Bản 0.4.1 kiểm tra script trong tab và giao thức
worker trước khi cho quét, thay vì tiếp tục với các phiên bản không tương thích.

API bổ sung đường dẫn trường lỗi đã lọc, không phản chiếu input. Extension hiển thị
chỉ dẫn và đường dẫn an toàn khi gặp 422. Không bỏ qua validation, không âm thầm
bỏ link, không tự đổi sang mock khi Gemini lỗi. OCR vẫn phải bấm nút riêng.

## Áp dụng trên trình duyệt đang mở

Khởi động lại backend để nhận chẩn đoán mới. Tại `chrome://extensions`, xác nhận
đúng extension từ thư mục `ScamShield_AI/extension`, bấm Tải lại (bản 0.4.1).
Tải lại trang cần quét bằng Ctrl+Shift+R rồi chọn vùng/bật quét. Các script cũ
đã chèn và huy hiệu lỗi cũ không tự được thay bằng mã mới khi chỉ sửa file trên đĩa.
