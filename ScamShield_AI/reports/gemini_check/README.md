# Kiểm thử Gemini thực tế — 08/11/2026

Cấu hình: hybrid, gemini-3.5-flash-lite, endpoint Google tương thích Chat Completions,
timeout 20 giây. Key đọc từ file riêng, không chép vào báo cáo. Không bật billing,
không thay tài khoản hay quota. Gọi API thành công không xác nhận dự án thuộc Free Tier.

Đã chạy lại 49 kiểm thử cục bộ: tất cả đạt. Đây là kiểm thử chức năng bằng provider mô phỏng,
không phải số liệu chất lượng Gemini.

| Ca tổng hợp công khai | Kết quả API thực | Nhận xét |
| --- | --- | --- |
| RC-01: chuyển phí mở hồ sơ để nhận lại tiền bị mất | 200, high | Provider trả 200; JSON hợp lệ; backend đối chiếu quote và liên kết yêu cầu với điều kiện nhận tiền |
| RC-02: lời đòi trả tiền bằng tiếng địa phương | 504, PROVIDER_TIMEOUT | Chưa có kết luận rủi ro |
| RC-03: trả nợ kèm bối cảnh xác nhận khoản vay | 504, PROVIDER_TIMEOUT | Chưa có kết luận rủi ro |

Tổng cộng thực hiện 3 lần phân tích qua adapter thật: 1 thành công, 2 timeout.
Hai lượt chạy đều dừng ở lỗi provider đầu tiên; các ca khác chưa chạy, không tính là đạt.
RC-04 (bài cảnh báo) và RC-09 (cách diễn đạt mới) đã chọn cho lượt bổ sung nhưng chưa
được gửi vì RC-03 timeout. Không chạy lại liên tục, không tự tăng timeout hay đổi model.

Dự đoán từng ca và thời gian thực: `predictions.json`, `additional/predictions.json`.
Tất cả input đều là fixture tổng hợp công khai; không dùng holdout. Dự đoán lưu trước khi
đọc expected. Một ca thành công không đủ đánh giá độ chính xác hoặc nghiệm thu toàn luồng.

Kết luận: cấu hình Gemini/key/model đã có ít nhất một lần gọi thành công. Độ trễ chưa
ổn định tại giới hạn 20 giây; cần kiểm tra mạng/provider trước khi quyết định tăng timeout
đồng bộ backend, web và extension. Dữ liệu hiện chưa phân biệt được mạng với thời gian
xử lý provider trong hai lần timeout. Chưa chứng minh tất cả ca suy luận chạy ổn định.

Chạy từ thư mục `ScamShield_AI` bên trong repo:

```powershell
python -m unittest discover -s tests -q
python reasoning_check.py --mode live --output-dir reports/gemini_check
python reasoning_check.py --mode live --output-dir reports/gemini_check/additional --case-ids RC-03 RC-04 RC-09
```

Hai lệnh cuối gọi API thực và tiêu thụ quota của dự án. Chỉ chạy khi đã kiểm tra gói/quota.
