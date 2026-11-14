# Bốn trạng thái và cách giải quyết thông tin thiếu

Áp dụng cho luồng hiện hành `SCAMSHIELD_MODE=two_pass`, quyết định `two-pass-6`, API 1.9.
Backend giữ quyền gán risk_status. Gemini trả hành vi, bằng chứng, quan hệ và phần
chưa rõ; không tự trả mức cảnh báo. Màu chỉ hiển thị kết quả backend.

## Đầu vào cần phân biệt

- **Hành động:** người gửi muốn người nhận làm gì, với đối tượng nào?
- **Vai câu:** yêu cầu trực tiếp, lời kể/tự nhận, phủ định, trích để cảnh báo hay chưa rõ?
- **Quan hệ:** nguyên văn có nêu hành động là điều kiện trước lợi ích/sức ép không?
- **Bối cảnh:** có giao dịch bình thường hoặc lời dẫn thay đổi cách hiểu không?
- **Bằng chứng:** đúng message, người nói và đoạn trích/offset Unicode không?

Các câu “đã cài từ trước”, “tôi tự nhập mã”, “không ai yêu cầu giao mã” không tự
trở thành yêu cầu cài/giao mã. “Chưa giải thích mục đích” không phải lời hứa hay
điều kiện nhận lợi ích. Regex bắt được từ khóa không chứng minh bất kỳ điều nào đó.

## high — Đã có căn cứ hành vi nguy hiểm đủ mạnh

Bản 6 không coi mọi request gắn lợi ích là high. Ngoài giao mã đăng nhập, các
quan hệ tiền/cài ứng dụng/cấp quyền gắn điều kiện rủi ro, backend nhận chuỗi có
bằng chứng: chia sẻ màn hình rồi mở ngân hàng; hoặc yêu cầu đọc dãy số được tin
liên quan xác định là mã đăng nhập. Chứng cứ xác định loại mã có thể thuộc người
nhận, còn yêu cầu giao mã vẫn thuộc người gửi. Không ghép hai người vào một finding.
Xin giấy tờ định danh qua chat chỉ để giữ suất chưa tự đủ high.

Một trong các căn cứ được backend chấp nhận:

1. Yêu cầu giao thông tin xác thực cho người khác được trích hợp lệ, không còn
   bất định về chính hành động. Tự nhập OTP trong ứng dụng của mình không thuộc căn cứ này.
2. Yêu cầu chuyển tiền, cài ứng dụng hoặc cấp quyền được nối tới inducement bằng quan hệ hợp lệ:
   có lời hứa, điều kiện, lợi ích hoặc sức ép thực sự trong văn bản, cùng người nói
   phù hợp và không bị bác bởi vai cảnh báo, giao dịch bình thường hoặc bất định chặn.
3. Chuỗi chia sẻ màn hình rồi mở dữ liệu ngân hàng, hoặc yêu cầu giao dãy ký tự
   được tin liên quan xác định là mã đăng nhập, có các fact/link đã kiểm chứng.

Ví dụ: “Gửi OTP cho tôi để tôi đăng nhập tài khoản của bạn”; “Nộp 500 nghìn trước
thì mới rút được tiền”. Đổi tên phí thành tiền đồng bộ không đổi quan hệ hành vi.

Không cần biết danh tính thật mới cảnh báo. Nếu hành động/quan hệ đủ rõ, có thể
vừa high vừa hỏi xác minh người gửi. Không dùng thiếu danh tính để xóa nguy hiểm.
High không xác nhận tội phạm, danh tính hoặc hiệu lực thực tế của một mã OTP.

## suspicious — Có yêu cầu đáng lo đã rõ nhưng chưa đủ căn cứ high

Bổ sung bản 6: giao tài sản khi thanh toán chưa được xác nhận; đổi tài khoản nhận
tiền rồi yêu cầu chuyển trước/xác minh sau; xin giấy tờ nhạy cảm qua kênh chưa xác
minh. Mỗi dấu hiệu cần fact và quote hợp lệ. Chưa xác minh tài khoản là thật không
làm thứ tự chuyển trước/xác minh sau thành chưa rõ. Không tự kết luận biên lai giả.

Có request cần xác minh, chưa có căn cứ high và không còn bất định chặn kết luận.
Yêu cầu cài APK/giao quyền đã rõ nhưng chưa xác minh nhà phát hành hoặc đơn vị hỗ
trợ có thể thuộc mức này. Trong chính sách hiện hành, bất định chỉ về identity/purpose
không chặn mức này cho install_app/grant_access khi không có yêu cầu tiền hoặc bất
đồng quan trọng. Hỏi thêm nguồn cài/mục đích cấp quyền vẫn hữu ích.

Dấu hiệu URL mạnh thật sự được quan sát có thể hỗ trợ suspicious nếu gắn với một
request hợp lệ; lời cảnh báo chứa URL không tự bị nâng mức. Chuyển miền, HTTP 200,
HTTP 404 hoặc tương tự một tài liệu RAG không tự quyết định trạng thái.

Ví dụ: “Cài APK tôi gửi qua tin nhắn riêng” chưa rõ nguồn, không có lời hứa/điều
kiện để kết luận high; nhãn đường dẫn khác đích đi cùng yêu cầu đăng nhập.

## need_context — Chưa đủ dữ kiện ảnh hưởng quyết định

Bản 6 dùng information_gaps gắn bằng chứng, ưu tiên hỏi bước, đối tượng hoặc điều
kiện thực sự thiếu. Trạng thái chờ rút chưa có yêu cầu tiếp theo hỏi có yêu cầu
chuyển tiền/cung cấp thông tin không, không suy ra đã có phí. Thu thập thêm dữ liệu
không tự hạ một dấu hiệu rõ đang đủ suspicious hoặc high.

Thiếu thông tin có thể làm thay đổi loại hành động hoặc cách đánh giá:

| Thiếu gì? | Ví dụ | Chủ đề hỏi |
| --- | --- | --- |
| Bước cụ thể | “Làm bước kia trước” | requested_action |
| Đối tượng được gửi | “Gửi cái đó cho tôi” | requested_object |
| Mục đích khoản tiền | “Chuyển khoản cho tôi” | payment_purpose |
| Quan hệ giữa hai bước | Không biết thao tác nào là điều kiện | action_relation |
| Nguồn cài/quyền | Chưa rõ tệp/kênh hoặc mục đích truy cập | file_origin/permission_purpose/channel |

Không tự đoán “cái đó” là OTP hoặc tiền. Cấu trúc “làm trước mới xử lý tiếp” chưa đủ
high nếu chưa biết hành động. Nhóm other còn chưa rõ mục đích có thể giữ need_context
theo chính sách hiện hành; không mặc định mọi yêu cầu khác là đáng ngờ.

Chỉ giữ trạng thái này do bất định thực sự hoặc quan sát Gemini đầu chưa được lượt
cuối giải quyết. Một gợi ý regex đã được rà và phân loại lại có căn cứ không tự
tạo xung đột. Nếu model không trả được cấu trúc hợp lệ sau lần rà sửa hữu hạn,
trả lỗi phân tích; không biến lỗi thực thi thành need_context.

Câu hỏi tối đa hai, ưu tiên phần thiếu trực tiếp ảnh hưởng kết luận. Chỉ xin loại
thông tin/nguyên văn đã che; không yêu cầu OTP, mật khẩu hoặc bí mật thật.

## clear — Chưa thấy yêu cầu đáng ngờ còn hiệu lực

Bối cảnh có thể nằm ngay trong messages. Bản 6 cho phép người nhận tiền cho biết
đã kiểm tra/nhận đủ, hoặc người được yêu cầu thanh toán xác nhận giao dịch thông
thường, hỗ trợ đúng request tương ứng. Quote phải từ người liên quan khác bên yêu
cầu, đúng metadata và cùng tình huống; người trả chỉ gửi biên lai không đủ thay thế.
Đây là đánh giá theo nội dung khai báo, không phải kết nối ngân hàng/xác minh ngoài
đời. Bối cảnh của khoản thanh toán không miễn một yêu cầu OTP hoặc khoản phí mới khác.

Sau khi đọc đúng vai/bối cảnh, không còn request đáng ngờ hoặc bất định quan trọng:
lịch họp, lời kể thao tác đã làm, trích lời dụ để cảnh báo, hoặc giao dịch bình thường
có bối cảnh được đối chiếu. Miễn một request thật nhờ bối cảnh cần context_evidence
khớp nguyên văn trong ô context hoặc situation fact/link hợp lệ từ hội thoại;
chỉ nói quen người gửi không đủ miễn việc giao OTP.

Ví dụ: “Cảnh giác với lời dụ nộp phí nhận thưởng”; tự nhập mã trong ứng dụng quen
dùng; nhắc trả đúng khoản vay có bối cảnh xác nhận. Không thấy kịch bản tương tự
trong RAG không phải lý do cho clear. Clear không chứng nhận an toàn hoặc danh tính.

## Thứ tự và sự khác biệt

Backend xét high đủ căn cứ trước; sau đó xử lý ngoại lệ suspicious rõ hành động,
bất định cần bối cảnh, request còn cần xác minh và cuối cùng clear. Đây không phải
phép cộng điểm: need_context là trạng thái kiến thức chưa đủ, không phải tỷ lệ rủi
ro 25%. suspicious/high là cảnh báo về hành vi đã quan sát. Mọi mức có thể cần xác
minh độc lập; hỏi thêm không tự làm một high đủ căn cứ bị hạ mức.

Regex hiện chỉ đưa tối đa 12 `rule_hints`. Lượt Gemini cuối phải trả đủ
`rule_hint_reviews`: xác nhận request, phân loại lại claim/denial/quoted_warning,
bác gợi ý không được hỗ trợ hoặc nêu phần chưa rõ. Backend kiểm tra trích dẫn,
tham chiếu, độ phủ và câu hỏi trước khi nhận. Quote đúng không tự chứng minh đúng
ngữ nghĩa; cần kiểm thử tiếp trên tập độc lập để đo giới hạn của phán đoán model.

Nhánh mock/hybrid cũ giữ để đối chứng; mô tả vai trò gợi ý mới áp dụng cho two_pass.

## Kiểm chứng và phục hồi

Provider dùng InitialReviewDraft/FinalReviewDraftV6, không chép lại speaker. Backend
nối tác giả bằng message_id gốc; ID lạ, quote sai, quote mơ hồ hoặc finding ghép nhiều
người nói bị chặn. Không sửa chữ, đoán ID hoặc đổi tác giả để cho qua.
Một lượt phân tích có tối đa một lần yêu cầu sửa dùng chung hai bước, tổng tối đa
ba lần gọi model trước retry HTTP cấu hình sẵn. Chẩn đoán công khai chỉ có loại lỗi/
vị trí, không echo quote, tên tùy ý hoặc bí mật. Còn lỗi trả “Chưa kiểm tra được”.

Situation facts tối đa 16, links 10, gaps 5, câu hỏi công khai tối đa 2. Supported
link nói về quan hệ trong lời gốc; thiếu xác minh danh tính không tự thành bất định
quan hệ. Uncertain link phải có gap thực sự về hành động/đối tượng/quan hệ. Dữ liệu
truy xuất chỉ hỗ trợ giải thích, không thay bằng chứng trong lời người dùng.
