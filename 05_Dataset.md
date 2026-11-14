# Dataset và kho tri thức

## Luồng hiện hành: tách ba kho

Bộ dữ liệu mới cho hướng thay dần cả hai lượt mô hình nằm tại [data/v2](data/v2/README.md):
70 ca pilot nhãn yếu (3 chuyển từ dev), schema 2.0, nhãn, rulebook, template,
hướng dẫn gán nhãn/chia tập, validator và công cụ xuất dữ liệu chỉ đã reviewed.
Không ghi đè dữ liệu cũ; không coi pilot phát triển là test độc lập. Chi tiết nguồn,
giới hạn và tình trạng chưa huấn luyện mô hình ở [dataset card](data/v2/DATASET_CARD.md).

Bổ sung 12/11/2026 cho bước Python /api/observe: `data/abbreviations_vi.json` là
kho viết tắt có ngữ cảnh, nghĩa cạnh tranh và phiên bản; `data/abbreviations_examples.jsonl`
chứa 29 mẫu phát triển có nhãn nháp, không phải dữ liệu độc lập hay nhãn rủi ro.
Không thay các tập cũ. Chỉ bản khớp luật được mở rộng, quote/offset dùng nguyên bản;
từ mơ hồ giữ lại và hỏi thêm. [Cấu trúc và giới hạn](data/README_ABBREVIATIONS.md).

Theo yêu cầu mới ngày 08/11/2026, two_pass dùng `ScamShield_AI/knowledge/scenarios.jsonl` cho ví dụ runtime, `data/knowledge_sources.jsonl` cho nguồn chính thống có phê duyệt; dev/validation/holdout chỉ phục vụ phát triển/đánh giá. Regex dò dấu hiệu cụ thể, retrieval xếp hạng từ vựng/action; không coi giống từ khóa là cùng nhãn. Kho runtime có 10 ví dụ tổng hợp viết riêng, gồm đối chứng bình thường, không lấy expected của tập đánh giá.

Nguồn hiện vẫn candidate. Điều kiện approved/reviewer/approved_at/checked_at/reuse_approved/valid_until/source_role tại [TWO_PASS.md](ScamShield_AI/TWO_PASS.md); không tự duyệt theo domain. Không có nguồn không chứng minh an toàn; ví dụ và tài liệu có thể cùng xuất xứ nên không là hai xác nhận độc lập. Khóa hash cả hai kho trước chấm; chỉ gửi input, lưu dự đoán trước khi đọc expected. Ca tổng hợp không thay đánh giá độc lập, ghi riêng lỗi và chưa chạy.

Đánh giá hybrid (08/11/2026) dùng ca tổng hợp công khai cho kiểm thử điều phối và transport giả lập. Không coi phản hồi live giả lập là năng lực mô hình thật. Giữ validation/holdout ngoài phiên chỉnh hybrid; không trộn dev/expected vào prompt, bộ quy tắc hoặc chỉ mục. Chỉ có input và giả thuyết quy tắc sinh từ input được gửi live. Chất lượng live thực và chênh lệch so với quy tắc phải đo riêng sau cấu hình provider.

## Phát triển mock hành vi — 08/11/2026

Số liệu file hiện tại được audit là 36 mẫu tổng hợp (12 mỗi tập), không phải 72 như mô tả gói dự kiến bên dưới. Dùng dev và ca tổng hợp công khai trong tests để phát triển quy tắc; mỗi nhóm có đối chứng hợp lệ/cảnh báo/phủ định/thiếu bối cảnh. Validation chỉ chọn cấu hình sau phát triển, holdout giữ độc lập, không mở để tìm từ khóa. Báo cáo dev là phân tích phát triển, không phải chất lượng độc lập. Quy tắc không tự đọc dev/validation/holdout/knowledge_seed khi phục vụ request. Đáp án không được vào runtime hay prompt/chỉ mục. Ca đã dùng sửa phải ghi là dữ liệu phát triển.

Dataset khởi tạo gồm 72 tình huống văn bản tiếng Việt tổng hợp, 24 mẫu mỗi tập dev, validation và holdout. Các nhóm tình huống giữa ba tập được tách theo family_id. Nhãn là kỳ vọng biên soạn, cần được rà lại độc lập trước khi báo cáo chất lượng. Tập này thích hợp cho kiểm thử sớm và thiết kế prompt, chưa đủ để kết luận độ chính xác ngoài thực tế hoặc để huấn luyện mô hình có độ phủ cao.

## Cách đưa dữ liệu cho máy

Định dạng JSONL UTF-8. Mỗi dòng là một object hoàn chỉnh. Đọc theo từng dòng để không phụ thuộc dữ liệu nằm vừa trong bộ nhớ. Các file tham chiếu tại [README](README.md).

| Trường | Vai trò |
| --- | --- |
| id, schema_version | Định danh ổn định và phiên bản |
| split, family_id | Kiểm soát chia tập theo họ tình huống, không gửi vào mô hình |
| provenance | Mẫu tổng hợp hay mẫu có nguồn, trạng thái rà soát |
| input.messages | Dữ liệu đầu vào có thứ tự, gồm id, speaker, text |
| expected.risk_status | Nhãn tham chiếu do người gán nhãn đặt |
| expected.findings | Hành vi có bằng chứng, gồm action, message_id, quote |
| expected.scenario_reference | Tên dùng cho người rà soát, không phải lớp bắt buộc mô hình dự đoán |
| expected.follow_up_example | Ví dụ câu hỏi hữu ích. Có thể chấm theo ý nghĩa thay vì khớp chữ |

Ví dụ hai tin nhắn chứa lời mời nhập mã để nhận tiền. Runtime chỉ nhận input.messages. Script đánh giá đối chiếu findings với mã hành vi và tin nhắn liên quan, rồi kiểm tra đoạn trích nguyên văn và đánh giá ý nghĩa. Không yêu cầu trích cả tin nếu một cụm ngắn hơn vẫn đủ rõ. Trường expected chỉ đọc sau khi có dự đoán.

## Hướng dẫn gán nhãn

1. Ghi rõ lời yêu cầu và ai đang nói. “Đừng gửi OTP” là lời ngăn cản. “Họ nhắn ‘gửi OTP cho tôi’” là nội dung được trích. Gắn đúng vai của người yêu cầu trước khi đánh giá.
2. Trích đoạn gốc đủ chứng minh hành vi. Nếu suy ra từ nhiều tin, liệt kê từng căn cứ. Không đưa suy đoán người gửi đã làm gì vào phần quan sát.
3. Chọn mức rủi ro theo 03 và nêu lý do. Nếu thiếu dữ liệu quan trọng, ghi một câu hỏi có thể thay đổi đánh giá. Một số mẫu mơ hồ có nhiều cách gán hợp lý, cần ghi lại bất đồng.
4. Hai người rà độc lập một phần mẫu, sau đó thống nhất cách xử lý ca tranh cãi. Đóng băng version và hash trước khi chạy đánh giá.
5. Khi mở rộng, nhóm theo chiến dịch, template, kịch bản gốc hoặc nguồn liên quan. Khử trùng lặp gần giống. Thêm câu chuyện hợp lệ, tiếng Việt không dấu, hội thoại nhiều người và trích dẫn lồng nhau.

## Tránh lộ tập đánh giá

Dùng dev để xây prompt. Dùng validation để chọn cấu hình. Chỉ cấp holdout cho công cụ chấm sau khi khóa prompt và quy tắc. Gói bàn giao có cả ba tập để Hòa quản lý, nên tách holdout khỏi workspace của AI triển khai. Nếu AI đã đọc gói đầy đủ hoặc ca đó đã xuất hiện trong tài liệu thiết kế, coi đó là tập kiểm tra công khai và tạo thêm holdout độc lập. Các biến thể cùng họ không được tách sang nhiều tập.

## Kho tri thức và nguồn

knowledge_seed.jsonl gồm năm kịch bản ứng viên để thiết kế tính năng truy xuất. Chúng có trạng thái candidate và block_eligible=false. Chỉ nhập vào chỉ mục phục vụ người dùng sau khi rà nguồn, chỉnh nội dung và duyệt. Không dùng knowledge_seed để nâng ca tương tự thành verified_match. Các mục có source_role=background_only dẫn đến tài liệu bối cảnh, chưa chứng minh một trường hợp cụ thể.

Nguồn mở rộng gồm thông báo của cơ quan nhà nước, cảnh báo từ tổ chức bị mạo danh và mẫu đã được đồng ý sử dụng. Lưu nguồn, ngày truy cập, giấy phép hoặc điều kiện sử dụng, loại nội dung và trạng thái rà soát. Khi nguồn là bài tuyên truyền, có thể biên soạn lại tình huống giả định và ghi rõ nguồn cảm hứng, tránh dùng bài tuyên truyền như lời dẫn dụ gốc. Không lưu danh tính, OTP, URL hoạt động độc hại hay thông tin thanh toán thật trong tập mẫu.

Nguồn bối cảnh [Bộ Công an về các kịch bản lừa đảo trên không gian mạng](https://www.bocongan.gov.vn/bai-viet/nang-cao-canh-giac-truoc-25-kich-ban-lua-dao-tren-khong-gian-mang-nam-2026-1788865614).

## Bản dữ liệu mở rộng

Bản này bổ sung 36 mẫu trong 12 họ hiện có. Ba tập có tổng cộng 13 họ. Từng họ mở rộng có tình huống dẫn dụ, đối chứng hợp lệ và thêm một biến thể đáng ngờ hoặc ca thiếu bối cảnh. Mẫu tổng hợp mô phỏng nội dung để kiểm thử. Nhãn là mức cảnh báo kỳ vọng của hệ thống, cần hai người rà độc lập trước khi dùng làm số liệu dự thi.

Ưu tiên đánh giá sự chuyển đổi về ngữ cảnh. Ví dụ, hành vi yêu cầu giao mã đăng nhập xuất hiện dưới vai kỹ thuật viên, người giao hàng hoặc người mua. Kiểm tra mô hình có nhận đúng hành vi khi đổi cách nói, trong khi bài cảnh báo có cùng từ khóa vẫn được hiểu đúng. Để kiểm tra suy luận qua nhiều tin, so ca đầy đủ với ca cắt mất điều kiện chuyển tiền hoặc cấp quyền. Tách kết quả theo nhóm ca, tránh dùng điểm gộp che khuất các lỗi này.

## Dữ liệu nguồn phục vụ RAG

`data/knowledge_sources.jsonl` chứa năm đoạn diễn giải theo năm nhóm cảnh báo trong bài Bộ Công an đã dẫn ở trên. Mỗi đoạn có mã nguồn, URL, cơ quan công bố, ngày, vị trí nhóm và trạng thái candidate. Đây là tri thức hướng dẫn chung. Sau khi nhóm đối chiếu và phê duyệt, nhập bản đã duyệt vào chỉ mục riêng và ghi phiên bản. Năm mục trong knowledge_seed vẫn là ứng viên biên soạn. Chỉ mục chạy thật chỉ nhận mục đã duyệt và còn hiệu lực.

Khi đánh giá có RAG, khóa cả phiên bản kho và cấu hình truy xuất trước khi chạy. Báo riêng hai nhóm. Nhóm thứ nhất có tài liệu hướng dẫn hành vi liên quan nhưng hội thoại chưa từng thấy. Nhóm thứ hai gồm họ tình huống chưa xuất hiện trong chỉ mục. Họ khác nhau giữa dev và holdout chỉ kiểm soát rò rỉ trong dataset. Nếu kho RAG có cùng họ, ca đó thuộc nhóm thứ nhất. Dùng cùng dữ liệu đầu vào cho cấu hình có và không có RAG. Đo mức cảnh báo đúng, độ đúng của bằng chứng, nguồn trích phù hợp và chênh lệch độ trễ. Không đưa nội dung hoặc đáp án holdout vào chỉ mục.

## Điều cần chuẩn bị để bảo vệ kết quả

| Câu hỏi | Bằng chứng cần đem theo |
| --- | --- |
| Nhãn do ai đặt? | Hướng dẫn gán nhãn, danh sách mẫu hai người rà và quyết định cho các ca bất đồng |
| Hệ thống có học thuộc ví dụ? | Danh sách family_id theo tập, báo cáo gần trùng, hash và tập đánh giá độc lập giữ ngoài workspace triển khai |
| Nguồn RAG có đáng tin? | Bản ghi URL, đoạn đối chiếu, người duyệt, thời điểm, phạm vi áp dụng và lịch sử cập nhật |
| Kết quả có phản ánh dữ liệu thật? | Báo riêng mẫu tổng hợp và mẫu thực đã xin quyền sử dụng, ẩn danh và gán nhãn. Bản hiện tại chỉ có mẫu tổng hợp. |
| Mô hình có nhận biết ảnh, URL hay deepfake? | Chuẩn bị tập riêng cho từng loại đầu vào trước khi tuyên bố có kết quả. Tập hiện tại đánh giá văn bản, kể cả văn bản nhắc tới QR hoặc ứng dụng. |

Chạy `python data/validate_dataset.py` từ thư mục dự án. Công cụ kiểm tra schema tối thiểu, trích dẫn, tập tách theo họ, trùng nội dung sau chuẩn hóa và in SHA-256 từng file. Rà trùng ngữ nghĩa và rà nhãn vẫn là các bước nghiệp vụ riêng.
