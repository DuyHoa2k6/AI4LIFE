# Chuyển OpenAI và thử một ví dụ — 11/11/2026

Đã thay cấu hình riêng `backend/local_settings.py`: mode two_pass,
endpoint `https://api.openai.com/v1/chat/completions`, model `gpt-4.1-mini`,
output_format json_schema. Key chỉ nằm trong file riêng đã được .gitignore bỏ qua;
không nằm trong website/extension/báo cáo. Không thay chính sách bốn mức.

Model hỗ trợ Chat Completions và Structured Outputs theo
[OpenAI Docs](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
Đây là lựa chọn để thử adapter hiện có, không phải kết luận model tối ưu hoặc
quyền truy cập tài khoản đã được xác nhận.

Ví dụ gửi qua POST /api/analyze:

```json
{"text":"Gửi mã OTP cho tôi để tôi đăng nhập tài khoản của bạn và xử lý hoàn tiền."}
```

- [Kết quả qua hệ thống](result.json): provider HTTP 429 ngay lượt observation;
  backend trả HTTP 503 / PROVIDER_UNAVAILABLE sau khoảng 1,82 giây, chưa có risk_status.
- [Yêu cầu tối thiểu độc lập](connectivity.json): “Reply with OK.” cũng HTTP 429,
  `error.code=credit_balance_exhausted`, `error.type=insufficient_quota`.

**Chưa nhận được câu trả lời từ GPT vì tài khoản/dự án hết credit API.** Không có
căn cứ quy lỗi cho nội dung ví dụ hoặc prompt backend. Không tự chuyển về Gemini
hay trả mock thay cho kết quả thật. Cần bổ sung credit cho dự án của key, rồi thử lại.
Key xuất hiện trong cuộc trò chuyện; nên thay bằng key mới khi hoàn tất thử nghiệm.

Chạy lại từ thư mục có backend, dùng output mới:

```powershell
python smoke_openai.py --output reports/openai_smoke_retry
```

Backend đang chạy cần dừng và khởi động lại để nhận cấu hình mới:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
```
