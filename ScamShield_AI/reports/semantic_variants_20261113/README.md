# Bổ sung dữ liệu và diễn giải ngữ nghĩa — 13/11/2026

Đã thêm 24 ca tổng hợp theo nhóm nghĩa, có đối chứng khác ngữ cảnh; input và
nhãn/chú giải nằm riêng trong [dataset](../../../data/v2/semantic_variants/README.md).
Các tập dữ liệu cũ và holdout không được sửa.

Runtime không đọc nhãn của các ca này, không học trọng số và không tìm câu
gần giống trong dataset. `semantic_phrases.json` chứa nhóm biểu thức ngôn ngữ;
`semantic_phrases.py` nạp config; `interaction.py` kết hợp chúng với vai trò,
phủ định, điều kiện, bên hưởng lợi và trạng thái thanh toán. `situation.py`
giữ cách giải thích mua tùy chọn khác với khoản phải nộp để lấy lại tiền.

## Kết quả thực tế

| Phép kiểm tra | Kết quả |
|---|---|
| 24 ca bổ sung, bốn mức | 24/24 khớp kỳ vọng development |
| Phân bố | high 4, suspicious 3, need_context 6, clear 11 |
| Trích dẫn của 24 ca | 63/63 khớp nguyên văn/offset |
| Bộ hồi quy cũ | 31/31 khớp mức kỳ vọng, không lỗi HTTP |
| Bộ hồi quy: trạng thái phân tích | complete 29, unsupported 2 |
| Bộ hồi quy: bằng chứng | 275/275 khớp nguyên văn |
| Kiểm thử Python | 225 tests qua |
| Lời gọi HTTP bên ngoài trong bài đo | 0 |
| Thời gian 24 ca, ASGI TestClient | p50 12,465 ms; p95 nearest-rank 18,91 ms |

[Nội dung và dự đoán từng ca](final/CASES.md), [summary](final/summary.json),
[dự đoán đầy đủ](final/predictions.json), [31 ca hồi quy](regression31_locked/CASES.md).
Hash config và code có trong summary/lock của các bài đo.

Hai lỗi M/NOVEL-ASSET trước đây hiện nhận lần lượt high/suspicious. Cải tiến
không chỉ thêm từ vào danh sách: đã kiểm tra quan hệ “mua gói → mới trả vốn”,
tránh lấy chữ “rút” trong tên gói làm hành động rút tiền, phân biệt mua tùy
chọn, ngăn lời phủ định bị coi như yêu cầu và tách bên hưởng lợi khác.

## Phạm vi cần hiểu đúng

Tất cả là **ca phát triển đã biết hoặc do cùng phiên làm việc tạo ra**. Không
tính chúng như đánh giá độc lập sau khi sửa; không suy ra độ chính xác thực tế
100% hoặc đạt 98%. Các nhóm gần nghĩa có thể chia sẻ cấu trúc; không cộng hai
bộ thành số mẫu độc lập. Lần đầu 20/24 và các dự đoán trước sửa vẫn giữ tại
`first`; `second` và `final` là những lần chạy sau.

Kiểm tra ký tự của bằng chứng không chứng minh diễn giải ngữ nghĩa hoàn toàn
đúng. Nhãn vai trò/quan hệ trong dataset mới là chú giải phát triển, chưa được
chuyên gia rà và chưa có phép chấm đầy đủ cho mọi trường. Bộ 31 vẫn còn một
required event không trích được dù mức cảnh báo khớp; xem summary của nó.

Đo mỗi ca một lượt tuần tự qua API thật trong cùng tiến trình, không phải độ
trễ website/Chrome/mạng, không đo tải đồng thời hay cold start có kiểm soát.
Chưa chạy lại Chrome E2E. Không có nguồn RAG thực trong bài này, không đo URL
redirect hoặc ảnh. Mẫu ngoài nhóm nghĩa hiện có vẫn có thể bị bỏ sót.

## Chạy lại

Từ thư mục ứng dụng `ScamShield_AI`:

```powershell
python -m unittest discover -s tests -q
python check_semantic_variants.py --output reports/semantic_variants_20261113/run_new
python evaluate_local_pipeline.py --output reports/semantic_variants_20261113/regression_new
```

Thư mục đầu ra mới chưa được tồn tại. Script gửi input và lưu dự đoán trước
khi đọc expected; không đưa nhãn vào payload API. Khởi động lại backend để nạp
config nhóm nghĩa mới. Không cần API key hoặc cài thêm công cụ.
