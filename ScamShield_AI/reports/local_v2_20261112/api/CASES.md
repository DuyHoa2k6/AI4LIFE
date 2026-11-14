# Kết quả từng ca cục bộ

Dữ liệu tổng hợp phát triển; nhãn chi tiết máy tạo, chưa là độ chính xác độc lập.

| Ca | Mức rủi ro | Khẩn cấp | Quy tắc | Thời gian API ms |
|---|---|---|---|---:|
| trust-N | clear | undetermined |  | 15.44 |
| trust-U | clear | undetermined |  | 7.04 |
| trust-P | suspicious | preventive | R-TRAVEL-SECRET | 5.92 |
| travel-N | clear | undetermined |  | 5.86 |
| travel-U | need_context | undetermined |  | 5.07 |
| travel-P | suspicious | preventive | R-TRAVEL-SECRET | 4.31 |
| employment-N | clear | undetermined |  | 5.39 |
| employment-U | need_context | undetermined |  | 4.62 |
| employment-P | suspicious | preventive | R-CHANGE-WORK | 4.55 |
| debt-N | clear | undetermined |  | 5.87 |
| debt-U | need_context | undetermined |  | 5.61 |
| debt-P | high | urgent | R-URGENT-CURRENT, R-DEBT-EXIT | 3.32 |
| secrecy-N | clear | undetermined |  | 5.53 |
| secrecy-U | need_context | undetermined |  | 5.76 |
| secrecy-P | suspicious | preventive | R-TRAVEL-SECRET | 4.89 |
| communication-N | clear | undetermined |  | 4.68 |
| communication-U | suspicious | preventive | R-CONTROL | 4.32 |
| communication-P | high | urgent | R-URGENT-CURRENT, R-CONTROL | 3.01 |
| documents-N | clear | undetermined |  | 5.85 |
| documents-U | suspicious | preventive | R-CONTROL | 4.41 |
| documents-P | high | urgent | R-URGENT-CURRENT, R-DOC-EXIT, R-CONTROL | 2.52 |
| movement-N | clear | undetermined |  | 4.67 |
| movement-U | need_context | undetermined |  | 5.26 |
| movement-P | high | urgent | R-URGENT-CURRENT | 2.63 |
| harm-N | clear | undetermined |  | 4.49 |
| harm-U | high | preventive | R-COERCION | 5.17 |
| harm-P | high | urgent | R-URGENT-THREAT, R-COERCION | 2.73 |
| disclosure-N | clear | undetermined |  | 4.34 |
| disclosure-U | need_context | undetermined |  | 3.93 |
| disclosure-P | high | preventive | R-COERCION | 4.04 |
| release-N | clear | undetermined |  | 4.43 |
| release-U | need_context | undetermined |  | 4.49 |
| release-P | high | preventive | R-RELEASE | 4.47 |
| forced_work-N | clear | undetermined |  | 4.82 |
| forced_work-U | need_context | undetermined |  | 4.34 |
| forced_work-P | high | urgent | R-URGENT-CURRENT, R-COERCION | 2.48 |
| illegal-N | clear | undetermined |  | 3.94 |
| illegal-U | need_context | undetermined |  | 4.28 |
| illegal-P | high | urgent | R-URGENT-CURRENT, R-COERCION | 2.67 |
| bodily-N | clear | undetermined |  | 4.53 |
| bodily-U | need_context | undetermined |  | 4.19 |
| bodily-P | high | urgent | R-URGENT-CURRENT, R-COERCION | 2.32 |
| change-N | clear | undetermined |  | 4.75 |
| change-U | need_context | undetermined |  | 4.93 |
| change-P | suspicious | preventive | R-CHANGE-WORK | 4.53 |
| finance-handover | suspicious | preventive | R-HANDOVER | 5.44 |
| finance-paid | clear | undetermined |  | 5.10 |
| finance-code | need_context | undetermined |  | 4.88 |
| finance-otp | high | preventive | R-CREDENTIAL | 4.17 |
| finance-warning | clear | undetermined |  | 4.55 |
| finance-withdraw | high | preventive | R-PAY-TO-WITHDRAW | 4.65 |
| finance-docs | suspicious | preventive | R-DATA | 4.24 |
| finance-app | suspicious | preventive | R-ACCESS | 21.30 |
| finance-outside | need_context | undetermined |  | 3.64 |
| finance-login-linked | high | preventive | R-CODE-IDENTITY | 5.21 |
| safety-past | clear | undetermined |  | 5.50 |
| threat-compels | high | urgent | R-URGENT-CURRENT, R-URGENT-THREAT, R-COERCION | 3.73 |
| bodily-sexual | high | urgent | R-URGENT-CURRENT, R-COERCION | 2.85 |
| bodily-explicit | high | urgent | R-URGENT-CURRENT, R-COERCION | 2.65 |
| no-organ-inference | need_context | undetermined |  | 4.66 |
| payment-update | clear | undetermined |  | 6.32 |
| payment-conflict | need_context | undetermined |  | 4.82 |
| two-transactions | need_context | undetermined |  | 4.27 |
| url-unverified | need_context | undetermined |  | 4.44 |
| family-user-report | clear | undetermined |  | 4.92 |
| warning-child-ocr | clear | undetermined |  | 5.00 |
| warning-child-comment | high | preventive | R-CREDENTIAL | 4.76 |
| legacy-SS-001 | need_context | undetermined |  | 8.71 |
| legacy-SS-002 | clear | undetermined |  | 5.33 |
| legacy-SS-003 | need_context | undetermined |  | 4.35 |

## trust-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cứ tin tôi, anh sẽ lo.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Cứ tin tôi, anh sẽ lo.

> Cứ tin tôi

> anh sẽ lo


## trust-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Anh là người quen của em.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> là người quen

> Anh là người quen của em.

> của em


## trust-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cứ tin tôi, hãy đi cùng và giấu gia đình.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Lời mời di chuyển đi cùng yêu cầu giấu người thân; cần xác minh điều kiện và đầu mối.

- Nếu an toàn, trao đổi với người tin cậy và xác minh độc lập trước khi di chuyển.

> Cứ tin tôi, hãy đi cùng và giấu gia đình.

> hãy đi

> giấu gia đình


## travel-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Mời bạn đi gặp mặt, địa điểm và điều kiện đã gửi rõ.",
      "scope_id": "case"
    }
  ],
  "context_facts": [
    {
      "id": "c1",
      "text": "Tôi đã gọi đầu mối độc lập để đối chiếu điều kiện và địa điểm; tôi có quyền từ chối và tự do rời đi.",
      "verification_status": "user_reports_verification",
      "applies_to_message_ids": [
        "m1"
      ]
    }
  ]
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Mời bạn đi gặp mặt, địa điểm và điều kiện đã gửi rõ.

> Mời bạn đi

> gặp mặt


## travel-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Sang bên này anh lo hết.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Bạn có biết người mời ngoài đời hoặc có thể xác minh công việc, địa điểm qua đầu mối độc lập không?
- Họ có yêu cầu giữ bí mật, giao giấy tờ hoặc hạn chế liên lạc không?

## travel-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hãy đi cùng và giấu gia đình.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Lời mời di chuyển đi cùng yêu cầu giấu người thân; cần xác minh điều kiện và đầu mối.

- Nếu an toàn, trao đổi với người tin cậy và xác minh độc lập trước khi di chuyển.

> Hãy đi cùng và giấu gia đình.

> Hãy đi

> giấu gia đình


## employment-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tuyển nhân viên, có hợp đồng và địa điểm để kiểm tra.",
      "scope_id": "case"
    }
  ],
  "context_facts": [
    {
      "id": "c1",
      "text": "Tôi đã gọi đầu mối độc lập để đối chiếu điều kiện và địa điểm; tôi có quyền từ chối và tự do rời đi.",
      "verification_status": "user_reports_verification",
      "applies_to_message_ids": [
        "m1"
      ]
    }
  ]
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Tuyển nhân viên, có hợp đồng và địa điểm để kiểm tra.

> Tuyển nhân viên


## employment-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Có việc làm nhưng chưa mô tả công việc.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Bạn có biết người mời ngoài đời hoặc có thể xác minh công việc, địa điểm qua đầu mối độc lập không?
- Họ có yêu cầu giữ bí mật, giao giấy tờ hoặc hạn chế liên lạc không?

## employment-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Mời làm việc nhưng công việc khác thỏa thuận.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung nêu thay đổi công việc hoặc điều kiện so với lời mời ban đầu.

- Chưa chấp nhận điều kiện mới trước khi đối chiếu thỏa thuận và quyền từ chối.

> Mời làm việc nhưng công việc khác thỏa thuận.

> Mời làm việc

> công việc khác thỏa thuận


## debt-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Chi phí đi lại được hỗ trợ, không ghi nợ và có thể rời đi bất cứ lúc nào.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Chi phí đi lại được hỗ trợ, không ghi nợ và có thể rời đi bất cứ lúc nào.

> ghi nợ

> có thể rời đi bất cứ lúc nào


## debt-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Có ghi nợ chi phí, chưa nêu điều kiện trả.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## debt-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi đang nợ chi phí và không được rời đi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Tôi đang nợ chi phí và không được rời đi.

> không được rời đi

> nợ chi phí

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## secrecy-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cảnh báo: đừng nghe yêu cầu “giấu gia đình để đi cùng”.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Cảnh báo: đừng nghe yêu cầu “giấu gia đình để đi cùng”.

> đi cùng

> giấu gia đình


## secrecy-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ nhắc giữ bí mật, chưa rõ nội dung nào.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## secrecy-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hãy đi cùng và đừng báo người nhà.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Lời mời di chuyển đi cùng yêu cầu giấu người thân; cần xác minh điều kiện và đầu mối.

- Nếu an toàn, trao đổi với người tin cậy và xác minh độc lập trước khi di chuyển.

> Hãy đi cùng và đừng báo người nhà.

> Hãy đi

> đừng báo người nhà


## communication-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cảnh báo “cắt liên lạc với gia đình” là dấu hiệu cần xác minh.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Cảnh báo “cắt liên lạc với gia đình” là dấu hiệu cần xác minh.

> cắt liên lạc


## communication-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ nói sẽ giữ điện thoại, chưa rõ thời hạn.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Có thông tin về kiểm soát liên lạc hoặc giữ giấy tờ; cần làm rõ khả năng tự quyết và nhận lại.

- Nếu an toàn, kiểm tra bạn có thể nhận lại giấy tờ, liên lạc và tự do rời đi không.

> Họ nói sẽ giữ điện thoại, chưa rõ thời hạn.

> giữ điện thoại


## communication-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi đang bị giữ điện thoại và không được rời đi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Tôi đang bị giữ điện thoại và không được rời đi.

> không được rời đi

> giữ điện thoại

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## documents-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ giữ hộ chiếu để đăng ký và trả lại hộ chiếu ngay; có thể rời đi bất cứ lúc nào.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Họ giữ hộ chiếu để đăng ký và trả lại hộ chiếu ngay;

> giữ hộ chiếu

> trả lại hộ chiếu ngay

>  có thể rời đi bất cứ lúc nào.

> có thể rời đi bất cứ lúc nào


## documents-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ nói sẽ giữ hộ chiếu, chưa rõ lúc nhận lại.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Có thông tin về kiểm soát liên lạc hoặc giữ giấy tờ; cần làm rõ khả năng tự quyết và nhận lại.

- Nếu an toàn, kiểm tra bạn có thể nhận lại giấy tờ, liên lạc và tự do rời đi không.

> Họ nói sẽ giữ hộ chiếu, chưa rõ lúc nhận lại.

> giữ hộ chiếu


## documents-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ đang giữ hộ chiếu của tôi và tôi không được rời đi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Họ đang giữ hộ chiếu của tôi và tôi không được rời đi.

> không được rời đi

> giữ hộ chiếu

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## movement-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi không bị cấm rời đi và được tự do rời đi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Tôi không bị cấm rời đi và được tự do rời đi.

> cấm rời đi

> không bị cấm rời đi

> được tự do rời đi


## movement-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ nói về việc không được rời đi, chưa rõ ai và thời điểm.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## movement-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hiện tại tôi bị giữ lại và không được rời đi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Hiện tại tôi bị giữ lại và không được rời đi.

> bị giữ lại

> không được rời đi

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## harm-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Bài tuyên truyền cảnh báo lời “sẽ gây hại” để ép người khác.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Bài tuyên truyền cảnh báo lời “sẽ gây hại” để ép người khác.

> sẽ gây hại


## harm-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Một lời đe dọa gây hại được kể lại, chưa rõ thời điểm.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung có thông tin về đe dọa hoặc cưỡng ép; chưa xác minh độc lập người gây ra hay toàn bộ sự việc.

- Không gửi thêm thông tin riêng tư. Nếu an toàn, tìm sự hỗ trợ từ người tin cậy hoặc đơn vị phù hợp.

> Một lời đe dọa gây hại được kể lại, chưa rõ thời điểm.

> đe dọa gây hại


## harm-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ đe dọa gây hại tôi ngay bây giờ.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung có lời đe dọa gây hại ở thời điểm hiện tại hoặc sắp tới; cần ưu tiên an toàn.

- Nếu an toàn, tìm người tin cậy hoặc hỗ trợ khẩn cấp phù hợp; không tự điều tra hay đối đầu.

> Họ đe dọa gây hại tôi ngay bây giờ.

> đe dọa gây hại

- Bạn có thể tiếp tục trao đổi ở đây một cách an toàn không? Có thể bỏ qua.

## disclosure-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cảnh báo tin nhắn “sẽ phát tán ảnh” là lời đe dọa.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Cảnh báo tin nhắn “sẽ phát tán ảnh” là lời đe dọa.

> sẽ phát tán ảnh


## disclosure-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ nhắc dữ liệu riêng tư, chưa rõ yêu cầu.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## disclosure-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Người gửi nói sẽ phát tán ảnh riêng tư.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung có thông tin về đe dọa hoặc cưỡng ép; chưa xác minh độc lập người gây ra hay toàn bộ sự việc.

- Không gửi thêm thông tin riêng tư. Nếu an toàn, tìm sự hỗ trợ từ người tin cậy hoặc đơn vị phù hợp.

> Người gửi nói sẽ phát tán ảnh riêng tư.

> sẽ phát tán ảnh


## release-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Bài cảnh báo trích “trả tiền để được thả”.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Bài cảnh báo trích “trả tiền để được thả”.

> trả tiền để được thả


## release-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Có nhắc khoản tiền nhưng chưa rõ điều kiện rời đi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## release-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Bên đòi tiền yêu cầu chuyển tiền để thả người nhà.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Có lời đòi tiền để được rời đi hoặc để thả người. Lời đòi tiền chưa chứng minh việc bắt giữ đã xảy ra.

- Nếu an toàn, xác minh qua đầu mối độc lập và tìm hỗ trợ phù hợp; không tự đối đầu.

> Bên đòi tiền yêu cầu chuyển tiền để thả người nhà.

> chuyển tiền để thả người


## forced_work-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi không bị ép làm việc; có thể dừng theo thỏa thuận.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Tôi không bị ép làm việc;

> bị ép làm việc


## forced_work-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ nhắc giờ làm việc, chưa rõ quyền từ chối.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## forced_work-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hiện tại tôi bị ép làm việc và không được rời đi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Hiện tại tôi bị ép làm việc và không được rời đi.

> không được rời đi

> bị ép làm việc

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## illegal-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cảnh báo: có người bị ép tham gia lừa đảo.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Cảnh báo: có người bị ép tham gia lừa đảo.

> bị ép tham gia lừa đảo


## illegal-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Chưa mô tả công việc yêu cầu thực hiện.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## illegal-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi đang bị ép tham gia lừa đảo.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Tôi đang bị ép tham gia lừa đảo.

> bị ép tham gia lừa đảo

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## bodily-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi tự nguyện can thiệp cơ thể và có quyền dừng, có thể từ chối.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Tôi tự nguyện can thiệp cơ thể và có quyền dừng, có thể từ chối.

> tự nguyện can thiệp cơ thể và có quyền dừng, có thể từ chối


## bodily-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Có nhắc can thiệp cơ thể, chưa rõ thủ tục hoặc sự tự nguyện.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## bodily-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hiện tại tôi bị ép can thiệp cơ thể.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Hiện tại tôi bị ép can thiệp cơ thể.

> bị ép can thiệp cơ thể

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## change-N

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cảnh báo về việc “đổi điểm đến” khác thỏa thuận.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Cảnh báo về việc “đổi điểm đến” khác thỏa thuận.

> đổi điểm đến


## change-U

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ nói đổi địa điểm, chưa rõ đã đồng ý hay chưa.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## change-P

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Mời làm việc và công việc khác thỏa thuận.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung nêu thay đổi công việc hoặc điều kiện so với lời mời ban đầu.

- Chưa chấp nhận điều kiện mới trước khi đối chiếu thỏa thuận và quyền từ chối.

> Mời làm việc và công việc khác thỏa thuận.

> Mời làm việc

> công việc khác thỏa thuận


## finance-handover

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Chưa thấy tiền về, nhưng cứ giao máy trước.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung yêu cầu giao tài sản khi người nhận tiền cho biết chưa xác nhận thanh toán. Chưa đủ căn cứ nói biên lai giả.

- Tự kiểm tra tiền thực nhận qua kênh ngân hàng quen dùng trước khi giao tài sản.

> giao

> nhưng cứ giao máy trước.

> máy trước

> thấy

> Chưa thấy tiền về,

> tiền về

> Chưa


## finance-paid

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy cho tài xế nhé.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> nhận

> Tôi đã kiểm tra và nhận đủ tiền.

> đủ tiền

> giao

> Anh giao máy cho tài xế nhé.

> máy cho tài xế nhé


## finance-code

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Đọc sáu số vừa hiện để nhận tiền.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Dãy số đó được thông báo dùng để làm gì? Chỉ mô tả loại mã, không gửi mã thật.

## finance-otp

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Gửi mã OTP cho tôi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung yêu cầu giao thông tin xác thực cho người khác; có nguy cơ mất quyền truy cập tài khoản.

- Không gửi mã hoặc mật khẩu; tự kiểm tra yêu cầu bằng kênh chính thức quen dùng.

> Gửi

> Gửi mã OTP cho tôi.

> mã OTP cho tôi


## finance-warning

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cảnh báo “gửi OTP cho tôi”.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> gửi

> Cảnh báo “gửi OTP cho tôi”.

> OTP cho tôi


## finance-withdraw

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Chuyển thêm tiền để rút số dư.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Nội dung liên kết việc chuyển thêm tiền với điều kiện nhận hoặc rút tiền.

- Tạm dừng nộp thêm và đối chiếu giao dịch qua đầu mối độc lập.

> Chuyển

> Chuyển thêm tiền

> thêm tiền

> rút

> để rút số dư.

> số dư


## finance-docs

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Gửi ảnh CCCD qua chat.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Có yêu cầu cung cấp giấy tờ cá nhân; cần xác minh đơn vị tiếp nhận và kênh gửi.

- Chưa gửi ảnh giấy tờ cho đến khi đã xác minh mục đích và kênh tiếp nhận.

> Gửi

> Gửi ảnh CCCD qua chat.

> ảnh CCCD qua chat


## finance-app

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Cài app này.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Có yêu cầu cài ứng dụng hoặc chia sẻ quyền truy cập cần xác minh.

- Kiểm tra nguồn ứng dụng và đầu mối hỗ trợ độc lập trước khi cấp quyền.

> Cài

> Cài app này.

> app này


## finance-outside

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Mây bay trên đỉnh núi.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## finance-login-linked

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "sender",
      "scope_id": "sale",
      "text": "Đọc sáu số vừa hiện để nhận tiền."
    },
    {
      "id": "m2",
      "speaker_id": "receiver",
      "scope_id": "sale",
      "text": "Đó là mã đăng nhập."
    }
  ]
}
```

Dãy số được xác định trong hội thoại là mã đăng nhập, trong khi người gửi yêu cầu bạn cung cấp.

- Không đọc mã cho người khác; tự kiểm tra bằng ứng dụng chính thức.

> Đọc

> Đọc sáu số vừa hiện

> sáu số vừa hiện

> Đó là mã đăng nhập

> Đó là mã đăng nhập.


## safety-past

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Năm ngoái tôi từng bị giữ lại, hiện sự việc đã kết thúc.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Năm ngoái tôi từng bị giữ lại, hiện sự việc đã kết thúc.

> bị giữ lại


## threat-compels

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Họ đang đe dọa gây hại tôi và tôi bị ép làm việc.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Họ đang đe dọa gây hại tôi và tôi bị ép làm việc.

> bị ép làm việc

> đe dọa gây hại

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## bodily-sexual

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hiện tại tôi bị ép quan hệ tình dục.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Hiện tại tôi bị ép quan hệ tình dục.

> bị ép quan hệ tình dục

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## bodily-explicit

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hiện tại tôi bị dọa lấy nội tạng.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Người dùng cho biết đang bị hạn chế tự do hoặc bị cưỡng ép. Cần ưu tiên an toàn trước khi thu thập thêm thông tin.

- Nếu có thể làm an toàn, liên hệ người tin cậy hoặc hỗ trợ khẩn cấp phù hợp tại nơi bạn đang ở; tránh đối đầu.

> Hiện tại tôi bị dọa lấy nội tạng.

> dọa lấy nội tạng

- Bạn có thể đọc và trả lời ở đây một cách an toàn không? Bạn có thể bỏ qua câu hỏi này.

## no-organ-inference

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Một người đi nước ngoài rồi mất liên lạc.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## payment-update

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Hôm qua chưa nhận tiền. Hôm nay tôi đã kiểm tra và nhận đủ. Anh giao máy nhé.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> nhận

> Hôm qua chưa nhận tiền.

> tiền

> chưa

> Hôm qua

> Hôm nay tôi đã kiểm tra và nhận đủ.

> đủ

> Hôm nay

> giao

> Anh giao máy nhé.

> máy nhé


## payment-conflict

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi đã nhận đủ tiền nhưng tôi chưa nhận tiền.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## two-transactions

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Đơn A chưa nhận tiền. Đơn B giao máy nhé.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## url-unverified

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Mở liên kết https://example.invalid để kiểm tra.",
      "scope_id": "case"
    }
  ],
  "context_facts": []
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

## family-user-report

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "user",
      "text": "Tôi là người quen của bạn.",
      "scope_id": "case"
    }
  ],
  "context_facts": [
    {
      "id": "family-user",
      "text": "Người gửi là anh trai tôi, đây là thông tin tôi cung cấp.",
      "applies_to_message_ids": [
        "m1"
      ]
    }
  ]
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Tôi là người quen của bạn.

> Tôi là người quen

> Tôi là

> người quen của bạn

> là người quen

> của bạn


## warning-child-ocr

```json
{
  "messages": [
    {
      "id": "post",
      "speaker_id": "author",
      "text": "Cảnh báo lời dụ bên dưới.",
      "content_type": "post"
    },
    {
      "id": "child",
      "speaker_id": "other",
      "text": "Gửi mã OTP cho tôi.",
      "content_type": "ocr",
      "parent_message_id": "post"
    }
  ]
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> Gửi

> Gửi mã OTP cho tôi.

> mã OTP cho tôi


## warning-child-comment

```json
{
  "messages": [
    {
      "id": "post",
      "speaker_id": "author",
      "text": "Cảnh báo lời dụ bên dưới.",
      "content_type": "post"
    },
    {
      "id": "child",
      "speaker_id": "other",
      "text": "Gửi mã OTP cho tôi.",
      "content_type": "comment",
      "parent_message_id": "post"
    }
  ]
}
```

Nội dung yêu cầu giao thông tin xác thực cho người khác; có nguy cơ mất quyền truy cập tài khoản.

- Không gửi mã hoặc mật khẩu; tự kiểm tra yêu cầu bằng kênh chính thức quen dùng.

> Gửi

> Gửi mã OTP cho tôi.

> mã OTP cho tôi


## legacy-SS-001

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "sender",
      "text": "Chị tuyển người đánh giá sản phẩm, làm thử miễn phí.",
      "scope_id": "SS-001"
    },
    {
      "id": "m2",
      "speaker_id": "sender",
      "text": "Đơn sau em ứng 500.000 đồng, xong sẽ hoàn gốc và hoa hồng.",
      "scope_id": "SS-001"
    },
    {
      "id": "m3",
      "speaker_id": "sender",
      "text": "Muốn rút số dư em chuyển thêm 2 triệu để mở khóa, trong 15 phút nhé.",
      "scope_id": "SS-001"
    }
  ]
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Bạn có biết người mời ngoài đời hoặc có thể xác minh công việc, địa điểm qua đầu mối độc lập không?
- Họ có yêu cầu giữ bí mật, giao giấy tờ hoặc hạn chế liên lạc không?

## legacy-SS-002

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "sender",
      "text": "Cảnh giác với tin nhắn “ứng tiền làm nhiệm vụ để nhận hoa hồng”. Nếu gặp hãy báo quản trị viên.",
      "scope_id": "SS-002"
    }
  ]
}
```

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

- Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

> ứng

> Cảnh giác với tin nhắn “ứng tiền làm nhiệm vụ để nhận hoa hồng”.

> tiền làm nhiệm vụ để nhận hoa hồng


## legacy-SS-003

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker_id": "sender",
      "text": "Lệnh rút bị treo. Em đợi chị kiểm tra nhé.",
      "scope_id": "SS-003"
    }
  ]
}
```

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

- Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

- Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.
