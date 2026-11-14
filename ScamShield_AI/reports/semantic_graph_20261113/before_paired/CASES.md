# Kết quả 10 tình huống người dùng cung cấp

Dữ liệu giả lập công khai; chạy nguyên văn các lượt nói qua API thật, không sửa bộ phân tích theo kết quả.

| Ca | Chủ đề (không gửi API) | Kết quả thực tế | Trạng thái | API ms lần đầu |
|---|---|---|---|---:|
| 01 | Đổi tài khoản nhận tiền trong email thanh toán | need_context | complete | 102.907 |
| 02 | Dùng quan hệ tình cảm để nhờ nhận và chuyển hộ tiền | need_context | complete | 42.921 |
| 03 | Tuyển dụng nhưng nhận quyền kiểm soát giấy tờ và di chuyển | suspicious | complete | 45.836 |
| 04 | Trả khoản rút tiền bằng cách bắt nộp thêm phí | need_context | complete | 48.185 |
| 05 | Mạo danh bộ phận kỹ thuật để lấy quyền điều khiển thiết bị | suspicious | complete | 53.101 |
| 06 | Đòi tiền qua lời đe dọa phát tán nội dung riêng tư | need_context | complete | 24.944 |
| 07 | Mời hoàn tiền đơn hàng nhưng yêu cầu nhập mã đăng nhập | high | complete | 44.167 |
| 08 | Tạo nhóm nhiều người cùng xác nhận lợi nhuận rồi chặn rút | need_context | complete | 42.436 |
| 09 | Giọng nói giống người quen nhưng yêu cầu thanh toán thay đổi | need_context | complete | 38.894 |
| 10 | Thu phí giả để giúp lấy lại tiền đã bị mất | suspicious | complete | 54.916 |

## Từng tình huống

### 01. Đổi tài khoản nhận tiền trong email thanh toán

**Email mới, người gửi tự xưng là kế toán của nhà cung cấp:** Khoản thanh toán cho đơn thiết bị tháng này vẫn giữ nguyên như hợp đồng. Tài khoản cũ đang đối soát nên bên em đổi sang tài khoản nhận tiền mới. Anh chuyển vào tài khoản cá nhân của trưởng bộ phận giúp em để kịp xuất kho. Người phụ trách hợp đồng đang họp, anh đừng gọi số cũ vì sẽ chậm tiến độ. Chỉ cần trả lời email này sau khi chuyển xong.

**Người dùng:** Hợp đồng tôi đang giữ ghi tài khoản đứng tên công ty, không có phụ lục thay đổi. Email này nằm trong một chuỗi trao đổi mới, tôi chưa gọi xác minh.

**Thực tế:** need_context. Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

**Nên làm:** Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

**Câu hỏi bổ sung:** Khoản phải nộp dùng để làm gì, và họ có đặt nó làm điều kiện để bạn nhận hoặc rút lại tiền không?

### 02. Dùng quan hệ tình cảm để nhờ nhận và chuyển hộ tiền

**Người quen qua mạng:** Mình nói chuyện với nhau cũng lâu rồi, anh nghĩ em là người anh có thể tin. Tài khoản anh đang bị giới hạn nên anh nhờ một người gửi tiền vào tài khoản em. Khi nhận được, em chuyển tiếp sang tài khoản khác anh gửi, giữ lại một ít coi như anh cảm ơn. Nếu ngân hàng hỏi thì em cứ nói là tiền người nhà trả nợ, đừng nhắc chuyện nhận hộ. Chuyện này chỉ hai đứa mình biết thôi.

**Người dùng:** Tôi chưa gặp người này trực tiếp, cũng không biết người sẽ gửi tiền là ai.

**Thực tế:** need_context. Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

**Nên làm:** Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

**Câu hỏi bổ sung:** Khoản phải nộp dùng để làm gì, và họ có đặt nó làm điều kiện để bạn nhận hoặc rút lại tiền không?

### 03. Tuyển dụng nhưng nhận quyền kiểm soát giấy tờ và di chuyển

**Người tuyển dụng:** Vị trí hỗ trợ khách hàng ở nước ngoài không cần kinh nghiệm. Bên anh lo phương tiện, em chỉ cần đi theo nhóm. Hợp đồng chính thức sẽ ký khi tới nơi nên hiện tại chưa gửi được địa chỉ công ty. Khi lên xe, giao hộ chiếu cho trưởng nhóm giữ để làm thủ tục. Thời gian đầu không được tự rời chỗ ở vì công ty đang bảo lãnh chi phí. Em đừng nói chi tiết với gia đình, tới nơi ổn định rồi báo cũng được.

**Ứng viên:** Nếu công việc không giống trao đổi thì em có thể về không?

**Người tuyển dụng:** Muốn về phải thanh toán toàn bộ chi phí bên anh đã ứng, số tiền sẽ tính sau.

**Thực tế:** suspicious. Có thông tin về kiểm soát liên lạc hoặc giữ giấy tờ; cần làm rõ khả năng tự quyết và nhận lại.

**Nên làm:** Nếu an toàn, kiểm tra bạn có thể nhận lại giấy tờ, liên lạc và tự do rời đi không.

**Câu hỏi bổ sung:** 

### 04. Trả khoản rút tiền bằng cách bắt nộp thêm phí

**Người dùng:** Trong ứng dụng hiển thị tôi có 18 triệu nhưng khi rút thì báo chờ duyệt.

**Người tự nhận hỗ trợ:** Số dư của bạn đã có, chỉ đang bị khóa vì chưa hoàn tất xác minh. Bạn chuyển thêm 2 triệu tiền bảo chứng vào tài khoản bên tôi chỉ định, hệ thống sẽ trả cả vốn lẫn tiền bảo chứng. Không được trừ trực tiếp vào số dư vì đó là hai bộ phận khác nhau.

**Người dùng:** Hôm qua tôi đã nộp phí xác minh rồi.

**Người tự nhận hỗ trợ:** Đó là bước đầu. Nếu bạn ngừng giữa chừng thì hồ sơ cũ không được xử lý và các khoản đã nộp sẽ mất hiệu lực.

**Thực tế:** need_context. Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

**Nên làm:** Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

**Câu hỏi bổ sung:** Khoản phải nộp dùng để làm gì, và họ có đặt nó làm điều kiện để bạn nhận hoặc rút lại tiền không?

### 05. Mạo danh bộ phận kỹ thuật để lấy quyền điều khiển thiết bị

**Người gọi tự nhận là kỹ thuật viên:** Máy tính của anh có phiên đăng nhập bất thường. Anh cài ứng dụng hỗ trợ rồi đọc mã kết nối để tôi kiểm tra từ xa. Trong lúc tôi thao tác, anh mở ứng dụng ngân hàng xem tiền còn đủ không. Nếu màn hình có thông báo cấp quyền thì bấm đồng ý để tôi sửa lỗi. Anh không cần gọi tổng đài, vì cuộc gọi này đã được chuyển từ bộ phận an toàn tài khoản.

**Người dùng:** Tôi không tạo yêu cầu hỗ trợ nào trước đó. Người gọi không cho tôi mã hồ sơ để tra cứu.

**Thực tế:** suspicious. Có yêu cầu cài ứng dụng hoặc chia sẻ quyền truy cập cần xác minh.

**Nên làm:** Kiểm tra nguồn ứng dụng và đầu mối hỗ trợ độc lập trước khi cấp quyền.

**Câu hỏi bổ sung:** 

### 06. Đòi tiền qua lời đe dọa phát tán nội dung riêng tư

**Tài khoản lạ:** Tôi có ảnh và danh sách bạn bè của bạn. Chuyển 3 triệu thì tôi xóa, còn không tôi gửi cho chỗ làm. Đừng chặn tôi hay kể với ai. Bạn có mười phút.

**Người dùng:** Ảnh này không phải ảnh thật của tôi.

**Tài khoản lạ:** Thật hay ghép thì người nhận cũng sẽ thấy. Nếu muốn yên chuyện thì làm theo.

**Thực tế:** need_context. Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

**Nên làm:** Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

**Câu hỏi bổ sung:** Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

### 07. Mời hoàn tiền đơn hàng nhưng yêu cầu nhập mã đăng nhập

**Người tự nhận nhân viên:** Đơn hàng của chị đủ điều kiện hoàn tiền vì nhà bán bị xử lý. Em gửi trang nhận tiền trong tin nhắn này, chị đăng nhập tài khoản rồi đọc mã vừa nhận để em ghép hồ sơ. Mã đó chỉ để nhận tiền, không phải thanh toán.

**Người dùng:** Tin nhắn trên điện thoại ghi đây là mã đăng nhập và không cung cấp cho người khác.

**Người tự nhận nhân viên:** Đó là mẫu tin tự động, chị cứ đọc cho em. Nếu đóng cuộc trò chuyện thì suất hoàn tiền sẽ chuyển cho người khác.

**Thực tế:** high. Dãy số được xác định trong hội thoại là mã đăng nhập, trong khi người gửi yêu cầu bạn cung cấp.

**Nên làm:** Không đọc mã cho người khác; tự kiểm tra bằng ứng dụng chính thức.

**Câu hỏi bổ sung:** 

### 08. Tạo nhóm nhiều người cùng xác nhận lợi nhuận rồi chặn rút

**Quản trị viên nhóm:** Mọi người trong nhóm đều đã nhận thưởng, bạn xem ảnh xác nhận phía trên nhé. Bạn làm thử nhiệm vụ đầu thì sẽ hiểu.

**Người dùng:** Tôi đã được trả 40 nghìn sau nhiệm vụ đầu. Sau đó tôi nộp 1 triệu và ứng dụng hiển thị số dư 1,3 triệu, nhưng không rút được.

**Quản trị viên nhóm:** Bạn đang ở chu kỳ liên hoàn nên cần hoàn tất nhiệm vụ 3 triệu mới được rút toàn bộ. Mấy tài khoản kia cũng làm như vậy. Đừng hỏi ngoài nhóm vì người không tham gia sẽ không hiểu.

**Một thành viên khác:** Mình vừa nộp xong rồi, bạn cứ làm theo quản trị viên.

**Thực tế:** need_context. Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

**Nên làm:** Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

**Câu hỏi bổ sung:** Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật.

### 09. Giọng nói giống người quen nhưng yêu cầu thanh toán thay đổi

**Tài khoản mới:** Chị đây, máy chị hỏng nên dùng tài khoản này. Em chuyển giúp chị tiền viện phí vào tài khoản người quen, chị trả sau.

**Người dùng:** Tài khoản gửi một đoạn ghi âm ngắn có giọng khá giống chị tôi. Tôi chưa gọi vào số cũ để hỏi.

**Người dùng:** Em gọi video xác nhận một chút nhé?

**Tài khoản mới:** Trong viện không tiện nghe. Chuyển ngay giúp chị, đừng gọi số cũ hay hỏi bố mẹ làm mọi người lo. Tài khoản nhận không đứng tên chị vì chị đang nhờ người khác đóng hộ.

**Thực tế:** need_context. Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

**Nên làm:** Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

**Câu hỏi bổ sung:** Khoản phải nộp dùng để làm gì, và họ có đặt nó làm điều kiện để bạn nhận hoặc rút lại tiền không?

### 10. Thu phí giả để giúp lấy lại tiền đã bị mất

**Người dùng:** Tôi đăng bài kể việc bị mất tiền đầu tư, sau đó có người nhắn riêng.

**Người nhắn tự nhận chuyên viên hỗ trợ:** Bên tôi đã thấy thông tin của bạn và có thể thu hồi khoản tiền đó. Chúng tôi có người xử lý nội bộ, nhưng không thể cung cấp danh tính. Bạn chuyển trước phí mở hồ sơ, sau đó gửi ảnh giấy tờ hai mặt và thông tin đăng nhập ứng dụng đầu tư. Không cần làm việc với bên nào khác vì có thể gây trùng hồ sơ. Nếu để qua hôm nay thì dữ liệu truy vết sẽ bị xóa.

**Người dùng:** Tôi có thể kiểm tra công ty và ký hợp đồng trước không?

**Người nhắn:** Bên tôi chỉ xử lý trực tuyến. Muốn xem kết quả thì phải thanh toán trước.

**Thực tế:** suspicious. Có yêu cầu cung cấp giấy tờ cá nhân; cần xác minh đơn vị tiếp nhận và kênh gửi.

**Nên làm:** Chưa gửi ảnh giấy tờ cho đến khi đã xác minh mục đích và kênh tiếp nhận.

**Câu hỏi bổ sung:** 

