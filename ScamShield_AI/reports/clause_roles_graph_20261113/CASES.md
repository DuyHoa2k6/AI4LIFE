# Kết quả kiểm thử cụm câu và vai trò

Tám ca người dùng đã cung cấp, dùng để phát triển; không phải tập độc lập. Luồng API thật, ASGI TestClient, URL network tắt, không gọi mô hình.

| Ca | Trước | Hiện tại | Kỳ vọng | API ms |
|---|---|---|---|---:|
| commission | high | high | high | 96.361 |
| alternate_account | need_context | high | high | 35.562 |
| refund_login_code | high | high | high | 36.691 |
| phone_handover_unpaid | suspicious | suspicious | suspicious | 32.279 |
| invoice_account_change | need_context | suspicious | suspicious | 28.362 |
| overseas_work_documents | need_context | high | high | 48.612 |
| login_code_warning | clear | clear | clear | 19.795 |
| phone_payment_updated | need_context | clear | clear | 32.182 |

## Nội dung và giải thích

### commission

Khoản hoa hồng của bạn đã được ghi nhận. Tuy nhiên, số dư đang chờ mở quyền rút. Bạn cần nộp thêm tiền bảo chứng trước thì mới nhận lại cả vốn lẫn hoa hồng.

Nội dung liên kết việc chuyển thêm tiền với điều kiện nhận hoặc rút tiền.

Hành động: Tạm dừng nộp thêm và đối chiếu giao dịch qua đầu mối độc lập.

### alternate_account

Anh dùng tài khoản này vì điện thoại cũ đang hỏng. Em chuyển giúp anh tiền vào tài khoản đứng tên người khác nhé. Anh đang gấp nên đừng gọi số cũ, tối anh giải thích sau.

Người gửi yêu cầu chuyển tiền sang nơi nhận khác thỏa thuận hoặc khác danh tính tự nhận, đồng thời cản trở xác minh qua kênh đã biết. Có nguy cơ chuyển tiền sai người nhận; chưa xác minh người gửi giả mạo.

Hành động: Tạm dừng chuyển tiền; tự liên hệ đầu mối hợp đồng hoặc người quen qua kênh đã biết để đối chiếu tài khoản.

### refund_login_code

Người gửi: Bên mình đang hoàn khoản phí cho bạn. Đọc giúp mình dãy số vừa hiện trên điện thoại để hoàn tất.
Người nhận: Thông báo ghi đây là mã đăng nhập tài khoản của tôi.
Người gửi: Đúng rồi, bên mình cần dãy đó để xử lý khoản hoàn.

Dãy số được xác định trong hội thoại là mã đăng nhập, trong khi người gửi yêu cầu bạn cung cấp.

Hành động: Không đọc mã cho người khác; tự kiểm tra bằng ứng dụng chính thức.

### phone_handover_unpaid

Mình đã gửi ảnh biên lai rồi. Bạn chưa thấy tiền vào thì có thể ngân hàng cập nhật chậm. Tài xế đang đứng chờ, bạn giao điện thoại trước giúp mình nhé.

Nội dung yêu cầu giao tài sản khi người nhận tiền cho biết chưa xác nhận thanh toán. Chưa đủ căn cứ nói biên lai giả.

Hành động: Tự kiểm tra tiền thực nhận qua kênh ngân hàng quen dùng trước khi giao tài sản.

### invoice_account_change

Hóa đơn vẫn như tháng trước, nhưng tài khoản nhận tiền vừa đổi. Bạn chuyển theo thông tin mình gửi riêng trước nhé. Đầu mối trên hợp đồng đang nghỉ, ngày mai gọi xác nhận cũng được.

Người gửi yêu cầu chuyển tiền theo tài khoản thay đổi hoặc khác tên trước khi xác minh qua kênh quen dùng.

Hành động: Xác nhận tài khoản nhận tiền qua đầu mối đã biết trước khi chuyển.

### overseas_work_documents

Công việc ở nước ngoài đã có người sắp xếp. Bạn chưa cần xem hợp đồng, cứ đi gặp bên tuyển dụng trước. Đừng kể với gia đình vì họ dễ ngăn cản. Giấy tờ cá nhân giao cho người đón để họ giữ trong thời gian làm việc.

Yêu cầu đi gặp tuyển dụng khi chưa xem hợp đồng, giấu gia đình và giao giấy tờ để người đón giữ có thể làm bạn bị cô lập và mất quyền chủ động rời đi. Chưa xác minh đã xảy ra cưỡng ép hoặc mua bán người.

Hành động: Tạm dừng di chuyển và giao giấy tờ; cùng người tin cậy xác minh đơn vị tuyển dụng, hợp đồng và quyền lấy lại giấy tờ.

### login_code_warning

Nếu có ai nói “đọc mã đăng nhập để nhận hoàn tiền”, đừng làm theo. Hãy tự mở ứng dụng đang sử dụng để kiểm tra thông báo.

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

Hành động: Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

### phone_payment_updated

Người bán: Lúc sáng tôi chưa thấy tiền vào.
Người bán: Tôi vừa kiểm tra lại, khoản tiền của đơn điện thoại đã vào đủ rồi.
Người mua: Vậy bạn giao điện thoại cho tài xế giúp mình nhé.

Người bán cho biết vừa kiểm tra và đã nhận đủ tiền, cập nhật thông tin chưa nhận lúc trước; chưa ghi nhận yêu cầu đáng ngờ còn hiệu lực. Đây là lời xác nhận trong hội thoại, chưa phải kiểm chứng ngân hàng.

Hành động: Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

