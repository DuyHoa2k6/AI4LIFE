# Kết quả các phiên Gemini thật

Nhãn do người triển khai đặt trước; mọi dự đoán ghi trước khi đọc nhãn. Validation và hồi quy đã biết không phải số liệu độc lập. Không gộp hoặc chọn kết quả tốt nhất.

| Phiên | Số ca | API thành công | Khớp kỳ vọng trên toàn bộ | Lỗi | API p50/p95 |
| --- | --- | --- | --- | --- | --- |
| live | 8 | 7/8 | 6/8 | 1 | 7.085s / 10.681s |
| checked | 8 | 6/8 | 5/8 | 2 | 7.532s / 44.820s |
| focused | 2 | 1/2 | 1/2 | 1 | 8.260s / 20.922s |

## Ca NW-02

- `live/RG-01`: need_context; model gộp thiếu thông tin về tính hợp lệ giao dịch vào bất định quan hệ. Đã dùng làm validation để sửa định nghĩa trường.
- `checked/RF-01`: model nhận đúng quan hệ nhưng ghép quote support bằng `[...]`; sửa một lần vẫn giữ quote không tồn tại. Backend từ chối với PROVIDER_INCONSISTENT_OUTPUT.
- `focused/RF-01`: provider trả 503 sau retry ở lượt quan sát; chưa có kết quả để đánh giá suy luận bản cuối. Không báo là đã sửa thành công ổn định.

## Đối chứng và lỗi khác

Hai biến thể nguy hiểm mới ở checked trả high, giao dịch mua sách và bản tin cảnh báo trả clear, ca thiếu tham chiếu trả need_context. Ca hai người nói của checked lỗi 503 nên không có kết luận ở phiên này; việc bác ghép người nói đã có unit test và từng chạy clear ở phiên validation. Ca chưa biết loại quyền ở checked vẫn suspicious thay vì need_context; chưa sửa nhãn hậu kiểm để nâng tỷ lệ đúng. Bản cuối focused có một bài cảnh báo trả clear, một ca 503.

Tăng độ chặt của kiểm chứng có thể tăng lỗi được hiển thị thay vì cho qua bằng chứng sai. Không coi lỗi là clear, không bỏ lỗi khỏi mẫu số. Không có nguồn chính thống đủ duyệt trong kho; chưa đo RAG thực, browser/extension, tải đồng thời hoặc độ chính xác dữ liệu thật. Các độ trễ gồm provider và mạng; timeout ứng dụng vẫn đang tắt theo yêu cầu trước.

Chi tiết input và assessment tại [CASES.md](CASES.md), dự đoán gốc trong từng thư mục phiên. Không có căn cứ tuyên bố đạt 98% hoặc đã khắc phục hoàn toàn mọi biến thể.
