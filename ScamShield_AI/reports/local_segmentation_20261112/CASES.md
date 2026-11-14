# Segmentation API development cases

Not independent accuracy; no final risk decision.

## S01

Chiều nay giao hàng nhé gửi mã OTP cho tôi

- Chiều nay giao hàng nhé | sentence_start / observed
- gửi mã OTP cho tôi | action_restart / inferred

Events:
- handover_asset / positive / request
- provide_code / positive / request

## S02

Đừng gửi OTP cho người lạ gửi mã đăng nhập cho tôi để hoàn tiền

- Đừng gửi OTP cho người lạ | sentence_start / observed
- gửi mã đăng nhập cho tôi | action_restart / inferred
- để hoàn tiền | connector / inferred

Events:
- provide_code / negative / request
- provide_code / positive / request

## S03

Chưa thấy tiền về, nhưng cứ giao máy trước.

- Chưa thấy tiền về, | sentence_start / observed
- nhưng cứ giao máy trước. | connector / inferred

Events:
- receive_funds / negative / claim
- handover_asset / positive / request

## S04

Nếu chưa nhận tiền thì đừng giao máy

- Nếu chưa nhận tiền | sentence_start / observed
- thì đừng giao máy | connector / inferred

Events:
- receive_funds / negative / claim
- handover_asset / negative / request

## S05

Đừng chuyển tiền và gửi OTP

- Đừng chuyển tiền và gửi OTP | sentence_start / uncertain

Events:
- transfer_funds / negative / request
- provide_code / uncertain / request

## S06

Gửi mã đăng nhập cho tôi

- Gửi mã đăng nhập cho tôi | sentence_start / observed

Events:
- provide_code / positive / request

## S07

Mở liên kết để đăng nhập

- Mở liên kết | sentence_start / observed
- để đăng nhập | connector / inferred

Events:
- open_link / positive / request
- login / positive / request

## S08

Tôi đã chuyển tiền rồi

- Tôi đã chuyển tiền rồi | sentence_start / observed

Events:
- transfer_funds / positive / claim

## S09

Công việc đã xong

- Công việc đã xong | sentence_start / observed

Events:

## S10

Tôi đi trên đê rồi về nhà

- Tôi đi trên đê rồi về nhà | sentence_start / observed

Events:

## S11

😀 Chuyển 500.000,50 đồng mở https://example.invalid/a?x=1&y=2

- 😀 Chuyển 500.000,50 đồng | sentence_start / observed
- mở https://example.invalid/a?x=1&y=2 | action_restart / inferred

Events:
- transfer_funds / positive / request
- open_link / positive / request

## S12

Cảnh báo “gửi OTP rồi chuyển tiền” gửi OTP cho tôi

- Cảnh báo “gửi OTP rồi chuyển tiền” | sentence_start / observed
- gửi OTP cho tôi | action_restart / inferred

Events:
- provide_code / positive / quoted_warning
- transfer_funds / positive / quoted_warning
- provide_code / positive / request

## S13

Tài xế đang chờ bạn giao hàng nhé

- Tài xế đang chờ | sentence_start / observed
- bạn giao hàng nhé | action_restart / inferred

Events:
- handover_asset / positive / request

## S14

Đơn A chưa thanh toán đơn B đã nhận đủ giao đơn B nhé

- Đơn A chưa thanh toán | sentence_start / observed
- đơn B đã nhận đủ | transaction_change / inferred
- giao đơn B nhé | action_restart / inferred

Events:
- transfer_funds / negative / claim
- receive_funds / positive / claim
- handover_asset / positive / request

## S15

Cài ứng dụng và cấp quyền điều khiển

- Cài ứng dụng và cấp quyền điều khiển | sentence_start / uncertain

Events:
- install_app / positive / request
- grant_control / uncertain / request

## S16

Đọc sáu số để nhận tiền

- Đọc sáu số | sentence_start / observed
- để nhận tiền | connector / inferred

Events:
- provide_code / positive / request
- receive_funds / positive / claim

