# Công cụ theo chức năng của ScamShield AI

Luồng hiện hành dùng TwoPassProvider trong `backend/two_pass.py`, prompt observation/review riêng và schema InitialReview/FinalReview. `backend/retrieval.py` tìm từ vựng chuẩn hóa + action tags trên kho runtime riêng; regex dò văn bản gốc sau lượt quan sát đầu. Hai nhánh local chạy asyncio.gather, có giới hạn/timeout và bộ lọc phê duyệt nguồn. Chưa dùng embeddings, chưa có tìm kiếm web tự động. SCAMSHIELD_MODE=two_pass bật luồng hai lần gọi; hybrid cũ là đối chứng một lần. Không thêm dependency, không đưa nhãn đánh giá vào prompt. Xem [TWO_PASS.md](ScamShield_AI/TWO_PASS.md).

## Bổ sung công cụ mock — 08/11/2026

`backend/mock_rules.py` quản lý registry quy tắc có ID, phiên bản, mô tả và regex/từ khóa. MockProvider chỉ gọi bộ này; không đọc dataset. Matching chuẩn hóa NFC để nhận dạng nhưng evidence giữ offset trên bản gốc. Mock xét text/messages, chưa suy luận từ context/question. Backend chỉ liên kết phát hiện đã kiểm chứng; yêu cầu và bối cảnh phải cùng người nói, cùng đoạn hoặc trong cửa sổ nhỏ có liên hệ tài chính rõ. Không ghép người nói khác hoặc chủ đề không liên quan chỉ vì cùng request. AI live và baseline từ khóa độc lập với mock. RAG nhỏ theo 07/prompt tuần ba được phép khi P0 và nguồn duyệt đạt cổng; quản trị kho lớn thuộc P2.

Mỗi chức năng dưới đây chỉ rõ dữ liệu đi vào, công cụ xử lý và kết quả trả về. P0 là phần bắt buộc trong ba tuần. P1 chỉ chọn một trong hai phần OCR hoặc kiểm tra cấu trúc URL sau khi P0 đạt nghiệm thu. P2 mở rộng khả năng thu thập và đối chiếu.

## 1 Lấy bài viết và bình luận từ extension

| Việc cụ thể | Công cụ | Cách dùng trong dự án |
| --- | --- | --- |
| Bật quyền đọc tab hiện tại | Chrome Manifest V3, `activeTab`, `chrome.scripting` | Khi người dùng mở tiện ích và bắt đầu chọn vùng, chèn content script vào tab theo quyền tạm. |
| Chọn vùng cần quét | TypeScript, DOM và CSS overlay | Khi người dùng di chuột, vẽ viền khối đang được trỏ tới. Khi họ bấm chọn và xác nhận bật, lưu tham chiếu vùng trong phiên quét. |
| Tách bài viết và bình luận | Content script, bộ đọc DOM theo trang thử nghiệm | Tách từng mục dựa trên ranh giới DOM. Lấy chữ hiển thị, mã mục và phiên bản nội dung. Nếu chưa tách được mục, hiển thị kết quả theo phạm vi khối hoặc đề nghị chọn khối nhỏ hơn. |
| Quét khi cuộn hoặc tải thêm | `IntersectionObserver`, `MutationObserver` | Theo dõi mục xuất hiện trong vùng nhìn thấy và phát hiện mục mới hoặc chữ thay đổi trong khối. Kiểm tra lại ranh giới và khả năng hiển thị trước khi xếp hàng. |
| Giữ đúng phạm vi | Hàng đợi TypeScript, debounce, dấu vân tay nội dung | Bỏ qua phần ẩn, vùng soạn thảo và trường nhập. Chống gửi trùng, hạn chế số mục chờ, dừng theo dõi khi người dùng tắt hoặc khối biến mất. |

**Đầu ra P0:** mỗi mục là một đơn vị văn bản riêng. Mã vùng, mã phiên và phiên bản mục nằm ở extension. Nội dung bài viết hợp lệ và bình luận đáng ngờ có kết quả riêng. Khi chọn quét vùng, người dùng biết nội dung nào sẽ được gửi và nơi xử lý.

Nguồn kỹ thuật: [Chrome activeTab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab) · [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts).

## 2 Chuyển dữ liệu từ extension về bộ phân tích

| Việc cụ thể | Công cụ | Cách dùng trong dự án |
| --- | --- | --- |
| Chuyển dữ liệu trong extension | `chrome.runtime.sendMessage` | Content script chuyển văn bản của mục cần kiểm tra cùng mã theo dõi cục bộ cho service worker. |
| Gọi máy chủ | `fetch` từ extension service worker | Gọi `POST /api/analyze` đến một API được cấu hình. Giới hạn quyền máy chủ ở origin đó, kiểm tra nơi gửi message và cố định đích gọi tại service worker. |
| Kiểm tra đầu vào | FastAPI và Pydantic | Kiểm tra schema, độ dài, định dạng tin nhắn và các trường tùy chọn. Website dùng cùng endpoint. |
| Ghép kết quả với trang | TypeScript, mã phiên và phiên bản mục | Bỏ qua kết quả nếu phiên đã dừng, nội dung đã thay đổi hoặc mục đã rời khỏi vùng. Hiển thị kết quả ở đúng mục còn hiệu lực. |

**Luồng P0:** content script → service worker → FastAPI → bộ phân tích → extension. Chỉ gửi các trường thuộc [hợp đồng API](04_API.md). Khóa mô hình nằm ở backend. Extension không gửi HTML nguyên trang, lịch sử hoặc giá trị trong form.

Nguồn kỹ thuật: [Chrome cross-origin network requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests) · [FastAPI request body](https://fastapi.tiangolo.com/tutorial/body/).

## 3 Phân tích bài viết, bình luận và chuỗi tin nhắn

| Việc cụ thể | Công cụ | Cách dùng trong dự án |
| --- | --- | --- |
| Hiểu hành vi trong nội dung | Mô hình ngôn ngữ qua adapter Python | Nhận văn bản và thứ tự tin nhắn. Trả JSON theo tám câu hỏi tại [luồng nghiệp vụ](03_Luong.md). Trích hành động, lời hứa, ai đang nói, câu gốc và phần chưa rõ. |
| Xác nhận trích dẫn | Pydantic và đối chiếu chuỗi Python | Kiểm tra cấu trúc và vị trí của đoạn trích. Bỏ phát hiện có bằng chứng sai. Regex hỗ trợ nhận dạng số tiền hoặc thời hạn. |
| Xác định mức cảnh báo | Bảng quyết định Python | Kết hợp hành động, bối cảnh và bằng chứng. Một lời cảnh báo trích câu “gửi OTP” được xử lý theo vai trò trích dẫn. Tên thủ đoạn có thể rỗng. |
| Giải thích kết quả | Mẫu hiển thị và dữ liệu đã kiểm chứng | Trả mức rủi ro, lý do, câu gốc và bước xác minh. Nếu còn thiếu chi tiết quan trọng, hỏi tối đa hai câu bổ sung. |

**Ví dụ P0:** bình luận “Ứng 500.000 đồng để mở đơn, xong sẽ hoàn gốc và hoa hồng” được trích thành yêu cầu ứng tiền và lời hứa hoàn tiền. Bộ quyết định đánh giá hai dấu hiệu cùng bối cảnh tuyển việc. Với một bài tuyên truyền trích lại nguyên câu, mô hình cần nhận diện đúng vai trò của lời trích.

Chọn cấu hình sau khi thử tiếng Việt, JSON, bằng chứng, độ trễ và chi phí. Hiện có bốn mode: `mock` kiểm thử quy tắc; `live` trích xuất một lượt riêng; `hybrid` quy tắc rồi một lượt model để đối chứng; `two_pass` là luồng sử dụng mới, model trước rồi hai nhánh song song và model rà lại. Mode dùng mô hình thật phải báo lỗi/quota và chất lượng riêng, không suy ra từ mock.

## 4 Phân tích đường dẫn và biểu mẫu

| Mức | Việc cụ thể | Công cụ và kết quả |
| --- | --- | --- |
| P1 nếu chọn URL | Nhận URL do người dùng cung cấp | FastAPI/Pydantic nhận chuỗi. `urllib.parse` tách scheme, hostname và đường dẫn. Kiểm tra đầu vào rõ ràng, chỉ nhận HTTP/HTTPS. Bộ phân tích cấu trúc không cần truy cập trang. |
| P1 nếu chọn URL | Xác định tên miền đăng ký | `tldextract` với dữ liệu Public Suffix List được quản lý, kết hợp xử lý IDNA. Tách miền đăng ký khỏi tên miền phụ và hiển thị cả dạng dễ đọc lẫn dạng ASCII khi phù hợp. |
| P1 nếu chọn URL | Tìm dấu hiệu có thể gây nhầm | Quy tắc Python xét tên miền mô phỏng thương hiệu, hostname là địa chỉ IP hoặc liên kết rút gọn. Trả các dấu hiệu và phần chưa xác minh. Dấu hiệu cấu trúc riêng lẻ chưa đủ để kết luận. |
| P2 | Lấy đích của liên kết trong vùng quét | Content script lấy thuộc tính href đã được giải tương đối theo trang và giữ chữ hiển thị để so sánh. Giới hạn lấy trong vùng đã cấp. |
| P2 | Tra cứu nguồn cảnh báo | Dùng snapshot đã duyệt hoặc dịch vụ như Google Safe Browsing nếu phù hợp điều khoản. So đúng phạm vi URL hoặc miền và lưu thời điểm nguồn. Chỉ dùng trạng thái khớp cảnh báo đã xác minh khi có bản ghi khớp cụ thể. |
| P2 | Theo dõi chuyển hướng | HTTP client trong dịch vụ riêng có giới hạn, kiểm tra DNS và địa chỉ đích tại từng bước, chặn mạng nội bộ và kiểm soát egress. Trả chuỗi chuyển hướng hoặc lý do chưa kiểm tra được. |
| P2 | Cảnh báo form | Content script đọc nhãn trường, loại trường và đích gửi quan sát được. Kết hợp yêu cầu nhập mã hoặc mật khẩu với bằng chứng về tên miền và nguồn. Form gửi bằng JavaScript có thể cần ghi đích chưa rõ. |

**Ví dụ:** với URL minh họa `https://nganhang.example.xacminh.test/dang-nhap`, bộ tách hostname và miền giúp cho thấy `nganhang.example` nằm ở phần tên miền phụ của `xacminh.test`. Tín hiệu này cần kết hợp với dữ liệu miền chính thức và ngữ cảnh người gửi trước khi gán mức cảnh báo.

Nguồn kỹ thuật: [urllib.parse](https://docs.python.org/3/library/urllib.parse.html) · [tldextract](https://github.com/john-kurkowski/tldextract) · [Google Safe Browsing](https://developers.google.com/safe-browsing).

## 5 Các chức năng còn lại

| Chức năng | Công cụ | Dữ liệu ra và giai đoạn |
| --- | --- | --- |
| Website kiểm tra tin nhắn từ Zalo, SMS và ứng dụng khác | React, TypeScript, Vite và fetch | Văn bản, ngữ cảnh và câu hỏi đi qua cùng API. Giao diện hiện bằng chứng và cho bổ sung thông tin. **P0.** |
| Đọc ảnh chụp hội thoại | PaddleOCR, xử lý ảnh bằng Python | Chữ theo từng vùng và thứ tự đọc. Cho người dùng sửa trước khi phân tích. **P1 nếu chọn OCR.** |
| Đọc audio và video | FFmpeg, công cụ nhận dạng lời nói như faster-whisper, OCR khung hình | Văn bản có mốc thời gian để đánh giá hành vi. Mô-đun deepfake/giả giọng cần dữ liệu và đánh giá riêng. **P2.** |
| Lưu mẫu và cập nhật tri thức | JSONL UTF-8 cho dataset. PostgreSQL cho nghiệp vụ kiểm duyệt khi triển khai | Dataset dùng kiểm thử. Kho tri thức dùng đối chiếu các mục đã duyệt. Báo cáo chưa duyệt giữ riêng. **JSONL ở P0, quản trị và truy xuất ở P2.** |
| Kiểm thử và đo hiệu năng | pytest, Playwright hoặc kịch bản trình duyệt có thể lặp, bộ đo thời gian đơn điệu | Kiểm tra phân tích, API, quét đúng vùng, số yêu cầu trùng, p50/p95 và tỷ lệ lỗi. **P0.** |

## 6 Kiến trúc và cấu hình tối thiểu

Cấu trúc repo gồm `backend`, `web`, `extension`, `shared`, `data` và `tests`. Dùng schema backend làm nguồn chuẩn và đồng bộ kiểu TypeScript. Ưu tiên một backend và một lần gọi mô hình cho mỗi mục được gửi. Giữ trạng thái phiên ở client. P0 có thể dùng JSONL cho dữ liệu đánh giá và chưa cần tài khoản người dùng.

Cấu hình backend gồm `MODEL_MODE`, `MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY` nếu cần, `MODEL_TIMEOUT_SECONDS`, `MAX_INPUT_CHARS` và `WEB_ORIGINS`. Tệp cấu hình mẫu dùng giá trị giả. Demo trên máy cá nhân với extension dạng unpacked.

Thứ tự triển khai là bộ phân tích và API, website, extension tự quét theo vùng, rồi đo chất lượng và hiệu năng. Chỉ bắt đầu OCR hoặc URL sau khi luồng chính đạt các mục trong [kiểm thử](06_Kiem_Thu.md).
