# 30 ca cụ thể và kết quả thực

Ca tổng hợp công khai; kỳ vọng do người triển khai viết. Phân loại đúng chưa chứng minh đúng đầy đủ ngữ nghĩa tám answers.

| ID | Nhóm | Ca | Kỳ vọng | Thực tế | API (s) | Đạt |
| --- | --- | --- | --- | --- | ---: | --- |
| SG-11 | Chuyển tiền | Phí xác nhận để lấy lại cọc | high | high | 16.82 | Có |
| SG-21 | Giao mã/mật khẩu | Đòi OTP để chống khóa tài khoản | high | high | 12.98 | Có |
| SG-31 | Cấp quyền | Điều khiển để nhận hoàn phí | high | need_context | 10.30 | Chưa |
| SG-41 | Cài ứng dụng | APK trợ cấp kèm cấp quyền | high | high | 11.21 | Có |
| SG-51 | Lời dụ/điều kiện | Làm thử rồi phải ứng vốn | high | error | 13.15 | Chưa |
| SG-61 | Hành vi khác | Xác nhận hàng chưa tới để được hoàn tiền | high | need_context | 13.81 | Chưa |
| SG-12 | Chuyển tiền | Đệm số dư thay cách nói nạp tiền | high | error | 31.85 | Chưa |
| SG-22 | Giao mã/mật khẩu | Chuỗi sáu số trong SMS | high | high | 22.05 | Có |
| SG-32 | Cấp quyền | Quyền quản trị trang không rõ mục đích | suspicious | error | 18.20 | Chưa |
| SG-42 | Cài ứng dụng | Cài APK ngoài kho chưa rõ lý do | suspicious | suspicious | 15.62 | Có |
| SG-52 | Lời dụ/điều kiện | Phí giữ suất để nhận tài trợ | high | high | 6.85 | Có |
| SG-62 | Hành vi khác | Tắt cảnh báo ví và ký chấp thuận | suspicious | error | 23.67 | Chưa |
| SG-13 | Chuyển tiền | Trả khoản vay đã đối chiếu | clear | need_context | 25.11 | Chưa |
| SG-23 | Giao mã/mật khẩu | Tự nhập mã trên máy mình | clear | clear | 31.41 | Có |
| SG-33 | Cấp quyền | Quyền thông báo hợp lệ | clear | clear | 21.89 | Có |
| SG-43 | Cài ứng dụng | Cập nhật ứng dụng đã xác nhận | clear | clear | 12.68 | Có |
| SG-53 | Lời dụ/điều kiện | Khuyến mại không đòi tài sản | clear | clear | 17.48 | Có |
| SG-63 | Hành vi khác | Xác nhận hàng đã kiểm tra đủ | clear | clear | 12.67 | Có |
| SG-14 | Chuyển tiền | Bài cảnh báo chứa chuyển phí | clear | need_context | 7.19 | Chưa |
| SG-24 | Giao mã/mật khẩu | Tập huấn trích câu dụ lấy mã | clear | clear | 6.15 | Có |
| SG-34 | Cấp quyền | Cảnh báo không chia sẻ màn hình | clear | clear | 5.96 | Có |
| SG-44 | Cài ứng dụng | Bài cảnh báo cài tệp | clear | error | 16.17 | Chưa |
| SG-54 | Lời dụ/điều kiện | Giảng giải lời hứa lợi nhuận | clear | clear | 5.44 | Có |
| SG-64 | Hành vi khác | Cảnh báo bảo vệ quyền khiếu nại | clear | clear | 13.75 | Có |
| SG-15 | Chuyển tiền | Nhắc chuyển tiền chưa rõ khoản gì | need_context | need_context | 14.29 | Có |
| SG-25 | Giao mã/mật khẩu | Chưa biết mã được yêu cầu là mã gì | need_context | need_context | 13.35 | Có |
| SG-35 | Cấp quyền | Chưa biết loại quyền | need_context | suspicious | 6.64 | Chưa |
| SG-45 | Cài ứng dụng | Tệp mới tải nhưng chưa biết loại | need_context | need_context | 16.09 | Có |
| SG-55 | Lời dụ/điều kiện | Hứa tiền nhưng chưa rõ điều kiện | need_context | need_context | 5.57 | Có |
| SG-65 | Hành vi khác | Yêu cầu xác nhận chưa rõ tác động | need_context | need_context | 18.39 | Có |

## SG-11 — Phí xác nhận để lấy lại cọc

Đầu vào:
```json
{
  "text": "Muốn nhận lại 6 triệu tiền cọc, bạn chuyển trước 650 nghìn phí xác nhận vào ví cá nhân của tôi. Chỉ khi có phí này tôi mới trả khoản cọc cũ."
}
```

Kỳ vọng: `high`. Thực tế: `high`, HTTP 200, 16.82 giây. Attempt provider: 2.
- `transfer_funds` / `request` / unknown: bạn chuyển trước 650 nghìn phí xác nhận vào ví cá nhân của tôi.
- `inducement` / `claim` / unknown: Muốn nhận lại 6 triệu tiền cọc

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? | Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

Điểm rà: Phải trả thêm là điều kiện hoàn cọc; chưa xác minh danh tính không phủ nhận quan hệ đã nêu.

## SG-21 — Đòi OTP để chống khóa tài khoản

Đầu vào:
```json
{
  "text": "Tôi là hỗ trợ ngân hàng. Đọc mã OTP đăng nhập cho tôi để chống khóa tài khoản ngay."
}
```

Kỳ vọng: `high`. Thực tế: `high`, HTTP 200, 12.98 giây. Attempt provider: 2.
- `share_auth_code` / `request` / unknown: Đọc mã OTP đăng nhập cho tôi
- `other` / `claim` / unknown: Tôi là hỗ trợ ngân hàng.
- `inducement` / `claim` / unknown: để chống khóa tài khoản ngay.

Câu hỏi: Thao tác được yêu cầu qua ứng dụng chính thức hay đường dẫn/kênh do người gửi cung cấp? | Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Điểm rà: Yêu cầu giao mã trực tiếp; tự xưng hỗ trợ không xác minh danh tính.

## SG-31 — Điều khiển để nhận hoàn phí

Đầu vào:
```json
{
  "text": "Bật quyền điều khiển từ xa cho tôi rồi mở ứng dụng ngân hàng. Đây là điều kiện để tôi giải ngân khoản hoàn phí cho bạn."
}
```

Kỳ vọng: `high`. Thực tế: `need_context`, HTTP 200, 10.30 giây. Attempt provider: 2.
- `grant_access` / `request` / unknown: Bật quyền điều khiển từ xa cho tôi
- `other` / `request` / unknown: mở ứng dụng ngân hàng
- `inducement` / `claim` / unknown: Đây là điều kiện để tôi giải ngân khoản hoàn phí cho bạn.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? | Vì sao họ cần chia sẻ màn hình hoặc quyền điều khiển, và bạn đã xác minh đầu mối hỗ trợ chưa?

## SG-41 — APK trợ cấp kèm cấp quyền

Đầu vào:
```json
{
  "text": "Cài TroCapMoi.apk tôi gửi và bật quyền điều khiển để được nhận khoản trợ cấp. Không cài thì không được giải ngân."
}
```

Kỳ vọng: `high`. Thực tế: `high`, HTTP 200, 11.21 giây. Attempt provider: 2.
- `install_app` / `request` / unknown: Cài TroCapMoi.apk tôi gửi
- `grant_access` / `request` / unknown: bật quyền điều khiển
- `inducement` / `request` / unknown: Không cài thì không được giải ngân.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào? | Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì?

## SG-51 — Làm thử rồi phải ứng vốn

Đầu vào:
```json
{
  "messages": [
    {
      "id": "d1",
      "speaker": "tuyển dụng",
      "text": "Nhiệm vụ đầu không mất phí, bạn được thưởng 40 nghìn."
    },
    {
      "id": "d2",
      "speaker": "tôi",
      "text": "Tôi đã làm xong việc đầu."
    },
    {
      "id": "d3",
      "speaker": "tuyển dụng",
      "text": "Bây giờ ứng trước 800 nghìn vào ví nhóm để mở nhiệm vụ cuối, xong sẽ được rút vốn cùng hoa hồng."
    }
  ]
}
```

Kỳ vọng: `high`. Thực tế: `error`, HTTP 503, 13.15 giây. Attempt provider: 2.
Lỗi: PROVIDER_UNAVAILABLE; bước: observation

Điểm rà: Nối đúng chuỗi người tuyển dụng, không ghép lời người nhận.

## SG-61 — Xác nhận hàng chưa tới để được hoàn tiền

Đầu vào:
```json
{
  "text": "Dù hàng chưa tới, bạn bấm xác nhận đã nhận đủ hàng trên sàn trước đi. Chỉ sau khi bạn xác nhận, tôi mới hoàn lại tiền cho bạn."
}
```

Kỳ vọng: `high`. Thực tế: `need_context`, HTTP 200, 13.81 giây. Attempt provider: 2.
- `other` / `request` / unknown: Dù hàng chưa tới, bạn bấm xác nhận đã nhận đủ hàng trên sàn trước đi.
- `inducement` / `request` / unknown: Chỉ sau khi bạn xác nhận, tôi mới hoàn lại tiền cho bạn.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? | Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

Điểm rà: Hành động làm mất bảo vệ giao dịch, không giới hạn vào chuyển tiền trực tiếp.

## SG-12 — Đệm số dư thay cách nói nạp tiền

Đầu vào:
```json
{
  "text": "Để giải phóng tiền công đang giữ, chị cần đệm 1 triệu số dư bảo chứng sang ví của em. Khi hệ thống ghi nhận khoản đệm, em mới mở quyền lấy cả tiền công lẫn vốn."
}
```

Kỳ vọng: `high`. Thực tế: `error`, HTTP 504, 31.85 giây. Attempt provider: 3.
Lỗi: PROVIDER_TIMEOUT; bước: review

Điểm rà: Biến thể đổi cách diễn đạt nhưng giữ cơ chế trả trước mới nhận tiền.

## SG-22 — Chuỗi sáu số trong SMS

Đầu vào:
```json
{
  "text": "Hãy chép cho tôi chuỗi sáu số trong SMS đăng nhập vừa tới, tôi sẽ dùng nó mở lại quyền truy cập hộ bạn."
}
```

Kỳ vọng: `high`. Thực tế: `high`, HTTP 200, 22.05 giây. Attempt provider: 2.
- `share_auth_code` / `request` / unknown: Hãy chép cho tôi chuỗi sáu số trong SMS đăng nhập vừa tới, tôi sẽ dùng nó mở lại quyền truy cập hộ bạn.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? | Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Điểm rà: Biến thể không dùng từ OTP nhưng đòi mã đăng nhập.

## SG-32 — Quyền quản trị trang không rõ mục đích

Đầu vào:
```json
{
  "text": "Thêm tài khoản của tôi làm quản trị viên trang và cho quyền xóa thành viên khác."
}
```

Kỳ vọng: `suspicious`. Thực tế: `error`, HTTP 503, 18.20 giây. Attempt provider: 3.
Lỗi: PROVIDER_UNAVAILABLE; bước: review

Điểm rà: Đã rõ yêu cầu quyền nhạy cảm; có thể cảnh báo và hỏi thêm, chưa khẳng định tội phạm.

## SG-42 — Cài APK ngoài kho chưa rõ lý do

Đầu vào:
```json
{
  "text": "Cài BanHoTro.apk tôi gửi trực tiếp trong tin nhắn, đừng dùng bản trên kho ứng dụng."
}
```

Kỳ vọng: `suspicious`. Thực tế: `suspicious`, HTTP 200, 15.62 giây. Attempt provider: 2.
- `install_app` / `request` / unknown: Cài BanHoTro.apk tôi gửi trực tiếp trong tin nhắn, đừng dùng bản trên kho ứng dụng.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào? | Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì?

Điểm rà: Cảnh báo trước thao tác cài đặt; không bịa thêm điều kiện tiền hay mã.

## SG-52 — Phí giữ suất để nhận tài trợ

Đầu vào:
```json
{
  "text": "Suất tài trợ của bạn đã được giữ. Nộp 500 nghìn phí giữ suất vào tài khoản riêng của tôi trong 10 phút thì mới được nhận tiền tài trợ."
}
```

Kỳ vọng: `high`. Thực tế: `high`, HTTP 200, 6.85 giây. Attempt provider: 2.
- `transfer_funds` / `request` / unknown: Nộp 500 nghìn phí giữ suất vào tài khoản riêng của tôi
- `inducement` / `claim` / unknown: trong 10 phút thì mới được nhận tiền tài trợ

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? | Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

## SG-62 — Tắt cảnh báo ví và ký chấp thuận

Đầu vào:
```json
{
  "text": "Tắt mọi cảnh báo an toàn của ví rồi ký chấp thuận không giới hạn cho địa chỉ tôi vừa gửi."
}
```

Kỳ vọng: `suspicious`. Thực tế: `error`, HTTP 504, 23.67 giây. Attempt provider: 2.
Lỗi: PROVIDER_TIMEOUT; bước: review

Điểm rà: Hành vi mới có thể được mô tả other hoặc grant_access; chấm mức cảnh báo, không ép taxonomy.

## SG-13 — Trả khoản vay đã đối chiếu

Đầu vào:
```json
{
  "text": "Bạn trả lại mình 320 nghìn đã vay hôm qua nhé.",
  "context": "Tôi xác nhận đây là bạn đã cho tôi mượn 320 nghìn. Tôi vừa gặp trực tiếp và đối chiếu đúng khoản vay cùng tài khoản nhận."
}
```

Kỳ vọng: `clear`. Thực tế: `need_context`, HTTP 200, 25.11 giây. Attempt provider: 2.
- `transfer_funds` / `request` / unknown: Bạn trả lại mình 320 nghìn đã vay hôm qua nhé.
- `other` / `unknown` / unknown: Bạn trả lại mình 320 nghìn đã vay hôm qua nhé.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## SG-23 — Tự nhập mã trên máy mình

Đầu vào:
```json
{
  "text": "Tôi tự mở ứng dụng ngân hàng chính thức và nhập OTP trên điện thoại của mình. Tôi không gửi mã cho ai."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 31.41 giây. Attempt provider: 2.
- `other` / `claim` / unknown: Tôi tự mở ứng dụng ngân hàng chính thức và nhập OTP trên điện thoại của mình.
- `other` / `denial` / unknown: Tôi không gửi mã cho ai.

Điểm rà: Tự nhập khác với giao mã cho người khác.

## SG-33 — Quyền thông báo hợp lệ

Đầu vào:
```json
{
  "text": "Ứng dụng lịch đang hỏi tôi có cho phép gửi thông báo nhắc lịch không.",
  "context": "Tôi tự mở ứng dụng lịch đã dùng lâu nay trong phần cài đặt, chỉ bật thông báo, không cấp điều khiển hay truy cập tài khoản."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 21.89 giây. Attempt provider: 2.
- `other` / `claim` / unknown: Ứng dụng lịch đang hỏi tôi có cho phép gửi thông báo nhắc lịch không.

## SG-43 — Cập nhật ứng dụng đã xác nhận

Đầu vào:
```json
{
  "text": "Bạn cập nhật ứng dụng họp đang dùng từ kho chính thức nhé.",
  "context": "Tôi đã đối chiếu yêu cầu cập nhật với quản trị công ty qua số nội bộ quen thuộc. Đó là ứng dụng đang dùng, đúng nhà phát hành trên kho, không phải tệp/link người gửi cung cấp."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 12.68 giây. Attempt provider: 2.
- `install_app` / `request` / unknown: Bạn cập nhật ứng dụng họp đang dùng từ kho chính thức nhé.

## SG-53 — Khuyến mại không đòi tài sản

Đầu vào:
```json
{
  "text": "Thư viện tặng dấu trang miễn phí cho người tới đọc sách vào chủ nhật, không cần đăng ký tài khoản hoặc đóng phí."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 17.48 giây. Attempt provider: 2.
- `other` / `claim` / unknown: Thư viện tặng dấu trang miễn phí cho người tới đọc sách vào chủ nhật, không cần đăng ký tài khoản hoặc đóng phí.

## SG-63 — Xác nhận hàng đã kiểm tra đủ

Đầu vào:
```json
{
  "text": "Bạn xác nhận đã nhận hàng sau khi kiểm tra đủ số lượng nhé.",
  "context": "Tôi đã nhận đủ kiện hàng đúng đơn, tự kiểm tra số lượng/chất lượng rồi mới xác nhận trên ứng dụng chính thức của sàn."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 12.67 giây. Attempt provider: 2.
- `other` / `request` / unknown: Bạn xác nhận đã nhận hàng sau khi kiểm tra đủ số lượng nhé.

## SG-14 — Bài cảnh báo chứa chuyển phí

Đầu vào:
```json
{
  "text": "Cảnh báo: câu “chuyển phí xác nhận để lấy lại cọc” là dấu hiệu cần xác minh. Đừng chuyển thêm theo tin nhắn của người lạ."
}
```

Kỳ vọng: `clear`. Thực tế: `need_context`, HTTP 200, 7.19 giây. Attempt provider: 2.
- `other` / `quoted_warning` / unknown: chuyển phí xác nhận để lấy lại cọc
- `transfer_funds` / `denial` / unknown: Đừng chuyển thêm theo tin nhắn của người lạ.
- `other` / `unknown` / unknown: Đừng chuyển thêm theo tin nhắn của người lạ.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Điểm rà: Lời trích cảnh báo/phủ định không phải yêu cầu chuyển tiền.

## SG-24 — Tập huấn trích câu dụ lấy mã

Đầu vào:
```json
{
  "text": "Buổi tập huấn đưa ví dụ “đọc OTP cho tôi để nhận quà”. Đây là lời dụ cần tránh, không đọc mã hoặc mật khẩu cho ai."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 6.15 giây. Attempt provider: 2.
- `share_auth_code` / `quoted_warning` / unknown: đọc OTP cho tôi để nhận quà
- `other` / `denial` / unknown: Đây là lời dụ cần tránh, không đọc mã hoặc mật khẩu cho ai.
- `inducement` / `quoted_warning` / unknown: đọc OTP cho tôi để nhận quà

Điểm rà: Đúng vai lời trích và phủ định.

## SG-34 — Cảnh báo không chia sẻ màn hình

Đầu vào:
```json
{
  "text": "Không cấp quyền điều khiển hoặc chia sẻ màn hình ngân hàng cho người lạ. Bài viết này hướng dẫn bảo vệ tài khoản."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 5.96 giây. Attempt provider: 2.
- `grant_access` / `quoted_warning` / unknown: Không cấp quyền điều khiển hoặc chia sẻ màn hình ngân hàng cho người lạ. Bài viết này hướng dẫn bảo vệ tài khoản.

## SG-44 — Bài cảnh báo cài tệp

Đầu vào:
```json
{
  "text": "Cảnh giác với lời nhắn “cài APK rồi bật trợ năng để nhận tiền”. Không cài tệp được gửi từ người chưa xác minh."
}
```

Kỳ vọng: `clear`. Thực tế: `error`, HTTP 502, 16.17 giây. Attempt provider: 2.
Lỗi: EVIDENCE_INVALID; bước: None

## SG-54 — Giảng giải lời hứa lợi nhuận

Đầu vào:
```json
{
  "text": "Bài học nhắc: đừng tin lời hứa lợi nhuận chắc chắn hoặc chuyển vốn cho người lạ. Ví dụ này là nội dung phòng tránh, lớp không nhận tiền đầu tư."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 5.44 giây. Attempt provider: 2.
- `other` / `quoted_warning` / unknown: Bài học nhắc: đừng tin lời hứa lợi nhuận chắc chắn hoặc chuyển vốn cho người lạ.
- `inducement` / `quoted_warning` / unknown: Ví dụ này là nội dung phòng tránh, lớp không nhận tiền đầu tư.

## SG-64 — Cảnh báo bảo vệ quyền khiếu nại

Đầu vào:
```json
{
  "text": "Đừng xác nhận đã nhận đủ hàng khi hàng chưa tới, cũng đừng rút khiếu nại chỉ vì người bán hứa hoàn tiền sau. Đây là bài hướng dẫn tự bảo vệ."
}
```

Kỳ vọng: `clear`. Thực tế: `clear`, HTTP 200, 13.75 giây. Attempt provider: 2.
- `other` / `quoted_warning` / unknown: Đừng xác nhận đã nhận đủ hàng khi hàng chưa tới, cũng đừng rút khiếu nại chỉ vì người bán hứa hoàn tiền sau. Đây là bài hướng dẫn tự bảo vệ.

## SG-15 — Nhắc chuyển tiền chưa rõ khoản gì

Đầu vào:
```json
{
  "text": "Chuyển lại cho tôi khoản hôm trước nhé."
}
```

Kỳ vọng: `need_context`. Thực tế: `need_context`, HTTP 200, 14.29 giây. Attempt provider: 2.
- `transfer_funds` / `request` / unknown: Chuyển lại cho tôi khoản hôm trước nhé.

Câu hỏi: Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không? | Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

Điểm rà: Hỏi quan hệ và mục đích khoản tiền, không tự kết luận lừa đảo.

## SG-25 — Chưa biết mã được yêu cầu là mã gì

Đầu vào:
```json
{
  "text": "Họ nhắn gửi cho họ mã đó. Tôi chưa biết họ nói mã đơn hàng hay mã xác thực nào."
}
```

Kỳ vọng: `need_context`. Thực tế: `need_context`, HTTP 200, 13.35 giây. Attempt provider: 2.
- `other` / `claim` / unknown: Họ nhắn gửi cho họ mã đó. Tôi chưa biết họ nói mã đơn hàng hay mã xác thực nào.

Câu hỏi: Thao tác được yêu cầu qua ứng dụng chính thức hay đường dẫn/kênh do người gửi cung cấp? | Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Điểm rà: Không tự coi mọi mã là OTP; hỏi loại mã và nguồn yêu cầu.

## SG-35 — Chưa biết loại quyền

Đầu vào:
```json
{
  "text": "Người gửi bảo bật quyền đó thì họ mới hỗ trợ được. Tôi chưa thấy họ chỉ rõ quyền gì hoặc trên ứng dụng nào."
}
```

Kỳ vọng: `need_context`. Thực tế: `suspicious`, HTTP 200, 6.64 giây. Attempt provider: 2.
- `grant_access` / `request` / unknown: Người gửi bảo bật quyền đó thì họ mới hỗ trợ được
- `other` / `claim` / unknown: Tôi chưa thấy họ chỉ rõ quyền gì hoặc trên ứng dụng nào.

Câu hỏi: Vì sao họ cần chia sẻ màn hình hoặc quyền điều khiển, và bạn đã xác minh đầu mối hỗ trợ chưa? | Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Điểm rà: Hỏi quyền gì/mục đích; không bịa quyền điều khiển đã xuất hiện.

## SG-45 — Tệp mới tải nhưng chưa biết loại

Đầu vào:
```json
{
  "text": "Họ gửi một tệp đính kèm và nhờ tôi mở. Tôi chưa biết đó là tài liệu hay chương trình."
}
```

Kỳ vọng: `need_context`. Thực tế: `need_context`, HTTP 200, 16.09 giây. Attempt provider: 2.
- `other` / `request` / unknown: Họ gửi một tệp đính kèm và nhờ tôi mở.

Câu hỏi: Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì? | Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

## SG-55 — Hứa tiền nhưng chưa rõ điều kiện

Đầu vào:
```json
{
  "text": "Có người bảo tôi sắp được nhận một khoản tiền, nhưng chưa nói vì sao hoặc phải làm gì.",
  "question": "Tôi nên hỏi gì để biết điều kiện có rủi ro không?"
}
```

Kỳ vọng: `need_context`. Thực tế: `need_context`, HTTP 200, 5.57 giây. Attempt provider: 2.
- `other` / `claim` / unknown: Có người bảo tôi sắp được nhận một khoản tiền, nhưng chưa nói vì sao hoặc phải làm gì.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào? | Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

Điểm rà: Hỏi nguồn/điều kiện, không tự thêm yêu cầu ứng tiền.

## SG-65 — Yêu cầu xác nhận chưa rõ tác động

Đầu vào:
```json
{
  "text": "Họ bảo tôi bấm xác nhận mục đó trong tài khoản. Tôi chưa biết xác nhận điều gì hoặc có mất quyền gì không."
}
```

Kỳ vọng: `need_context`. Thực tế: `need_context`, HTTP 200, 18.39 giây. Attempt provider: 3.
- `other` / `request` / unknown: Họ bảo tôi bấm xác nhận mục đó trong tài khoản.
- `other` / `denial` / unknown: Tôi chưa biết xác nhận điều gì hoặc có mất quyền gì không.

Câu hỏi: Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào? | Vì sao họ cần chia sẻ màn hình hoặc quyền điều khiển, và bạn đã xác minh đầu mối hỗ trợ chưa?
