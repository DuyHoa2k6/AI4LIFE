# Kiểm thử cảnh báo hiện tại — 10/11/2026

Giữ nguyên backend, prompt, model, quy tắc và chỉ mục trong suốt phiên chạy. Chưa triển khai phần gợi ý nội dung linh hoạt. Dữ liệu mới được viết trước khi gọi model: 18 tình huống nguy hiểm và 6 ca bình thường đối chứng, sáu nhóm hành vi. Đây là bộ tổng hợp do người triển khai đặt kỳ vọng, không phải tập gán nhãn độc lập.

| Chỉ số | Quan sát |
| --- | --- |
| API thành công | 24/24 |
| Lỗi / chưa chạy | 0 / 0 |
| Ca nguy hiểm trả high | 17/18 (94.4%) |
| Ca nguy hiểm có cảnh báo high hoặc suspicious | 17/18 |
| Ca nguy hiểm chưa trả high, kể cả lỗi/chưa chạy | 1/18 |
| Ca bình thường bị high/suspicious | 0/6 |
| Khớp mức kỳ vọng trên toàn bộ bộ ca | 23/24 (95.8%) |
| High precision trên mẫu có nhãn | 100.0% (TP=17, FP=0) |
| API p50 / p95 | 6.890 / 9.592 giây |
| Tổng phiên gồm khoảng nghỉ | 243.088 giây |
| HTTP attempt tới provider | 50 |
| Số lần sửa mâu thuẫn quan sát ở phản hồi thành công | 1 |
| Quote khớp ở phản hồi thành công | 51/51 |
| Sai tham chiếu người nói ở phản hồi thành công | 0 |

Không coi need_context là clear: đó là chưa nâng cảnh báo đúng mức kỳ vọng. Lỗi API cũng là không bàn giao được cảnh báo; vẫn tính trong mẫu số recall toàn luồng. High precision trên mẫu ít ca bình thường không chứng minh tỷ lệ báo nhầm ngoài thực tế.

## Theo nhóm

| Nhóm | Ca nguy hiểm high / tổng | Tổng ca khớp | Lỗi/chưa thành công |
| --- | --- | --- | --- |
| transfer_funds | 2/3 | 3/4 | 0 |
| share_auth_code | 3/3 | 4/4 | 0 |
| grant_access | 3/3 | 4/4 | 0 |
| install_app | 3/3 | 4/4 | 0 |
| inducement | 3/3 | 4/4 | 0 |
| other | 3/3 | 4/4 | 0 |

## Phân bố kết quả

| Nhãn kỳ vọng | high | suspicious | need_context | clear | lỗi | chưa chạy |
| --- | --- | --- | --- | --- | --- | --- |
| scam | 17 | 0 | 1 | 0 | 0 | 0 |
| normal | 0 | 0 | 0 | 6 | 0 | 0 |

## Thời gian từng bước

Chỉ tính các ca API thành công; nhánh provider thứ hai gồm cả yêu cầu sửa nếu có. Không tách được thời gian mạng khỏi thời gian xử lý nội bộ của Google.

| Bước | n | p50 | p95 |
| --- | --- | --- | --- |
| first_provider | 24 | 3.2524s | 3.6451s |
| retrieval_parallel | 24 | 0.0027s | 0.0056s |
| second_provider | 24 | 3.4043s | 6.6134s |
| verification_render | 24 | 0.0007s | 0.0016s |

## Phạm vi và tái lập

Model `gemini-3.5-flash-lite`, mode `two_pass`, output `auto`, retry HTTP=1, concurrency=1, nghỉ 3.0 giây giữa ca. Tắt response timeout=True; không đổi cấu hình này khi đo.

Các hash prompt/mã/dữ liệu/chỉ mục trong live/lock.json đã đối chiếu lại và không đổi. Mọi dự đoán được ghi trước khi script chấm đọc expected. Không đọc hoặc chỉnh holdout. Không chạy lại ca lỗi để chọn kết quả tốt hơn. Không sửa hệ thống dựa vào kết quả trong phiên.

Đo qua ASGI TestClient và HTTP Gemini thật, chưa đo từ lúc bấm gửi ở browser/extension, chưa đo tải đồng thời, cold start được kiểm soát hoặc chất lượng trên dữ liệu người dùng thật. Không có nguồn chính thống được duyệt nên đây không phải phép đo chất lượng RAG có tài liệu thực. Không tính các câu trả lời đúng cấu trúc là chứng minh tám câu hỏi đều đúng ngữ nghĩa. Kết quả không chứng minh đạt mục tiêu 98%.

```powershell
python mixed_check.py --mode two_pass --output reports/scam_warning_20261110/live --fixtures-dir fixtures/scam_warning_20261110 --pause 3 --service-error-limit 6
python scam_warning_report.py
```

Lệnh chạy từ thư mục ứng dụng ScamShield_AI. Thư mục output phải chưa tồn tại; đổi output cho phiên mới thay vì ghi đè. Báo cáo chi tiết ở [CASES.md](CASES.md), [cases.csv](cases.csv), [summary.json](summary.json), [dự đoán gốc](live/predictions.json). Rà lỗi và giới hạn ngữ nghĩa ở [MANUAL_REVIEW.md](MANUAL_REVIEW.md).
