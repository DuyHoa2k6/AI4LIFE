# Lộ trình triển khai ScamShield AI trong ba tuần

Luồng mới theo sơ đồ đã chốt: Gemini quan sát → kiểm chứng → hai nhánh song song → Gemini rà lại với bản gốc → kiểm chứng nguồn/kết quả. Người dùng đã yêu cầu dựng RAG thử nghiệm trong giai đoạn này; không phục vụ nguồn candidate và không tự tính P0/RAG đạt. Khóa cấu hình trước chấm, sau khi chỉnh theo lỗi cần tập độc lập khác. Mock/hybrid một lượt giữ cho đối chứng. Xem [TWO_PASS.md](ScamShield_AI/TWO_PASS.md).

## Bổ sung cổng mock hành vi — 08/11/2026

Sau tuần 1–2 có thể nâng mock bằng registry quy tắc, kiểm thử đối chứng và liên kết bằng chứng. Cổng riêng gồm hồi quy API, sai người nói, cảnh báo/phủ định, bằng chứng/Unicode và tương thích client. Khóa phiên bản quy tắc, ghi kết quả dev và lỗi còn lại trước dùng validation. Không tính mock đạt là P0 live đạt; AI live và nguồn RAG vẫn cần nghiệm thu riêng. Ưu tiên mock để kiểm thử tích hợp, không tiếp tục thêm regex vô hạn nhằm thay thế hiểu ngữ cảnh của mô hình.

Mục tiêu ngày 15 là trình diễn một nội dung tiếng Việt đi từ website hoặc vùng quét trên Chrome qua cùng API, rồi nhận cảnh báo có hành vi, đoạn bằng chứng và hướng xác minh. Luồng truy xuất nguồn RAG được chuẩn bị từ tuần một và tích hợp sau khi bộ phân tích cơ sở ổn định. OCR hoặc URL chỉ được chọn sau khi luồng chính đạt nghiệm thu.

## Cách dùng bộ tài liệu để giao việc

| Tài liệu | Quyết định cần lấy trước khi triển khai |
| --- | --- |
| [01 Ý tưởng](01_Y_Tuong.md) | Phạm vi sản phẩm, người dùng, đầu ra cần trình diễn |
| [02 Công cụ](02_Cong_Cu.md) | Công cụ cho từng chức năng và cách chúng trao đổi dữ liệu |
| [03 Luồng](03_Luong.md) | Thứ tự thao tác, chuyển trạng thái và nhánh lỗi |
| [04 API](04_API.md) | Cấu trúc request, response, bằng chứng và mã lỗi |
| [05 Dataset](05_Dataset.md) | Dữ liệu được dùng khi phát triển, tập giữ riêng và điều kiện duyệt nguồn |
| [06 Kiểm thử](06_Kiem_Thu.md) | Mã ca kiểm thử, kết quả mong đợi và chỉ số cần đo |
| [08 Mở rộng](08_Mo_Rong.md) | Quyền riêng tư và điều kiện nghiệm thu OCR, URL, media, cộng đồng |

Mỗi đầu việc cần có bản chạy được, lệnh chạy, ca kiểm thử và kết quả quan sát. Ví dụ hoặc ảnh giao diện chỉ dùng minh họa cho phần đã chạy. Nếu thiếu cấu hình mô hình thật, ghi rõ luồng nào đã kiểm tra bằng mock và phần live còn chờ gì.

## Tuần 1 — Xây đường đi từ văn bản đến cảnh báo

| Ngày | Việc phải làm trực tiếp | Tài liệu và đầu ra |
| --- | --- | --- |
| 1 | Kiểm tra repo, chạy script xác thực dataset. Giữ holdout ngoài workspace dùng để chỉnh prompt. Tạo fixture từ dev cho ba ca có bằng chứng, thiếu ngữ cảnh và bài cảnh báo trích lời dụ. | Đọc 01, 04, 05. Lưu hash và nhãn kỳ vọng. Khởi tạo môi trường chạy API và test. |
| 2 | Làm request và response Pydantic. Chốt điều kiện chỉ nhận một trong text hoặc messages, thứ tự tin và cách tính offset. Thử một lượt live tiếng Việt và kiểm tra JSON, đoạn trích, độ trễ ban đầu. | Đọc 02, 04. Có endpoint mock chạy được, ví dụ request và kết quả live hoặc nguyên nhân chưa chạy. |
| 3 | Viết adapter trích xuất tám câu hỏi, hành vi, người nói và đoạn bằng chứng. Tách lỗi timeout, lỗi JSON và lỗi đầu vào. | Đọc 03, 04. Chạy API-01 đến API-03 và ca nội dung cố điều khiển AI. |
| 4 | Xây bộ đối chiếu trích dẫn rồi mới gán mức rủi ro. Kiểm tra câu trùng, Unicode và nội dung đã che. Thêm trả lời câu hỏi riêng và tối đa hai câu hỏi bổ sung. | Đọc 03, 04, 06. Qua API-04, API-05 và các ca AI-01 đến AI-06 theo cấu hình phù hợp. |
| 5 | Chạy ba ca từ đầu đến cuối qua API. Tạo baseline dò từ khóa dùng để so sánh. Song song rà mục nguồn RAG ứng viên, ghi URL, phần được dùng, người duyệt và phiên bản. | Đọc 05, 06. Có kết quả từng ca và bộ nguồn đủ điều kiện đưa vào chỉ mục hoặc danh sách mục còn chờ duyệt. |

**Cổng tuần 1:** API trả được cảnh báo dựa trên hành vi dù tên thủ đoạn trống. Trích dẫn không tồn tại không được dùng để nâng mức. Khi thiếu đoạn quyết định, hệ thống hỏi đúng chi tiết còn thiếu. Chuẩn bị nguồn có thể chạy song song, còn tích hợp truy xuất phụ thuộc bộ phân tích và bằng chứng đã qua cổng này.

## Tuần 2 — Đưa luồng vào website và extension

| Ngày | Việc phải làm trực tiếp | Tài liệu và đầu ra |
| --- | --- | --- |
| 6 | Tạo website dán hội thoại và nhập câu hỏi. Cho xem lại, che dữ liệu và gửi qua API chung. | Đọc 02–04 và 08. Có một lượt web gửi thật đến backend và hiển thị kết quả. |
| 7 | Làm thẻ cảnh báo, bằng chứng, câu hỏi bổ sung, phân tích lại và trạng thái mất mạng. Kiểm tra lần trả lời cũ không ghi đè lần mới. | Đọc 04, 06. Qua WEB-01, kiểm tra tô đúng đoạn Unicode và lỗi kết nối. |
| 8 | Làm extension chọn khối DOM bằng viền xem trước. Chỉ mở phiên sau khi người dùng bấm **Bật quét vùng này**. Gắn mã tab, phiên và vùng. | Đọc 01–04. Fixture có bài viết, bình luận trong vùng, mục ngoài vùng và trường nhập. Qua EXT-01. |
| 9 | Tự đọc mục hiển thị, theo dõi cuộn và nội dung mới, chống gửi trùng và giới hạn hàng đợi. Gọi API qua service worker và gắn cảnh báo vào đúng mục. | Đọc 02–04 và 06. Qua EXT-02 đến EXT-04, PRIV-01 và so sánh với website bằng E2E-01. |
| 10 | Hoàn thiện tạm dừng, tiếp tục, đổi vùng, điều hướng và bỏ phản hồi muộn. Chạy thử khi mất mạng hoặc nhiều mục xuất hiện. | Đọc 03, 06. Qua EXT-05 đến EXT-07. Có hướng dẫn cài unpacked và bản demo chọn vùng chạy được. |

**Cổng tuần 2:** Chọn khu vực bình luận rồi bật một lần. Extension tự quét nội dung hiển thị và mục mới tải vào, không gửi nội dung ngoài vùng hay dữ liệu trong trường nhập. Kết quả gắn đúng bình luận. Dừng quét thì không phát sinh yêu cầu phân tích mới.

## Tuần 3 — Tích hợp tri thức, đánh giá và đóng gói

| Ngày | Việc phải làm trực tiếp | Tài liệu và đầu ra |
| --- | --- | --- |
| 11 | Theo yêu cầu mới, dựng two_pass thử nghiệm: Gemini quan sát trước, kiểm chứng, hai nhánh nguồn đã duyệt và tình huống/quy tắc song song, Gemini rà lại bản gốc. Giữ cờ bật/tắt và chỉ trả nguồn thực sự dùng. Không đưa candidate vào phục vụ. | Đọc 03–06 và TWO_PASS.md. Kiểm thử nguồn phù hợp/chưa duyệt/hết hạn/không thấy/timeout, không tự công bố P0/RAG đạt hoặc gán verified_match từ nguồn tương tự. |
| 12 | Chạy validation để chốt cấu hình. Khóa prompt, model, quy tắc và phiên bản chỉ mục. Chạy tập đánh giá độc lập trên baseline, mô hình không RAG và có RAG nếu đã tích hợp. | Đọc 05, 06. Có dự đoán từng ca, số đếm, độ đúng của bằng chứng và phân tích lỗi. Không dùng holdout để chọn cấu hình. |
| 13 | Đo p50/p95 cho website, API và extension. Thử cuộn nhiều mục, ghi chờ hàng đợi, gửi trùng, lỗi và chênh lệch độ trễ khi bật RAG. | Đọc 06. Báo số lượt, cấu hình máy, cold/warm và mock/live. |
| 14 | Sửa lỗi ảnh hưởng kết quả hoặc phạm vi quét, chạy hồi quy. Nếu thay đổi mô hình hoặc quy tắc dựa trên tập đã chấm, dùng tập độc lập khác cho phép đo cuối. | Đọc 05, 06. Có danh sách ca đã qua, lỗi còn lại và giới hạn của số liệu. |
| 15 | Chạy demo từ repo sạch theo README. Chuẩn bị ba ca gồm biến thể đáng ngờ, bài cảnh báo chứa cùng từ khóa và tin nhắn thiếu bối cảnh. Nếu có RAG, thêm ca trích nguồn và ca fallback. | Bàn giao mã nguồn, cấu hình mẫu, lệnh chạy, báo cáo kiểm thử, hash dữ liệu và kịch bản demo. |

Khi chậm tiến độ, giữ API văn bản, website và extension tự quét đúng phạm vi. Nếu kho chưa có mục được duyệt hoặc luồng P0 chưa ổn định, báo RAG là phần chuẩn bị hoặc thử nghiệm tùy kết quả đã chạy. Chỉ thêm OCR hoặc URL khi các cổng chính đã qua và còn thời gian đo riêng. Media, form nâng cao và cộng đồng thuộc lộ trình mở rộng tại 08.

## Prompt giao cho AI

Chạy theo thứ tự [khởi động](prompts/00_Bat_Dau.md), [tuần 1](prompts/01_Tuan_1.md), [tuần 2](prompts/02_Tuan_2.md) và [tuần 3](prompts/03_Tuan_3.md). Mỗi lần giao việc, chỉ định ngày hoặc đầu việc cần làm và yêu cầu AI đối chiếu hàng tương ứng trong bảng. Sau mỗi cổng, yêu cầu AI ghi file đã sửa, lệnh đã chạy, kết quả thực tế và đầu việc tiếp theo.
