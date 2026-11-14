# Đo backend với 10 tình huống được cung cấp

Đã đọc tệp đính kèm và gửi riêng nội dung từng lượt nói qua `POST /api/analyze`
dưới dạng `messages`, giữ thứ tự và speaker nhất quán. Không gửi tiêu đề, tên
phương thức hoặc đáp án. Phần “người dùng bổ sung” được giữ thành lượt nói của
người dùng trong hội thoại, không bỏ đi hoặc thay bằng kết luận.

Không sửa bộ phân tích theo kết quả bài này. SHA-256 tệp gốc, các file suy luận
và rulebook nằm trong `summary.json`. Chế độ local_rules/legacy/context enabled;
URL network tắt, HTTP transport bên ngoài bị chặn trong bài đo.

## Kết quả thực tế

- 10 tình huống × 3 lượt = 30 request phân tích công khai, cộng 10 request
  `/api/analyze-local` để lưu cấu trúc nội bộ, không tính vào thống kê độ trễ công khai.
- 6 ca need_context, 3 ca suspicious, 1 ca high; mức cảnh báo ổn định cả 3 lượt.
- 0 lỗi HTTP, 0 lời gọi HTTP bên ngoài.
- p50 57,903 ms, p95 nearest-rank 88,35 ms trên 30 request công khai.
- 405/405 quote trong 3 lượt khớp nội dung theo message_id/start/end.

Đây là phép đo ASGI TestClient tuần tự trong một tiến trình. Không phải thời
gian từ nút gửi ở web/extension, không đo tải đồng thời hoặc cold start có
kiểm soát. Một lượt gọi đầu tiên mất 121,681 ms, được giữ trong dữ liệu đo.

[Nội dung và kết quả từng ca](CASES.md) · [Rà lỗi từng ca](MANUAL_REVIEW.md) ·
[Dự đoán và cấu trúc BE](predictions.json) · [Số liệu và hash](summary.json).

## Kết luận có thể rút ra

Backend chạy nhanh và không lỗi hạ tầng trong phép thử, nhưng chưa phân tích
đủ nhiều cách diễn đạt và chuỗi hành vi của bộ hội thoại mới. Không được lấy
24/24 hoặc 31/31 của bộ development trước làm chứng minh tổng quát hóa. Bộ này
là giả lập công khai, không phải vụ việc thật hoặc tập độc lập có nhãn chuyên gia.
Tệp không có bảng đáp án chính thức; các mức đề xuất trong MANUAL_REVIEW là
nhận xét cần rà, không dùng để công bố accuracy/precision/recall.

## Chạy lại

Từ thư mục ứng dụng, dùng đường dẫn tệp đính kèm ban đầu hoặc bản sao của nó:

```powershell
python check_user_scenarios10.py --source "C:\Users\nhoa4\.codex\attachments\c23e52f9-f527-4757-9ba6-4a4c9ffd89d1\Pasted text.txt" --output reports/user_scenarios10_repeat --rounds 3
```

Thư mục đầu ra phải chưa tồn tại. `inputs.json` đã lưu payload dùng thực tế,
`metadata.json` giữ tiêu đề và ánh xạ nhãn người nói để rà ngoài API.
