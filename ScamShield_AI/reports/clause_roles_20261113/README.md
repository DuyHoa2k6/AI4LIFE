# Kiểm thử vai trò và hành động chủ chốt — 13/11/2026

Thay đổi dùng Python cục bộ, không thêm mô hình hoặc công cụ bên ngoài.
Các câu dưới là ca phát triển đã biết, không phải holdout hoặc độ chính xác
trên người dùng thật. Nhãn kỳ vọng do dự án đặt, chưa có rà độc lập chuyên gia.

- Tám ca người dùng: từ 4/8 khớp kỳ vọng ở dự đoán trước lên 8/8 sau sửa.
- Lưu đầu ra thực từ `/api/analyze` và `/api/analyze-local` tại `predictions.json`.
- [Nội dung, mức cảnh báo và giải thích từng ca](CASES.md).
- 14 kiểm thử mới cho phân vai, nguồn, scope, cập nhật thanh toán, Unicode,
  phủ định, giả định, lời cảnh báo và quyền lấy lại giấy tờ.
- Toàn bộ 220 kiểm thử Python qua sau lần sửa cuối.
- Bộ 31 ca hồi quy vẫn 29/31 khớp kỳ vọng, HTTP lỗi 0. Không chỉnh theo hai ca
  sai này. Hai ca M và NOVEL-ASSET vẫn ngoài khả năng nhận diện hiện tại.
- 271/271 đoạn trích của bộ 31 khớp nguyên văn; đây là kiểm tra trích dẫn,
  không chứng minh tất cả suy luận đúng ngữ nghĩa.
- Không gọi transport HTTP bên ngoài trong bài tám ca. Không có URL trong các
  đầu vào này; chưa đánh giá chất lượng nguồn RAG hoặc redirect thực tế.

Thời gian lần chạy tám ca được lưu: p50 27,396 ms, p95 nearest-rank 67,399 ms,
gồm lần gọi đầu tiên. Đo ASGI TestClient tuần tự, một lượt/ca; chưa đo giao diện,
extension, tải đồng thời hay cold start có kiểm soát. `summary.json` là số liệu
của lần chạy gần nhất nếu chạy lại script, không so trực tiếp với độ trễ UI.

## Các thay đổi quyết định đã kiểm chứng

| Ca | Trước | Sau |
|---|---|---|
| Đổi tài khoản, chuyển vào tên người khác và đừng gọi số cũ | need_context | suspicious |
| Hóa đơn đổi tài khoản, chuyển trước rồi ngày mai xác minh | need_context | suspicious |
| Đi tuyển dụng trước hợp đồng, giấu gia đình, bên đón giữ giấy tờ | need_context | high |
| Cùng người bán cập nhật đã kiểm tra và nhận đủ tiền | need_context | clear |

Các ca nộp bảo chứng và giao mã đăng nhập vẫn high, giao điện thoại trước khi
nhận tiền vẫn suspicious, bài cảnh báo trích lời dụ vẫn clear.

## Giới hạn

Đây là bổ sung luật có cấu trúc, chưa phải hiểu ngôn ngữ tổng quát. Một vai trò
trong câu không phải danh tính ngoài đời. Cập nhật thanh toán mới hiện bị giới
hạn ở các mẫu tường minh cùng nguồn trong một text. Không suy mua bán người
hoặc thiệt hại đã xảy ra. Không nâng mức chỉ vì đi nước ngoài hay thiếu danh tính.
Chưa chạy lại Chrome E2E trong thay đổi này; các thử nghiệm đi qua API thật
nhưng không bao gồm việc chọn vùng hay render trình duyệt.

## Lệnh chạy

Từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests -q
python check_clause_roles.py
python evaluate_local_pipeline.py --output reports/clause_roles_20261113/regression31_new
```

Xem [thiết kế và cách chạy hệ thống](../../CLAUSE_ROLES.md).
