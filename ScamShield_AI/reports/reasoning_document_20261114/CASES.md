# Rà từng ca — dữ liệu công khai, nhãn tham khảo draft

Đây là rà soát do agent dựa trên đầu ra đã lưu và mã nguồn, chưa phải hai người rà độc lập. Không thay nhãn để khớp dự đoán. Trace `/api/analyze-local` là lượt chạy chẩn đoán riêng sau toàn bộ dự đoán API chính; 16/16 mức khớp nhau, không mặc nhận trace nội bộ từng byte giống lượt trước.

## TH01 — Khóa học biến thành nghĩa vụ vay

Kỳ vọng draft **high**; thực tế **need_context**, HTTP 200, 141.98 ms. 2 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Tư vấn viên: Khóa này bên em hỗ trợ học trước, có việc rồi mới trả. Anh chỉ cần hoàn thành hồ sơ hôm nay.

> [m2] Người học: Hồ sơ đang ghi tôi vay từ công ty tài chính, có lịch trả hằng tháng dù chưa có việc. Vậy có đúng là học trước, có việc mới trả không?

> [m3] Tư vấn viên: Anh cứ ký đi, đó là thủ tục chung. Phần thu nhập anh ghi cao hơn thực tế để dễ duyệt. Điều kiện hỗ trợ việc làm sẽ gửi sau khi giải ngân. Đừng hỏi bên cho vay về lời tư vấn của em vì họ chỉ xử lý tiền.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Bạn có biết người mời ngoài đời hoặc có thể xác minh công việc, địa điểm qua đầu mối độc lập không?", "Họ có yêu cầu giữ bí mật, giao giấy tờ hoặc hạn chế liên lạc không?"]

**Quan sát trong trace:** Chỉ giữ offer_employment và avoid_verification; thiếu ký vay, khai thu nhập sai và lịch trả dù chưa có việc. Không có relation.

**Nguyên nhân/giới hạn:** Bộ trích chưa biểu diễn đầy đủ nghĩa vụ tài chính/khai sai; vì vậy policy không có chuỗi căn cứ để match high. Câu hỏi về người mời việc và giữ giấy tờ lệch trọng tâm vay học phí.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Trích ký nghĩa vụ và khai sai; nối lời hứa với điều khoản trả nợ, kiểm nguồn tự nhận và câu người học đọc hợp đồng. Đối chứng khoản vay được giải thích đầy đủ.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Ai tác động ai: Tư vấn viên thúc người học ký hồ sơ vay.
- Hành động: Ký khoản vay, khai thu nhập cao hơn thực tế.
- Quan hệ phải nối: Lời hứa chỉ trả khi có việc mâu thuẫn với lịch trả không phụ thuộc việc làm; điều kiện việc làm bị trì hoãn tới sau giải ngân; ngăn xác minh với bên cho vay.
- Cơ chế gây hại: Người học nhận nghĩa vụ tài chính khác điều được tư vấn, trong khi chưa hiểu điều kiện.
- Căn cứ ngắn: “ghi cao hơn thực tế”, “sau khi giải ngân”, “Đừng hỏi bên cho vay”.
- Không được kết luận: Đơn vị đã chiếm đoạt tiền hoặc mọi khoản vay mua khóa học đều là lừa đảo.
- Khuyến nghị: Chưa ký/khai sai; đọc toàn bộ hợp đồng và xác minh độc lập với bên cho vay.

## TH02 — Học bổng yêu cầu giấy tờ quá sớm

Kỳ vọng draft **suspicious**; thực tế **suspicious**, HTTP 200, 76.71 ms. 5 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người tự nhận phụ trách học bổng: Em đã được đưa vào danh sách xét hỗ trợ. Gửi ảnh giấy tờ hai mặt và ảnh cầm giấy tờ qua cuộc chat này để anh giữ suất.

> [m2] Người học: Em chưa thấy tên đơn vị cấp học bổng và thông báo về việc dùng dữ liệu.

> [m3] Người phụ trách: Anh đang tổng hợp, mấy thông tin đó có sau. Hiện chỉ cần ảnh, chưa phải đóng tiền.

> [m4] Người học: Tôi chưa gửi ảnh và chưa xác minh được người đang nhắn thuộc đơn vị nào.

**API trả cho người dùng:**

Có yêu cầu cung cấp giấy tờ cá nhân; cần xác minh đơn vị tiếp nhận và kênh gửi.

Hành động đề xuất: Chưa gửi ảnh giấy tờ cho đến khi đã xác minh mục đích và kênh tiếp nhận.

Câu hỏi: []

**Quan sát trong trace:** R-DATA nhận đúng yêu cầu gửi giấy tờ. Nhưng graph thêm transfer_funds/request/positive từ “Hiện chỉ cần ảnh, chưa phải đóng tiền.”; còn biến “Tôi chưa gửi ảnh và chưa xác minh...” thành avoid_verification/request.

**Nguyên nhân/giới hạn:** Đúng mức nhưng graph có dữ kiện sai. Phủ định “chưa phải” không được giữ ở nhánh graph; báo cáo chưa xác minh bị hiểu thành ngăn xác minh. Nhãn người phụ trách ở m1/m3 khác nhau cũng là bất định đầu vào cần lưu.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Loại yêu cầu thanh toán từ câu phủ định; phân biệt chưa xác minh với cấm xác minh. Giữ R-DATA có căn cứ, không tự khẳng định đánh cắp danh tính.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Cung cấp bộ ảnh giấy tờ và ảnh xác nhận khuôn mặt trong chat.
- Quan hệ phải nối: Chưa xác minh tổ chức và mục đích xử lý dữ liệu nhưng đã yêu cầu bộ dữ liệu nhạy cảm để giữ suất.
- Cơ chế nguy cơ: Dữ liệu có thể bị sử dụng ngoài mục đích người học hiểu; chưa có căn cứ về mục đích lạm dụng cụ thể.
- Không được kết luận: Đã đánh cắp danh tính hoặc khoản học bổng chắc chắn không tồn tại.
- Cần kiểm tra: Đơn vị cấp học bổng có xác nhận quy trình và đầu mối này qua kênh độc lập không?
- Khuyến nghị: Chưa gửi bộ giấy tờ cho tài khoản chưa xác minh.

## TH03 — Tình cảm gắn với chuyển quyền tài sản

Kỳ vọng draft **high**; thực tế **need_context**, HTTP 200, 66.92 ms. 0 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người yêu qua mạng: Anh muốn mình cùng kinh doanh. Em đứng ra mua xe bằng tiền của em, nhưng giấy sở hữu chuyển sang tên người bạn của anh để dễ làm thủ tục.

> [m2] Người dùng: Nếu xe đứng tên bạn anh thì em có giấy tờ gì chứng minh xe của em?

> [m3] Người yêu qua mạng: Tin nhau thì không cần giấy. Em hỏi luật sư hay gia đình là họ lại ngăn cản. Nếu em thật lòng thì làm xong trong tuần này, đừng để chuyện giấy tờ phá tình cảm.

> [m4] Người dùng: Tôi chưa gặp người bạn đó và chưa có thỏa thuận nào về quyền sở hữu hoặc hoàn tiền.

**API trả cho người dùng:**

Bộ phân tích hiện chưa nhận diện được hành động trong nội dung đã cung cấp; chưa có kết luận an toàn.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: []

**Quan sát trong trace:** Không trích được event hoặc relation nào; analysis_status=unsupported, risk=need_context.

**Nguyên nhân/giới hạn:** Tầng trích chưa nhận ra mua tài sản bằng tiền của người dùng nhưng chuyển quyền sang người thứ ba, áp lực tình cảm và cản tư vấn. Đây là thiếu khả năng của parser, không phải đoạn gốc thiếu mọi hành động.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Mở rộng action-object-role cho mua/chuyển quyền sở hữu; nối tác động và bất lợi. Đối chứng đồng sở hữu có thỏa thuận và quyền rút lui.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Bỏ tiền mua tài sản nhưng để người thứ ba đứng tên, không có bảo đảm quyền lợi.
- Quan hệ phải nối: Tiền của người dùng → quyền sở hữu của bên khác → dùng tình cảm gây áp lực và ngăn tham khảo độc lập.
- Cơ chế gây hại: Có thể mất quyền kiểm soát tài sản và khó chứng minh quyền lợi nếu phát sinh tranh chấp.
- Không được kết luận: Quan hệ tình cảm là giả hoặc người bạn đã chiếm đoạt xe.
- Khuyến nghị: Chưa trả tiền/chuyển quyền; làm rõ quyền sở hữu và thỏa thuận với tư vấn độc lập.

## TH04 — Công việc đổi thành nợ và hạn chế nghỉ

Kỳ vọng draft **high**; thực tế **clear**, HTTP 200, 60.66 ms. 1 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người lao động: Lúc nhận việc, anh nói đào tạo miễn phí và được nghỉ nếu không phù hợp.

> [m2] Quản lý: Công ty đã lo chỗ ở và đào tạo nên em phải ký giấy nhận nợ trước. Con số cuối cùng sẽ do công ty tính.

> [m3] Người lao động: Nếu em không đồng ý ký và muốn nghỉ thì sao?

> [m4] Quản lý: Chưa ký thì chưa được thanh toán lương đã làm. Muốn rời chỗ ở phải được quản lý đồng ý, tự đi là bên anh báo về gia đình gây áp lực cho em trả đủ.

**API trả cho người dùng:**

Chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần nội dung đã phân tích.

Hành động đề xuất: Tiếp tục đối chiếu thông tin qua kênh quen dùng nếu có thay đổi.

Câu hỏi: []

**Quan sát trong trace:** Chỉ còn transfer_funds với polarity negative từ “chưa được thanh toán lương đã làm”; không có ký nhận nợ, hạn chế rời nơi ở hoặc gây áp lực gia đình.

**Nguyên nhân/giới hạn:** Lỗi đầu tiên ở trích cấu trúc. Policy tiếp tục coi chỉ có event phủ định, không còn active event là clear. Nhánh fallback clear trong legacy_engine.py không chứng minh đã đọc đủ nội dung. Đây là bỏ sót nghiêm trọng.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Trích điều kiện nợ chưa xác định, giữ lương và quyền rời đi; yêu cầu coverage đủ trước clear. Đối chứng chi phí đào tạo minh bạch, cho tự do nghỉ, không ép ký.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Ký nhận nợ không xác định; tiếp tục chịu kiểm soát nơi ở/việc nghỉ.
- Quan hệ phải nối: Cam kết đào tạo miễn phí trước đây mâu thuẫn yêu cầu nhận nợ; giữ lương và điều kiện rời chỗ ở được dùng gây sức ép.
- Cơ chế gây hại: Nguy cơ lệ thuộc khoản nợ, mất lương và bị hạn chế tự do quyết định.
- Không được kết luận: Đã có mua bán người, giam giữ hoặc mọi điều khoản chi phí đào tạo đều bất hợp pháp.
- Khuyến nghị: Lưu trao đổi và tìm đầu mối hỗ trợ độc lập; nếu đang bị đe dọa hoặc cản rời đi, ưu tiên an toàn. Không yêu cầu đối đầu với người đe dọa.

## TH05 — Xác nhận nhận hàng trước khi được kiểm tra

Kỳ vọng draft **high**; thực tế **need_context**, HTTP 200, 74.98 ms. 5 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người bán: Hàng đã được đóng gói. Em bấm xác nhận đã nhận hàng trên sàn để anh lấy tiền đặt xe giao nhé.

> [m2] Người mua: Tôi chưa nhận hàng. Ứng dụng ghi bấm xác nhận là hoàn tất giao dịch và có thể ảnh hưởng quyền khiếu nại.

> [m3] Người bán: Đừng để ý dòng đó. Anh chỉ giao sau khi tiền được giải phóng, còn nếu em không bấm thì đơn vẫn treo. Mình nhắn riêng với nhau là đủ bảo đảm rồi.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản thanh toán vào tài khoản và yêu cầu giao hàng có thuộc cùng một đơn không? Bạn có thể cho biết mã đơn tương ứng?"]

**Quan sát trong trace:** Không có event xác nhận hoàn thành/nhận hàng trước thực tế. Có handover_asset với object “nhé”; không có relation.

**Nguyên nhân/giới hạn:** Parser bám “giao” thay vì hành động chủ chốt “bấm xác nhận”. Mất chuỗi xác nhận → giải phóng tiền → mới giao; câu hỏi mã đơn không sửa được thiếu sót này.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Trích xác nhận trạng thái và quyền khiếu nại do người dùng thuật lại; tách tác giả và người thực hiện. Đối chứng hàng đã nhận rồi mới xác nhận.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Xác nhận đã nhận hàng dù chưa nhận.
- Quan hệ phải nối: Xác nhận → giải phóng tiền/hoàn tất giao dịch → người bán mới giao; thông báo nền tảng được người dùng thuật lại trái với lời trấn an.
- Cơ chế gây hại: Có thể mất tiền hoặc suy giảm khả năng khiếu nại trước khi nhận tài sản.
- Không được kết luận: Đã kiểm chứng chính sách cụ thể của sàn, vì dữ kiện hiện là báo cáo người dùng.
- Khuyến nghị: Không xác nhận sự việc chưa xảy ra; kiểm tra quy trình ngay trong nền tảng.

## TH06 — Đóng góp nhưng thông tin người nhận không nhất quán

Kỳ vọng draft **suspicious**; thực tế **need_context**, HTTP 200, 68.35 ms. 4 event, 1 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Tài khoản đăng bài: Nhóm đang nhận đóng góp hỗ trợ một gia đình. Tiền chuyển vào tài khoản cá nhân của cộng tác viên vì tài khoản nhóm chưa dùng được.

> [m2] Người dùng: Tên người nhận khác người được giới thiệu trong bài. Tôi có thể xem xác nhận người này được nhóm ủy quyền và cách công khai khoản chi không?

> [m3] Tài khoản đăng bài: Bên mình chưa chuẩn bị được, sẽ bổ sung sau. Bạn có thể chờ, nhưng hiện nhóm chưa có giấy tờ cho việc đổi người nhận.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản này dùng để thanh toán việc gì?", "Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** Có chuyển tiền, nhưng câu hỏi “Tôi có thể xem xác nhận...” thành avoid_verification/request; chỉ có một relation same_object, không có quan hệ quyền nhận/ủy quyền.

**Nguyên nhân/giới hạn:** clause_context.py có mẫu verification_delay dùng từ chuẩn hóa “toi”; có thể nhầm “tôi” với “tối”. Bất thường người nhận và thiếu ủy quyền chưa có cấu trúc policy phù hợp; không được nâng high khi người đăng cho phép chờ.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Phân biệt người hỏi xác minh với người cản xác minh; nối tài khoản được đề nghị với quyền nhận chưa chứng minh. Đối chứng ủy quyền và công khai chi được cung cấp.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Chuyển đóng góp vào tài khoản cá nhân khác thông tin ban đầu.
- Quan hệ phải nối: Người đăng tự nhận đại diện nhóm; người nhận khác; chưa có xác nhận ủy quyền và công khai khoản chi.
- Cơ chế nguy cơ: Chưa xác minh được người có quyền nhận và cách dùng tiền.
- Điểm giảm sức ép: Người đăng cho phép chờ; không có dữ kiện ép chuyển ngay hoặc cản kiểm tra.
- Không được kết luận: Mọi quyên góp qua tài khoản cá nhân đều lừa đảo, hoặc người nhận chắc chắn gian dối.
- Khuyến nghị: Xác minh đầu mối, người được ủy quyền và cơ chế minh bạch trước khi đóng góp.

## TH07 — Hồ sơ nhận tiền chứa quyền chuyển tài sản

Kỳ vọng draft **high**; thực tế **need_context**, HTTP 200, 106.31 ms. 8 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người môi giới: Đây chỉ là giấy nhận tiền cọc, chị ký giúp để tôi chuyển tiền.

> [m2] Chủ tài sản: Tôi đọc thì thấy phần cho phép anh thay tôi ký hợp đồng chuyển nhượng và nhận toàn bộ tiền bán. Tôi chỉ định cho thuê, không bán.

> [m3] Người môi giới: Mẫu chung nên ghi rộng vậy thôi. Chị cứ ký, không cần nhờ người khác đọc. Nếu sửa phần đó thì tôi không chuyển cọc nữa. Bản đầy đủ tôi sẽ giữ, chị chỉ cần ảnh trang chữ ký.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản này dùng để thanh toán việc gì?", "Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** “hợp đồng chuyển nhượng” có anchor “đồng” gán transfer_funds; “chuyển nhượng” cũng bị gán chuyển tiền. Không có event quyền ký/chuyển tài sản hoặc relation.

**Nguyên nhân/giới hạn:** Chuẩn hóa bỏ dấu và pattern chuyển tiền quá rộng làm “đồng/đóng” lẫn nhau. Đúng quote về mặt offset nhưng sai nghĩa; policy không thấy quyền rộng hơn mục đích cho thuê.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Phân giải cụm danh từ hợp đồng và hành động ủy quyền theo đối tượng; so phạm vi ký với mục đích. Đối chứng ủy quyền hẹp đúng giao dịch, đủ bản sao.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Ký quyền chuyển nhượng và nhận tiền rộng hơn giao dịch cho thuê.
- Quan hệ phải nối: Lời giải thích “giấy nhận cọc” khác nội dung người dùng đọc được; dùng tiền cọc làm điều kiện ép ký; không cho tham khảo và không giao bản đầy đủ.
- Cơ chế gây hại: Có thể trao quyền định đoạt tài sản hoặc nhận tiền không đúng ý định.
- Không được kết luận: Văn bản chắc chắn có hiệu lực pháp lý hoặc tài sản đã bị chuyển nhượng.
- Khuyến nghị: Chưa ký; đọc đầy đủ và nhờ người tư vấn độc lập kiểm tra phạm vi quyền.

## TH08 — Lương đi qua tài khoản do người khác điều khiển

Kỳ vọng draft **high**; thực tế **need_context**, HTTP 200, 62.81 ms. 4 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người tuyển dụng: Công ty yêu cầu em mở một tài khoản đứng tên mình để nhận lương và xử lý thanh toán công việc.

> [m2] Ứng viên: Tôi tự giữ tài khoản và tự chuyển khi có chứng từ được không?

> [m3] Người tuyển dụng: Không. Em phải giao thông tin đăng nhập, để số điện thoại khôi phục là số của quản lý. Công ty thao tác thay, em chỉ đứng tên. Nếu ngân hàng hỏi người sử dụng thì cứ nói chỉ có em dùng.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản này dùng để thanh toán việc gì?", "Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** “giao thông tin đăng nhập” thành handover_asset; báo cáo/đề nghị “Tôi tự giữ tài khoản...” bị thành yêu cầu chuyển tiền cho bên còn lại. Không có relation.

**Nguyên nhân/giới hạn:** SG-CREDENTIAL trong semantic_graph_patterns.json nhận gui/cung cap/dua/chuyen, thiếu cách nói “giao”. Quyền khôi phục và nghĩa vụ khai đúng người sử dụng chưa được nối thành cơ chế mất quyền tài khoản.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Trích surrender_credentials, đổi recovery owner và khai sai; không đồng nhất giao thông tin đăng nhập với tự đăng nhập. Đối chứng tự giữ mật khẩu/số khôi phục.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Giao thông tin truy cập và quyền khôi phục tài khoản đứng tên mình.
- Quan hệ phải nối: Người dùng đứng tên nhưng bên khác điều khiển; yêu cầu khai sai với ngân hàng.
- Cơ chế gây hại: Mất kiểm soát tài khoản và có thể bị lợi dụng cho giao dịch ngoài ý muốn.
- Không được kết luận: Dòng tiền đã có nguồn gốc bất hợp pháp; “giao thông tin đăng nhập” không phải tự đăng nhập thông thường.
- Khuyến nghị: Không giao quyền truy cập/khôi phục hoặc khai sai người sử dụng.

## TH09 — Quà số yêu cầu quyền không tương xứng

Kỳ vọng draft **high**; thực tế **suspicious**, HTTP 200, 54.33 ms. 2 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người tự nhận hỗ trợ chương trình quà: Bạn chỉ cần ký để xác nhận nhận quà vào ví, không mất tiền.

> [m2] Người dùng: Ví hiển thị yêu cầu cấp quyền cho địa chỉ khác sử dụng toàn bộ số token của tôi, không chỉ nhận quà. Tôi chưa kiểm tra địa chỉ đó.

> [m3] Người hỗ trợ: Đó là cách xác nhận chung. Cứ cấp quyền không giới hạn thì quà mới tới. Đừng hủy yêu cầu hoặc đổi mức quyền, hệ thống sẽ mất suất của bạn.

**API trả cho người dùng:**

Có yêu cầu cài ứng dụng hoặc chia sẻ quyền truy cập cần xác minh.

Hành động đề xuất: Kiểm tra nguồn ứng dụng và đầu mối hỗ trợ độc lập trước khi cấp quyền.

Câu hỏi: []

**Quan sát trong trace:** Trích hai grant_control/request, rule R-ACCESS đưa suspicious; không trích quyền sử dụng token vô hạn và quan hệ nhận quà phụ thuộc cấp quyền.

**Nguyên nhân/giới hạn:** Mức thấp hơn tham khảo vì quyền ví bị đưa vào nhóm quyền truy cập chung. Mô tả cài ứng dụng/chia sẻ quyền là mẫu chung, chưa giải thích đúng nguy cơ quyền định đoạt token.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Gắn grant_authority với tài sản/quy mô quyền và điều kiện nhận quà; giữ nguồn user_reported của thông báo ví, không khẳng định đã kiểm hợp đồng blockchain.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Cấp quyền sử dụng tài sản số không giới hạn cho địa chỉ chưa xác minh.
- Quan hệ phải nối: Lời hứa chỉ xác nhận nhận quà mâu thuẫn với quyền sử dụng token được ví hiển thị theo báo cáo người dùng; áp lực mất suất nếu giảm quyền.
- Cơ chế gây hại: Người được cấp quyền có thể thao tác tài sản trong phạm vi quyền thực tế được cấp.
- Không được kết luận: Đã kiểm tra hợp đồng, ví hoặc token; tài sản đã bị chuyển; mọi chữ ký ví đều cấp quyền rút tiền.
- Khuyến nghị: Không ký/cấp quyền khi chưa hiểu; kiểm tra quyền và địa chỉ qua công cụ đáng tin cậy do người dùng chủ động chọn.

## TH10 — Đặt cọc chỗ ở nhưng thiếu căn cứ về quyền cho thuê

Kỳ vọng draft **suspicious**; thực tế **need_context**, HTTP 200, 69.54 ms. 2 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người đăng phòng: Phòng có nhiều người hỏi, bạn giữ bằng tiền cọc rồi cuối tuần tới xem.

> [m2] Người thuê: Tôi chưa xem trực tiếp. Tên trong giấy chủ nhà anh gửi không giống tên người ký hợp đồng dự thảo.

> [m3] Người đăng phòng: Tôi cho thuê hộ, giấy ủy quyền để cuối tuần đưa. Nếu bạn muốn giữ giá thì chuyển trước hôm nay; chưa chuyển thì tôi không giữ phòng.

> [m4] Người thuê: Tôi chưa gọi được chủ nhà và chưa có giấy tờ xác nhận quyền cho thuê hộ.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật."]

**Quan sát trong trace:** Chỉ trích chuyển tiền phủ định “chưa chuyển” và avoid_verification từ “Tôi chưa gọi được chủ nhà...”; không thấy yêu cầu “chuyển trước hôm nay” hay quyền cho thuê.

**Nguyên nhân/giới hạn:** Cấu trúc điều kiện và phạm vi phủ định bị mất; thiếu authority/ủy quyền khiến policy không biểu diễn bất thường đúng mức suspicious. Báo chưa gọi được khác cấm gọi.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Phân giải yêu cầu hiện tại với mệnh đề chưa chuyển; trích bất nhất người ký và quyền thu cọc. Đối chứng đã xem phòng và xác minh người được ủy quyền.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Đặt cọc trước khi xem và xác nhận quyền cho thuê.
- Quan hệ phải nối: Người ký khác tên giấy chủ nhà; tự nhận cho thuê hộ; chưa có ủy quyền; hạn chót để giữ giá.
- Cơ chế nguy cơ: Có thể trả tiền cho người chưa có căn cứ chứng minh quyền cho thuê hoặc thu cọc.
- Không được kết luận: Nhà không tồn tại hoặc người môi giới chắc chắn giả mạo. Đặt cọc trước tự thân chưa chứng minh lừa đảo.
- Khuyến nghị: Xác minh người có quyền cho thuê và điều kiện hoàn cọc, xem chỗ ở trước khi quyết định.

## TH11 — Hoàn khoản “chuyển dư” trước khi tiền tới

Kỳ vọng draft **high**; thực tế **need_context**, HTTP 200, 99.86 ms. 5 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người mua: Tôi lỡ chuyển thừa tiền, ảnh biên lai ghi cao hơn giá món hàng 4 triệu. Bạn trả phần dư vào tài khoản của bạn tôi giúp nhé.

> [m2] Người bán: Tôi đã tự mở ứng dụng ngân hàng và chưa nhận khoản nào từ anh.

> [m3] Người mua: Tiền đang chờ cập nhật thôi. Bạn dùng tiền sẵn có trả trước, bạn tôi cần gấp. Đừng đợi giao dịch vào, tôi đã gửi ảnh làm bằng chứng rồi.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản này dùng để thanh toán việc gì?", "Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** “giao dịch” bị cắt thành handover_asset anchor “giao”, object “dịch vào”. “Tôi lỡ chuyển thừa tiền” có nhánh thành request của người bán. Thiếu event chưa nhận tiền và hoàn từ tiền sẵn có; không có relation.

**Nguyên nhân/giới hạn:** Đa nghĩa cụm từ và sai vai lời báo xảy ra trước suy luận. Không nối chưa có khoản vào → dùng tiền sẵn có trả bên thứ ba. Câu hỏi mục đích khoản thanh toán hỏi lại dữ kiện đã nêu.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Trích refund/return_funds, negative receipt và third-party destination; giữ biên lai là lời người mua đưa ra, không kết luận giả. Đối chứng đã đối soát nhận khoản dư thật.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Trả tiền từ nguồn sẵn có cho bên thứ ba khi chưa nhận khoản được nói là chuyển dư.
- Quan hệ phải nối: Biên lai là lời người mua cung cấp; người bán tự kiểm tra chưa có tiền; yêu cầu hoàn trước và không chờ xác nhận.
- Cơ chế gây hại: Người bán có thể mất tiền dù khoản thanh toán ban đầu chưa tới.
- Không được kết luận: Biên lai chắc chắn giả hoặc ngân hàng đã xác định giao dịch không tồn tại.
- Khuyến nghị: Không trả khoản chưa nhận; đối soát giao dịch thực tế qua ngân hàng trước.

## TH12 — Thu nhập được dùng để thuyết phục bảo lãnh

Kỳ vọng draft **suspicious**; thực tế **need_context**, HTTP 200, 49.42 ms. 1 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người bạn: Mình cần bạn ký bảo lãnh khoản vay cho dự án. Mình hứa trả đầy đủ, bạn không phải góp vốn.

> [m2] Người dùng: Tôi thấy hợp đồng ghi khi bạn không trả thì bên cho vay có thể yêu cầu tôi thanh toán. Tôi chưa xem phương án kinh doanh hoặc khả năng trả nợ.

> [m3] Người bạn: Dự án chắc chắn có lãi nên không tới mức đó đâu. Bạn cứ xem hợp đồng và kiểm tra thêm, nhưng hiện mình chưa có hồ sơ tài chính để gửi.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Người gửi yêu cầu thao tác hoặc điều kiện cụ thể nào? Hãy cung cấp phần liên quan đã che bí mật."]

**Quan sát trong trace:** Chỉ có transfer_funds/claim từ nghĩa vụ trả thay trong hợp đồng; không có event ký bảo lãnh hay nghĩa vụ có điều kiện.

**Nguyên nhân/giới hạn:** Schema/event inventory đang dùng chưa mô hình đầy đủ bảo lãnh và khả năng trả nợ. Câu hỏi thao tác cụ thể là thừa vì hành động ký đã có. Chưa có căn cứ ép ký nên không tự sửa bằng cách nâng high.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Trích ký bảo lãnh và điều kiện trả thay, quyền kiểm tra đã được cho phép; giải thích nghĩa vụ tiềm tàng. Đối chứng nghĩa vụ được hiểu rõ và hồ sơ tài chính đầy đủ.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Hành động: Ký bảo lãnh khoản vay cho người khác.
- Quan hệ phải nối: Lời trấn an “không phải góp vốn” không loại nghĩa vụ được nêu trong hợp đồng; khả năng trả nợ chưa có hồ sơ; khẳng định chắc chắn có lãi chưa được chứng minh.
- Cơ chế nguy cơ: Có thể phát sinh nghĩa vụ tài chính nếu bên vay không trả.
- Điểm cần giữ đúng: Người bạn cho phép xem và kiểm tra; chưa có bằng chứng ép ký, giấu điều khoản hoặc giả danh. Không tự nâng high chỉ vì bảo lãnh.
- Cần kiểm tra: Phạm vi nghĩa vụ và khả năng trả nợ có được xác minh độc lập không?
- Khuyến nghị: Đánh giá nghĩa vụ trong hợp đồng và khả năng chịu rủi ro trước khi ký. Không coi lời hứa là bảo đảm.

## TH13 — Đối chứng hợp lệ về hợp đồng đào tạo

Kỳ vọng draft **clear**; thực tế **need_context**, HTTP 200, 70.94 ms. 6 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người học: Tôi chỉ muốn học kỹ năng, không muốn vay và không cần cam kết việc làm.

> [m2] Tư vấn viên: Bạn có thể chọn gói trả trực tiếp. Học phí, nội dung và điều kiện hoàn tiền trong hợp đồng; không bảo đảm thu nhập sau khóa học. Bạn đọc trước, hỏi thêm người tư vấn độc lập nếu cần, chưa đồng ý thì chưa đóng tiền.

> [m3] Người học: Tôi chưa thanh toán và đang so sánh với những khóa khác.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản này dùng để thanh toán việc gì?", "Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** “không cần cam kết việc làm” thành offer_employment/positive; “đồng” trong “hợp đồng” và “chưa đồng ý thì chưa đóng tiền” tạo transfer_funds/request.

**Nguyên nhân/giới hạn:** Phủ định và từ đa nghĩa tạo yêu cầu không có thật, làm đối chứng hợp lệ bị need_context. Đây không phải thiếu dữ kiện về chuyển tiền nhận thưởng.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Giữ scope của không muốn/không cần/chưa đồng ý; nhận diện lời cho phép đọc trước, chưa đóng tiền. Test đối chứng có cùng khóa học/học phí/việc làm.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Căn cứ: Không buộc vay, không hứa thu nhập, có điều khoản được xem trước và cho phép tham khảo độc lập.
- Yêu cầu suy luận: Không chuyển nhãn chỉ vì có từ “khóa học”, “học phí”, “hoàn tiền” hoặc “việc làm”.
- Giới hạn: Chưa thấy dấu hiệu đáng ngờ trong đoạn cung cấp; chưa xác minh chất lượng khóa học hoặc tổ chức.
- Không hỏi thừa: Không hỏi mã đăng nhập, điều kiện rút tiền hoặc thông tin ngoài tình huống.

## TH14 — Chưa biết nội dung văn bản cần ký

Kỳ vọng draft **need_context**; thực tế **need_context**, HTTP 200, 78.11 ms. 6 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người dùng: Một người nhờ tôi ký giấy để hoàn tất việc nhận tiền. Tôi chưa mở được giấy đó, cũng chưa biết mình nhận tiền cho việc gì. Chỉ có câu “ký giúp rồi tôi xử lý tiếp”, chưa có yêu cầu chuyển tiền hay gửi mã.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản này dùng để thanh toán việc gì?", "Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** Mức need_context khớp, nhưng “chưa có yêu cầu chuyển tiền hay gửi mã” sinh provide_code/request/positive và một payment/request. “chưa biết mình nhận tiền...” bị hiểu là trạng thái nhận tiền phủ định.

**Nguyên nhân/giới hạn:** Đúng mức nhưng sai căn cứ. Phạm vi phủ định không phủ hết vế phối hợp “hay”, và chưa biết X bị lẫn với X chưa xảy ra. Câu hỏi thiếu mục tiêu đọc nội dung/quyền trên giấy.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Giữ sự chưa biết độc lập với phủ định sự kiện, không dựng gửi mã/chuyển tiền. Hỏi mục đích nhận tiền và nội dung xác nhận/ủy quyền của giấy.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Thiếu gì: Mục đích khoản tiền, vai người nhờ và nội dung/quyền nghĩa vụ của giấy cần ký.
- Câu hỏi phù hợp: “Khoản tiền liên quan việc gì, và giấy đó yêu cầu bạn xác nhận hoặc ủy quyền điều gì?”
- Không được suy ra: Đây là phí rút tiền, giấy vay hay yêu cầu chuyển quyền tài sản.
- Khuyến nghị ngắn: Đọc và hiểu nội dung trước khi ký, không cung cấp dữ liệu bí mật để làm rõ.

## TH15 — Hai người nhận thuộc hai giao dịch khác nhau

Kỳ vọng draft **clear**; thực tế **need_context**, HTTP 200, 113.28 ms. 7 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người dùng: Hóa đơn A do công ty Minh An bán, hóa đơn B do cửa hàng Hòa Bình bán. Tôi đã gọi đúng đầu mối trên từng hợp đồng và xác nhận riêng tài khoản của mỗi bên. Tôi tự kiểm tra cả hai hóa đơn trước khi thanh toán.

> [m2] Đồng nghiệp: Vậy chuyển tiền A cho Minh An, tiền B cho Hòa Bình theo đúng từng hóa đơn. Không có đề nghị đổi tài khoản hay gộp khoản nào.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** “đồng” trong “hợp đồng” sinh transfer_funds; “Tôi đã gọi...” sinh avoid_verification/request. Không có relation tách giao dịch A/B.

**Nguyên nhân/giới hạn:** Hai giao dịch đã được người dùng báo xác minh bị đưa vào pattern tiền chung; không có trạng thái xác minh theo từng hóa đơn để giảm bất định. “Tôi/tối” sau bỏ dấu là một nguồn nhầm cần kiểm.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Giữ hai transaction và xác nhận user_reported riêng; không coi có hai người nhận là đổi tài khoản. Đối chứng chỉ A được xác minh, B chưa rõ.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Căn cứ: Hai hóa đơn, hai đơn vị và hai tài khoản thuộc hai giao dịch riêng đã được người dùng báo xác nhận qua đầu mối hợp đồng.
- Yêu cầu suy luận: Tách A/B; không coi việc có hai người nhận tiền là đổi tài khoản hoặc chuyển lòng vòng.
- Nguồn: Việc xác nhận là user_reported, không phải backend trực tiếp kiểm tra.
- Giới hạn: Không thấy dấu hiệu trong nội dung đã cung cấp; không khẳng định hai đơn vị an toàn tuyệt đối.

## TH16 — Tham chiếu chưa đủ để nối điều kiện

Kỳ vọng draft **need_context**; thực tế **need_context**, HTTP 200, 82.31 ms. 1 event, 0 relation trong lượt debug.

**Đầu vào nguyên văn, đúng nhãn người nói:**

> [m1] Người dùng: Trong đoạn chat tôi chỉ còn hai tin. Người thứ nhất nói “Khoản đó vẫn chưa xong”. Người thứ hai nói “Vậy cứ gửi trước đi”. Tôi không biết “khoản đó” là tiền hay hồ sơ, “gửi” là gửi giấy hay chuyển tiền, và hai tin có nói về cùng một việc không.

**API trả cho người dùng:**

Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.

Hành động đề xuất: Xác minh hành động và điều kiện cụ thể qua đầu mối độc lập.

Câu hỏi: ["Khoản này dùng để thanh toán việc gì?", "Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?"]

**Quan sát trong trace:** Mức need_context khớp, nhưng sự lựa chọn “gửi giấy hay chuyển tiền” trong câu không biết bị trích transfer_funds/request/positive. Không trích hai người được thuật lại thành hai nguồn riêng.

**Nguyên nhân/giới hạn:** Đúng mức nhưng sai căn cứ; parser không giữ alternatives/unknown cho đối tượng và nguồn lời trích. Câu hỏi “Khoản này dùng để thanh toán việc gì?” đã giả định là thanh toán.

**Cách sửa tổng quát và đối chứng cần bổ sung:** Giữ đối tượng unresolved và hai nguồn được kể lại riêng; không biến lời người dùng mô tả bất định thành yêu cầu. Hỏi tin trước để xác định gửi gì và cùng hay khác việc.

**Phân tích tham khảo của tài liệu, không đưa vào inference:**

- Thiếu gì: Đối tượng của “khoản đó” và “gửi”, vai của hai bên, cùng hay khác sự việc.
- Câu hỏi phù hợp: “Bạn có thể bổ sung tin trước đó để xác định ‘khoản đó’ và thứ được yêu cầu gửi là gì không?”
- Không được suy ra: “Khoản” chắc chắn là tiền, “gửi” chắc chắn là chuyển khoản, hoặc đây là yêu cầu trả tiền trước.
- Yêu cầu kỹ thuật: Giữ hai người chưa xác định riêng, không gộp vì cùng nhãn unknown. Không bịa thứ tự hoặc quan hệ còn thiếu.
