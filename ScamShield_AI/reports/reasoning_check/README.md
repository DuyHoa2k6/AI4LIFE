# Kiểm thử các trường hợp cần suy luận — 08/11/2026

Đây là 10 ca chức năng tổng hợp công khai, không phải holdout hoặc đánh giá độc lập. Không chỉnh prompt/quy tắc theo kết quả lượt này. Dữ liệu ở `fixtures/reasoning_checks/inputs.json`, kỳ vọng tách ở `expected.json`. Script lưu dự đoán trước khi chấm kỳ vọng.

## Lượt gọi model thật

Tên model trong local_settings.py đang trống. Script thử chọn riêng `gpt-5.6-terra` theo phương án đã đề xuất; không ghi model này vào cấu hình backend. API key được đọc nội bộ từ cấu hình riêng, không in hoặc lưu trong báo cáo.

- Preflight đọc model: HTTP 403, từ chối truy cập; chưa đủ căn cứ kết luận key sai hoặc model không tồn tại.
- Endpoint phân tích thật: đã thử RC-01 qua HybridProvider/LiveProvider, provider trả HTTP 429, backend trả 503/PROVIDER_UNAVAILABLE. Không có risk_status và không âm thầm fallback mock.
- Một lần thử bổ sung để phân loại lỗi cũng trả 429; phản hồi không cung cấp mã lỗi thuộc nhóm đã xác định, nên chưa phân biệt hết quota với rate limit. Lượt trước được giữ trong live/previous_attempts.
- Dừng các ca live còn lại. **0 ca nhận được phân tích live thành công; chưa đo được chất lượng suy luận, bằng chứng hoặc câu hỏi của mô hình thật.** Không coi lỗi truy cập là model phân tích sai kịch bản.

Xem preflight.json, live/predictions.json và live/summary.json. Cần kiểm tra quyền và giới hạn sử dụng trên tài khoản API, chọn model có quyền truy cập rồi chạy lại. Không khẳng định nguyên nhân quota/tốc độ khi chưa có mã lỗi cụ thể. RAG chưa được tích hợp.

## Kết quả mock chạy riêng

| Ca | Nội dung | Kỳ vọng chức năng | Quan sát mock |
| --- | --- | --- | --- |
| RC-01 | Nộp phí để nhận lại tiền bị mất | high | high — khớp |
| RC-02 | Đòi trả tiền đã mượn bằng tiếng địa phương | need_context, hỏi quan hệ/mục đích | suspicious, không hỏi — chưa đạt |
| RC-03 | Trả nợ có context xác nhận | clear theo bối cảnh được cung cấp | suspicious — chưa đạt; mock không đọc context |
| RC-04 | Bài cảnh báo trích lời dụ | clear | clear — khớp |
| RC-05 | Làm nhiệm vụ rồi ứng thêm để rút | high | clear — chưa đạt, bỏ sót mẫu “Ứng thêm” |
| RC-06 | Hai người nói, lời hứa không liên quan | không high | suspicious — khớp tiêu chí không ghép nhầm |
| RC-07 | Khoản rút treo, thiếu điều kiện | need_context, hỏi thêm | need_context và có câu hỏi — khớp |
| RC-08 | Chỉ thị nhúng kèm yêu cầu mã đăng nhập | high, không nguồn bịa | high, source_matches rỗng — khớp |
| RC-09 | Quyền giám sát thiết bị diễn đạt mới | high | clear — chưa đạt, ngoài cách nói của bộ quy tắc |
| RC-10 | Tự nhập OTP trên ứng dụng chính thức | clear | clear — khớp |

Mock khớp nhãn/tiêu chí ở **6/10 ca**, không phải độ chính xác mô hình AI. Hai ca high bị trả clear (RC-05/09) là giới hạn cần ưu tiên xử lý bằng luồng live đã nghiệm thu hoặc phát triển mock với bộ đánh giá khác. Các trường hợp trả nợ cho thấy chỉ nhận từ khóa chuyển tiền chưa đủ hiểu ngữ cảnh. Không sửa theo tập này rồi tiếp tục gọi nó là tập độc lập.

49 kiểm thử tự động điều phối/hồi quy hiện có vẫn qua (reports/hybrid/python_tests.txt). Các kiểm thử đó có phản hồi live giả lập, nên không thay thế kết quả live đang bị chặn ở trên.

## Chạy lại

```powershell
python ScamShield_AI/reasoning_check.py --mode mock
python ScamShield_AI/reasoning_check.py --mode live --model TEN_MODEL_DUOC_CAP_QUYEN
```

Lượt live có thể phát sinh phí nếu provider trả phân tích. Chỉ dùng dữ liệu tổng hợp công khai; không gửi holdout hoặc dữ liệu riêng. Script dừng sau lỗi provider đầu tiên, lưu dự đoán trước chấm và giữ lịch sử lần chạy trước.

## Xem hệ thống đang chọn model nào

Đọc `SCAMSHIELD_MODEL` trong `backend/local_settings.py`; biến môi trường cùng tên được ưu tiên nếu terminal còn đặt từ trước. Không chia sẻ toàn bộ file cấu hình vì nó có key. Key không phải tên model. Tham số --model của script chỉ chọn model cho lần chạy đó, không sửa model mặc định của ứng dụng. Lượt này ghi nhận model yêu cầu, chưa có phản hồi thành công để xác nhận model thực tế. Tài liệu model đã đối chiếu: https://developers.openai.com/api/docs/models/gpt-5.6-terra
