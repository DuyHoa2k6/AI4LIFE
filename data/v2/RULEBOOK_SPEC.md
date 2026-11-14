# Đặc tả suy luận và giải thích cục bộ

rulebook.json là dữ liệu kiểm tra được bằng Rulebook/Pydantic và rulebook.schema.json.
Mỗi rule có ID/version/description/scope/required_facts/required_relations/exclusions/
missing_fact_policy/conclusion/evidence_requirements/follow_up_question_template/
explanation_template_id/test_case_ids. Không eval, Python expression hoặc template code.

## Điều kiện áp dụng

Fact chỉ lấy từ event có quote/offset/tham chiếu hợp lệ, polarity phù hợp, đúng vai,
thời gian và attribution. Quoted_warning/denial/hypothetical/unknown không thành
yêu cầu dương tính. Sự kiện quá khứ không áp như nguy hiểm hiện tại. Multi-fact
rule cần cùng scope và người bị tác động. Relation cần đúng hướng, cả hai đầu mút
và status khác unknown. Chỉ đối chiếu tên thủ đoạn hoặc quốc gia không đủ điều kiện.

| Quy tắc | Căn cứ cần thiết | Kết luận tham chiếu / ngoại lệ |
|---|---|---|
| R-HANDOVER | Request giao + trạng thái chưa nhận + before cùng giao dịch | suspicious; cập nhật nhận đủ có thời gian loại căn cứ cũ |
| R-CREDENTIAL | Request giao mật khẩu/mã rõ loại | high; tự nhập mã không thuộc điều kiện |
| R-CODE-IDENTITY | Request dãy số + tin xác định là mã đăng nhập + liên kết | high; sáu số chưa rõ loại phải hỏi |
| R-PAY-TO-WITHDRAW | Chuyển tiền + lợi ích rút/nhận + prerequisite_for | high; không ghép hai giao dịch |
| R-DATA | Request giấy tờ qua nội dung đang xét | suspicious, không khẳng định người gửi mạo danh |
| R-ACCESS | Cài/giao quyền trực tiếp | suspicious, không suy app chắc độc hại |
| R-TRAVEL-SECRET | Lời mời + yêu cầu giấu, cùng người/phạm vi | suspicious, không kết luận mua bán người |
| R-DEBT-EXIT | Nợ + hạn chế rời đi + quan hệ | high, urgency xét riêng |
| R-DOC-EXIT | Giữ giấy tờ + hạn chế rời đi + quan hệ | high, không suy nội tạng |
| R-CONTROL | Giữ giấy tờ/hạn chế liên lạc chưa rõ quyền tự quyết | suspicious; trả giấy tờ tự do chỉ miễn đúng việc giữ giấy tờ, không miễn kiểm soát điện thoại |
| R-CHANGE-WORK | Lời mời và điều kiện thực khác thỏa thuận | suspicious, relation inferred cần người rà |
| R-RELEASE | Đòi tiền để rời đi/thả người, hai vế có quote | high/preventive; chưa chứng minh bắt giữ thật |
| R-COERCION | Đe dọa/ép làm việc/ép hành vi phạm pháp/đe dọa thân thể | high, chưa xác minh toàn bộ sự việc |
| R-URGENT-CURRENT | Self/user report đang bị hạn chế/cưỡng ép | high/urgent, không chờ đủ 18 ô |
| R-URGENT-THREAT | Đe dọa gây hại trực tiếp đang/sắp xảy ra | high/urgent, không đòi danh tính tổ chức trước hỗ trợ |

## Tổng hợp và xung đột

Không cộng điểm hoặc bỏ phiếu. Lấy mức cao nhất trong các rule **đã đủ căn cứ**;
urgent có ưu tiên trình bày riêng. Gộp ID và evidence bằng tập để không cộng lặp.
Các xung đột thật chưa giải quyết giữ need_context khi không có căn cứ high/urgent
độc lập. Không hạ hành vi rõ chỉ vì thiếu danh tính. Không biến lỗi thực thi thành clear.

Clear chỉ cho các vai/căn cứ đã giải thích được trong phạm vi hiện có, ví dụ lời
cảnh báo/phủ định/quá khứ hoặc điều kiện đối chứng phù hợp. Ngoài độ phủ là need_context.
Bối cảnh xác minh do người dùng báo chỉ hỗ trợ message nó áp dụng, không miễn lời
mời khác trong chuỗi. Nó không phải xác minh của hệ thống.

## Khẩn cấp và lỗi

Safety precheck chạy trước bộ trích đầy đủ. Khi rule urgent đủ căn cứ, trả ngay
thông tin hỗ trợ, 18 trường còn thiếu giữ unknown, không đợi RAG hoặc hỏi thêm.
Nếu bước khác lỗi, tín hiệu urgent đã kiểm chứng không bị đổi thành ít rủi ro.
Nếu bản thân cấu hình/bằng chứng không kiểm chứng được, API trả error và
risk_status=null, kèm hướng hỗ trợ chung; không có màu clear.

Không tự tạo hotline/địa chỉ. support_directory.json hiện rỗng; support_contacts=[]
cho đến khi có danh bạ vùng đã duyệt/còn hiệu lực và cơ chế chọn vùng phù hợp.
Không yêu cầu người dùng gửi giấy tờ/ảnh riêng tư/mô tả tổn hại chi tiết; câu hỏi có thể bỏ qua.

## Mẫu diễn đạt

templates.json dùng schema Templates, chỉ text có kiểm soát và slot verified_quotes.
Backend chọn template theo rule đã áp dụng, quote nằm riêng trong annotations và
UI chỉ dựng khi đối chiếu lại đúng input. Thiếu slot hoặc bằng chứng thì dùng
TPL-UNKNOWN/TPL-ERROR thay vì tự điền. Không dùng prose tự do hay tên tội danh do
mô hình sinh. prohibited_conclusions cấm receipt_is_fake, trafficking_confirmed,
kidnapping_proven, organ_removal_inferred, identity_verified_by_system và suy an
toàn chỉ vì không có RAG match.

## Tri thức và nguồn

Mô-đun search chỉ đọc kho nguồn chính thống qua cổng approved/reviewer/ngày/hiệu lực/
reuse_approved. Candidate và community_reports không vào kết quả. Hiện 0 nguồn
đủ điều kiện nên fallback là bình thường, không xóa cảnh báo từ lời gốc.
Local v2 gắn nguồn ở mức background_only, entity_verified=false; chưa có bộ đọc hiểu
nguồn học máy hay đối chiếu đối tượng cụ thể. Không khôi phục trạng thái verified_match
đã bỏ khỏi sản phẩm. Không dùng nguồn làm quote cho hành vi trong hội thoại.
