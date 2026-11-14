# Tách mệnh đề thiếu dấu câu — 12/11/2026

Áp dụng cho bộ Python riêng POST /api/observe, rules vi-observer-rules-1.1.
Không thay /api/analyze, không gọi Gemini hoặc quyết định cảnh báo cuối.

## Thay đổi

- Bảo vệ URL, số tiền, Unicode và lời trích; mọi quote/offset vẫn từ nguyên bản.
- Dấu phẩy gắn với đoạn trước, không trả đoạn chỉ có dấu phẩy.
- Từ nối cần có vị ngữ theo sau; “đã chuyển tiền rồi”, “công việc đã xong” không tự
  sinh đoạn mới. Không biến danh từ “đê” thành liên từ “để” chỉ vì bỏ dấu.
- Hai cụm hành động có dấu hiệu yêu cầu độc lập có thể tách khi không có dấu câu.
  Không cắt chỉ vì câu dài. Giữ từ phủ định/chủ thể/chỉ dẫn đi cùng hành động sau.
- Ranh giới suy ra ghi action_restart/inferred. Phạm vi ngữ cảnh sau ranh giới mới
  không kế thừa phủ định hoặc vai cảnh báo của đoạn trước.
- Đổi mã Đơn A/Đơn B có trạng thái riêng được tách phạm vi; không nối hai giao dịch.
- Với “đừng chuyển tiền và gửi OTP”, không ép tách: Unit boundary_status=uncertain,
  hành động gửi mã có polarity=uncertain và câu hỏi làm rõ. Mệnh đề “người vừa gửi mã”
  không tự thành yêu cầu trực tiếp mới.

Ví dụ:

```text
Đừng gửi OTP cho người lạ gửi mã đăng nhập cho tôi để hoàn tiền
```

Đầu ra:

1. “Đừng gửi OTP cho người lạ”: hành động gửi mã bị phủ định.
2. “gửi mã đăng nhập cho tôi”: yêu cầu dương tính, phạm vi độc lập suy ra.
3. “để hoàn tiền”: mục đích người gửi nêu.

Đây là cách hiểu theo quy tắc của mẫu trên; không chứng minh mọi cấu trúc tương tự
đều có duy nhất cách hiểu này. Không chèn dấu câu vào đầu vào hoặc dựng quote mới.

## Kiểm thử thực tế

- **233 unittest đạt**, gồm 10 bài chuyên cho tách đoạn (một bài có bảng 16 ca).
- **16/16 ca ranh giới phát triển**, 28/28 span đoạn khớp tham chiếu nháp.
- **30/30 ca trích hành vi hồi quy** vẫn đạt, 41 hành động, 15 quan hệ, 137 quote khớp.
- **0 provider calls, 0 request mạng** khi chạy các ca qua API /api/observe.
- Thử riêng Unicode phân rã, phủ định phối hợp, lời cảnh báo có lời trích rồi tới
  yêu cầu mới, lời trích nối bằng “nhưng”, mệnh đề quan hệ và tin nhắn khác người nói.

[16 ca và các đoạn/hành động trả về](CASES.md) · [JSON dự đoán](predictions.json) ·
[Số liệu và hash](summary.json) · [Hồi quy 30 ca và đo thời gian](regression30/summary.json).

Các ca là dữ liệu phát triển đã dùng chỉnh luật, không phải phép đo độc lập về độ
chính xác ngắt câu tiếng Việt. Chưa đo precision/recall ranh giới trên dữ liệu thật,
chưa chạy lại browser/extension ở lượt này. Câu không dấu, từ lóng, tham chiếu xa,
giao dịch ngầm, trích dẫn thiếu dấu đóng hoặc mệnh đề phức vẫn có thể sai. Không
tự khôi phục dấu câu bằng AI, không bảo đảm hiểu mọi câu thiếu dấu câu.

Từ thư mục có backend:

```powershell
python -m unittest discover -s tests -p test_local_segmentation.py -v
python -m unittest discover -s tests -p 'test_*.py' -q
python local_observation_check.py --output reports/local_segmentation_regression_rerun
```

Khởi động lại backend để nạp bộ luật có cache, rồi xem POST /api/observe trong /docs.
