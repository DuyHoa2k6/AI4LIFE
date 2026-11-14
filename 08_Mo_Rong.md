# Quyền riêng tư và phần mở rộng

Cập nhật theo yêu cầu triển khai trực tiếp ngày 10/11/2026: đã thêm OCR local có
xem trước và nhánh URL offline cùng nội dung. Không coi cổng chất lượng/P0/RAG là
đã đạt. Quy định “không mở thêm OCR/URL” trong mô tả MVP cũ dưới đây được thay thế
cho hai phạm vi này; vẫn không mở trang đích, media/video hoặc tự duyệt nguồn gov.
Chi tiết giới hạn, consent và kiểm thử tại README_OCR.md, README_URL.md trong ứng dụng.

## Quyền riêng tư của MVP

Two_pass gửi nội dung/bối cảnh hai lượt tới provider đã cấu hình, xen giữa là truy xuất cục bộ. Không tải URL người dùng, không tự duyệt tài liệu, không truy xuất dev/validation/holdout. Nội dung và tài liệu là dữ liệu, không phải chỉ thị thực thi. Client vẫn giữ cơ chế vùng/phiên/stale response và thông báo nơi xử lý trước khi bật. Không mở thêm OCR/media/URL theo luồng mới, không lưu hội thoại thật/key vào báo cáo thử tổng hợp.

Người dùng xem trước đoạn được gửi và tự che dữ liệu nhạy cảm. Nếu dùng nhà cung cấp bên ngoài, nói rõ nội dung sẽ được xử lý ở đâu trước thao tác gửi. Giữ khóa ở backend, giới hạn origin và quyền extension, dùng HTTPS khi chạy ngoài máy cá nhân. Không lưu hội thoại thô mặc định. Kiểm tra log lỗi và log đo hiệu năng để tránh lộ nội dung. Áp dụng giới hạn kích thước, timeout và hiển thị trích dẫn dưới dạng văn bản.

## Phần mở rộng và điều kiện triển khai

| Mô-đun | Phương án | Điều kiện nghiệm thu |
| --- | --- | --- |
| OCR ảnh chat | Dùng PaddleOCR hoặc công cụ OCR tiếng Việt đã đo trên mẫu của nhóm. Giữ thứ tự vùng chữ, cho sửa bản nhận dạng rồi gọi API phân tích. | Có tập ảnh chữ nhỏ, tiếng Việt có dấu và ảnh thiếu ngữ cảnh. Đo lỗi chữ và tác động lên bằng chứng. |
| URL và form | Phân tích cấu trúc URL và miền đăng ký trước. Form chỉ đọc nhãn, kiểu trường và đích gửi nếu xác định được. | Không đọc giá trị nhập. Chặn danh sách đã xác minh theo phạm vi chính xác. Nếu mở rộng sang fetch URL, thiết kế chống SSRF và kiểm tra mọi chuyển hướng. |
| Quét mạng xã hội | Thử theo từng nền tảng, chỉ đọc vùng hiển thị theo quyền người dùng cấp. Giữ đối tượng bài viết và bình luận riêng. | Có fallback bôi đen khi cấu trúc trang thay đổi. Kiểm thử bài bình thường có bình luận đáng ngờ. |
| Audio và video | Tách audio bằng FFmpeg, chuyển lời nói thành chữ và lấy khung hình OCR. Giữ mốc thời gian. | Báo rõ vùng được phân tích và vùng chất lượng thấp. Đo thời gian, RAM và độ chính xác trích xuất. |
| Deepfake và giả giọng | Mô-đun nghiên cứu riêng với dữ liệu có quyền dùng, test dữ liệu nén và trường hợp chưa gặp. | Đánh giá riêng dấu hiệu media và rủi ro hành vi. Có trạng thái chất lượng không đủ để đánh giá. |
| Cộng đồng và tri thức | Báo cáo riêng tư, chờ duyệt, đối chiếu nguồn, biên tập và phiên bản hóa trước khi công bố. | Báo cáo chưa duyệt không xuất hiện trong kho truy xuất hoặc danh sách chặn. Có thu hồi và lịch sử quyết định. |

Khi kho tri thức lớn hơn, có thể thử truy xuất từ khóa rồi đối chiếu với embedding tiếng Việt trên tập có câu hỏi chuẩn. RAG dùng các đoạn đã duyệt để giải thích nguồn tương tự. Kết quả truy xuất không quyết định danh tính hay xác minh trường hợp. Theo dõi lỗi theo thời gian và chỉ đổi quy tắc, dữ liệu hoặc mô hình sau khi đánh giá hồi quy.
