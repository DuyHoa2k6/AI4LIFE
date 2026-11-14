# Tạm chuyển luồng chính sang local_rules — 12/11/2026

Đã nối BE v2 vào endpoint đang dùng của website và extension: /api/analyze.
Không chỉ chạy trang /local riêng. Cấu hình lưu local_rules, key/model Gemini giữ
nguyên nhưng không được gọi. Có thể quay lại two_pass bằng cấu hình.

## Kiểm thử

- **275 unittest backend đạt**, gồm 4 bài mới cho adapter production, một bài bảng 12 ca.
- **12/12 ca qua API chính đúng target phát triển**, 0 provider calls và 0 network
  calls. Không có nhãn/expected trong request, source/reference dùng đúng bản gốc.
  [Các ca](api/CASES.md), [dự đoán](api/predictions.json), [hash/số liệu](api/summary.json).
- Các ca gồm OTP trực tiếp, lời cảnh báo OTP, sáu số chưa rõ, giao tài sản trước/
  sau xác nhận tiền, nộp thêm để rút, giấy tờ, ngoài độ phủ, nguy hiểm đang xảy ra,
  di chuyển/giấu gia đình, viết tắt và bài tuyên truyền.
- Kiểm tra cả message ID/speaker, bối cảnh nguồn user_report, lỗi không trả clear,
  thông báo xử lý đúng, không kiểm tra URL mạng và công tắc quay lại two_pass.
- **13 kiểm tra worker + 4 kiểm tra version popup đạt**, extension 0.7.1.
- **10 kiểm tra Chrome thật đạt**: website chính hiển thị đủ bốn mức, tóm tắt BE,
  banner khẩn có quote hợp lệ, ẩn nội bộ; extension unpacked gửi /api/analyze,
  chọn chưa bật không gửi, ngoài vùng không bị gửi, hiện kết quả BE và hỗ trợ khẩn.
  Model endpoint được cố tình trỏ địa chỉ không dùng được, không có mock model;
  không fallback sang Gemini. [Browser report](browser/report.json),
  [website](browser/web.png), [extension](browser/extension.png).

Hai lượt browser đầu dừng ở thao tác test harness (panel Shadow DOM đóng, rồi cố
bấm nút cũ trong khi kết quả đã tự mở); đã sửa harness và chạy đủ 10. Log đầu được
giữ trong report_first_attempt/report_second_attempt, không phải lỗi API phân loại.

## Điều kiện áp dụng và giới hạn

Đây là thử nghiệm trên ca phát triển, không phải accuracy độc lập hoặc chứng minh
đạt 98%. Các giới hạn v2 như quan hệ ngầm, chuỗi nhiều tin đảo điều kiện và actor/
coreference còn tồn tại; xem [review queue](../../../data/v2/REVIEW_QUEUE.md).
Mode này không chạy kiểm tra URL/chuyển hướng mạng. Nguồn chính thống chưa đủ duyệt,
không có danh bạ hỗ trợ vùng đã xác minh, không tự tạo số/URL hoặc gán tội danh.

Lỗi local trả LOCAL_ANALYSIS_UNAVAILABLE/503 khi không có kết luận, không thành
clear. Khi còn tín hiệu urgent có căn cứ, giữ high/urgent và analysis_status=error
nếu cần; UI kiểm tra lại urgency_evidence rồi mới hiển thị banner.

Chưa tự khởi động server người dùng. Probe port 8000 cho thấy chưa có backend chạy;
cần khởi động lại/khởi động theo [hướng dẫn](../../TEMP_LOCAL_MODE.md). Extension cần
Reload và tải lại trang để nạp 0.7.1. Kiểm thử Chrome dùng API cục bộ port 18771
riêng, không thay hoặc dừng server người dùng.

Từ thư mục ứng dụng có backend, mode hiệu dụng phải local_rules:

```powershell
python check_local_switch.py --output reports/local_switch_rerun
python -m unittest discover -s tests -p test_local_provider.py -v
node tests/browser_local_provider.mjs
```
