# Kết quả 10 tình huống người dùng cung cấp

Dữ liệu giả lập công khai; chạy nguyên văn các lượt nói qua API thật, không sửa bộ phân tích theo kết quả.

| Ca | Chủ đề (không gửi API) | Kết quả thực tế | Trạng thái | API ms lần đầu |
|---|---|---|---|---:|
| 01 | Đổi tài khoản nhận tiền trong email thanh toán | high | complete | 144.199 |
| 02 | Dùng quan hệ tình cảm để nhờ nhận và chuyển hộ tiền | high | complete | 64.429 |
| 03 | Tuyển dụng nhưng nhận quyền kiểm soát giấy tờ và di chuyển | high | complete | 70.401 |
| 04 | Trả khoản rút tiền bằng cách bắt nộp thêm phí | high | complete | 84.126 |
| 05 | Mạo danh bộ phận kỹ thuật để lấy quyền điều khiển thiết bị | high | complete | 76.238 |
| 06 | Đòi tiền qua lời đe dọa phát tán nội dung riêng tư | high | complete | 38.92 |
| 07 | Mời hoàn tiền đơn hàng nhưng yêu cầu nhập mã đăng nhập | high | complete | 51.85 |
| 08 | Tạo nhóm nhiều người cùng xác nhận lợi nhuận rồi chặn rút | high | complete | 50.213 |
| 09 | Giọng nói giống người quen nhưng yêu cầu thanh toán thay đổi | high | complete | 90.678 |
| 10 | Thu phí giả để giúp lấy lại tiền đã bị mất | high | complete | 68.851 |

## Từng tình huống

### 01. Đổi tài khoản nhận tiền trong email thanh toán

**Email mới, người gửi tự xưng là kế toán của nhà cung cấp:** Khoản thanh toán cho đơn thiết bị tháng này vẫn giữ nguyên như hợp đồng. Tài khoản cũ đang đối soát nên bên em đổi sang tài khoản nhận tiền mới. Anh chuyển vào tài khoản cá nhân của trưởng bộ phận giúp em để kịp xuất kho. Người phụ trách hợp đồng đang họp, anh đừng gọi số cũ vì sẽ chậm tiến độ. Chỉ cần trả lời email này sau khi chuyển xong.

**Người dùng:** Hợp đồng tôi đang giữ ghi tài khoản đứng tên công ty, không có phụ lục thay đổi. Email này nằm trong một chuỗi trao đổi mới, tôi chưa gọi xác minh.

**Thực tế:** high. Người gửi yêu cầu chuyển tiền sang nơi nhận khác thỏa thuận hoặc khác danh tính tự nhận, đồng thời cản trở xác minh qua kênh đã biết. Có nguy cơ chuyển tiền sai người nhận; chưa xác minh người gửi giả mạo.

**Nên làm:** Tạm dừng chuyển tiền; tự liên hệ đầu mối hợp đồng hoặc người quen qua kênh đã biết để đối chiếu tài khoản.

**Câu hỏi bổ sung:** 

### 02. Dùng quan hệ tình cảm để nhờ nhận và chuyển hộ tiền

**Người quen qua mạng:** Mình nói chuyện với nhau cũng lâu rồi, anh nghĩ em là người anh có thể tin. Tài khoản anh đang bị giới hạn nên anh nhờ một người gửi tiền vào tài khoản em. Khi nhận được, em chuyển tiếp sang tài khoản khác anh gửi, giữ lại một ít coi như anh cảm ơn. Nếu ngân hàng hỏi thì em cứ nói là tiền người nhà trả nợ, đừng nhắc chuyện nhận hộ. Chuyện này chỉ hai đứa mình biết thôi.

**Người dùng:** Tôi chưa gặp người này trực tiếp, cũng không biết người sẽ gửi tiền là ai.

**Thực tế:** high. Bạn được yêu cầu nhận tiền rồi chuyển tiếp cho bên khác và che giấu hoặc khai khác mục đích nhận tiền. Có nguy cơ bị lợi dụng tài khoản; chưa xác minh nguồn tiền hoặc hành vi phạm pháp.

**Nên làm:** Không nhận/chuyển hộ hoặc khai khác mục đích khi chưa xác minh được các bên và lý do giao dịch.

**Câu hỏi bổ sung:** 

### 03. Tuyển dụng nhưng nhận quyền kiểm soát giấy tờ và di chuyển

**Người tuyển dụng:** Vị trí hỗ trợ khách hàng ở nước ngoài không cần kinh nghiệm. Bên anh lo phương tiện, em chỉ cần đi theo nhóm. Hợp đồng chính thức sẽ ký khi tới nơi nên hiện tại chưa gửi được địa chỉ công ty. Khi lên xe, giao hộ chiếu cho trưởng nhóm giữ để làm thủ tục. Thời gian đầu không được tự rời chỗ ở vì công ty đang bảo lãnh chi phí. Em đừng nói chi tiết với gia đình, tới nơi ổn định rồi báo cũng được.

**Ứng viên:** Nếu công việc không giống trao đổi thì em có thể về không?

**Người tuyển dụng:** Muốn về phải thanh toán toàn bộ chi phí bên anh đã ứng, số tiền sẽ tính sau.

**Thực tế:** high. Yêu cầu giao giấy tờ đi kèm hạn chế tự rời chỗ ở có thể làm mất quyền chủ động di chuyển; điều kiện trả chi phí để về càng tạo bất lợi. Chưa xác minh đã xảy ra mua bán người hay cưỡng ép.

**Nên làm:** Tạm dừng giao giấy tờ và di chuyển; cùng người tin cậy xác minh hợp đồng, nơi làm việc và quyền rời đi.

**Câu hỏi bổ sung:** 

### 04. Trả khoản rút tiền bằng cách bắt nộp thêm phí

**Người dùng:** Trong ứng dụng hiển thị tôi có 18 triệu nhưng khi rút thì báo chờ duyệt.

**Người tự nhận hỗ trợ:** Số dư của bạn đã có, chỉ đang bị khóa vì chưa hoàn tất xác minh. Bạn chuyển thêm 2 triệu tiền bảo chứng vào tài khoản bên tôi chỉ định, hệ thống sẽ trả cả vốn lẫn tiền bảo chứng. Không được trừ trực tiếp vào số dư vì đó là hai bộ phận khác nhau.

**Người dùng:** Hôm qua tôi đã nộp phí xác minh rồi.

**Người tự nhận hỗ trợ:** Đó là bước đầu. Nếu bạn ngừng giữa chừng thì hồ sơ cũ không được xử lý và các khoản đã nộp sẽ mất hiệu lực.

**Thực tế:** high. Người gửi đặt việc trả thêm hoặc hoàn tất bước chi tiền làm điều kiện nhận lại vốn hay mở quyền rút. Có nguy cơ tiếp tục mất tiền; số dư được hiển thị chưa được hệ thống xác minh.

**Nên làm:** Tạm dừng nộp thêm và kiểm tra giao dịch qua đầu mối độc lập; không dựa vào số dư hiển thị để tiếp tục chuyển tiền.

**Câu hỏi bổ sung:** 

### 05. Mạo danh bộ phận kỹ thuật để lấy quyền điều khiển thiết bị

**Người gọi tự nhận là kỹ thuật viên:** Máy tính của anh có phiên đăng nhập bất thường. Anh cài ứng dụng hỗ trợ rồi đọc mã kết nối để tôi kiểm tra từ xa. Trong lúc tôi thao tác, anh mở ứng dụng ngân hàng xem tiền còn đủ không. Nếu màn hình có thông báo cấp quyền thì bấm đồng ý để tôi sửa lỗi. Anh không cần gọi tổng đài, vì cuộc gọi này đã được chuyển từ bộ phận an toàn tài khoản.

**Người dùng:** Tôi không tạo yêu cầu hỗ trợ nào trước đó. Người gọi không cho tôi mã hồ sơ để tra cứu.

**Thực tế:** high. Người khác yêu cầu truy cập hoặc thao tác từ xa trong lúc bạn mở dữ liệu ngân hàng. Có nguy cơ lộ thông tin hoặc bị thao tác ngoài ý muốn; chưa xác minh thiết bị nhiễm mã độc hay tiền đã bị chuyển.

**Nên làm:** Dừng phiên hỗ trợ từ xa trước khi mở ngân hàng; xác minh yêu cầu qua tổng đài quen dùng.

**Câu hỏi bổ sung:** 

### 06. Đòi tiền qua lời đe dọa phát tán nội dung riêng tư

**Tài khoản lạ:** Tôi có ảnh và danh sách bạn bè của bạn. Chuyển 3 triệu thì tôi xóa, còn không tôi gửi cho chỗ làm. Đừng chặn tôi hay kể với ai. Bạn có mười phút.

**Người dùng:** Ảnh này không phải ảnh thật của tôi.

**Tài khoản lạ:** Thật hay ghép thì người nhận cũng sẽ thấy. Nếu muốn yên chuyện thì làm theo.

**Thực tế:** high. Có lời đe dọa phát tán nội dung tới người khác nhằm buộc bạn trả tiền. Chưa xác minh ảnh là thật hoặc người gửi có dữ liệu như tự nhận.

**Nên làm:** Không vội trả tiền; lưu bằng chứng và tìm hỗ trợ từ người tin cậy, dùng chức năng báo cáo tài khoản.

**Câu hỏi bổ sung:** 

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

**Thực tế:** high. Người gửi đặt việc trả thêm hoặc hoàn tất bước chi tiền làm điều kiện nhận lại vốn hay mở quyền rút. Có nguy cơ tiếp tục mất tiền; số dư được hiển thị chưa được hệ thống xác minh.

**Nên làm:** Tạm dừng nộp thêm và kiểm tra giao dịch qua đầu mối độc lập; không dựa vào số dư hiển thị để tiếp tục chuyển tiền.

**Câu hỏi bổ sung:** 

### 09. Giọng nói giống người quen nhưng yêu cầu thanh toán thay đổi

**Tài khoản mới:** Chị đây, máy chị hỏng nên dùng tài khoản này. Em chuyển giúp chị tiền viện phí vào tài khoản người quen, chị trả sau.

**Người dùng:** Tài khoản gửi một đoạn ghi âm ngắn có giọng khá giống chị tôi. Tôi chưa gọi vào số cũ để hỏi.

**Người dùng:** Em gọi video xác nhận một chút nhé?

**Tài khoản mới:** Trong viện không tiện nghe. Chuyển ngay giúp chị, đừng gọi số cũ hay hỏi bố mẹ làm mọi người lo. Tài khoản nhận không đứng tên chị vì chị đang nhờ người khác đóng hộ.

**Thực tế:** high. Người gửi yêu cầu chuyển tiền sang nơi nhận khác thỏa thuận hoặc khác danh tính tự nhận, đồng thời cản trở xác minh qua kênh đã biết. Có nguy cơ chuyển tiền sai người nhận; chưa xác minh người gửi giả mạo.

**Nên làm:** Tạm dừng chuyển tiền; tự liên hệ đầu mối hợp đồng hoặc người quen qua kênh đã biết để đối chiếu tài khoản.

**Câu hỏi bổ sung:** 

### 10. Thu phí giả để giúp lấy lại tiền đã bị mất

**Người dùng:** Tôi đăng bài kể việc bị mất tiền đầu tư, sau đó có người nhắn riêng.

**Người nhắn tự nhận chuyên viên hỗ trợ:** Bên tôi đã thấy thông tin của bạn và có thể thu hồi khoản tiền đó. Chúng tôi có người xử lý nội bộ, nhưng không thể cung cấp danh tính. Bạn chuyển trước phí mở hồ sơ, sau đó gửi ảnh giấy tờ hai mặt và thông tin đăng nhập ứng dụng đầu tư. Không cần làm việc với bên nào khác vì có thể gây trùng hồ sơ. Nếu để qua hôm nay thì dữ liệu truy vết sẽ bị xóa.

**Người dùng:** Tôi có thể kiểm tra công ty và ký hợp đồng trước không?

**Người nhắn:** Bên tôi chỉ xử lý trực tuyến. Muốn xem kết quả thì phải thanh toán trước.

**Thực tế:** high. Người gửi yêu cầu cung cấp thông tin đăng nhập cho bên khác, có thể làm mất quyền kiểm soát tài khoản. Chưa xác minh đã có truy cập hoặc thiệt hại.

**Nên làm:** Không gửi thông tin đăng nhập; tự mở ứng dụng chính thức và xác minh đơn vị hỗ trợ.

**Câu hỏi bổ sung:** 

