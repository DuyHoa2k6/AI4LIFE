# Kiểm tra nhất quán và tách thông tin thiếu — 09/11/2026

## Thay đổi

- `backend/review_consistency.py`: kiểm tra ID trùng/tham chiếu sai, cặp quan hệ sai
  vai/người nói, benign mâu thuẫn với risky/uncertain, giao OTP bị gọi benign và các
  liên kết vừa khẳng định vừa bị đánh dấu chưa rõ. Chỉ phát hiện lỗi logic; không
  chứng nhận suy luận ngữ nghĩa đúng chỉ vì các trường nhất quán.
- `schemas.py`, `review_prompt.txt`: bổ sung `uncertain_relations` theo từng cặp.
  Thiếu danh tính khác thiếu ý nghĩa hành động/quan hệ. Quan hệ khác còn chưa rõ
  không vô hiệu quan hệ đủ bằng chứng trên cùng hành động.
- `two_pass.py`: yêu cầu sửa đúng một lần nếu phát hiện mâu thuẫn, với đầu vào gốc
  và hai nhánh giữ nguyên. Không tự sửa bằng cách xóa bất định hoặc chọn mức cao.
  Nếu vẫn mâu thuẫn trả HTTP 502 `PROVIDER_INCONSISTENT_OUTPUT`.
- `hybrid.py`: trong two_pass cho phép other → action cụ thể trên cùng toàn bộ
  khoảng bằng chứng và cùng người nói; warning/denial phải bao phủ bằng chứng gốc.
  Không cho request cụ thể biến thành claim chung hoặc biến mất im lặng.
- `main.py`, extension: thông báo chưa kiểm tra được nếu model không giải quyết
  được mâu thuẫn. Thông báo xử lý nói rõ khả năng có một lần gọi sửa bổ sung.
- `mixed_check.py`: khóa hash module mới và tính tối đa ba lời gọi model/ca trước
  retry, thay vì hai. Không đưa nhãn hoặc dữ liệu holdout vào pipeline.

Không thay nguồn candidate thành approved. Chưa có nguồn chính thống đủ duyệt;
không chứng nhận verified_match. Giữ cấu hình tạm bỏ response timeout theo yêu cầu
trước: lời gọi có thể chờ lâu; giới hạn truy xuất và số retry vẫn hữu hạn.

## Kiểm thử xác định

`python -m unittest discover -s tests -q`: **100 kiểm thử đạt**, gồm 11 ca mới:

1. Liên kết + relation uncertainty được sửa thành high kèm câu hỏi danh tính.
2. Lần sửa có thể bỏ link, giữ quan hệ chưa rõ và trả need_context.
3. Mâu thuẫn lặp lại dừng sau một lần sửa, không giả kết quả phân tích.
4. Bất định theo một cặp không vô hiệu cặp khác có bằng chứng.
5. Cùng cặp không được vừa rõ vừa chưa rõ.
6. Một hành vi không được vừa benign vừa tham gia liên kết rủi ro.
7. Nhờ chuyển tiền trống bối cảnh vẫn hỏi thêm.
8. Đổi nhãn other → transfer_funds trên cùng câu có bối cảnh trả nợ không xung đột giả.
9. Lời cảnh báo được phân loại lại đúng vai, không thành request.
10. Giao OTP không được biến mất vào claim chung.
11. Chưa biết loại quyền thực sự thì không tự nâng cảnh báo.

Các kiểm thử chính sách cũ được cập nhật để model tự mâu thuẫn nhận lỗi, thay vì
need_context. Đây là dữ liệu mô phỏng đầu ra model, không phải 100 ca Gemini live
hay tỷ lệ chính xác thực tế. `node tests/worker_security.mjs`: 10 kiểm thử đạt.

## Hồi quy Gemini

Lệnh từ thư mục `ScamShield_AI`:

```powershell
python mixed_check.py --mode two_pass --output reports/consistency_v3/live_network --fixtures-dir fixtures/six_groups_30 --case-ids SG-31 SG-61 SG-13 SG-14 SG-15 SG-21 --pause 3 --service-error-limit 6
```

Sáu ca công khai đã biết: hai ca high bị hạ mức trước đây, hai ca normal xung đột
taxonomy, một ca thiếu bối cảnh, một ca OTP. Đây là hồi quy được chọn theo lỗi,
không phải tập độc lập đo chất lượng. Bộ 30 ca gốc và báo cáo cũ giữ nguyên.

`live_regression/` lưu lần thử mạng trong sandbox; `live_network/` lưu lần thực sự
có kết nối tới Gemini. Không gộp hai phiên hoặc chọn lại dự đoán tốt nhất từng ca.
Kết quả chi tiết được lưu sau khi hoàn tất cả sáu dự đoán rồi mới đọc expected.

### Kết quả phiên có mạng

| Ca | Nội dung | Kỳ vọng | Thực tế | API |
| --- | --- | --- | --- | --- |
| SG-21 | Yêu cầu đọc OTP đăng nhập | high | high | 200 |
| SG-31 | Điều khiển từ xa/mở ngân hàng để hoàn phí | high | high | 200 |
| SG-61 | Xác nhận nhận hàng chưa tới để hoàn tiền | high | high | 200 |
| SG-13 | Trả khoản vay có bối cảnh đã đối chiếu | clear | clear | 200 |
| SG-14 | Bài cảnh báo về phí hoàn cọc | clear | clear | 200 |
| SG-15 | Nhờ chuyển lại tiền chưa rõ khoản gì | need_context | need_context | 200 |

Sáu ca khớp mức kỳ vọng, 0 lỗi; 11/11 quote khớp, 0 sai tham chiếu người nói.
p50 **6,281 giây**, p95 **6,632 giây** trên cả sáu API; tổng batch **55,770 giây**
gồm khoảng nghỉ 3 giây. 12 HTTP request tới provider, 12 phản hồi; mọi ca đều
`consistency_repairs=0`, tức prompt mới đã trả nhất quán ngay ở lượt rà ban đầu.
Nhánh sửa một lần được kiểm tra bằng model giả lập; chưa quan sát nhánh đó xảy ra
trên sáu lời gọi live này. Không khẳng định cải thiện là do duy nhất một thay đổi
hay đảm bảo cùng kết quả nếu gọi model lại.

Rà thủ công các quote/vai cuối: OTP là request; điều khiển ngân hàng và xác nhận
nhận hàng trước có request + điều kiện hoàn tiền; ca vay có request nhưng bối cảnh
liên quan; bài cảnh báo có quoted_warning/denial; khoản chuyển không rõ vẫn hỏi thêm.
Các ca high vẫn có câu hỏi danh tính. Câu hỏi payment_purpose trong SG-61 còn chung
chung đối với hành vi xác nhận hàng; chưa đo đầy đủ tính hữu ích của tám answers.
Người triển khai tự rà, không phải hai người gán nhãn độc lập.

Không chạy lại cả 30 ca, không lấy 6/6 suy ra độ chính xác 100% hoặc đạt mục tiêu
98% cho toàn hệ thống. Không có nguồn chính thống đủ duyệt trong kho, không đo
chất lượng RAG thực hoặc độ trễ website/extension trong phiên này.

Xem `live_network/summary.json`, `cases.json`, `predictions.json`, `lock.json` để
đối chiếu dự đoán, chi phí thời gian và cấu hình. Không bật lại timeout sau khi đo.
