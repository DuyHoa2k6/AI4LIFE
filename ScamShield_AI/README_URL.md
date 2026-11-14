# URL đi cùng bài viết và OCR

Nhánh cấu trúc URL chạy offline bằng urllib.parse, **tldextract 5.4.0**, **idna 3.11**,
**RapidFuzz 3.14.6** và bảng Unicode confusables **17.0.0**. Bổ sung kiểm tra HTTP
HEAD bằng thư viện chuẩn Python để quan sát redirect và origin đích phản hồi cuối.
Không dùng key/API kiểm tra danh tiếng. Chế độ mock vẫn không gửi yêu cầu ra mạng.
Kết quả là dấu hiệu kỹ thuật, không phải xác nhận trang độc hại hoặc an toàn.

## Kiểm tra chuyển hướng — 10/11/2026

- Bật mặc định ở live/hybrid/two_pass; tắt bằng `SCAMSHIELD_URL_NETWORK_ENABLED="0"`
  trong cấu hình backend hoặc biến môi trường. Không cần thêm thư viện hay API key.
- Sau Gemini 1, URL chạy song song RAG/quy tắc; HTTP HEAD quan sát status và Location,
  rồi kiểm tra lại DNS/IP từng đích trước khi theo. Không đọc body, không chạy JS,
  không thực thi meta-refresh, không dùng proxy từ môi trường, cookie hoặc tài khoản.
- Tối đa 3 URL mỗi yêu cầu, 3 lần chuyển hướng (4 HEAD) mỗi URL, ngân sách 6 giây
  mỗi chuỗi, chờ nhánh tối đa 6,25 giây; tối đa 8 tác vụ mạng đang chạy toàn tiến trình.
  URL còn lại báo deferred. Giới hạn mạng này vẫn bật khi tắt deadline phản hồi Gemini.
- Chỉ HTTP(S), cổng 80/443; chặn userinfo, localhost/địa chỉ nội bộ/metadata/multicast/
  reserved/IPv6 transition và DNS trả lẫn IP public/private. Kết nối ghim IP đã kiểm tra,
  TLS vẫn xác thực hostname/chứng chỉ. DNS hệ điều hành có thể còn chạy sau khi nhánh
  hết hạn; giới hạn 8 slot giữ tác vụ nền hữu hạn, không gửi HTTP sau DNS quá ngân sách.
- HEAD không được hỗ trợ (405/501) báo unsupported, không tự chuyển sang GET.
  `reachable=true` chỉ có nghĩa đã nhận phản hồi HTTP; kể cả 404/403 cũng không phải
  chứng nhận tài nguyên tồn tại hoặc truy cập được bằng trình duyệt.
- API/AI/UI chỉ nhận origin của từng bước, không công khai path/query/fragment hoặc
  Location thô. Yêu cầu mạng dùng path/query thực để kiểm tra đúng link; máy chủ đích
  có thể ghi nhận IP backend và yêu cầu. Tránh gửi link chứa token riêng tư.
- Kết quả lỗi mạng không xóa bằng chứng văn bản. Chuyển miền và HTTP 200 không tự
  nâng cảnh báo; dấu hiệu miền đích kết hợp request hợp lệ chỉ có thể hỗ trợ suspicious,
  không tự tạo high/verified_match. Không thay nguồn RAG được duyệt.

Kết quả thật, lệnh chạy và giới hạn tại [báo cáo redirect](reports/url_redirects/README.md).

## Dùng ngay

Máy hiện tại đã cài thư viện/dữ liệu. Khởi động lại backend, Reload extension và tải
lại tab. Với máy mới, từ thư mục ứng dụng:

```powershell
python -m pip install -r requirements.txt
python setup_url_data.py
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Website: dán bài viết có URL HTTP/HTTPS hoặc www vào ô nội dung. Với link ẩn sau
chữ “bấm vào đây”, mở **Đính kèm địa chỉ đích của liên kết**, nhập đích và nhãn có
nguyên văn trong bài. Có thể nhập riêng URL tại trường đích nếu chưa có văn bản.
Xem lại JSON trước khi gửi. Chỉ URL không đủ để kết luận người gửi lừa đảo.

Extension: chọn vùng và **Bật quét vùng này**. Chỉ gửi chữ hiển thị và tối đa 20
href HTTP/HTTPS có nhãn chữ trong từng mục đủ điều kiện; bỏ vùng ẩn/trường nhập/
ngoài vùng. Chưa lấy link chỉ có biểu tượng/ảnh mà không có nhãn chữ, shadow DOM
đóng hoặc iframe. Đổi href dù chữ không đổi vẫn tạo phiên bản mục mới, bỏ phản hồi
cũ. Luồng OCR thủ công gửi kèm các link của phần DOM cùng vùng nếu có.

URL nhận diện từ OCR được đánh dấu origin=ocr; đọc sai ký tự trong ảnh có thể làm
đổi tên miền. Chỉ khớp bản OCR, không phải xác minh ảnh đọc đúng.

## Luồng và bằng chứng

1. Client gửi text/messages và links nếu lấy được href. ID/nhãn/offset ràng buộc
   vào message; sai/trùng/ngoài message bị từ chối trước khi gọi provider.
2. Gemini 1 nhận nội dung và đích liên kết đã rút về origin, không có userinfo,
   path, query hay fragment bí mật của href thu thập riêng. Văn bản người dùng dán
   hoặc OCR vẫn giữ nguyên để đối chiếu; không tự xóa URL đang hiện trong văn bản.
3. Sau kiểm chứng hành vi, chạy song song nhánh quy tắc/kho tình huống, RAG nguồn
   đã duyệt và URL. URL tự xuất hiện trong văn bản cũng được trích tại backend.
4. Nhánh URL xác định hostname ASCII/Unicode, miền đăng ký theo PSL gồm private
   suffix, tên gần giống, ký tự dễ nhầm, miền phụ chứa tên tham chiếu, userinfo,
   IP/cổng/HTTP và nhãn khác đích. Không chỉ lấy hai phần cuối bằng cắt chuỗi.
5. Gemini 2 đọc url_observations cùng văn bản gốc và hai nhánh cũ. Trả url_uses
   theo link_id, signal_codes thực sự có, finding_refs và vai trò sử dụng.
6. Backend loại ID/tín hiệu bịa, ref sai hoặc ghép link với request khác message.
   Dấu hiệu URL mạnh + request hợp lệ có thể hỗ trợ suspicious, không tự tạo high
   hoặc verified_match. High vẫn phải có căn cứ hành vi theo bộ quyết định hiện có.
   Lời cảnh báo/phủ định và request benign/bất định hành động không bị tự nâng mức.

URL phân tích giữ ở url_analysis, tách khỏi quote tin nhắn và source_matches của
RAG. Phần kết quả hiển thị hostname/miền/dấu hiệu bằng textContent, không tạo nút
mở URL đáng ngờ. Khớp miền tham chiếu hoặc không có dấu hiệu không chứng minh an toàn.
Mức tổng thể phản ánh hành vi văn bản; phải đọc cả thẻ URL, không dùng clear như
chứng nhận an toàn liên kết.

## Phạm vi dữ liệu

`knowledge/url/domain_references.json` khởi đầu chỉ YouTube và Google, đối chiếu
từ liên kết trên tài liệu trợ giúp chính thức, ghi source/date/status. Đây là
**documented_reference**, không giả định có người duyệt độc lập và không phải
allowlist an toàn. Chưa có danh sách đầy đủ ngân hàng/thương hiệu Việt Nam. Muốn
bổ sung phải đối chiếu nguồn chính thức và ghi xuất xứ/ngày kiểm tra.

Kho tham chiếu URL khác kho nguồn chính thống RAG; không tự duyệt các candidate
trong data/knowledge_sources.jsonl. Không có trong danh sách không có nghĩa giả mạo.
Miền gần giống chỉ là dấu hiệu so sánh chuỗi, không phải xác suất lừa đảo.

PSL dùng snapshot đóng gói trong tldextract, tắt tải mạng/cache ngoài. Unicode
17.0.0 được tải lúc setup, URL/hash/license tại unicode_manifest.json; header dữ
liệu giữ điều khoản Unicode. Bộ skeleton là gợi ý từ mapping, chưa tuyên bố tuân
thủ toàn bộ UTS #39/bidi. Cập nhật dữ liệu/thư viện cần khóa phiên bản và kiểm thử lại.

## Hợp đồng

API vẫn POST `/api/analyze`; links tối đa 20, URL tối đa 2.048 ký tự, label tối đa
1.000, tổng body 65.536 byte. Bare host ở trường URL riêng được giả định https để
phân tích cú pháp, không phải kiểm tra TLS. Tự trích trong text/OCR hỗ trợ HTTP(S)
và www, không tự đoán mọi tên miền rời. Vượt giới hạn có thể không được trích hết.

LinkInput: id, message_id, url, display_text, start/end theo Unicode code point
(có thể null), origin dom_href/user_supplied. Nhãn lặp không rõ vị trí vẫn có thể
phân tích cấu trúc href, nhưng không coi nhãn là bằng chứng đích không khớp.
Metadata href do client báo, backend không chứng nhận pháp y rằng trang thật chứa nó.

Có URL thì response schema 1.8, thêm url_analysis.network và url_uses; không URL giữ bản
1.5/1.6 như trước. reputation_status luôn not_checked. FinalReviewV4 nội bộ có
url_uses. background có thể rỗng signal_codes/finding_refs; hỗ trợ request rủi ro
phải có tín hiệu mạnh đã quan sát và finding request còn hiệu lực. Model không thể
tự tạo tín hiệu hay kết quả danh sách độc hại. Chuẩn kiểu tại backend/schemas.py.

Mock/live legacy trả quan sát URL nhưng chỉ two_pass có bước model rà chung và
backend nối URL với hành vi như mô tả. Cấu hình máy hiện tại dùng two_pass.

## Kiểm thử

[Báo cáo](reports/urls/README.md), [từng ca](reports/urls/CASES.md).
Số liệu trước bổ sung redirect: 137 unittest, 8 kiểm tra Chrome URL và 10 kiểm tra Chrome OCR hồi quy đạt.
Sáu ca Gemini hồi quy sau sửa hợp đồng đúng kỳ vọng; không chứng minh đạt 98% hoặc
độ chính xác trên dữ liệu thật. Bản này đã kiểm tra redirect HTTP HEAD; chưa kiểm tra WHOIS/tuổi miền,
Safe Browsing/VirusTotal, nội dung trang đích hoặc form. HTTPS không đủ kết luận an toàn.
