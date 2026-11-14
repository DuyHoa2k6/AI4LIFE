# 12 ca: dữ kiện BE, quy tắc và thời gian HTTP

Mỗi câu đo 10 lượt qua HTTP TCP localhost, tuần tự, cùng process. Không phải browser/extension hay tải đồng thời.
API tính từ trước POST đến sau đọc JSON; Engine chỉ v2, chưa gồm adapter/schema/HTTP. Lượt đầu không được chứng minh là cold start hoàn toàn.

| Ca | Câu đầu vào | Kết quả | HTTP p50 ms | HTTP p95 ms | Engine p50 ms |
|---|---|---|---:|---:|---:|
| P01 | Gửi mã OTP cho tôi. | high / preventive | 4.56 | 20.75 | 2.77 |
| P02 | Cảnh báo: đừng gửi OTP. | clear / undetermined | 4.87 | 7.29 | 3.02 |
| P03 | Đọc sáu số vừa hiện để nhận tiền. | need_context / undetermined | 5.29 | 9.49 | 3.43 |
| P04 | Chưa thấy tiền về, nhưng cứ giao máy trước. | suspicious / preventive | 4.99 | 19.99 | 3.34 |
| P05 | Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy nhé. | clear / undetermined | 5.16 | 6.10 | 3.35 |
| P06 | Chuyển thêm tiền để rút số dư. | high / preventive | 4.83 | 7.12 | 3.10 |
| P07 | Gửi ảnh CCCD qua chat. | suspicious / preventive | 4.50 | 7.74 | 2.95 |
| P08 | Mây bay trên núi. | need_context / undetermined | 3.81 | 4.53 | 2.36 |
| P09 | Hiện tại tôi bị giữ lại và không được rời đi. | high / urgent | 3.06 | 4.00 | 1.51 |
| P10 | Hãy đi cùng và giấu gia đình. | suspicious / preventive | 4.35 | 5.73 | 2.82 |
| P11 | ko ck tiền trước gửi mk tk cho tôi | high / preventive | 7.97 | 8.90 | 5.98 |
| P12 | Bài tuyên truyền cảnh báo: có người bị ép làm việc. | clear / undetermined | 5.28 | 5.67 | 3.40 |

## P01

Gửi mã OTP cho tôi.

Nội dung yêu cầu giao thông tin xác thực cho người khác; có nguy cơ mất quyền truy cập tài khoản.

Đường chạy: full_local. Rules: R-CREDENTIAL. Template: TPL-R-CREDENTIAL.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| provide_code | request | positive | requested | sender_claim | Gửi |

Quan hệ:
- Chưa trích được quan hệ đủ điều kiện.

Không có câu hỏi bổ sung.

HTTP p50/p95: 4.56/20.75 ms; Engine p50: 2.77 ms; lượt đo đầu của câu: 20.75 ms.

## P02

Cảnh báo: đừng gửi OTP.

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

Đường chạy: full_local. Rules: fallback, chưa đủ điều kiện rule cảnh báo. Template: TPL-CLEAR.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| provide_code | quoted_warning | negative | unknown | quoted_warning | gửi |

Quan hệ:
- warning_about: old:p1 → old:a1 (observed); REL-QUOTED-WARNING.

Không có câu hỏi bổ sung.

HTTP p50/p95: 4.87/7.29 ms; Engine p50: 3.02 ms; lượt đo đầu của câu: 7.29 ms.

## P03

Đọc sáu số vừa hiện để nhận tiền.

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Đường chạy: full_local. Rules: fallback, chưa đủ điều kiện rule cảnh báo. Template: TPL-UNKNOWN.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| provide_code | request | positive | requested | sender_claim | Đọc |
| receive_funds | claim | positive | unknown | sender_claim | nhận |

Quan hệ:
- prerequisite_for: old:a1 → old:a2 (observed); REL-EXPLICIT-PURPOSE.
- reason_given_for: old:a2 → old:a1 (observed); REL-STATED-REASON.
- same_transaction: old:a1 → old:a2 (inferred); LINK-SAME-TRANSACTION.

Câu hỏi:
- Dãy số đó được thông báo dùng để làm gì? Chỉ mô tả loại mã, không gửi mã thật.

HTTP p50/p95: 5.29/9.49 ms; Engine p50: 3.43 ms; lượt đo đầu của câu: 6.29 ms.

## P04

Chưa thấy tiền về, nhưng cứ giao máy trước.

Nội dung yêu cầu giao tài sản khi người nhận tiền cho biết chưa xác nhận thanh toán. Chưa đủ căn cứ nói biên lai giả.

Đường chạy: full_local. Rules: R-HANDOVER. Template: TPL-R-HANDOVER.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| receive_funds | claim | negative | pending | sender_claim | thấy |
| handover_asset | request | positive | requested | sender_claim | giao |

Quan hệ:
- before: old:a2 → old:a1 (observed); REL-HANDOVER-BEFORE-CONFIRMATION.
- same_transaction: old:a2 → old:a1 (inferred); LINK-SAME-TRANSACTION.

Không có câu hỏi bổ sung.

HTTP p50/p95: 4.99/19.99 ms; Engine p50: 3.34 ms; lượt đo đầu của câu: 5.23 ms.

## P05

Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy nhé.

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

Đường chạy: full_local. Rules: fallback, chưa đủ điều kiện rule cảnh báo. Template: TPL-CLEAR.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| receive_funds | claim | positive | completed | sender_claim | nhận |
| handover_asset | request | positive | requested | sender_claim | giao |

Quan hệ:
- before: old:a1 → old:a2 (inferred); REL-REPORTED-PAYMENT-FIRST.
- same_transaction: old:a1 → old:a2 (inferred); LINK-SAME-TRANSACTION.

Không có câu hỏi bổ sung.

HTTP p50/p95: 5.16/6.10 ms; Engine p50: 3.35 ms; lượt đo đầu của câu: 5.19 ms.

## P06

Chuyển thêm tiền để rút số dư.

Nội dung liên kết việc chuyển thêm tiền với điều kiện nhận hoặc rút tiền.

Đường chạy: full_local. Rules: R-PAY-TO-WITHDRAW. Template: TPL-R-PAY-TO-WITHDRAW.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| transfer_funds | request | positive | requested | sender_claim | Chuyển |
| withdraw_funds | claim | positive | unknown | sender_claim | rút |

Quan hệ:
- prerequisite_for: old:a1 → old:a2 (observed); REL-EXPLICIT-PURPOSE.
- reason_given_for: old:a2 → old:a1 (observed); REL-STATED-REASON.
- same_transaction: old:a1 → old:a2 (inferred); LINK-SAME-TRANSACTION.

Không có câu hỏi bổ sung.

HTTP p50/p95: 4.83/7.12 ms; Engine p50: 3.10 ms; lượt đo đầu của câu: 4.67 ms.

## P07

Gửi ảnh CCCD qua chat.

Có yêu cầu cung cấp giấy tờ cá nhân; cần xác minh đơn vị tiếp nhận và kênh gửi.

Đường chạy: full_local. Rules: R-DATA. Template: TPL-R-DATA.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| provide_documents | request | positive | requested | sender_claim | Gửi |

Quan hệ:
- Chưa trích được quan hệ đủ điều kiện.

Không có câu hỏi bổ sung.

HTTP p50/p95: 4.50/7.74 ms; Engine p50: 2.95 ms; lượt đo đầu của câu: 4.43 ms.

## P08

Mây bay trên núi.

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Đường chạy: full_local. Rules: fallback, chưa đủ điều kiện rule cảnh báo. Template: TPL-UNKNOWN.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|

Quan hệ:
- Chưa trích được quan hệ đủ điều kiện.

Câu hỏi:
- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

HTTP p50/p95: 3.81/4.53 ms; Engine p50: 2.36 ms; lượt đo đầu của câu: 3.99 ms.

## P09

Hiện tại tôi bị giữ lại và không được rời đi.

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

Đường chạy: urgent_precheck. Rules: R-URGENT-CURRENT. Template: TPL-R-URGENT-CURRENT.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| restrict_movement | claim | positive | ongoing | self_report | Hiện tại tôi bị giữ lại và không được rời đi. |
| restrict_movement | claim | positive | ongoing | self_report | Hiện tại tôi bị giữ lại và không được rời đi. |

Quan hệ:
- Chưa trích được quan hệ đủ điều kiện.

Câu hỏi:
- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

HTTP p50/p95: 3.06/4.00 ms; Engine p50: 1.51 ms; lượt đo đầu của câu: 3.68 ms.

## P10

Hãy đi cùng và giấu gia đình.

Lời mời di chuyển đi cùng yêu cầu giấu người thân; cần xác minh điều kiện và đầu mối.

Đường chạy: full_local. Rules: R-TRAVEL-SECRET. Template: TPL-R-TRAVEL-SECRET.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| invite_travel_or_meeting | request | positive | requested | sender_claim | Hãy đi cùng và giấu gia đình. |
| request_secrecy | request | positive | requested | sender_claim | Hãy đi cùng và giấu gia đình. |

Quan hệ:
- travel_conditioned_on_secrecy: safe:e1 → safe:e2 (inferred); LINK-travel_conditioned_on_secrecy.

Không có câu hỏi bổ sung.

HTTP p50/p95: 4.35/5.73 ms; Engine p50: 2.82 ms; lượt đo đầu của câu: 4.45 ms.

## P11

ko ck tiền trước gửi mk tk cho tôi

Nội dung yêu cầu giao thông tin xác thực cho người khác; có nguy cơ mất quyền truy cập tài khoản.

Đường chạy: full_local. Rules: R-CREDENTIAL. Template: TPL-R-CREDENTIAL.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| transfer_funds | denial | negative | requested | sender_claim | ck |
| provide_credentials | request | positive | requested | sender_claim | gửi |

Quan hệ:
- Chưa trích được quan hệ đủ điều kiện.

Không có câu hỏi bổ sung.

HTTP p50/p95: 7.97/8.90 ms; Engine p50: 5.98 ms; lượt đo đầu của câu: 8.13 ms.

## P12

Bài tuyên truyền cảnh báo: có người bị ép làm việc.

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

Đường chạy: full_local. Rules: fallback, chưa đủ điều kiện rule cảnh báo. Template: TPL-CLEAR.

| Hành vi | Vai | Phủ định | Trạng thái | Nguồn nhận định | Căn cứ |
|---|---|---|---|---|---|
| compel_work | quoted_warning | positive | unknown | quoted_warning | Bài tuyên truyền cảnh báo: có người bị ép làm việc. |

Quan hệ:
- Chưa trích được quan hệ đủ điều kiện.

Không có câu hỏi bổ sung.

HTTP p50/p95: 5.28/5.67 ms; Engine p50: 3.40 ms; lượt đo đầu của câu: 4.49 ms.
