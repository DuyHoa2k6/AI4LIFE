# Kiểm thử biến thể ngữ nghĩa

24 ca tổng hợp dùng để phát triển; không phải độ chính xác độc lập. Dự đoán được lưu trước khi đọc expected.

| Ca | Nội dung | Kỳ vọng | Thực tế | ms |
|---|---|---|---|---:|
| P01 | Số dư đã được niêm phong. Bạn mua thêm một gói xác thực thì bên mình mới nhả lại vốn. | high | high | 70.289 |
| P02 | Bạn mua gói mở quyền rút trước để nhận lại số dư. | high | high | 14.745 |
| P03 | Bạn nộp thêm khoản đảm bảo trước thì mới được trả lại vốn. | high | high | 16.397 |
| P04 | Bạn có thể mua thêm một gói xác thực, không ảnh hưởng việc nhận lại vốn. | clear | clear | 15.652 |
| P05 | Cảnh báo: đừng mua gói xác thực để được nhả lại vốn. | clear | clear | 11.828 |
| P06 | Bạn đừng mua thêm gói xác thực để nhận lại tiền. | clear | clear | 12.976 |
| P07 | Bạn mua gói xác thực nhé. | need_context | need_context | 15.766 |
| P08 | Bạn thanh toán tiền chiếc ghế trước để nhận hàng nhé. | clear | clear | 15.716 |
| H01 | Ngân hàng vẫn chưa báo có tiền. Anh cho người tới mang chiếc đàn đi luôn trước nhé. | suspicious | suspicious | 14.802 |
| H02 | Chưa ghi nhận thanh toán. Bạn cho tài xế mang chiếc tủ đi trước nhé. | suspicious | suspicious | 14.588 |
| H03 | Tôi chưa thấy tiền vào. Bạn để tài xế lấy chiếc tủ trước nhé. | suspicious | suspicious | 13.893 |
| H04 | Tôi đã tự kiểm tra và nhận đủ tiền. Bạn cho người tới mang chiếc đàn đi nhé. | clear | clear | 15.921 |
| H05 | Cảnh báo: chưa báo có tiền thì đừng cho người tới mang chiếc đàn đi trước. | clear | clear | 19.249 |
| H06 | Bạn đừng cho người tới mang chiếc đàn đi trước khi nhận tiền. | clear | clear | 14.265 |
| H07 | Bạn cho tài xế mang chiếc tủ đi nhé. | need_context | need_context | 10.71 |
| H08 | Đơn A chưa báo có tiền. Đơn B bạn cho người tới mang chiếc đàn đi trước nhé. | need_context | need_context | 14.269 |
| C01 | Bạn thanh toán tiền chiếc bàn trước để nhận hàng. | clear | clear | 13.736 |
| C02 | Tôi mua gói xác thực trước để nhận lại vốn. | need_context | need_context | 13.614 |
| C03 | Bạn mua gói xác thực tùy chọn, không phải điều kiện để nhận lại tiền. | clear | clear | 15.758 |
| C04 | Nếu có ai nói “mua gói xác thực thì mới nhả lại vốn”, đừng làm theo. | clear | clear | 18.546 |
| C05 | 📩 Bạn mua thêm một gói xác thực thì mới nhận lại vốn. | high | high | 18.686 |
| C06 | Bạn không cần mua gói xác thực để nhận lại tiền. | clear | clear | 13.452 |
| C07 | Bạn bổ sung khoản đảm bảo nhé. | need_context | need_context | 11.605 |
| C08 | Bạn nộp tiền trước để công ty nhận lại vốn. | need_context | need_context | 14.224 |
