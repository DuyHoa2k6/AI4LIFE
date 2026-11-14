# Luồng nghiệp vụ

Cập nhật 10/11/2026: bản hiện hành **two-pass-6 / API 1.9** dùng sự kiện tình huống,
quan hệ và khoảng trống có bằng chứng. Người nói được nối từ ID gốc; có tối đa một
lần rà sửa dùng chung hai lượt. Bối cảnh bình thường có thể nằm trong hội thoại,
không chỉ ô context. Không tự nâng mọi hành động gắn lợi ích thành high, không hạ
nguy hiểm đã rõ chỉ vì chưa xác minh danh tính. Xem
[định nghĩa bốn mức](ScamShield_AI/RISK_STATES.md).

Luồng hiện hành two_pass (08/11/2026): xác thực input → Gemini quan sát/giả thuyết/thông tin thiếu → kiểm chứng quote → hai nhánh chạy song song: (a) trích quy tắc và tìm kho tình huống từ văn bản/bối cảnh gốc cùng quan sát, (b) tìm nguồn chính thống đã duyệt → Gemini lượt 2 đọc lại bản gốc với kết quả hai nhánh → backend kiểm chứng kết quả/nguồn → cảnh báo/giải thích/hỏi thêm. Không chờ regex xong mới khởi chạy nhánh nguồn. Không coi quan sát là kết luận lừa đảo; không chờ có tên thủ đoạn mới truy xuất. Lượt cuối được bác bỏ lượt đầu và phải xét giải thích bình thường, không bỏ phiếu/cộng điểm hai nhánh. Hybrid cũ là đối chứng, không phải luồng mới. Xem [TWO_PASS.md](ScamShield_AI/TWO_PASS.md).

## Nhánh mock có phiên bản — 08/11/2026

Nhánh cục bộ mới 12/11/2026: /api/analyze-local và /local dùng Python trích dữ kiện
→ kiểm chứng → rulebook/ngoại lệ → mẫu giải thích; safety precheck có thể trả hỗ trợ
khẩn trước bộ trích đầy đủ. Không tự thay luồng /api/analyze. Xem
[LOCAL_REASONING_V2.md](ScamShield_AI/LOCAL_REASONING_V2.md).

Đầu vào hợp lệ → tách câu/đoạn giữ offset gốc → nhận dạng từng hành vi và vai request/claim/quoted_warning/denial/unknown → trích đoạn bằng chứng → kiểm chứng ID/speaker/offset → liên kết hành động với điều kiện liên quan cùng người nói → quyết định rủi ro → dựng câu trả lời từ bằng chứng. Cảnh báo ở câu trước không che yêu cầu ở câu sau. Câu hỏi/thuật lại không tự coi là yêu cầu trực tiếp. Chỉ hỗ trợ cửa sổ liên kết hữu hạn và mẫu đã mô tả; nếu không đủ điều kiện nâng high thì suspicious hoặc need_context tùy chứng cứ. Nguồn/verified_match vẫn rỗng/chưa triển khai trong mock. Nội dung chỉ thị nhúng không được thực thi.

## Từ nội dung đến cảnh báo

1. Website nhận văn bản hoặc danh sách tin nhắn có thứ tự. Extension chọn khối DOM, hiển thị viền và thông báo nơi xử lý. Sau khi người dùng bật, tự gửi từng mục văn bản đang hiển thị trong phạm vi đã chọn.
2. Backend kiểm tra định dạng, giới hạn, khoảng trắng và dữ liệu nhạy cảm. Giữ văn bản dùng để đối chiếu nguyên vẹn. Nếu che dữ liệu, dùng chính bản đã che để tạo và kiểm tra bằng chứng.
3. Mô hình đọc nội dung và trả tám câu trả lời, hành vi, vai người nói, đoạn trích và thông tin còn thiếu. Nội dung người dùng là dữ liệu cần phân tích, kể cả câu yêu cầu AI bỏ qua chỉ thị.
4. Backend kiểm tra cấu trúc, đối chiếu đoạn trích và giới hạn phát hiện hợp lệ. Câu trích trong bài tuyên truyền, câu phủ định và lời người gửi tự nhận cần bối cảnh riêng.
5. Bảng quyết định gán trạng thái. Kho tri thức nếu bật chỉ hỗ trợ đối chiếu và giải thích. Kết quả có thể để tên thủ đoạn rỗng.
6. Giao diện hiện mức cảnh báo, tóm tắt, hướng xác minh và bằng chứng đã kiểm chứng. Không hiển thị khối answers, danh sách nguồn RAG hoặc suy luận nội bộ. Hỏi thêm tối đa hai câu gắn với phần thiếu thực sự.

## Tám câu hỏi máy tự trả lời

| Mã | Câu hỏi |
| --- | --- |
| claim | Nội dung tuyên bố hay hứa điều gì? |
| claimed_identity | Người gửi tự nhận là ai và danh tính đã được xác minh đến đâu? |
| requested_action | Người gửi muốn người nhận làm gì? |
| persuasion | Họ dùng lý do và cách thuyết phục nào? |
| assets_at_risk | Tiền, dữ liệu hoặc quyền truy cập nào có thể bị ảnh hưởng? |
| impersonation | Có chi tiết nào cho thấy mạo danh hoặc mâu thuẫn? |
| sequence | Hành vi có thay đổi theo thời gian hoặc có áp lực bất thường không? |
| evidence_sufficiency | Bằng chứng đã đủ đến đâu và thiếu gì? |

Mỗi câu có trạng thái observed, inferred hoặc unknown. Với inferred, ghi căn cứ và diễn đạt theo điều kiện. Nội dung do người gửi tuyên bố chỉ chứng minh họ đã nói như vậy.

## Quy tắc quyết định ưu tiên

Tiêu chí hiện hành và ví dụ phân biệt bốn mức được mô tả tại
[RISK_STATES.md](ScamShield_AI/RISK_STATES.md). Từ two-pass-5, regex chỉ gửi dấu
hiệu để Gemini rà, không tự chặn kết quả vì từ khóa. Mỗi dấu hiệu phải được đọc lại
trong văn bản gốc và xác nhận/phân loại lại/nêu phần thiếu trước khi backend quyết định.

Hiện chỉ có bốn mức: clear (xanh lá), need_context (xanh dương), suspicious (cam),
high (đỏ). High là mức cao nhất; lỗi phân tích vẫn là “Chưa kiểm tra được”.

| Trạng thái | Điều kiện đề xuất |
| --- | --- |
| high | Bằng chứng rõ về yêu cầu có thể gây hại gắn với bối cảnh dẫn dụ mạnh, ví dụ nhập mã đăng nhập qua kênh người gửi chỉ định để nhận tiền. |
| suspicious | Có yêu cầu hoặc dấu hiệu đáng lo, nhưng còn thiếu căn cứ để đánh giá cao. |
| need_context | Thiếu thông tin có thể đổi đánh giá và các dấu hiệu hiện tại chưa đủ mạnh để dùng trạng thái trên. |
| clear | Đã phân tích được phần đầu vào, chưa ghi nhận dấu hiệu đáng ngờ trong phạm vi đó. |

Xem xét theo thứ tự trên sau khi lọc bằng chứng. Nếu mô hình lỗi hoặc mọi phát hiện quan trọng đều sai định dạng và không thể phục hồi, trả lỗi phân tích. Nếu bằng chứng còn lại dùng được nhưng thiếu chi tiết, trả need_context khi phù hợp. Câu hỏi bổ sung cần hỏi về mục đích của thao tác, kênh thực hiện hoặc điều kiện của người gửi. Tránh yêu cầu gửi mã thật.

## Ví dụ chạy xuyên suốt

“Hãy cài tệp kế toán gửi” rồi “Bật chia sẻ màn hình và mở ứng dụng ngân hàng để nhận lại tiền cọc”. Trích hai hành động, nối chúng với lý do hoàn cọc và chỉ ra dữ liệu ngân hàng có thể bị nhìn thấy. Chỉ định kênh xác minh độc lập, chẳng hạn đầu mối trên hợp đồng. Tên thủ đoạn được phép để trống. Tình huống này nằm trong tập đánh giá mẫu và cần loại khỏi holdout thực tế nếu đã dùng để chỉnh prompt.

## Phiên quét extension

- Trạng thái phiên gồm tắt, đang chọn vùng, đang quét, tạm dừng và cần chọn lại. Phiên mang mã tab, tài liệu và mã phiên. Đổi vùng tạo phiên mới.
- Lấy các mục con phù hợp trong khối đã chọn. Trên fixture dùng ranh giới bài và bình luận rõ ràng. Khối chưa xác định ranh giới chỉ phân tích như một đơn vị và hiển thị đúng phạm vi đó. Khi khối quá rộng, đề nghị chọn vùng nhỏ hơn.
- Theo dõi DOM trong khối, theo dõi phần đang hiện trong viewport và kiểm tra lại giới hạn ngay trước khi gửi. Nội dung ẩn, trường nhập, vùng soạn thảo và nội dung bên ngoài không vào hàng đợi.
- Áp dụng debounce, một yêu cầu đồng thời và hàng đợi có giới hạn cho bản demo. Khử trùng theo mã mục và dấu vân tay nội dung trong phiên. Hủy hàng đợi khi dừng. Yêu cầu đã tới máy chủ có thể vẫn xử lý, client bỏ qua phản hồi của phiên cũ.
- Mỗi mục gửi qua API hiện có. Client giữ mã phiên, mã mục và phiên bản để ghép đúng phản hồi. Khi tab điều hướng, kể cả thay tuyến ở ứng dụng một trang, hoặc vùng mất kết nối DOM, dừng quét và yêu cầu chọn lại.

## Luồng sử dụng theo chức năng

Các luồng dưới đây mô tả thao tác người dùng, phản hồi của hệ thống và cách người dùng thấy kết quả. Mỗi kênh đưa bằng chứng về bộ phân tích chung theo phần trên. Một nhánh lỗi hiển thị trạng thái chưa kiểm tra được và cho phép thử lại khi phù hợp.

### 1 Extension tự quét bài viết và bình luận — P0

1. Người dùng mở tiện ích trên tab hiện tại và chọn **Chọn vùng quét**. Tiện ích vẽ viền quanh khối dưới con trỏ, chẳng hạn danh sách bình luận.
2. Người dùng bấm chọn khối. Tiện ích hiện phạm vi, loại dữ liệu sẽ đọc và nơi xử lý. Người dùng bấm **Bật quét vùng này** một lần cho phiên đó.
3. Tiện ích tự lấy từng bài viết hoặc bình luận đang hiển thị trong vùng và đánh dấu mục đang kiểm tra. Khi người dùng cuộn hoặc trang tải thêm, tiện ích tự xếp các mục mới vào hàng đợi. Nội dung trùng, mục ngoài vùng và trường soạn thảo được bỏ qua.
4. Backend phân tích mỗi mục, kiểm tra trích dẫn và trả trạng thái. Tiện ích kiểm tra mục vẫn thuộc đúng phiên và đúng phiên bản trước khi gắn nhãn cạnh bài hoặc bình luận.
5. Người dùng bấm nhãn để xem câu bằng chứng, lý do và cách xác minh. Ví dụ, bình luận yêu cầu “Ứng 500.000 đồng để mở đơn” hiện nhãn **Có dấu hiệu đáng ngờ**. Người dùng có thể mở chi tiết để thấy yêu cầu ứng tiền trước và lời hứa hoàn tiền nếu có.
6. Người dùng có thể tạm dừng, tiếp tục, đổi vùng hoặc tắt. Khi trang đổi hoặc khối biến mất, tiện ích yêu cầu chọn lại. Mục lỗi có trạng thái **Chưa kiểm tra được**. Kết quả về muộn từ phiên cũ bị bỏ qua.

### 2 Website kiểm tra tin nhắn hoặc trả lời câu hỏi — P0

1. Người dùng mở **Kiểm tra nội dung**, dán văn bản hoặc chuỗi tin nhắn từ Zalo, SMS hay nguồn khác. Có thể ghi câu hỏi như “Vì sao họ muốn tôi mở ứng dụng ngân hàng?”.
2. Website giữ thứ tự tin nhắn, cho xem lại và che thông tin cá nhân trước khi bấm **Phân tích**. Nếu đầu vào trống hoặc quá dài, website chỉ vị trí cần sửa.
3. Backend tự trả lời tám câu hỏi, tìm hành vi và kiểm chứng bằng chứng. Nếu có câu hỏi riêng, backend trả lời dựa trên dữ liệu đã kiểm chứng.
4. Website hiển thị mức rủi ro, câu gốc, lý do và cách xác minh. Nếu thiếu bối cảnh, website có thể hỏi “Họ có yêu cầu bạn chia sẻ màn hình khi mở ứng dụng không?”. Người dùng bổ sung rồi bấm **Phân tích lại**. Kết quả mới áp dụng cho nội dung đã bổ sung.

### 3 Kiểm tra liên kết — P1 nếu chọn URL, mở rộng ở P2

Bổ sung triển khai 10/11/2026: theo yêu cầu người dùng, URL hiện đã được ghép vào
API phân tích chung. Sau Gemini 1/kiểm chứng, nhánh URL cấu trúc + HTTP HEAD chạy song song hai
nhánh quy tắc/tình huống và RAG; Gemini 2 đối chiếu, backend kiểm chứng. Extension
thu href có nhãn trong vùng và fingerprint cả href để bỏ phản hồi cũ. Theo redirect
HTTP có giới hạn và chặn đích nội bộ, không đọc body/JS; reputation not_checked.
Chi tiết hiện hành tại README_URL.md trong ứng dụng; chưa có mục URL riêng.

1. Người dùng dán URL vào mục **Kiểm tra liên kết**. Ở giai đoạn mở rộng, extension có thể đưa liên kết trong vùng đã cấp vào luồng này.
2. Hệ thống tách địa chỉ và xác định tên miền đăng ký, rồi kiểm tra các dấu hiệu cấu trúc. Website hiển thị tên miền thật để người dùng dễ đối chiếu với tổ chức mà người gửi tự nhận.
3. Nếu có nguồn tra cứu hoặc mô-đun kiểm tra chuyển hướng, hệ thống ghi rõ nguồn, phạm vi khớp và đích quan sát được. Khi chỉ kiểm tra cấu trúc, kết quả nói rõ đích sau chuyển hướng chưa được kiểm tra.
4. Người dùng thấy dấu hiệu, trạng thái và hướng xác minh. Nếu tên thương hiệu chỉ xuất hiện trong miền phụ, giải thích điều đó và gợi ý mở trang chính thức qua địa chỉ do người dùng tự tìm. URL sai định dạng được báo để nhập lại.

### 4 Cảnh báo biểu mẫu trên trang — P2

1. Người dùng bật kiểm tra vùng có biểu mẫu. Tiện ích nhận diện trường cần nhập, nhãn trường và đích gửi nếu quan sát được.
2. Hệ thống đối chiếu yêu cầu như nhập mã xác thực hoặc mật khẩu với tên miền và ngữ cảnh trang. Dữ liệu người dùng đã gõ không được đọc.
3. Nếu có dấu hiệu đáng ngờ, tiện ích hiện cảnh báo gần form và giải thích bằng nhãn trường, tên miền hoặc đích gửi quan sát được. Nếu form gửi bằng JavaScript và không thấy đích, giao diện ghi rõ phần chưa xác định. Cảnh báo trên form được hiển thị sau khi trang đã tải.

### 5 Kiểm tra ảnh chụp — P1 nếu chọn OCR

1. Người dùng tải ảnh, xem trước và che phần nhạy cảm. Hệ thống nhận dạng chữ theo vùng và thứ tự đọc.
2. Website hiện bản chữ để người dùng sửa nếu đọc nhầm số tiền hoặc nội dung. Nếu ảnh mờ, đề nghị gửi lại hoặc dán văn bản.
3. Người dùng xác nhận gửi phần chữ đã rà soát. Bộ phân tích trả cảnh báo có bằng chứng theo bản chữ đó. Giao diện chỉ rõ nội dung nào được nhận dạng từ ảnh.

### 6 Kiểm tra âm thanh và video — P2

1. Người dùng chọn tệp, xem giới hạn và bấm gửi. Website hiện tiến độ và cho hủy.
2. Hệ thống chuyển lời nói thành chữ, trích chữ trên các khung hình được lấy mẫu và lưu mốc thời gian. Nếu chất lượng thấp, nêu đoạn chưa đọc được.
3. Bộ phân tích tìm yêu cầu đáng ngờ trong phần đọc được và trả cảnh báo kèm mốc thời gian. Nếu có mô-đun nghiên cứu giả giọng hoặc deepfake, hiển thị kết quả đó riêng với rủi ro hành vi và nêu khi dữ liệu chưa đủ để đánh giá.

### 7 Gửi báo cáo cộng đồng và cập nhật kho tri thức — P2

1. Người dùng chọn **Báo cáo tình huống**, thêm mô tả và bằng chứng đã che dữ liệu cá nhân, rồi xác nhận quyền sử dụng nội dung.
2. Hệ thống xác nhận đã nhận và hiện **Chờ duyệt**. Người kiểm duyệt có thể yêu cầu bổ sung, từ chối hoặc duyệt sau khi kiểm tra bằng chứng và nguồn.
3. Người gửi xem trạng thái xử lý. Nội dung đã duyệt có thể xuất hiện dưới dạng bài chia sẻ hoặc mục tri thức tùy quyết định kiểm duyệt.
4. Lần phân tích sau có thể truy xuất mục phù hợp để giải thích. Việc đưa đối tượng vào danh sách cảnh báo đã xác minh cần một quyết định riêng có nguồn và phạm vi khớp.
# Bổ sung luồng kiểm tra nhất quán — 09/11/2026

Cập nhật 10/11: lượt rà hiện yêu cầu `relation_assessments` kèm quote quan hệ. Nếu
request và điều kiện đã được trích nhưng có thể bỏ sót liên kết, backend gửi gợi ý
rà lại cả hai khả năng giữ/bác liên kết, thay vì chỉ gợi ý xóa link chưa rõ. Tín hiệu
từ điều kiện không tự tạo high, không ghép người nói khác và không thêm lượt sửa
vượt quá một lần. Xem hợp đồng API 1.5 và báo cáo `reports/relation_v4` trong ứng dụng.

Trong two_pass, sau khi Gemini rà tổng thể, backend kiểm tra quan hệ giữa các trường
đầu ra trước khi quyết định cảnh báo. Nếu cùng quan hệ vừa được khẳng định vừa bị
đánh dấu chưa rõ, hoặc một hành vi vừa benign vừa risky, yêu cầu sửa tối đa một lần
ngay trong bước rà tổng thể, kèm nguyên văn input. Nếu vẫn mâu thuẫn trả lỗi chưa
kiểm tra được; không gán need_context cho lỗi model. Một phiên thường hai lần gọi
model, tối đa ba nếu cần sửa, chưa tính retry HTTP hữu hạn.

Bất định danh tính có thể đi kèm cảnh báo high khi hành vi và quan hệ nguy hiểm đã
rõ. Bất định quan hệ dùng từng cặp request/support, không vô hiệu mọi quan hệ khác
của cùng một hành động. Yêu cầu chuyển tiền trống bối cảnh vẫn hỏi thêm. Đổi nhãn
other sang hành vi cụ thể trên cùng đoạn/cùng người nói không tự tạo bất đồng.
Chi tiết hợp đồng tại 04, triển khai tại `ScamShield_AI/backend/review_consistency.py`.

