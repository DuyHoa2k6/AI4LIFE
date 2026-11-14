# 24 ca kiểm thử bốn trạng thái

Cột API mô phỏng kiểm tra quyết định backend, không đo model. Live chỉ lấy các phiên bản cuối; lỗi/chưa chạy giữ nguyên. Chi tiết phiên bản và giới hạn trong README.

| Ca | Kỳ vọng | API mô phỏng | Live bản cuối |
|---|---|---|---|
| U01 | suspicious | suspicious | focused: lỗi HTTP 503 |
| U02 | clear | clear | chưa gửi ở bản cuối |
| U03 | need_context | need_context | focused: lỗi HTTP 503 |
| U04 | high | high | focused: lỗi HTTP 503 |
| U05 | suspicious | suspicious | focused: lỗi HTTP 503 |
| U06 | clear | clear | focused: lỗi HTTP 503 |
| U07 | high | high | chưa gửi ở bản cuối |
| U08 | need_context | need_context | chưa gửi ở bản cuối |
| U09 | suspicious | suspicious | chưa gửi ở bản cuối |
| U10 | high | high | chưa gửi ở bản cuối |
| F01 | clear | clear | followup_live: clear |
| F02 | clear | clear | followup_live: lỗi HTTP 503 |
| F03 | clear | clear | followup_live: lỗi HTTP 503 |
| F04 | clear | clear | followup_live: lỗi HTTP 503 |
| F05 | need_context | need_context | followup_stratified_live: need_context |
| F06 | need_context | need_context | followup_remaining_live: need_context |
| F07 | need_context | need_context | followup_remaining_live: lỗi HTTP 503 |
| F08 | need_context | need_context | followup_remaining_live: lỗi HTTP 503 |
| F09 | suspicious | suspicious | followup_stratified_live: suspicious |
| F10 | suspicious | suspicious | followup_remaining_live: lỗi HTTP 502 |
| F11 | suspicious | suspicious | chưa gửi ở bản cuối |
| F12 | high | high | followup_stratified_live: high |
| F13 | high | high | chưa gửi ở bản cuối |
| F14 | high | high | chưa gửi ở bản cuối |

## U01 — Biên lai và yêu cầu giao laptop trước khi thấy tiền

```json
{
  "text": "Mình đã gửi ảnh biên lai mua laptop. Bạn nói vẫn chưa thấy tiền vào tài khoản, nhưng tài xế đang chờ. Bạn giao máy cho tài xế trước nhé, lát nữa kiểm tra lại."
}
```

**Điều cần nhận ra:** Biên lai và yêu cầu giao laptop trước khi thấy tiền

**API mô phỏng:** suspicious. Người gửi yêu cầu giao tài sản khi khoản thanh toán chưa được xác nhận. Có dấu hiệu cần xác minh trước khi giao.

**Nên làm:** Tự kiểm tra tiền thực nhận trong ứng dụng ngân hàng trước khi giao tài sản; không dựa riêng vào ảnh biên lai.

**Hỏi bổ sung:** Bạn có thể xác nhận người gửi qua đầu mối quen dùng hoặc kênh chính thức độc lập nào?

**Giải thích:** Có yêu cầu giao tài sản trước khi khoản thanh toán được xác nhận; chưa đủ căn cứ kết luận biên lai giả.
- m1: “Bạn giao máy cho tài xế trước nhé, lát nữa kiểm tra lại.”
- m1: “Bạn nói vẫn chưa thấy tiền vào tài khoản, nhưng tài xế đang chờ.”

## U02 — Nhắc mọi người cảnh giác lời dụ giao OTP

```json
{
  "text": "Nhắc mọi người: nếu có ai nhắn “gửi mã OTP để nhận hoàn tiền”, đừng làm theo. Hãy tự mở ứng dụng chính thức để kiểm tra giao dịch."
}
```

**Điều cần nhận ra:** Nhắc mọi người cảnh giác lời dụ giao OTP

**API mô phỏng:** clear. Chưa ghi nhận dấu hiệu đáng ngờ trong phần nội dung đã kiểm tra.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

## U03 — Hoàn cọc sau một bước chưa có hướng dẫn

```json
{
  "text": "Bên mình sẽ trả lại tiền cọc sau khi hoàn tất một bước xác nhận. Chiều nay mình gửi hướng dẫn cụ thể."
}
```

**Điều cần nhận ra:** Hoàn cọc sau một bước chưa có hướng dẫn

**API mô phỏng:** need_context. Chưa biết bước xác nhận hoặc xử lý tiếp yêu cầu làm gì. Cần làm rõ thao tác trước khi đánh giá.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

**Hỏi bổ sung:** Bước xác nhận hoặc xử lý tiếp yêu cầu bạn thực hiện thao tác cụ thể gì? Hãy chép nguyên văn, không gửi mã hoặc mật khẩu thật.

**Hỏi bổ sung:** Bạn có thể xác nhận người gửi qua đầu mối quen dùng hoặc kênh chính thức độc lập nào?

## U04 — Chia sẻ màn hình ngân hàng để duyệt hoàn cọc

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Người gửi",
      "text": "Bấm chia sẻ màn hình để bên mình duyệt hoàn cọc nhé."
    },
    {
      "id": "m2",
      "speaker": "Người nhận",
      "text": "Sau khi chia sẻ thì mình cần làm gì?"
    },
    {
      "id": "m3",
      "speaker": "Người gửi",
      "text": "Mở ứng dụng ngân hàng và vào phần số dư để bên mình xem."
    }
  ]
}
```

**Điều cần nhận ra:** Chia sẻ màn hình ngân hàng để duyệt hoàn cọc

**API mô phỏng:** high. Người gửi yêu cầu chia sẻ màn hình rồi mở thông tin ngân hàng. Chuỗi thao tác này có nguy cơ làm lộ dữ liệu tài chính.

**Nên làm:** Dừng chia sẻ màn hình trước khi mở ứng dụng ngân hàng và xác minh yêu cầu qua kênh chính thức.

**Giải thích:** Yêu cầu chia sẻ màn hình đi cùng việc mở thông tin ngân hàng có thể làm lộ dữ liệu tài chính.
- m1: “Bấm chia sẻ màn hình để bên mình duyệt hoàn cọc nhé.”
- m3: “Mở ứng dụng ngân hàng và vào phần số dư để bên mình xem.”

## U05 — Đổi tài khoản nhận hóa đơn và trì hoãn xác minh

```json
{
  "text": "Hóa đơn tháng này vẫn như cũ, nhưng bên mình đổi tài khoản nhận tiền. Bạn chuyển theo thông tin gửi riêng trong chat trước, ngày mai hãy gọi đầu mối trong hợp đồng để đối chiếu."
}
```

**Điều cần nhận ra:** Đổi tài khoản nhận hóa đơn và trì hoãn xác minh

**API mô phỏng:** suspicious. Người gửi đổi tài khoản nhận tiền và yêu cầu chuyển trước, đối chiếu sau. Cần xác minh thay đổi trước khi thanh toán.

**Nên làm:** Gọi đầu mối trong hợp đồng hoặc số đã biết để xác nhận tài khoản mới trước khi chuyển tiền.

**Hỏi bổ sung:** Bạn có thể xác nhận người gửi qua đầu mối quen dùng hoặc kênh chính thức độc lập nào?

**Giải thích:** Tài khoản nhận tiền bị thay đổi và người gửi muốn thanh toán trước khi đối chiếu với đầu mối đã biết.
- m1: “bên mình đổi tài khoản nhận tiền. Bạn chuyển theo thông tin gửi riêng trong chat trước”
- m1: “ngày mai hãy gọi đầu mối trong hợp đồng để đối chiếu.”

## U06 — Giao laptop khi người bán đã tự kiểm tra đủ tiền

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Người mua",
      "text": "Tài xế mình đặt đã tới. Bạn giao laptop cho anh ấy nhé."
    },
    {
      "id": "m2",
      "speaker": "Người bán",
      "text": "Mình vừa kiểm tra ứng dụng ngân hàng, khoản tiền mua laptop đã vào đúng tài khoản và đủ số tiền rồi."
    }
  ]
}
```

**Điều cần nhận ra:** Giao laptop khi người bán đã tự kiểm tra đủ tiền

**API mô phỏng:** clear. Người nhận tiền cho biết đã kiểm tra và nhận đủ tiền trước khi giao tài sản. Chưa ghi nhận dấu hiệu đáng ngờ trong đoạn hội thoại này.

**Nên làm:** Chỉ giao đúng tài sản và đúng người nhận theo thỏa thuận; kiểm tra lại nếu có thay đổi.

**Giải thích:** Người nhận tiền cho biết đã tự kiểm tra và nhận đủ tiền; đây là bối cảnh trong hội thoại, không phải xác minh ngân hàng của hệ thống.
- m1: “Tài xế mình đặt đã tới. Bạn giao laptop cho anh ấy nhé.”
- m2: “Mình vừa kiểm tra ứng dụng ngân hàng, khoản tiền mua laptop đã vào đúng tài khoản và đủ số tiền rồi.”

## U07 — Sáu số được xác nhận là mã đăng nhập

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Người gửi",
      "text": "Đọc giúp mình sáu số vừa hiện trên máy để khoản tiền bán hàng được giải ngân."
    },
    {
      "id": "m2",
      "speaker": "Người nhận",
      "text": "Thông báo ghi đây là mã dùng để đăng nhập tài khoản của tôi."
    },
    {
      "id": "m3",
      "speaker": "Người gửi",
      "text": "Đúng dãy đó, đọc cho mình để xử lý tiếp nhé."
    }
  ]
}
```

**Điều cần nhận ra:** Sáu số được xác nhận là mã đăng nhập

**API mô phỏng:** high. Người gửi yêu cầu đọc một dãy số được xác định là mã đăng nhập tài khoản. Việc giao mã có thể khiến tài khoản bị truy cập trái phép.

**Nên làm:** Không đọc mã đăng nhập cho người khác; tự kiểm tra giao dịch trên ứng dụng hoặc kênh chính thức.

**Giải thích:** Dãy số được xác định trong hội thoại là mã đăng nhập, nhưng người gửi vẫn yêu cầu cung cấp mã đó.
- m1: “Đọc giúp mình sáu số vừa hiện trên máy để khoản tiền bán hàng được giải ngân.”
- m2: “Thông báo ghi đây là mã dùng để đăng nhập tài khoản của tôi.”

## U08 — Lệnh rút chờ kiểm tra, chưa có bước tiếp theo

```json
{
  "text": "Lệnh rút tiền của bạn đang chờ kiểm tra bổ sung. Hiện chưa có thông báo về bước tiếp theo."
}
```

**Điều cần nhận ra:** Lệnh rút chờ kiểm tra, chưa có bước tiếp theo

**API mô phỏng:** need_context. Nội dung mới thông báo lệnh rút đang chờ kiểm tra, chưa nêu bước tiếp theo. Chưa có căn cứ nói người gửi yêu cầu nộp phí hoặc giao mã.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

**Hỏi bổ sung:** Để tiếp tục rút tiền, họ có yêu cầu chuyển tiền hoặc cung cấp thông tin gì không? Nếu chưa có hướng dẫn, hãy cho biết điều đó.

## U09 — Tự nhận hỗ trợ phường, xin căn cước và chân dung

```json
{
  "text": "Mình phụ trách đợt hỗ trợ của phường. Để giữ suất, bạn gửi ảnh hai mặt căn cước và ảnh chân dung vào cuộc trò chuyện này nhé."
}
```

**Điều cần nhận ra:** Tự nhận hỗ trợ phường, xin căn cước và chân dung

**API mô phỏng:** suspicious. Người gửi yêu cầu cung cấp giấy tờ định danh và ảnh qua chat. Cần xác minh đơn vị tiếp nhận và mục đích trước khi gửi.

**Nên làm:** Xác minh yêu cầu qua kênh chính thức của đơn vị được nhắc đến, trước khi gửi ảnh giấy tờ qua chat.

**Giải thích:** Người gửi yêu cầu giấy tờ định danh hoặc ảnh chân dung qua cuộc trò chuyện; cần xác minh kênh thu thập và mục đích.
- m1: “bạn gửi ảnh hai mặt căn cước và ảnh chân dung vào cuộc trò chuyện này nhé.”

## U10 — Hoa hồng mồi rồi nộp thêm tiền mở khóa

```json
{
  "text": "Đơn thử đầu tiên bạn đã nhận được hoa hồng. Đơn tiếp theo cần bạn ứng 500.000 đồng. Nếu muốn rút cả tiền gốc và hoa hồng, bạn chuyển thêm 2 triệu để mở khóa số dư."
}
```

**Điều cần nhận ra:** Hoa hồng mồi rồi nộp thêm tiền mở khóa

**API mô phỏng:** high. Có yêu cầu có thể gây hại dựa trên bằng chứng trong nội dung.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

## F01 — Tự nhập mã trên ứng dụng

```json
{
  "text": "Tôi tự mở ứng dụng chính thức và nhập mã xác thực trên điện thoại của mình. Tôi không gửi mã cho ai."
}
```

**Điều cần nhận ra:** Tự thao tác, phủ định việc giao mã cho người khác.

**API mô phỏng:** clear. Chưa ghi nhận dấu hiệu đáng ngờ trong phần nội dung đã kiểm tra.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

## F02 — Giao loa sau khi tự kiểm tra tiền

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Khách mua",
      "text": "Người vận chuyển đã đến, bạn bàn giao bộ loa giúp tôi."
    },
    {
      "id": "m2",
      "speaker": "Chủ hàng",
      "text": "Tôi vừa tự xem ứng dụng ngân hàng: tiền mua bộ loa đã vào đúng tài khoản, đủ số tiền."
    }
  ]
}
```

**Điều cần nhận ra:** Người nhận tiền tự báo đã kiểm tra; không phải lời khẳng định của người mua.

**API mô phỏng:** clear. Người nhận tiền cho biết đã kiểm tra và nhận đủ tiền trước khi giao tài sản. Chưa ghi nhận dấu hiệu đáng ngờ trong đoạn hội thoại này.

**Nên làm:** Chỉ giao đúng tài sản và đúng người nhận theo thỏa thuận; kiểm tra lại nếu có thay đổi.

**Giải thích:** Người nhận tiền cho biết đã tự kiểm tra và nhận đủ tiền; đây là bối cảnh trong hội thoại, không phải xác minh ngân hàng của hệ thống.
- m1: “Người vận chuyển đã đến, bạn bàn giao bộ loa giúp tôi.”
- m2: “Tôi vừa tự xem ứng dụng ngân hàng: tiền mua bộ loa đã vào đúng tài khoản, đủ số tiền.”

## F03 — Bài cảnh báo thu giấy tờ

```json
{
  "text": "Lưu ý: có người giả danh ban học bổng nhắn “gửi căn cước hai mặt và ảnh chân dung qua chat để giữ suất”. Đừng gửi theo lời nhắn đó; tự hỏi nhà trường qua kênh chính thức."
}
```

**Điều cần nhận ra:** Lời dụ nằm trong bài cảnh báo, không phải yêu cầu trực tiếp.

**API mô phỏng:** clear. Chưa ghi nhận dấu hiệu đáng ngờ trong phần nội dung đã kiểm tra.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

## F04 — Khoản vay có đối chiếu trong hội thoại

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Chủ nợ",
      "text": "Bạn chuyển trả khoản vay tuần trước giúp tôi nhé."
    },
    {
      "id": "m2",
      "speaker": "Người vay",
      "text": "Đúng khoản tôi đã vay. Tôi vừa gọi số quen của bạn để đối chiếu số tiền và tài khoản, đều đúng thỏa thuận."
    }
  ]
}
```

**Điều cần nhận ra:** Bối cảnh trong messages giải thích riêng khoản thanh toán này.

**API mô phỏng:** clear. Người được yêu cầu thanh toán cho biết đã đối chiếu giao dịch và mục đích. Chưa ghi nhận dấu hiệu đáng ngờ trong phần nội dung này.

**Nên làm:** Đối chiếu lại số tiền và người nhận đã thống nhất; xác minh độc lập nếu có thay đổi mới.

**Giải thích:** Người được yêu cầu thanh toán cho biết đã đối chiếu mục đích hoặc giao dịch; bối cảnh này chỉ hỗ trợ yêu cầu thanh toán tương ứng.
- m1: “Bạn chuyển trả khoản vay tuần trước giúp tôi nhé.”
- m2: “Đúng khoản tôi đã vay. Tôi vừa gọi số quen của bạn để đối chiếu số tiền và tài khoản, đều đúng thỏa thuận.”

## F05 — Đối tượng chưa rõ

```json
{
  "text": "Bạn gửi lại cái đó qua đây để bên mình xử lý tiếp nhé."
}
```

**Điều cần nhận ra:** Hỏi “cái đó” là loại thông tin hoặc đối tượng gì, không tự đoán là OTP.

**API mô phỏng:** need_context. Chưa rõ thao tác hoặc thông tin quan trọng để đánh giá tiếp.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

**Hỏi bổ sung:** Thông tin hoặc “cái đó” được yêu cầu gửi là gì? Chỉ mô tả loại thông tin, không gửi mã hoặc mật khẩu thật.

## F06 — Chờ xét lệnh rút

```json
{
  "text": "Yêu cầu rút số dư đang được bộ phận kiểm tra xem xét. Khi có hướng dẫn tiếp theo, chúng tôi sẽ thông báo."
}
```

**Điều cần nhận ra:** Chưa có yêu cầu chuyển tiền hay giao thông tin; hỏi bước tiếp theo.

**API mô phỏng:** need_context. Nội dung mới thông báo lệnh rút đang chờ kiểm tra, chưa nêu bước tiếp theo. Chưa có căn cứ nói người gửi yêu cầu nộp phí hoặc giao mã.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

**Hỏi bổ sung:** Để tiếp tục rút tiền, họ có yêu cầu chuyển tiền hoặc cung cấp thông tin gì không? Nếu chưa có hướng dẫn, hãy cho biết điều đó.

## F07 — Thủ tục hoàn cọc chưa mô tả

```json
{
  "text": "Để nhận lại tiền đặt chỗ, bạn cần hoàn tất thủ tục Z. Mình chưa gửi mô tả thủ tục đó, mai mình báo."
}
```

**Điều cần nhận ra:** Hỏi thao tác cụ thể trong thủ tục, không tự thêm phí hay mã.

**API mô phỏng:** need_context. Chưa biết bước xác nhận hoặc xử lý tiếp yêu cầu làm gì. Cần làm rõ thao tác trước khi đánh giá.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

**Hỏi bổ sung:** Bước xác nhận hoặc xử lý tiếp yêu cầu bạn thực hiện thao tác cụ thể gì? Hãy chép nguyên văn, không gửi mã hoặc mật khẩu thật.

## F08 — Chuyển phần còn lại chưa rõ mục đích

```json
{
  "text": "Bạn chuyển nốt phần còn lại cho mình nhé."
}
```

**Điều cần nhận ra:** Chưa rõ là khoản nợ, mua bán hay tiền để nhận lợi ích.

**API mô phỏng:** need_context. Chưa rõ thao tác hoặc thông tin quan trọng để đánh giá tiếp.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.

**Hỏi bổ sung:** Khoản tiền được yêu cầu dùng để thanh toán việc gì, hay là điều kiện để nhận hoặc rút tiền?

## F09 — Giao loa khi tiền chưa vào

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Khách mua",
      "text": "Người vận chuyển đã đến, bạn bàn giao bộ loa giúp tôi."
    },
    {
      "id": "m2",
      "speaker": "Chủ hàng",
      "text": "Tôi vừa tự xem ứng dụng ngân hàng: tiền mua bộ loa chưa vào tài khoản."
    },
    {
      "id": "m3",
      "speaker": "Khách mua",
      "text": "Tôi có ảnh chuyển tiền rồi, bạn giao bộ loa trước đi, kiểm tra tiền sau."
    }
  ]
}
```

**Điều cần nhận ra:** Đối chứng F02: ảnh chuyển tiền không thay việc người nhận tự kiểm tra.

**API mô phỏng:** suspicious. Người gửi yêu cầu giao tài sản khi khoản thanh toán chưa được xác nhận. Có dấu hiệu cần xác minh trước khi giao.

**Nên làm:** Tự kiểm tra tiền thực nhận trong ứng dụng ngân hàng trước khi giao tài sản; không dựa riêng vào ảnh biên lai.

**Giải thích:** Có yêu cầu giao tài sản trước khi khoản thanh toán được xác nhận; chưa đủ căn cứ kết luận biên lai giả.
- m3: “Tôi có ảnh chuyển tiền rồi, bạn giao bộ loa trước đi, kiểm tra tiền sau.”
- m2: “Tôi vừa tự xem ứng dụng ngân hàng: tiền mua bộ loa chưa vào tài khoản.”

## F10 — Thay tài khoản và hoãn đối chiếu

```json
{
  "text": "Hóa đơn bảo trì giữ nguyên, nhưng tháng này bên mình dùng tài khoản cá nhân mới. Cứ thanh toán theo số tài khoản trong chat ngay hôm nay, tuần tới hãy gọi số trên hợp đồng để đối chiếu."
}
```

**Điều cần nhận ra:** Thay người nhận tiền và yêu cầu thanh toán trước, xác minh sau.

**API mô phỏng:** suspicious. Người gửi đổi tài khoản nhận tiền và yêu cầu chuyển trước, đối chiếu sau. Cần xác minh thay đổi trước khi thanh toán.

**Nên làm:** Gọi đầu mối trong hợp đồng hoặc số đã biết để xác nhận tài khoản mới trước khi chuyển tiền.

**Giải thích:** Tài khoản nhận tiền bị thay đổi và người gửi muốn thanh toán trước khi đối chiếu với đầu mối đã biết.
- m1: “Hóa đơn bảo trì giữ nguyên, nhưng tháng này bên mình dùng tài khoản cá nhân mới. Cứ thanh toán theo số tài khoản trong chat ngay hôm nay, tuần tới hãy gọi số trên hợp đồng để đối chiếu.”
- m1: “Cứ thanh toán theo số tài khoản trong chat ngay hôm nay, tuần tới hãy gọi số trên hợp đồng để đối chiếu.”

## F11 — Giữ suất học bổng bằng giấy tờ qua chat

```json
{
  "text": "Mình là cộng tác viên chương trình học bổng. Muốn giữ suất, bạn gửi ảnh căn cước cả hai mặt cùng ảnh chân dung vào chat riêng này nhé."
}
```

**Điều cần nhận ra:** Thu giấy tờ nhạy cảm qua chat; không mặc định high chỉ vì có lợi ích.

**API mô phỏng:** suspicious. Người gửi yêu cầu cung cấp giấy tờ định danh và ảnh qua chat. Cần xác minh đơn vị tiếp nhận và mục đích trước khi gửi.

**Nên làm:** Xác minh yêu cầu qua kênh chính thức của đơn vị được nhắc đến, trước khi gửi ảnh giấy tờ qua chat.

**Giải thích:** Người gửi yêu cầu giấy tờ định danh hoặc ảnh chân dung qua cuộc trò chuyện; cần xác minh kênh thu thập và mục đích.
- m1: “Mình là cộng tác viên chương trình học bổng. Muốn giữ suất, bạn gửi ảnh căn cước cả hai mặt cùng ảnh chân dung vào chat riêng này nhé.”

## F12 — Mã đăng nhập bị gọi là chuỗi tám ký tự

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Hỗ trợ",
      "text": "Đọc giúp tôi chuỗi tám ký tự vừa hiện để mở khoản tiền đang chờ."
    },
    {
      "id": "m2",
      "speaker": "Người nhận",
      "text": "Thông báo trên máy ghi đó là mã đăng nhập của tài khoản tôi."
    },
    {
      "id": "m3",
      "speaker": "Hỗ trợ",
      "text": "Chính chuỗi đó, đọc cho tôi để làm tiếp."
    }
  ]
}
```

**Điều cần nhận ra:** Nối ý nghĩa mã từ câu người nhận; không cần chữ OTP trong lời yêu cầu.

**API mô phỏng:** high. Người gửi yêu cầu đọc một dãy số được xác định là mã đăng nhập tài khoản. Việc giao mã có thể khiến tài khoản bị truy cập trái phép.

**Nên làm:** Không đọc mã đăng nhập cho người khác; tự kiểm tra giao dịch trên ứng dụng hoặc kênh chính thức.

**Giải thích:** Dãy số được xác định trong hội thoại là mã đăng nhập, nhưng người gửi vẫn yêu cầu cung cấp mã đó.
- m1: “Đọc giúp tôi chuỗi tám ký tự vừa hiện để mở khoản tiền đang chờ.”
- m2: “Thông báo trên máy ghi đó là mã đăng nhập của tài khoản tôi.”

## F13 — Chia sẻ màn hình rồi mở lịch sử ngân hàng

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Hỗ trợ",
      "text": "Bật chia sẻ màn hình để mình kiểm tra hồ sơ hoàn phí."
    },
    {
      "id": "m2",
      "speaker": "Người nhận",
      "text": "Tiếp theo tôi mở mục nào?"
    },
    {
      "id": "m3",
      "speaker": "Hỗ trợ",
      "text": "Giữ chia sẻ và mở ứng dụng ngân hàng vào lịch sử giao dịch cho mình xem."
    }
  ]
}
```

**Điều cần nhận ra:** Hai yêu cầu của cùng người gửi tạo chuỗi lộ dữ liệu tài chính.

**API mô phỏng:** high. Người gửi yêu cầu chia sẻ màn hình rồi mở thông tin ngân hàng. Chuỗi thao tác này có nguy cơ làm lộ dữ liệu tài chính.

**Nên làm:** Dừng chia sẻ màn hình trước khi mở ứng dụng ngân hàng và xác minh yêu cầu qua kênh chính thức.

**Giải thích:** Yêu cầu chia sẻ màn hình đi cùng việc mở thông tin ngân hàng có thể làm lộ dữ liệu tài chính.
- m1: “Bật chia sẻ màn hình để mình kiểm tra hồ sơ hoàn phí.”
- m3: “Giữ chia sẻ và mở ứng dụng ngân hàng vào lịch sử giao dịch cho mình xem.”

## F14 — Tiền đồng bộ để giải phóng số dư

```json
{
  "text": "Số dư của bạn đã hiện nhưng chưa rút được. Muốn giải phóng toàn bộ khoản đó, bạn phải chuyển thêm 700 nghìn tiền đồng bộ trước; không chuyển thì hệ thống tiếp tục giữ tiền."
}
```

**Điều cần nhận ra:** Đổi cách gọi phí nhưng vẫn phải nộp thêm tiền để rút số dư.

**API mô phỏng:** high. Có yêu cầu có thể gây hại dựa trên bằng chứng trong nội dung.

**Nên làm:** Xác minh yêu cầu qua kênh quen dùng hoặc đầu mối chính thức trước khi thực hiện.
