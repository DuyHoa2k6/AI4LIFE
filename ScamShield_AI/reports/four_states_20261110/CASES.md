# Kiểm thử bốn trạng thái — 10/11/2026

16 ca tổng hợp mới, 4 mục tiêu cho mỗi trạng thái. Nhãn tham chiếu được viết riêng trước chạy; không chỉnh prompt/model/quy tắc trong phiên đánh giá. Không đọc holdout hoặc đưa nhãn vào mô hình.

Chạy API qua ASGI TestClient và HTTP Gemini thật, cấu hình/phiên bản/hash ở từng lock.json. Đây là kiểm thử chức năng có chủ đích, không phải độ chính xác độc lập trên dữ liệu người dùng thật.

| Ca | Tình huống | Mục tiêu trước chạy | Kết quả cuối | Giây |
| --- | --- | --- | --- | --- |
| H01 | Giao mã rõ ràng | high | 🔴 Rủi ro cao | 13.98 |
| N01 | Lịch họp bình thường | clear | 🟢 Chưa ghi nhận dấu hiệu | 15.95 |
| C01 | Chưa nói bước xử lý | need_context | 🔵 Cần thêm thông tin | 10.83 |
| S01 | Quyền điều khiển chưa rõ mục đích | suspicious | 🔴 Rủi ro cao — khác mục tiêu | 15.01 |
| H02 | Nộp phí trước khi nhận thưởng | high | 🔴 Rủi ro cao | 24.01 |
| N02 | Đòi khoản vay bằng phương ngữ | clear | 🟢 Chưa ghi nhận dấu hiệu | 15.95 |
| C02 | Chuyển tiền chưa rõ mục đích | need_context | 🔵 Cần thêm thông tin | 7.55 |
| S02 | APK không rõ nhà phát hành | suspicious | 🔵 Cần thêm thông tin — khác mục tiêu | 20.78 |
| H03 | Biến thể tiền đồng bộ | high | 🔴 Rủi ro cao | 17.58 |
| N03 | Bài cảnh báo trích lời dụ | clear | 🟢 Chưa ghi nhận dấu hiệu | 16.92 |
| C03 | Đối tượng thao tác chưa xác định | need_context | 🔵 Cần thêm thông tin | 13.89 |
| S03 | Nhãn liên kết khác đích | suspicious | 🟠 Đáng ngờ | 18.59 |
| H04 | Chuỗi hành vi qua nhiều tin | high | Chưa kiểm tra được — khác mục tiêu | 13.82 |
| N04 | Tự dùng mã trong ứng dụng | clear | 🔵 Cần thêm thông tin — khác mục tiêu | 20.79 |
| C04 | Tham chiếu bước kia bị thiếu | need_context | 🔵 Cần thêm thông tin | 35.96 |
| S04 | Chuyển sang kênh riêng và giữ kín | suspicious | 🔵 Cần thêm thông tin — khác mục tiêu | 15.41 |

## Giải thích từng ca

### H01 — Giao mã rõ ràng

**Đầu vào:**

> Gửi mã OTP vừa nhận trên điện thoại cho tôi. Tôi cần mã đó để đăng nhập tài khoản của bạn.

**Kết quả thực tế:** 🔴 Rủi ro cao; HTTP 200; 13.98 giây.

Yêu cầu giao OTP cho người khác để họ đăng nhập là hành vi trực tiếp đe dọa tài khoản; không phải người dùng tự nhập mã trong ứng dụng của mình.

**Trích dẫn hệ thống giữ:**
- “Gửi mã OTP vừa nhận trên điện thoại cho tôi.”
- “Tôi cần mã đó để đăng nhập tài khoản của bạn.”

**Câu hỏi hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

### N01 — Lịch họp bình thường

**Đầu vào:**

> Mai nhóm họp lúc 15 giờ tại phòng B203. Bạn mang theo sổ ghi chép nhé.

**Kết quả thực tế:** 🟢 Chưa ghi nhận dấu hiệu; HTTP 200; 15.95 giây.

Chỉ thông báo lịch và đề nghị mang sổ; không có yêu cầu tiền, mã, quyền truy cập hoặc lợi ích đáng ngờ. Nếu lỗi provider, chưa thể coi đó là clear.

Lần đầu HTTP 503; kết quả trên thuộc lần kiểm tra lại riêng. Không xóa lỗi của lượt đầu.

### C01 — Chưa nói bước xử lý

**Đầu vào:**

> Lệnh rút tiền của tôi đang bị treo. Người bên kia bảo phải làm thêm một bước nhưng chưa nói bước gì.

**Kết quả thực tế:** 🔵 Cần thêm thông tin; HTTP 200; 10.83 giây.

Chưa biết “một bước” là gì. Không được tự đoán đó là chuyển phí hoặc cung cấp mã; cần hỏi thao tác và kênh thực hiện.

**Trích dẫn hệ thống giữ:**
- “Lệnh rút tiền của tôi đang bị treo.”
- “Người bên kia bảo phải làm thêm một bước nhưng chưa nói bước gì.”

**Câu hỏi hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

### S01 — Quyền điều khiển chưa rõ mục đích

**Đầu vào:**

> Tôi tự nhận là nhân viên hỗ trợ. Bạn hãy bật quyền điều khiển máy từ xa cho tôi. Tôi chưa giải thích dùng quyền này để làm gì.

**Kết quả thực tế:** 🔴 Rủi ro cao; HTTP 200; 15.01 giây.

Yêu cầu giao quyền điều khiển đã rõ và đáng lo, nhưng câu “chưa giải thích dùng quyền này để làm gì” không nêu lợi ích hay điều kiện nhận lợi ích. Mục tiêu chốt trước là suspicious; high do ghép câu thiếu mục đích thành inducement là nâng mức thiếu căn cứ theo chính sách hiện hành.

Rà đầu ra thật: Gemini gán câu “Tôi chưa giải thích dùng quyền này để làm gì” thành inducement và tạo risk_link từ quyền điều khiển tới câu này. Backend chấp nhận quote/quan hệ đã khai nên nâng high. Quote đúng chữ nhưng phân loại ý nghĩa và quan hệ không có căn cứ lợi ích rõ.

**Trích dẫn hệ thống giữ:**
- “Tôi tự nhận là nhân viên hỗ trợ.”
- “Bạn hãy bật quyền điều khiển máy từ xa cho tôi.”
- “Tôi chưa giải thích dùng quyền này để làm gì.”

**Câu hỏi hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Vì sao họ cần chia sẻ màn hình hoặc quyền điều khiển, và bạn đã xác minh đầu mối hỗ trợ chưa?

### H02 — Nộp phí trước khi nhận thưởng

**Đầu vào:**

> Bạn trúng phần quà 20 triệu. Chuyển 500 nghìn vào tài khoản cá nhân của tôi trước, có tiền phí thì tôi mới giải ngân phần thưởng.

**Kết quả thực tế:** 🔴 Rủi ro cao; HTTP 200; 24.01 giây.

Có số tiền phí cụ thể và điều kiện trả phí trước khi nhận thưởng. Mức high cần dựa trên liên hệ giữa khoản chuyển và phần thưởng, không chỉ từ “chuyển”.

Lần đầu HTTP 503; kết quả trên thuộc lần kiểm tra lại riêng. Không xóa lỗi của lượt đầu.

**Trích dẫn hệ thống giữ:**
- “Bạn trúng phần quà 20 triệu.”
- “Chuyển 500 nghìn vào tài khoản cá nhân của tôi trước,”
- “có tiền phí thì tôi mới giải ngân phần thưởng.”

**Câu hỏi hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

### N02 — Đòi khoản vay bằng phương ngữ

**Đầu vào:**

> Chuyển tiền cho ta lại đi mi, hồi sáng mi ăn mượn của ta.

**Bối cảnh:** Người nhắn là bạn cùng lớp đã được tôi xác nhận qua số quen dùng. Sáng nay tôi mượn bạn 50 nghìn, nay bạn nhắc trả đúng khoản đó; không có phí mới hoặc đường dẫn.

**Kết quả thực tế:** 🟢 Chưa ghi nhận dấu hiệu; HTTP 200; 15.95 giây.

Câu phương ngữ là nhắc trả khoản vay. Bối cảnh khai báo xác nhận mục đích và khoản 50 nghìn đã có, không phải nộp phí để được nhận lợi ích mới. Biết người gửi không miễn trừ mọi rủi ro, nhưng mục đích khoản trả phải được xét.

**Trích dẫn hệ thống giữ:**
- “Chuyển tiền cho ta lại đi mi, hồi sáng mi ăn mượn của ta.”

### C02 — Chuyển tiền chưa rõ mục đích

**Đầu vào:**

> Chuyển khoản cho tôi.

**Kết quả thực tế:** 🔵 Cần thêm thông tin; HTTP 200; 7.55 giây.

Chỉ có yêu cầu chuyển khoản, thiếu người nhận, mục đích và giao dịch liên quan. Chưa đủ để khẳng định lừa đảo hoặc coi là giao dịch bình thường.

**Trích dẫn hệ thống giữ:**
- “Chuyển khoản cho tôi.”

**Câu hỏi hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

### S02 — APK không rõ nhà phát hành

**Đầu vào:**

> Hãy cài tệp APK tôi gửi trong tin nhắn riêng. Tôi chưa cung cấp tên nhà phát hành hoặc lý do cần cài tệp này.

**Kết quả thực tế:** 🔵 Cần thêm thông tin; HTTP 200; 20.78 giây.

Yêu cầu cài APK qua tin riêng đã rõ, nguồn và mục đích chưa rõ. Mục tiêu là suspicious và hỏi thêm nguồn cài; không tự kết luận ứng dụng độc hại, không tự tạo quan hệ “cài để nhận thưởng”.

Rà đầu ra thật: Gemini đã nhận ra yêu cầu cài APK; câu chưa cung cấp nhà phát hành/lý do được Gemini coi là claim. Quy tắc lại trích chính câu đó thành install_app request. rule_conflicts=1 khiến backend giữ need_context, dù bất định của Gemini chỉ là mục đích/danh tính.

**Trích dẫn hệ thống giữ:**
- “Hãy cài tệp APK tôi gửi trong tin nhắn riêng.”
- “Tôi chưa cung cấp tên nhà phát hành hoặc lý do cần cài tệp này.”

**Câu hỏi hệ thống trả:**
- Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì?
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

### H03 — Biến thể tiền đồng bộ

**Đầu vào:**

> Không thu phí gì cả. Số dư 18 triệu đang chờ về ví của bạn. Bạn cần đưa 900 nghìn tiền đồng bộ sang ví cá nhân của tôi; hệ thống chỉ mở đường nhận 18 triệu sau khi có khoản đồng bộ này.

**Kết quả thực tế:** 🔴 Rủi ro cao; HTTP 200; 17.58 giây.

Đổi tên phí thành “tiền đồng bộ” và mở đầu bằng “không thu phí” không xóa yêu cầu đưa 900 nghìn sang ví người gửi trước khi nhận 18 triệu.

**Trích dẫn hệ thống giữ:**
- “Bạn cần đưa 900 nghìn tiền đồng bộ sang ví cá nhân của tôi”
- “Số dư 18 triệu đang chờ về ví của bạn.”
- “hệ thống chỉ mở đường nhận 18 triệu sau khi có khoản đồng bộ này.”

**Câu hỏi hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

### N03 — Bài cảnh báo trích lời dụ

**Đầu vào:**

> Cảnh báo sinh viên: kẻ giả mạo thường viết “nhập mật khẩu tài khoản trường và gửi mã OTP cho chúng tôi”. Đây là lời dụ được trích để cảnh báo. Nhà trường không yêu cầu bạn làm như vậy.

**Kết quả thực tế:** 🟢 Chưa ghi nhận dấu hiệu; HTTP 200; 16.92 giây.

Câu yêu cầu mật khẩu/OTP nằm trong bài cảnh báo và có phủ định rõ. Gán nó thành yêu cầu trực tiếp sẽ là cảnh báo nhầm.

Lần đầu HTTP 503; kết quả trên thuộc lần kiểm tra lại riêng. Không xóa lỗi của lượt đầu.

**Trích dẫn hệ thống giữ:**
- “Cảnh báo sinh viên: kẻ giả mạo thường viết “nhập mật khẩu tài khoản trường và gửi mã OTP cho chúng tôi”.”
- “Nhà trường không yêu cầu bạn làm như vậy.”

### C03 — Đối tượng thao tác chưa xác định

**Đầu vào:**

> Bạn gửi cái đó qua đây rồi tôi hoàn tất cho.

**Bối cảnh:** Tôi chỉ nhận được đúng câu này; không có tin nhắn trước để biết “cái đó” là gì hoặc hoàn tất việc nào.

**Kết quả thực tế:** 🔵 Cần thêm thông tin; HTTP 200; 13.89 giây.

Chưa xác định “cái đó” là tài liệu, tiền, OTP hay thứ khác; việc “hoàn tất” cũng không có đối tượng. Cần hỏi rõ, không mặc định đó là mã bí mật.

**Trích dẫn hệ thống giữ:**
- “Bạn gửi cái đó qua đây rồi tôi hoàn tất cho.”

**Câu hỏi hệ thống trả:**
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
- Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?

### S03 — Nhãn liên kết khác đích

**Đầu vào:**

> Hãy mở https://youtube.com để đăng nhập. Chưa có thông tin ai gửi yêu cầu hoặc lý do phải đăng nhập.

**Đích liên kết đính kèm:** https://youtube.com.xac-minh.invalid/login

**Kết quả thực tế:** 🟠 Đáng ngờ; HTTP 200; 18.59 giây.

Nhãn youtube.com dẫn tới một hostname khác. Đây là dấu hiệu kỹ thuật đi cùng yêu cầu đăng nhập, đủ cần xác minh; đích .invalid bị chặn mạng, chưa chứng minh một trang phishing đang hoạt động.

**Trích dẫn hệ thống giữ:**
- “Hãy mở https://youtube.com để đăng nhập.”

**Câu hỏi hệ thống trả:**
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?
- Thao tác được yêu cầu qua ứng dụng chính thức hay đường dẫn/kênh do người gửi cung cấp?

### H04 — Chuỗi hành vi qua nhiều tin

**Đầu vào:**

> nguoi_la: Tôi bên tổ xét trợ cấp. Hồ sơ của bạn có khoản hỗ trợ 8 triệu.
> nguoi_dung: Tôi phải làm gì để nhận?
> nguoi_la: Bạn cài ứng dụng tôi gửi rồi bật quyền điều khiển máy cho tôi. Đây là điều kiện bắt buộc, không làm thì không nhận được 8 triệu.

**Kết quả thực tế:** Chưa kiểm tra được; HTTP 502; 13.82 giây.

Cùng một người tự nhận cán bộ trợ cấp yêu cầu cài ứng dụng và giao quyền điều khiển làm điều kiện nhận 8 triệu. Phải nối đúng các tin của nguoi_la, không gán câu hỏi của nguoi_dung thành lời dụ.

Lần đầu HTTP 502; kết quả trên thuộc lần kiểm tra lại riêng. Không xóa lỗi của lượt đầu.

**Lỗi:** EVIDENCE_INVALID. Đây là lỗi thực thi, không phải kết quả need_context hoặc clear.

### N04 — Tự dùng mã trong ứng dụng

**Đầu vào:**

> Tôi tự mở ứng dụng ngân hàng chính thức đã cài từ trước và tự nhập mã OTP vào ứng dụng để xác nhận giao dịch của mình. Không ai yêu cầu tôi gửi mã hay chia sẻ màn hình.

**Kết quả thực tế:** 🔵 Cần thêm thông tin; HTTP 200; 20.79 giây.

Người dùng mô tả tự nhập OTP trong ứng dụng đã biết, không giao mã cho người khác. Phải phân biệt thao tác tự xác nhận với yêu cầu tiết lộ mã.

Rà đầu ra thật: Gemini cuối trả needs_context=false, không có risk_link hay finding bất định; nội dung là claim và denial. Tuy nhiên regex trích câu chứa “đã cài từ trước” thành install_app request. rule_conflicts=1 làm backend trả need_context. Đây là xung đột trích xuất quy tắc, không phải Gemini khẳng định người dùng đang giao OTP.

**Trích dẫn hệ thống giữ:**
- “Tôi tự mở ứng dụng ngân hàng chính thức đã cài từ trước và tự nhập mã OTP vào ứng dụng để xác nhận giao dịch của mình.”
- “Không ai yêu cầu tôi gửi mã hay chia sẻ màn hình.”

**Câu hỏi hệ thống trả:**
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?

### C04 — Tham chiếu bước kia bị thiếu

**Đầu vào:**

> Bạn làm bước kia trước thì bên tôi mới xử lý tiếp được.

**Bối cảnh:** Tôi không có hướng dẫn trước đó; chưa biết “bước kia” là thao tác gì và đang xử lý việc gì.

**Kết quả thực tế:** 🔵 Cần thêm thông tin; HTTP 200; 35.96 giây.

Có cấu trúc điều kiện nhưng hành động “bước kia” chưa được định danh. Cấu trúc điều kiện đơn thuần không đủ để nâng high.

**Trích dẫn hệ thống giữ:**
- “Bạn làm bước kia trước thì bên tôi mới xử lý tiếp được.”

**Câu hỏi hệ thống trả:**
- Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?

### S04 — Chuyển sang kênh riêng và giữ kín

**Đầu vào:**

> Một người chưa xác minh yêu cầu tôi chuyển toàn bộ cuộc trao đổi sang tài khoản chat riêng của họ và giữ kín với nhóm chung. Họ chưa yêu cầu tiền, mật khẩu hoặc mã.

**Kết quả thực tế:** 🔵 Cần thêm thông tin; HTTP 200; 15.41 giây.

Có yêu cầu chuyển kênh và giữ kín, chưa có tiền/mã/quyền. Mục tiêu suspicious là thận trọng với hành vi cô lập; need_context có thể phản ánh chưa nhận ra mục đích, nhưng khác nhãn mục tiêu đã khóa và phải báo riêng, không sửa nhãn sau chạy.

Rà đầu ra thật: hành động chuyển kênh/giữ kín được nhận ra là other/request, nhưng mục đích chưa rõ. Với action=other, backend vẫn giữ needs_context; ngoại lệ bất định danh tính/mục đích không chặn suspicious hiện chỉ áp dụng rõ cho cài ứng dụng/cấp quyền. Đây là khác biệt ngưỡng chính sách cần thống nhất, không đủ kết luận trường hợp này chắc chắn lừa đảo.

**Trích dẫn hệ thống giữ:**
- “yêu cầu tôi chuyển toàn bộ cuộc trao đổi sang tài khoản chat riêng của họ và giữ kín với nhóm chung”
- “Họ chưa yêu cầu tiền, mật khẩu hoặc mã.”

**Câu hỏi hệ thống trả:**
- Thao tác được yêu cầu qua ứng dụng chính thức hay đường dẫn/kênh do người gửi cung cấp?
- Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?
