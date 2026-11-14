# Ý tưởng tổng thể dự án ScamShield AI

Luồng hiện hành theo yêu cầu mới (08/11/2026): Gemini quan sát trước → backend đối chiếu bằng chứng → hai nhánh kho tình huống/quy tắc và nguồn chính thống đã duyệt chạy song song → Gemini rà lại toàn bộ văn bản → backend quyết định cảnh báo. Kho tình huống có ví dụ tổng hợp và đối chứng bình thường, tách dữ liệu đánh giá. Không nguồn không nghĩa an toàn; hai hit không phải hai xác nhận độc lập. Xem [thiết kế và giới hạn](ScamShield_AI/TWO_PASS.md). Chế độ two_pass là thử nghiệm; mock/live/hybrid cũ giữ cho đối chứng. Nguồn candidate vẫn ngoài chỉ mục, chưa nghiệm thu P0/RAG.

## Bổ sung mock theo hành vi — 08/11/2026

Mock là bộ quy tắc xác định phục vụ phát triển, hồi quy và demo. Quy tắc có ID/phiên bản, tách câu/đoạn, phân vai và liên kết bằng chứng; không học tự động từ dataset và không thay thế AI live. Baseline từ khóa, mock hành vi và live là ba cấu hình khác nhau. Tăng độ phủ mock không chứng minh năng lực hiểu tình huống mới hay hoàn thành P0 live. Dataset đánh giá không phải kho truy xuất runtime.

ScamShield AI hỗ trợ người dùng phát hiện yêu cầu đáng ngờ ngay khi đọc bài viết, bình luận hoặc tin nhắn. Hệ thống xác định người gửi đang muốn người dùng thực hiện hành động gì, chỉ ra bằng chứng trong nội dung và đề xuất một cách xác minh trước khi chuyển tiền, chia sẻ thông tin hoặc cấp quyền truy cập.

## 1 Bài toán và đối tượng sử dụng

Một yêu cầu đáng ngờ có thể xuất hiện dưới bài viết hợp lệ, nằm ở cuối cuộc hội thoại hoặc dẫn tới website giả mạo. Người dùng thường thấy từng mẩu thông tin và cần biết đâu là dấu hiệu đáng chú ý. ScamShield AI nối các chi tiết có liên quan trong đúng phạm vi được cung cấp, phân biệt lời người gửi tự nhận, hành động thực sự được yêu cầu và suy luận của hệ thống.

Đối tượng chính là người dùng mạng xã hội, người mua bán trực tuyến, người tìm việc và người nhận tin nhắn đáng ngờ. Người kiểm duyệt phụ trách đánh giá báo cáo cộng đồng, kiểm tra nguồn và cập nhật kho tri thức ở giai đoạn mở rộng.

## 2 Hai kênh tiếp cận

| Kênh | Vai trò | Đầu vào |
| --- | --- | --- |
| Extension | Tự kiểm tra nội dung trong vùng đã bật quét trên tab hiện tại | Bài viết, bình luận và nội dung chữ đang hiển thị trong vùng |
| Website | Kiểm tra nội dung người dùng chủ động đưa vào từ Zalo, SMS, ứng dụng desktop hoặc nguồn khác | Văn bản và chuỗi tin nhắn trong MVP. Ảnh, URL, audio và video được thêm theo giai đoạn. |

Hai kênh dùng chung bộ phân tích và cùng định dạng kết quả. Website nhận nội dung do người dùng cung cấp. Extension lấy nội dung trong phạm vi được cấp trên trình duyệt.

## 3 Tự quét vùng người dùng chỉ định

Người dùng mở extension, bấm **Chọn vùng quét**, di chuột để viền chỉ ra khối đang được chọn rồi bấm vào khối cần theo dõi. Ví dụ, họ chọn phần bình luận của một bài viết, một bài đăng hoặc một cột nội dung. Vùng là **một khối giao diện** có ranh giới trực quan, được xác định bằng phần tử DOM. Phương án này giúp MVP bắt đầu trên một trang thử nghiệm có DOM ổn định, rồi mở rộng dần theo nền tảng.

Sau khi chọn, extension làm nổi viền vùng, hiển thị phạm vi và nơi xử lý dữ liệu. Khi người dùng bấm **Bật quét vùng này**, extension tự lấy nội dung chữ đang hiển thị trong vùng và gửi các mục cần phân tích. Khi người dùng cuộn trong vùng hoặc nội dung mới tải vào vùng, extension tự kiểm tra phần mới. Việc bật quét là thao tác xác nhận cho cả phiên, vì vậy người dùng không cần chọn chữ hoặc xác nhận từng bình luận. Họ có thể **Tạm dừng**, **Tiếp tục**, **Đổi vùng** hoặc **Dừng quét** từ giao diện extension.

Phiên quét gắn với tab, tài liệu trang và vùng đã chọn. Khi đổi trang hoặc vùng bị gỡ khỏi trang, extension dừng theo dõi và yêu cầu chọn lại. Mỗi mục có mã riêng để cảnh báo bình luận không gắn nhầm vào bài viết. Nếu giao diện cập nhật nội dung của một mục đang hiển thị, extension đánh giá lại phiên bản mới và bỏ qua phản hồi từ phiên bản cũ. Giới hạn tốc độ gửi, khử trùng lặp và chỉ báo trạng thái giúp người dùng thấy phần đã kiểm tra, đang chờ hoặc chưa kiểm tra được.

MVP xử lý văn bản hiển thị trong DOM của tài liệu chính. Đọc chữ trong ảnh, phát lại video, khung nhúng khác nguồn và bộ đọc riêng cho từng mạng xã hội là các hạng mục mở rộng. Giới hạn quyền và quản lý phiên được mô tả tại [Luồng triển khai](03_Luong.md).

## 4 Bộ phân tích hành vi dùng chung

Hệ thống tự trả lời tám câu hỏi về lời tuyên bố, danh tính tự nhận, hành động được yêu cầu, cách thuyết phục, tài sản hoặc quyền có nguy cơ, dấu hiệu giả mạo, chuỗi bất thường và độ đủ của bằng chứng. Người dùng có thể đặt câu hỏi riêng, chẳng hạn “Vì sao họ bảo tôi bật chia sẻ màn hình?”. Hệ thống chỉ hỏi thêm nếu câu trả lời có thể đổi mức cảnh báo hoặc hướng xác minh.

Bộ phân tích kết hợp bốn góc nhìn từ sườn Word:

| Góc nhìn | Trách nhiệm |
| --- | --- |
| Ngữ nghĩa | Hiểu hành động, lời hứa, yêu cầu, người nói và ngữ cảnh trích dẫn |
| Kỹ thuật | Kiểm tra cấu trúc liên kết, tên miền, form hoặc tệp khi có mô-đun tương ứng |
| Bất thường | Nối các dấu hiệu như đổi điều kiện, tăng số tiền, gây áp lực hoặc chuyển kênh |
| Tri thức | Tìm kịch bản tương tự trong kho đã duyệt và nêu nguồn khi phù hợp |

Backend kiểm tra trích dẫn với nội dung gốc trước khi dùng chúng để đánh giá. Khi gặp thủ đoạn mới, hệ thống vẫn mô tả hành vi và nêu rủi ro. Trường tên thủ đoạn có thể để trống. Ví dụ, yêu cầu bật chia sẻ màn hình rồi mở ứng dụng ngân hàng để nhận hoàn cọc có thể được cảnh báo dựa trên hai hành động quan sát được.

## 5 Cảnh báo và cách hiển thị

| Trạng thái | Ý nghĩa đối với người dùng |
| --- | --- |
| Chưa ghi nhận dấu hiệu đáng ngờ | Phần nội dung đã kiểm tra chưa cho thấy dấu hiệu đủ rõ |
| Cần xác minh thêm | Một dữ kiện quan trọng còn thiếu, hệ thống nêu câu hỏi cụ thể |
| Có dấu hiệu đáng ngờ | Có bằng chứng về một hành vi cần thận trọng |
| Rủi ro cao | Có yêu cầu có thể gây hại và bối cảnh dẫn dụ đủ mạnh |
| Khớp cảnh báo đã xác minh | Đối tượng khớp bản ghi đang hiệu lực có nguồn và phạm vi cụ thể |

Cảnh báo hiển thị trên đúng mục được phân tích, gồm câu gốc, lý do và bước tiếp theo. Ví dụ, người dùng thấy bình luận đề nghị ứng tiền để mở nhiệm vụ, kèm gợi ý kiểm tra nhà tuyển dụng qua kênh độc lập. Mất kết nối hoặc phân tích lỗi hiển thị **Chưa kiểm tra được**. Mức khớp cảnh báo đã xác minh chỉ khả dụng khi có nguồn đối chiếu thật.

## 6 Phạm vi toàn dự án

- **URL và form.** Kiểm tra tên miền, liên kết chuyển hướng và cấu trúc form. Cảnh báo khi dấu hiệu kỹ thuật kết hợp yêu cầu như nhập OTP hoặc mật khẩu. Chỉ đọc nhãn, kiểu trường và đích gửi có thể quan sát, bảo vệ giá trị người dùng nhập.
- **Ảnh chụp và nội dung ngoài trình duyệt.** Cho xem trước và che dữ liệu, trích chữ bằng OCR, cho sửa kết quả rồi chạy cùng bộ phân tích.
- **Audio và video.** Tách lời nói, lấy mẫu khung hình và giữ mốc thời gian. Phát hiện giả giọng hoặc chỉnh sửa khuôn mặt là nhánh nghiên cứu riêng, có chỉ số và tập kiểm tra riêng.
- **Kho tri thức và cộng đồng.** Tách kịch bản đã duyệt, mẫu dùng để đánh giá và báo cáo đang chờ. Thành viên gửi tình huống, người kiểm duyệt xác minh và công bố nội dung đã biên tập. Kết quả tương đồng chỉ dùng để tham khảo. Cập nhật mô hình hoặc quy tắc cần kiểm thử và lưu phiên bản.
- **Dữ liệu và đánh giá.** Mẫu có thứ tự tin nhắn, đoạn bằng chứng và nhãn kỳ vọng. Tách tình huống theo họ để kiểm tra khả năng áp dụng sang ca mới. Đo độ đúng của hành vi, bằng chứng, mức rủi ro và tốc độ hiển thị cảnh báo.

## 7 Phạm vi bàn giao trong ba tuần

**P0** gồm API phân tích tiếng Việt, web nhập nội dung, extension chọn một vùng và tự quét trên tab hiện tại, mô hình live và mock, kiểm chứng trích dẫn, cảnh báo có giải thích và báo cáo đánh giá. Tuần một kiểm chứng bộ phân tích. Tuần hai nối web và quét vùng tự động. Tuần ba đo chất lượng, độ trễ và hoàn thiện demo.

**P1** ưu tiên độ ổn định của quét vùng. Khi P0 đã đạt, chọn thêm OCR ảnh chat hoặc kiểm tra cấu trúc URL. **P2** mở rộng bộ đọc theo từng mạng xã hội, kiểm tra form nâng cao, media, phát hiện deepfake và quản trị cộng đồng.

Nghiệm thu bản đầu bằng một bài viết hợp lệ có bình luận đáng ngờ trong vùng đã bật và một bình luận khác ngoài vùng. Kiểm tra extension nhận ra đúng mục, tự phân tích mục mới, bỏ qua mục ngoài vùng, không gửi lại nội dung không đổi và dừng gửi sau khi tắt. Kết quả phân tích cần có bằng chứng và cùng hợp đồng với website.
