# Kiểm thử bốn mức cảnh báo và chính sách tình huống

Thực hiện 10–11/11/2026. Bản bàn giao: two-pass-6 / API 1.9, extension 0.7.0.

## Thay đổi đã triển khai

- Gemini trả sự kiện, quan hệ và khoảng trống có bằng chứng; regex chỉ là gợi ý bắt buộc rà, không bỏ phiếu hoặc ép mức.
- Backend nối người nói bằng ID gốc. Không cho finding ghép nhiều tác giả; quote sai được yêu cầu chép lại tối đa một lần dùng chung hai lượt, không nới kiểm chứng.
- Đánh giá cả bối cảnh ngay trong hội thoại: tự báo nhận đủ tiền khác bên trả chỉ đưa biên lai; bối cảnh bình thường chỉ giải thích yêu cầu tương ứng.
- Chuỗi chia sẻ màn hình/mở ngân hàng và dãy ký tự được xác định là mã đăng nhập có thể high. Giao tài sản khi chưa xác nhận tiền, đổi tài khoản/xác minh sau, giấy tờ qua chat thuộc suspicious khi đủ bằng chứng.
- Không nâng mọi other + lợi ích thành high. Không hạ hành vi rõ chỉ do chưa biết danh tính; uncertain cần khoảng trống thực về hành động/đối tượng/quan hệ.
- Câu hỏi tối đa hai, ưu tiên bước/đối tượng/mục đích thực sự thiếu; không tự tạo phí hoặc yêu cầu người dùng gửi OTP thật.
- Website/extension dùng bản tóm tắt, hành động và quote giải thích đã kiểm chứng; không hiện answers, nguồn RAG hoặc nội dung suy luận nội bộ.

## Kiểm thử chính sách và giao diện

**24/24 ca API với đầu ra Gemini mô phỏng đúng mức kỳ vọng**, mỗi mức 6 ca. Đây kiểm tra logic và kiểm chứng khi model trả các fact đã định, không phải độ chính xác suy luận Gemini 100%. 40/40 quote khớp, 0 lỗi tham chiếu người nói, cả 6 ca need_context có câu hỏi.

- 203 unittest backend đạt, bao gồm một kiểm thử bảng 14 ca mới và các ca giả bằng chứng, Unicode, sai tác giả, quan hệ thiếu đầu mút, mâu thuẫn, sửa hữu hạn.
- Chrome thật: 30 kiểm tra toàn luồng website/extension với provider tổng hợp; 44 kiểm tra URL/hiển thị kết quả; 11 kiểm tra OCR thật với phân tích mock.
- 13 kiểm tra worker và 4 kiểm tra phiên bản popup đạt. Hàng đợi 35 mục chạy 35 request, tối đa một request đồng thời trong phép thử Chrome, dung lượng 20 và quan sát 15 mục hoãn.

## Gemini thật — giữ riêng từng phiên

Model trong các lock: gemini-3.5-flash-lite. Dữ liệu tổng hợp; 10 ca gốc đã được dùng chỉnh cấu hình nên chỉ là hồi quy. 14 ca bổ sung được khóa sau sửa và không dùng sửa lại thuật toán trong lượt này. Không đọc holdout. Không gộp các bản prompt/code khác nhau để báo một tỷ lệ đúng.

| Thư mục | Thực chạy | Có kết luận | Lỗi | Chưa chạy | Đúng mức / có kết luận | p50/p95 thành công (giây) |
|---|---:|---:|---:|---:|---:|---|
| [regression](regression/summary.json) | 10 | 7 | 3 | 0 | 6 / 7 | 20.19 / 29.12 |
| [checked](checked/summary.json) | 10 | 3 | 7 | 0 | 3 / 3 | 12.11 / 22.83 |
| [focused](focused/summary.json) | 5 | 0 | 5 | 2 | 0 / 0 | chưa đo |
| [followup_live](followup_live/summary.json) | 4 | 1 | 3 | 10 | 1 / 1 | 11.20 / 11.20 |
| [followup_stratified_live](followup_stratified_live/summary.json) | 3 | 3 | 0 | 0 | 3 / 3 | 33.06 / 41.04 |
| [followup_remaining_live](followup_remaining_live/summary.json) | 4 | 1 | 3 | 3 | 1 / 1 | 16.49 / 16.49 |

regression dùng prompt v7: U05 bị need_context vì model nhầm thiếu xác thực tài khoản với thiếu quan hệ chuyển trước/xác minh sau. Đã sửa prompt/kiểm chứng trong v7.1. checked là lượt kế tiếp, trước khi thêm bối cảnh thanh toán thông thường và chặn uncertain không có lý do; focused dùng bản cuối nhưng cả 5 ca thực gửi đều 503, hai ca còn lại không gửi. Không thể khẳng định U05 live đã sửa thành công từ các kết quả này.

Ba batch followup cùng bản cuối: **11 ca duy nhất đã gửi, 5 có kết luận đúng kỳ vọng, 6 lỗi dịch vụ 503, 3 chưa gửi**. Các ca có kết luận: F01 clear, F05 need_context, F06 need_context, F09 suspicious, F12 high. Có đủ bốn mức trong kết quả live nhưng mẫu quá nhỏ để kết luận chất lượng tổng thể. Các batch có thể giao nhau về thời gian; concurrency=1 trong từng runner, không phải phép đo tải đồng thời có kiểm soát.

Độ trễ live đo qua ASGI và HTTP thật; chưa phải từ lúc bấm trên browser. Mẫu p95 rất nhỏ, deadline trả lời vẫn tắt theo yêu cầu trước. Lỗi 503 là chưa kiểm tra được, không ép clear/need_context. Không có nguồn chính thống thật được duyệt nên không phải đo chất lượng RAG có nguồn thực. Chưa đo độ chính xác độc lập, ngữ nghĩa đủ tám câu hỏi hoặc đạt mục tiêu 98%.

## Xem và chạy lại

- [24 tình huống, lời giải thích, câu hỏi và kết quả từng ca](CASES.md).
- [Dự đoán API với model mô phỏng](policy_api/predictions.json) và [hash/matrix](policy_api/summary.json).
- [Màu, cuộn và giải thích trên Chrome](../urls/browser/) · [toàn luồng two_pass](browser_two_pass/browser.json) · [OCR](../ocr/browser/report.json).

Từ thư mục ứng dụng ScamShield_AI (thư mục có backend):

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
python run_situation_checks.py --output reports/situation_policy_rerun
node tests/worker_security.mjs
node tests/popup_version.mjs
$env:SCAMSHIELD_BROWSER_TWO_PASS='1'
$env:SCAMSHIELD_REPORT_DIR='reports/situation_browser_rerun'
node tests/browser_week2.mjs
node tests/browser_url.mjs
node tests/browser_ocr.mjs
python mixed_check.py --mode two_pass --output reports/situation_live_rerun --fixtures-dir fixtures/situation_followup_20261110 --pause 8 --service-error-limit 3
```

Dùng thư mục output mới. Lệnh live dùng provider/model đang cấu hình: ngày 11/11 đã chuyển OpenAI theo yêu cầu; các số liệu Gemini ở đây là bản lưu trước khi chuyển. Tập kỳ vọng luôn lưu riêng và script ghi dự đoán trước khi đọc expected. Không lấy các ca này làm holdout độc lập trong tương lai.

Khởi động lại backend, Reload extension 0.7.0 tại chrome://extensions và tải lại tab để nhận bản mới.
