# Ghép RAG và URL vào BE — 12/11/2026

Luồng hiện hành: trích hành vi → kiểm chứng → quy tắc văn bản → **song song nguồn đã duyệt + URL/redirect** → ghép bằng chứng → cảnh báo/giải thích. Không gọi Gemini.

## Đã triển khai

- `backend/local_reasoning/support.py` nối dữ kiện từ hai nhánh với yêu cầu hợp lệ; không lấy URL đứng riêng/lời trích cảnh báo/nguồn trùng từ làm kết luận.
- URL có dấu hiệu mạnh cùng yêu cầu có thể nâng tối đa suspicious; high từ nội dung giữ nguyên. HEAD/redirect dùng bộ kiểm tra mạng đã có, giữ giới hạn và chặn SSRF.
- RAG truy vấn từ bằng chứng đã kiểm chứng; chỉ nguồn behavior_support đã duyệt, còn hiệu lực và có liên hệ được dùng bổ trợ giải thích/hướng xác minh. Không tự nâng high, không exact_entity/verified_match. Chỉ trả nguồn thực sự dùng.
- API chung và API v2 thô cùng enrichment. Lõi engine tách khỏi I/O. Nhánh khẩn không chờ nguồn hoặc URL. Có cấu hình tắt RAG/mạng URL, thời gian từng nhánh và fallback.
- Giao diện website/extension nhận cùng response; vẫn ẩn answers, danh sách RAG và dữ liệu thô. Nhận diện decision_version mới để giữ đúng tóm tắt BE.
- Sửa ghép href DOM liền kề khi extension tách text node bằng xuống dòng; có kiểm thử không ghép câu/người khác.

## Xác minh

- **161/161 backend tests pass**, gồm 17 ca hỗ trợ mới. Log: [backend_tests.txt](backend_tests.txt).
- **12/12 ca phát triển trước đó** giữ mức rủi ro/khẩn, không có cuộc gọi mô hình hay mạng ngoài trong các ca đó: [regression12](regression12/summary.json).
- **10 ví dụ API**, HTTP 200 toàn bộ: xem [bảng kết quả bản cuối](verified/CASES.md), [JSON đầy đủ](verified/predictions.json), [hash mã và chỉ mục](verified/hashes.json).
- Chrome thật + extension unpacked: **12/12 checks pass**, bao gồm cảnh báo URL trên website và cập nhật cảnh báo theo URL trên extension: [browser_verified/report.json](browser_verified/report.json).
- Worker security 13 checks pass; popup version 4 checks pass; JavaScript kết quả hợp lệ cú pháp.

Lần browser_final trước đó dừng vì href bị tách dòng, dẫn tới không nâng cảnh báo như kỳ vọng. Đã sửa với ca hồi quy, chạy lại và lưu bản đạt riêng trong browser_verified; không dùng bản chạy dừng làm bằng chứng đã đạt.

## Giới hạn

Kho thật **chưa có nguồn được duyệt**, không sửa candidate thành approved. Ca có tài liệu approved và redirect là fixture tổng hợp được ghi rõ; không khẳng định đã đối chiếu nguồn thật hay đo danh tiếng website. Kiểm thử mạng chỉ dùng quan sát/máy chủ giả lập, browser tắt mạng URL để không truy cập miền minh họa. Chưa nghiệm thu redirect trên mạng công cộng thực.

RAG hiện là truy xuất từ khóa có trọng số; ghép hành vi dựa trên loại hành động và token, chưa có suy luận ngữ nghĩa bằng mô hình. RAG bổ trợ giải thích, không thay thế chứng cứ hành vi. URL ghép thận trọng theo đoạn; có thể bỏ sót khi liên kết nằm ở câu khác. Không đọc nội dung trang, không chạy JS, không đánh giá mã độc. Không có embedding/huấn luyện mới.

Không phải đánh giá độc lập độ chính xác 98% hoặc phép đo tải/độ trễ browser. Thời gian testclient trong ví dụ chỉ là quan sát chạy thử, có ca giả lập, không đại diện mạng thật.

Hợp đồng: [04_API.md](../../../04_API.md). Hướng dẫn cấu hình và quy tắc: [LOCAL_SUPPORT.md](../../LOCAL_SUPPORT.md). Cần khởi động lại backend và tải lại extension để dùng đầy đủ bản mới.
