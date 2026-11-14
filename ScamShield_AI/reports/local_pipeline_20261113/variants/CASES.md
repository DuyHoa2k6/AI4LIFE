# Novel development cases — real local API; no network URL or model

Targets authored for development; not independent quality. X cases deliberately probe broader unsupported reasoning.

| ID | Input | Expected | Before | After |
|---|---|---|---|---|
| N01 | Khoản tiền gốc vẫn nằm trong hệ thống. Bạn đóng thêm phí xác minh trước thì mới rút được số dư. | high | high | high |
| N02 | Để nhận lại tiền đã nạp, bạn bổ sung khoản bảo đảm trước nhé. | high | need_context | high |
| N03 | Bạn nộp phí kích hoạt trước. Sau đó mới nhận lại tiền gốc. | high | need_context | high |
| N04 | Chưa thấy khoản thanh toán vào tài khoản. Anh đưa chiếc đồng hồ cho người đến lấy trước nhé. | suspicious | clear | suspicious |
| N05 | Mình chưa nhận được tiền. Bạn giao bộ máy ảnh cho người giao hàng trước giúp mình. | suspicious | need_context | suspicious |
| N06 | Bạn gửi ảnh căn cước qua tin nhắn để giữ chỗ nhận hỗ trợ. | suspicious | suspicious | suspicious |
| N07 | Bạn giao chiếc đàn cho người đến lấy nhé. | need_context | need_context | need_context |
| N08 | Bạn chuyển giúp khoản này trước nhé, mục đích mình sẽ nói sau. | need_context | need_context | need_context |
| N09 | Số dư đang chờ kiểm tra. Bên mình chưa thông báo bước tiếp theo. | need_context | need_context | need_context |
| N10 | Cảnh giác: đừng nộp phí để rút tiền đang bị giữ. | clear | clear | clear |
| N11 | Chưa nhận được tiền thì đừng giao máy ảnh. | clear | clear | clear |
| N12 | Tôi đã tự kiểm tra và nhận đủ tiền. Bạn giao chiếc đàn cho người đến lấy nhé. | clear | need_context | clear |
| X01 | Hãy bật chia sẻ màn hình rồi mở ứng dụng ngân hàng để họ xem số dư. | high | suspicious | high |
| X02 | Bạn thanh toán tiền chiếc ghế trước để nhận hàng nhé. | clear | need_context | clear |
| X03 | Người gửi yêu cầu đọc dãy số để giải ngân. Màn hình của người nhận ghi đây là mã đăng nhập tài khoản. | high | high | high |
| X04 | Muốn lấy lại khoản đang bị treo, bạn bổ sung một khoản đảm bảo trước. Xong bước này bên mình mới giải phóng tiền gốc. | high | need_context | high |
