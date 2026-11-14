# Nội dung và dự đoán từng ca

Ca tổng hợp công khai; kỳ vọng do người triển khai đặt trước khi chạy. Không phải nhãn độc lập.

## NW-01 — Tiền công bị giữ

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.897 giây.

```json
{
  "text": "Tiền công của chị đang nằm ở ngăn chờ. Chị chuyển 840 nghìn vào ví của em làm khoản đối ứng, đủ đối ứng thì em mới giải phóng tiền công."
}
```

- `inducement` / `claim` / người nói `unknown`: Tiền công của chị đang nằm ở ngăn chờ.
- `transfer_funds` / `request` / người nói `unknown`: Chị chuyển 840 nghìn vào ví của em làm khoản đối ứng
- `inducement` / `claim` / người nói `unknown`: đủ đối ứng thì em mới giải phóng tiền công.

Câu hỏi: Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền? Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?

## NW-02 — Đổi phí thành dấu xác nhận

Kỳ vọng `high` → thực tế `need_context`; HTTP 200; 9.592 giây.

```json
{
  "text": "Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về."
}
```

- `transfer_funds` / `request` / người nói `unknown`: Anh gửi 1,2 triệu sang tài khoản em trước
- `inducement` / `claim` / người nói `unknown`: thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

## NW-03 — Đòi thêm vốn qua hội thoại

Kỳ vọng `high` → thực tế `high`; HTTP 200; 6.543 giây.

```json
{
  "messages": [
    {
      "id": "a",
      "speaker": "khach",
      "text": "Tôi đã hoàn tất việc rồi, sao chưa rút được?"
    },
    {
      "id": "b",
      "speaker": "quan_ly",
      "text": "Chị cần chuyển thêm 2 triệu để bù điểm tín nhiệm."
    },
    {
      "id": "c",
      "speaker": "quan_ly",
      "text": "Có khoản bù đó thì bên em mới mở rút toàn bộ vốn và lãi cho chị."
    }
  ]
}
```

- `transfer_funds` / `request` / người nói `quan_ly`: Chị cần chuyển thêm 2 triệu để bù điểm tín nhiệm.
- `inducement` / `claim` / người nói `quan_ly`: Có khoản bù đó thì bên em mới mở rút toàn bộ vốn và lãi cho chị.

## NW-04 — Trả tiền ăn có bối cảnh

Kỳ vọng `clear` → thực tế `clear`; HTTP 200; 5.992 giây.

```json
{
  "text": "Chuyển lại mình 75 nghìn phần bún trưa nay nhé.",
  "context": "Tôi và bạn vừa ăn cùng, bạn thanh toán hộ. Tôi đã đối chiếu đúng phần ăn và tài khoản của bạn."
}
```

- `transfer_funds` / `request` / người nói `unknown`: Chuyển lại mình 75 nghìn phần bún trưa nay nhé.

## NW-05 — Mã sáu số tránh chữ OTP

Kỳ vọng `high` → thực tế `high`; HTTP 200; 6.851 giây.

```json
{
  "text": "Ngân hàng vừa gửi sáu chữ số đăng nhập về điện thoại chị. Đọc nguyên dãy đó cho tôi qua cuộc gọi để tôi hủy giao dịch đang treo; đừng tự nhập."
}
```

- `share_auth_code` / `request` / người nói `unknown`: Đọc nguyên dãy đó cho tôi qua cuộc gọi để tôi hủy giao dịch đang treo; đừng tự nhập.
- `other` / `claim` / người nói `unknown`: Ngân hàng vừa gửi sáu chữ số đăng nhập về điện thoại chị.
- `inducement` / `claim` / người nói `unknown`: để tôi hủy giao dịch đang treo; đừng tự nhập.

## NW-06 — Mật khẩu để chống khóa

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.552 giây.

```json
{
  "text": "Tài khoản mua sắm của anh sắp bị khóa. Nhắn cho tôi mật khẩu đăng nhập hiện tại, tôi mới giữ tài khoản hoạt động cho anh được."
}
```

- `inducement` / `claim` / người nói `unknown`: Tài khoản mua sắm của anh sắp bị khóa. Nhắn cho tôi mật khẩu đăng nhập hiện tại, tôi mới giữ tài khoản hoạt động cho anh được.
- `share_auth_code` / `request` / người nói `unknown`: Nhắn cho tôi mật khẩu đăng nhập hiện tại
- `other` / `unknown` / người nói `unknown`: Nhắn cho tôi mật khẩu đăng nhập hiện tại, tôi mới giữ tài khoản hoạt động cho anh được.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## NW-07 — Chuỗi khôi phục ví

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.041 giây.

```json
{
  "text": "Muốn nhận lại số dư ví, chép toàn bộ 12 từ khôi phục bí mật rồi gửi riêng cho tôi. Tôi phải có đủ 12 từ mới mở lại số dư cho bạn."
}
```

- `share_auth_code` / `request` / người nói `unknown`: chép toàn bộ 12 từ khôi phục bí mật rồi gửi riêng cho tôi
- `inducement` / `claim` / người nói `unknown`: Tôi phải có đủ 12 từ mới mở lại số dư cho bạn.

## NW-08 — Tự nhập mã trong ứng dụng

Kỳ vọng `clear` → thực tế `clear`; HTTP 200; 6.976 giây.

```json
{
  "text": "Tôi tự mở ứng dụng ngân hàng đã cài, tự nhập mã xác thực để trả hóa đơn. Tôi không đọc hoặc gửi mã cho người khác."
}
```

- `other` / `denial` / người nói `unknown`: Tôi tự mở ứng dụng ngân hàng đã cài, tự nhập mã xác thực để trả hóa đơn. Tôi không đọc hoặc gửi mã cho người khác.

## NW-09 — Điều khiển máy để mở trợ cấp

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.069 giây.

```json
{
  "text": "Bật điều khiển từ xa và cho tôi thao tác trên điện thoại của cô. Chỉ khi tôi điều khiển được máy thì hồ sơ trợ cấp mới được duyệt giải ngân."
}
```

- `inducement` / `claim` / người nói `unknown`: Chỉ khi tôi điều khiển được máy thì hồ sơ trợ cấp mới được duyệt giải ngân.
- `grant_access` / `request` / người nói `unknown`: Bật điều khiển từ xa và cho tôi thao tác trên điện thoại của cô.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? Vì sao họ cần chia sẻ màn hình hoặc quyền điều khiển, và bạn đã xác minh đầu mối hỗ trợ chưa?

## NW-10 — Thêm quản trị viên trang

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.289 giây.

```json
{
  "text": "Muốn nhận gói tài trợ cho trang, thêm tài khoản của tôi làm quản trị viên toàn quyền trước. Khi có toàn quyền tôi mới chuyển tiền tài trợ."
}
```

- `grant_access` / `request` / người nói `unknown`: thêm tài khoản của tôi làm quản trị viên toàn quyền trước
- `inducement` / `claim` / người nói `unknown`: Muốn nhận gói tài trợ cho trang
- `transfer_funds` / `unknown` / người nói `unknown`: Khi có toàn quyền tôi mới chuyển tiền tài trợ.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## NW-11 — Chia sẻ ngân hàng để hoàn phí

Kỳ vọng `high` → thực tế `high`; HTTP 200; 6.821 giây.

```json
{
  "messages": [
    {
      "id": "s1",
      "speaker": "hotro",
      "text": "Bật chia sẻ màn hình và mở phần số dư trong ứng dụng ngân hàng."
    },
    {
      "id": "s2",
      "speaker": "hotro",
      "text": "Đây là bước bắt buộc để tôi xử lý khoản hoàn phí cho anh."
    }
  ]
}
```

- `grant_access` / `request` / người nói `hotro`: Bật chia sẻ màn hình và mở phần số dư trong ứng dụng ngân hàng.
- `inducement` / `claim` / người nói `hotro`: Đây là bước bắt buộc để tôi xử lý khoản hoàn phí cho anh.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## NW-12 — Quyền thông báo lịch có bối cảnh

Kỳ vọng `clear` → thực tế `clear`; HTTP 200; 6.032 giây.

```json
{
  "text": "Cho phép ứng dụng lịch gửi thông báo để nhắc buổi học nhé.",
  "context": "Tôi tự cài ứng dụng lịch của trường từ cửa hàng chính thức. Quyền đang hỏi chỉ là thông báo nhắc lịch, không xem màn hình hoặc điều khiển."
}
```

- `grant_access` / `request` / người nói `unknown`: Cho phép ứng dụng lịch gửi thông báo để nhắc buổi học nhé.

## NW-13 — Tệp ngoài cửa hàng để nhận hỗ trợ

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.321 giây.

```json
{
  "text": "Cài tệp ho-tro.apk tôi gửi ngoài cửa hàng ứng dụng, bật quyền trợ năng cho nó. Cài xong và cấp quyền thì tôi mới mở khoản hỗ trợ cho cô."
}
```

- `install_app` / `request` / người nói `unknown`: Cài tệp ho-tro.apk tôi gửi ngoài cửa hàng ứng dụng
- `inducement` / `claim` / người nói `unknown`: Cài xong và cấp quyền thì tôi mới mở khoản hỗ trợ cho cô.
- `grant_access` / `request` / người nói `unknown`: bật quyền trợ năng cho nó.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào? Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì?

## NW-14 — Phần mềm máy tính để lấy tiền

Kỳ vọng `high` → thực tế `high`; HTTP 200; 6.730 giây.

```json
{
  "text": "Tải bộ cài exe qua đường dẫn riêng của tôi rồi tắt phần mềm bảo vệ để cài. Đây là điều kiện bắt buộc để nhận lại tiền đơn hàng bị hủy."
}
```

- `install_app` / `request` / người nói `unknown`: Tải bộ cài exe qua đường dẫn riêng của tôi rồi tắt phần mềm bảo vệ để cài.
- `inducement` / `claim` / người nói `unknown`: Đây là điều kiện bắt buộc để nhận lại tiền đơn hàng bị hủy.

Câu hỏi: Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì? Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## NW-15 — Đổi tên app thành công cụ đối soát

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.431 giây.

```json
{
  "text": "Đây chỉ là công cụ đối soát, không phải ứng dụng ngân hàng. Cài gói tôi gửi và bật quyền điều khiển thiết bị; đủ hai bước này bên tôi mới giải ngân tiền hoàn."
}
```

- `install_app` / `request` / người nói `unknown`: Cài gói tôi gửi
- `grant_access` / `request` / người nói `unknown`: bật quyền điều khiển thiết bị
- `inducement` / `claim` / người nói `unknown`: đủ hai bước này bên tôi mới giải ngân tiền hoàn.

Câu hỏi: Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì? Vì sao họ cần chia sẻ màn hình hoặc quyền điều khiển, và bạn đã xác minh đầu mối hỗ trợ chưa?

## NW-16 — Bài cảnh báo tệp APK

Kỳ vọng `clear` → thực tế `clear`; HTTP 200; 6.508 giây.

```json
{
  "text": "Bản tin an toàn: kẻ gian thường nói “cài tệp APK này để nhận trợ cấp”. Đó là lời dụ được trích để cảnh báo. Đừng cài tệp người lạ gửi hoặc cấp quyền điều khiển."
}
```

- `inducement` / `quoted_warning` / người nói `unknown`: kẻ gian thường nói “cài tệp APK này để nhận trợ cấp”.
- `install_app` / `denial` / người nói `unknown`: Đừng cài tệp người lạ gửi hoặc cấp quyền điều khiển.

## NW-17 — Nhiệm vụ nhỏ dẫn sang ứng vốn

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.854 giây.

```json
{
  "messages": [
    {
      "id": "j1",
      "speaker": "tuyendung",
      "text": "Lượt đầu bấm thích bài đăng được trả 20 nghìn, không cần vốn."
    },
    {
      "id": "j2",
      "speaker": "ungvien",
      "text": "Tôi đã nhận 20 nghìn rồi."
    },
    {
      "id": "j3",
      "speaker": "tuyendung",
      "text": "Muốn nhận thưởng 900 nghìn ở lượt kế, em phải chuyển trước 500 nghìn tiền giữ suất cho chị."
    }
  ]
}
```

- `inducement` / `claim` / người nói `tuyendung`: Lượt đầu bấm thích bài đăng được trả 20 nghìn, không cần vốn.
- `transfer_funds` / `request` / người nói `tuyendung`: Muốn nhận thưởng 900 nghìn ở lượt kế, em phải chuyển trước 500 nghìn tiền giữ suất cho chị.
- `inducement` / `claim` / người nói `tuyendung`: Muốn nhận thưởng 900 nghìn ở lượt kế, em phải chuyển trước 500 nghìn tiền giữ suất cho chị.

## NW-18 — Gây áp lực giả cơ quan

Kỳ vọng `high` → thực tế `high`; HTTP 200; 6.504 giây.

```json
{
  "text": "Tôi là cán bộ xử lý hồ sơ. Trong mười phút anh phải chuyển 8 triệu vào tài khoản tôi cung cấp để kiểm tra nguồn tiền; chuyển xong mới được gỡ phong tỏa."
}
```

- `transfer_funds` / `request` / người nói `unknown`: Trong mười phút anh phải chuyển 8 triệu vào tài khoản tôi cung cấp để kiểm tra nguồn tiền
- `inducement` / `request` / người nói `unknown`: Trong mười phút anh phải chuyển 8 triệu vào tài khoản tôi cung cấp để kiểm tra nguồn tiền; chuyển xong mới được gỡ phong tỏa.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## NW-19 — Nạp tiền giải phóng lợi nhuận

Kỳ vọng `high` → thực tế `high`; HTTP 200; 7.584 giây.

```json
{
  "text": "Anh đã thắng 30 triệu nhưng hệ thống giữ khoản lãi. Nạp thêm 3 triệu bảo lãnh vào ví riêng của tôi ngay hôm nay, tôi mới cho rút cả gốc lẫn lãi."
}
```

- `other` / `claim` / người nói `unknown`: Anh đã thắng 30 triệu nhưng hệ thống giữ khoản lãi.
- `transfer_funds` / `request` / người nói `unknown`: Nạp thêm 3 triệu bảo lãnh vào ví riêng của tôi ngay hôm nay
- `inducement` / `claim` / người nói `unknown`: tôi mới cho rút cả gốc lẫn lãi.

## NW-20 — Phần thưởng không yêu cầu tài sản

Kỳ vọng `clear` → thực tế `clear`; HTTP 200; 5.392 giây.

```json
{
  "text": "Thư viện tặng một cuốn sách cho người tham dự buổi đọc. Đến quầy nhận miễn phí, không đóng phí, không cung cấp mã hay thông tin ngân hàng."
}
```

- `other` / `claim` / người nói `unknown`: Thư viện tặng một cuốn sách cho người tham dự buổi đọc. Đến quầy nhận miễn phí, không đóng phí, không cung cấp mã hay thông tin ngân hàng.

## NW-21 — Xác nhận nhận hàng để được hoàn

Kỳ vọng `high` → thực tế `high`; HTTP 200; 6.423 giây.

```json
{
  "text": "Bưu kiện chưa giao cũng cứ bấm đã nhận hàng trên sàn trước. Sau khi anh xác nhận hoàn tất đơn thì tôi mới hoàn lại tiền cho anh qua kênh riêng."
}
```

- `other` / `request` / người nói `unknown`: Bưu kiện chưa giao cũng cứ bấm đã nhận hàng trên sàn trước.
- `inducement` / `request` / người nói `unknown`: Sau khi anh xác nhận hoàn tất đơn thì tôi mới hoàn lại tiền cho anh qua kênh riêng.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

## NW-22 — Ký quyền ví để nhận thưởng

Kỳ vọng `high` → thực tế `high`; HTTP 200; 6.890 giây.

```json
{
  "text": "Ký chấp thuận cho địa chỉ tôi gửi được chi tiêu toàn bộ token trong ví trước. Chữ ký cấp quyền đó là điều kiện để tôi chuyển phần thưởng vào ví của bạn."
}
```

- `inducement` / `claim` / người nói `unknown`: Chữ ký cấp quyền đó là điều kiện để tôi chuyển phần thưởng vào ví của bạn.
- `grant_access` / `request` / người nói `unknown`: Ký chấp thuận cho địa chỉ tôi gửi được chi tiêu toàn bộ token trong ví trước.

## NW-23 — Gửi ảnh giấy tờ và video

Kỳ vọng `high` → thực tế `high`; HTTP 200; 9.811 giây.

```json
{
  "text": "Gửi riêng cho tôi ảnh hai mặt căn cước và video quay mặt cầm căn cước. Có đủ bộ đó tôi mới duyệt suất vay ưu đãi, không gửi thì không nhận được khoản vay."
}
```

- `other` / `request` / người nói `unknown`: Gửi riêng cho tôi ảnh hai mặt căn cước và video quay mặt cầm căn cước.
- `inducement` / `request` / người nói `unknown`: Có đủ bộ đó tôi mới duyệt suất vay ưu đãi, không gửi thì không nhận được khoản vay.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## NW-24 — Nhận hàng sau khi kiểm tra

Kỳ vọng `clear` → thực tế `clear`; HTTP 200; 6.645 giây.

```json
{
  "text": "Tôi chỉ bấm đã nhận hàng sau khi nhận đúng gói và kiểm tra đủ sản phẩm. Không ai yêu cầu tôi xác nhận trước hoặc hoàn tiền ngoài sàn."
}
```

- `other` / `denial` / người nói `unknown`: Tôi chỉ bấm đã nhận hàng sau khi nhận đúng gói và kiểm tra đủ sản phẩm. Không ai yêu cầu tôi xác nhận trước hoặc hoàn tiền ngoài sàn.
