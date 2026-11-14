# Kết quả chạy đúng 10 trường hợp người dùng cung cấp

Đây là phản hồi thực của POST /api/analyze qua ASGI TestClient và provider cấu hình thật. Không dùng nhãn mục tiêu, không sửa prompt/quy tắc trong lượt chạy, không thay kết quả bằng nhận định thủ công. Phần “Nhận xét rà soát” là đối chiếu riêng với đầu vào.

| Ca | Tình huống | Kết quả cuối | Giây |
| --- | --- | --- | --- |
| U01 | Biên lai và yêu cầu giao laptop trước khi thấy tiền | 🔵 need_context | 58.22 |
| U02 | Nhắc mọi người cảnh giác lời dụ giao OTP | 🟢 clear | 14.71 |
| U03 | Hoàn cọc sau một bước chưa có hướng dẫn | 🔵 need_context | 16.57 |
| U04 | Chia sẻ màn hình ngân hàng để duyệt hoàn cọc | Chưa kiểm tra được | 19.59 |
| U05 | Đổi tài khoản nhận hóa đơn và trì hoãn xác minh | 🔵 need_context | 26.77 |
| U06 | Giao laptop khi người bán đã tự kiểm tra đủ tiền | Chưa kiểm tra được | 4.81 |
| U07 | Sáu số được xác nhận là mã đăng nhập | Chưa kiểm tra được | 11.68 |
| U08 | Lệnh rút chờ kiểm tra, chưa có bước tiếp theo | 🔵 need_context | 16.96 |
| U09 | Tự nhận hỗ trợ phường, xin căn cước và chân dung | 🔴 high | 33.99 |
| U10 | Hoa hồng mồi rồi nộp thêm tiền mở khóa | 🔴 high | 20.68 |

## U01 — Biên lai và yêu cầu giao laptop trước khi thấy tiền

**Đầu vào:**

> Mình đã gửi ảnh biên lai mua laptop. Bạn nói vẫn chưa thấy tiền vào tài khoản, nhưng tài xế đang chờ. Bạn giao máy cho tài xế trước nhé, lát nữa kiểm tra lại.

**Kết quả API:** 🔵 need_context

**Nhận xét rà soát:** Nội dung nêu chưa thấy tiền nhưng yêu cầu giao tài sản trước, kèm sức ép tài xế chờ. Đây là dấu hiệu cần được rà kỹ về khả năng mất hàng. Chỉ có lời nhắn nhắc ảnh biên lai, không có ảnh thực để OCR hoặc xác minh giao dịch.

**Tóm tắt backend:** Cần thêm bối cảnh hoặc giải quyết bất đồng trước khi kết luận.

**Trích dẫn đã giữ trong kết quả:**
- “Bạn giao máy cho tài xế trước nhé, lát nữa kiểm tra lại.”

**Câu hỏi thực tế hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?

Kiểm tra: 1/1 quote khớp; quan hệ rủi ro được giữ: 0; xung đột quan sát: 0; hint regex đã rà: 0.

**Các lần chạy:** lần 1: HTTP 200, need_context, 58.22s

## U02 — Nhắc mọi người cảnh giác lời dụ giao OTP

**Đầu vào:**

> Nhắc mọi người: nếu có ai nhắn “gửi mã OTP để nhận hoàn tiền”, đừng làm theo. Hãy tự mở ứng dụng chính thức để kiểm tra giao dịch.

**Kết quả API:** 🟢 clear

**Nhận xét rà soát:** Câu giao OTP nằm trong lời nhắc phòng tránh có “đừng làm theo”. Cần phân biệt lời trích cảnh báo với yêu cầu trực tiếp.

**Tóm tắt backend:** Chưa ghi nhận dấu hiệu đáng ngờ trong nội dung và bối cảnh bạn cung cấp; danh tính chưa được xác minh.

**Trích dẫn đã giữ trong kết quả:**
- “Nhắc mọi người: nếu có ai nhắn “gửi mã OTP để nhận hoàn tiền”, đừng làm theo. Hãy tự mở ứng dụng chính thức để kiểm tra giao dịch.”

Kiểm tra: 1/1 quote khớp; quan hệ rủi ro được giữ: 0; xung đột quan sát: 0; hint regex đã rà: 2.

**Các lần chạy:** lần 1: HTTP 200, clear, 14.71s

## U03 — Hoàn cọc sau một bước chưa có hướng dẫn

**Đầu vào:**

> Bên mình sẽ trả lại tiền cọc sau khi hoàn tất một bước xác nhận. Chiều nay mình gửi hướng dẫn cụ thể.

**Kết quả API:** 🔵 need_context

**Nhận xét rà soát:** Có nói hoàn cọc sau một bước nhưng chưa nêu thao tác cụ thể. Không được tự suy bước đó là chuyển tiền hoặc giao mã.

**Tóm tắt backend:** Cần thêm bối cảnh hoặc giải quyết bất đồng trước khi kết luận.

**Trích dẫn đã giữ trong kết quả:**
- “Bên mình sẽ trả lại tiền cọc sau khi hoàn tất một bước xác nhận.”
- “Chiều nay mình gửi hướng dẫn cụ thể.”

**Câu hỏi thực tế hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?

Kiểm tra: 2/2 quote khớp; quan hệ rủi ro được giữ: 0; xung đột quan sát: 0; hint regex đã rà: 0.

**Các lần chạy:** lần 1: HTTP 200, need_context, 16.57s

## U04 — Chia sẻ màn hình ngân hàng để duyệt hoàn cọc

**Đầu vào:**

> Người gửi: Bấm chia sẻ màn hình để bên mình duyệt hoàn cọc nhé.
> Người nhận: Sau khi chia sẻ thì mình cần làm gì?
> Người gửi: Mở ứng dụng ngân hàng và vào phần số dư để bên mình xem.

**Kết quả API:** PROVIDER_UNAVAILABLE

**Nhận xét rà soát:** Yêu cầu chia sẻ màn hình và mở phần số dư ngân hàng liên quan dữ liệu tài chính; đọc cùng lời duyệt hoàn cọc và đúng người nói. Chưa có căn cứ nói đã có chuyển tiền hoặc chiếm quyền thực tế.

API lỗi; không có risk_status để coi là clear hoặc need_context.

**Các lần chạy:** lần 1: HTTP 502, EVIDENCE_INVALID, 9.59s, lần 2: HTTP 503, PROVIDER_UNAVAILABLE, 19.59s

## U05 — Đổi tài khoản nhận hóa đơn và trì hoãn xác minh

**Đầu vào:**

> Hóa đơn tháng này vẫn như cũ, nhưng bên mình đổi tài khoản nhận tiền. Bạn chuyển theo thông tin gửi riêng trong chat trước, ngày mai hãy gọi đầu mối trong hợp đồng để đối chiếu.

**Kết quả API:** 🔵 need_context

**Nhận xét rà soát:** Có thay đổi tài khoản nhận tiền qua chat và yêu cầu chuyển trước khi gọi đầu mối hợp đồng. Cần xét việc trì hoãn xác minh, không chỉ riêng từ khóa chuyển khoản.

**Tóm tắt backend:** Cần thêm bối cảnh hoặc giải quyết bất đồng trước khi kết luận.

**Trích dẫn đã giữ trong kết quả:**
- “bên mình đổi tài khoản nhận tiền. Bạn chuyển theo thông tin gửi riêng trong chat trước”
- “ngày mai hãy gọi đầu mối trong hợp đồng để đối chiếu.”

**Câu hỏi thực tế hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Kiểm tra: 2/2 quote khớp; quan hệ rủi ro được giữ: 0; xung đột quan sát: 0; hint regex đã rà: 0.

**Các lần chạy:** lần 1: HTTP 200, need_context, 26.77s

## U06 — Giao laptop khi người bán đã tự kiểm tra đủ tiền

**Đầu vào:**

> Người mua: Tài xế mình đặt đã tới. Bạn giao laptop cho anh ấy nhé.
> Người bán: Mình vừa kiểm tra ứng dụng ngân hàng, khoản tiền mua laptop đã vào đúng tài khoản và đủ số tiền rồi.

**Kết quả API:** EVIDENCE_INVALID

**Nhận xét rà soát:** Người bán nói đã tự kiểm tra đúng tài khoản và đủ tiền. Đây là bối cảnh khác ca U01; hệ thống chỉ nhận lời khai trong hội thoại, không kết nối ngân hàng để xác minh tiền thật.

API lỗi; không có risk_status để coi là clear hoặc need_context.

**Các lần chạy:** lần 1: HTTP 503, PROVIDER_UNAVAILABLE, 11.59s, lần 2: HTTP 502, EVIDENCE_INVALID, 4.81s

## U07 — Sáu số được xác nhận là mã đăng nhập

**Đầu vào:**

> Người gửi: Đọc giúp mình sáu số vừa hiện trên máy để khoản tiền bán hàng được giải ngân.
> Người nhận: Thông báo ghi đây là mã dùng để đăng nhập tài khoản của tôi.
> Người gửi: Đúng dãy đó, đọc cho mình để xử lý tiếp nhé.

**Kết quả API:** EVIDENCE_INVALID

**Nhận xét rà soát:** Người nhận xác định dãy số là mã đăng nhập tài khoản của mình; người gửi vẫn yêu cầu đọc mã để giải ngân. Cần nối ba tin và không nhầm với tự nhập mã trong ứng dụng.

API lỗi; không có risk_status để coi là clear hoặc need_context.

**Các lần chạy:** lần 1: HTTP 502, EVIDENCE_INVALID, 8.69s, lần 2: HTTP 502, EVIDENCE_INVALID, 11.68s

## U08 — Lệnh rút chờ kiểm tra, chưa có bước tiếp theo

**Đầu vào:**

> Lệnh rút tiền của bạn đang chờ kiểm tra bổ sung. Hiện chưa có thông báo về bước tiếp theo.

**Kết quả API:** 🔵 need_context

**Nhận xét rà soát:** Chỉ có trạng thái chờ kiểm tra, chưa có yêu cầu hành động. Không có căn cứ tự tạo phí bổ sung hoặc yêu cầu OTP.

**Tóm tắt backend:** Cần thêm bối cảnh hoặc giải quyết bất đồng trước khi kết luận.

**Trích dẫn đã giữ trong kết quả:**
- “Lệnh rút tiền của bạn đang chờ kiểm tra bổ sung. Hiện chưa có thông báo về bước tiếp theo.”

**Câu hỏi thực tế hệ thống trả:**
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Kiểm tra: 1/1 quote khớp; quan hệ rủi ro được giữ: 0; xung đột quan sát: 0; hint regex đã rà: 0.

**Các lần chạy:** lần 1: HTTP 503, PROVIDER_UNAVAILABLE, 9.88s, lần 2: HTTP 200, need_context, 16.96s

## U09 — Tự nhận hỗ trợ phường, xin căn cước và chân dung

**Đầu vào:**

> Mình phụ trách đợt hỗ trợ của phường. Để giữ suất, bạn gửi ảnh hai mặt căn cước và ảnh chân dung vào cuộc trò chuyện này nhé.

**Kết quả API:** 🔴 high

**Nhận xét rà soát:** Tự nhận phụ trách hỗ trợ phường không xác minh được danh tính. Xin hai mặt căn cước và chân dung qua chat để giữ suất có rủi ro lộ dữ liệu định danh.

**Tóm tắt backend:** Có yêu cầu có thể gây hại dựa trên bằng chứng đã đối chiếu; cần xác minh độc lập.

**Trích dẫn đã giữ trong kết quả:**
- “bạn gửi ảnh hai mặt căn cước và ảnh chân dung vào cuộc trò chuyện này nhé.”
- “Để giữ suất, bạn gửi ảnh hai mặt căn cước và ảnh chân dung vào cuộc trò chuyện này nhé.”

**Câu hỏi thực tế hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

Kiểm tra: 2/2 quote khớp; quan hệ rủi ro được giữ: 1; xung đột quan sát: 0; hint regex đã rà: 0.

**Các lần chạy:** lần 1: HTTP 503, PROVIDER_UNAVAILABLE, 14.98s, lần 2: HTTP 200, high, 33.99s

## U10 — Hoa hồng mồi rồi nộp thêm tiền mở khóa

**Đầu vào:**

> Đơn thử đầu tiên bạn đã nhận được hoa hồng. Đơn tiếp theo cần bạn ứng 500.000 đồng. Nếu muốn rút cả tiền gốc và hoa hồng, bạn chuyển thêm 2 triệu để mở khóa số dư.

**Kết quả API:** 🔴 high

**Nhận xét rà soát:** Nội dung chuyển từ hoa hồng ban đầu sang ứng tiền và nộp thêm để mở khóa. Cần nối quan hệ nộp tiền trước với khả năng rút tiền được hứa.

**Tóm tắt backend:** Có yêu cầu có thể gây hại dựa trên bằng chứng đã đối chiếu; cần xác minh độc lập.

**Trích dẫn đã giữ trong kết quả:**
- “Đơn tiếp theo cần bạn ứng 500.000 đồng.”
- “Nếu muốn rút cả tiền gốc và hoa hồng, bạn chuyển thêm 2 triệu để mở khóa số dư.”
- “Đơn thử đầu tiên bạn đã nhận được hoa hồng.”

Kiểm tra: 4/4 quote khớp; quan hệ rủi ro được giữ: 1; xung đột quan sát: 0; hint regex đã rà: 5.

**Các lần chạy:** lần 1: HTTP 200, high, 20.68s

## Phạm vi và số liệu

{
  "planned": 10,
  "api_executions": 15,
  "cases_executed": 10,
  "first_successful": 5,
  "final_successful": 7,
  "final_errors": 3,
  "not_run": 0,
  "distribution": {
    "need_context": 4,
    "clear": 1,
    "high": 2
  },
  "p50_ms": 20680.30639999779,
  "p95_ms": 58220.306999995955,
  "batch_wall_ms": 308796.02680000244,
  "hashes_verified": true,
  "accuracy": "Not scored: no expected labels; results are actual system outputs, not manual replacements."
}

Không đo thời gian từ lúc bấm gửi ở trình duyệt/extension. Không có ảnh biên lai hoặc ảnh căn cước thực; không chạy OCR trên các câu nhắc đến ảnh. Quote khớp không tự chứng minh đúng ý nghĩa. Các thông tin người nói tự khai không được xác nhận ngoài đời. Không tính độ chính xác vì không có bộ nhãn độc lập.

Lệnh đã chạy: `python run_user_ten_cases.py`; xuất báo cáo: `python summarize_user_ten_cases.py`. Output không ghi đè; đổi OUT nếu cần một lượt chạy mới.