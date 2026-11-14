# OCR ảnh và phân tích có nguồn

Tesseract.js **7.0.0**, mô hình **vie+eng**, chạy tại backend local bằng Node.js.
Ảnh không gửi tới Gemini/dịch vụ OCR cloud. Văn bản sau khi xem trước và xác nhận
được gửi qua API phân tích hiện có, theo mode backend. OCR không xác minh danh tính.

## Thiết lập

Máy hiện tại đã cài thư viện/mô hình và thử thật. Khởi động lại backend, Reload
extension ở `chrome://extensions`, tải lại tab. Với máy mới, từ thư mục ứng dụng:

```powershell
python -m pip install -r requirements.txt
npm.cmd ci --prefix ocr --ignore-scripts --no-audit --no-fund
python setup_ocr.py
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Cần Python, Node.js và npm; PowerShell có thể chặn npm.ps1 nên dùng npm.cmd.
URL/hash mô hình ở `ocr/models/hashes.json`. Runtime chỉ đọc mô hình local; không
cần key OCR hoặc GPU. Key Gemini và cấu hình hiện có giữ nguyên ở backend.

## Website

1. Mở `http://127.0.0.1:8000`, mở **Đọc chữ trong ảnh (OCR cục bộ)**.
2. Chọn ảnh PNG/JPEG/WebP, bấm **Đọc chữ trong ảnh**, đối chiếu chữ với ảnh.
3. Giữ lời dẫn của bài viết trong ô nội dung: bài cảnh báo có ảnh lời dụ phải gửi
   cả lời dẫn, không chỉ chữ trong ảnh.
4. Bấm **Xem lại trước khi gửi**, kiểm tra messages/ocr_sources, rồi **Phân tích**.

Nếu sửa/che message OCR trong JSON nhưng giữ source_id, API trả OCR_TEXT_CHANGED:
bản sửa không còn là OCR nguyên gốc. Hãy che ảnh rồi OCR lại, hoặc gửi phần đã sửa
như văn bản tự nhập, bỏ tham chiếu OCR. Nguồn hết hạn sau 15 phút hoặc restart:
đọc ảnh lại. Ảnh trắng/không đọc được chữ không tự gửi phân tích và không coi an toàn.

## Extension

Quét vùng tự động chỉ gửi văn bản DOM và liên kết; không tự chụp, đọc chữ hoặc
phân tích ảnh. Bấm xem trước chỉ chụp tại máy. Bấm **Đọc chữ trong ảnh này** mới
gửi ảnh để OCR; sau đó bấm **Phân tích bài và chữ trong ảnh** mới đánh giá rủi ro
từ phần chữ OCR. Chưa bấm nút phân tích ảnh thì chữ OCR chưa được gửi phân tích.

1. Mở extension từ thanh công cụ để cấp activeTab, chọn vùng chứa ảnh và lời dẫn.
2. Bấm **Ảnh trong vùng · xem trước**; chưa gửi ảnh/phân tích, không cần bật tự quét.
3. Xem kỹ ảnh cắt. Nếu có phần hiển thị đè lên vùng/ngoài ý muốn, chọn vùng nhỏ hơn.
4. Bấm **Đọc chữ trong ảnh này** để gửi ảnh cắt tới backend local.
5. Đối chiếu chữ, bấm **Phân tích bài và chữ trong ảnh**.

Chỉ chụp phần đang hiển thị. Viewport được chụp tạm trong worker rồi cắt local,
không gửi nguyên viewport tới API. Giá trị input/textarea/select/contenteditable
trong vùng được che trước preview. Đổi vùng/tab/tài liệu/URL, cuộn/resize làm đổi
hình học vùng hoặc đổi DOM/img khiến bản chụp không còn hợp lệ; phải chụp lại.
Dừng phiên bỏ phản hồi cũ. Nếu gặp BUSY do lượt quét chữ đang chạy, đợi xong hoặc
chọn lại vùng và dùng OCR trước khi bật tự quét chữ.

Đây là OCR có nút xác nhận, chưa OCR tự động hàng loạt mọi ảnh khi cuộn. Không tải
URL ảnh tùy ý. Manifest phân phối không thêm quyền host rộng; dùng activeTab đã cấp.

## Hợp đồng và giới hạn

- POST `/api/ocr`: body là bytes ảnh, Content-Type image/png, image/jpeg hoặc
  image/webp; không multipart, không nhận URL. Tối đa **4 MB, 8 triệu pixel**.
- Tối đa hai tiến trình OCR đồng thời, giới hạn tài nguyên **60 giây/ảnh**. Cấu hình
  tạm tắt response timeout của Gemini trước đây vẫn giữ, độc lập với giới hạn OCR.
- Trả text, source_id, image_sha256, engine, confidence, width/height sau xoay EXIF,
  blocks gồm text/tọa độ dòng chữ, ocr_ms, status ready/low_confidence/no_text.
  Điểm <60 là ngưỡng chất lượng thử nghiệm, không phải xác suất cảnh báo đúng.
- POST `/api/analyze` giữ text/messages, thêm tối đa 4 `ocr_sources` dạng
  `{message_id, source_id}`. Backend kiểm tra nguồn còn hiệu lực và text khớp cache
  trước khi gọi provider. Payload không có OCR hoạt động như trước.
- Phản hồi có OCR dùng schema **1.6**, thêm input_sources/input_warnings. Nguồn ảnh
  tách khỏi source_matches của RAG, không tạo verified_match từ OCR.
- Quote/start/end kiểm tra trên message OCR theo Unicode code point. Khớp bản OCR
  không chứng minh đọc đúng ảnh. Tọa độ dòng có trong API; giao diện hiện tô chữ
  trên bản đã gửi, chưa có overlay từng quote lên ảnh.

Ảnh chuẩn hóa được lưu tạm `.ocr-tmp` và xóa trong finally. Nếu backend bị tắt đột
ngột có thể còn file tạm; thư mục được bỏ qua khi commit. Cache RAM giữ text/blocks/
hash, tối đa 128 nguồn; token hiệu lực 15 phút, bản hết hạn dọn ở lượt OCR kế tiếp
hoặc mất khi restart. Không đưa ảnh/OCR thử vào dataset hoặc chỉ mục RAG runtime.

## Kiểm thử

Xem [báo cáo](reports/ocr/README.md). Ba ảnh chữ in tiếng Việt và một ảnh trắng đã
chạy OCR thật; ba bản có chữ được phân tích Gemini thật. Chưa đánh giá ảnh mờ, chữ
viết tay, QR, video, bố cục phức tạp hoặc ảnh ngoài màn hình.

Mock còn hạn chế: bài cảnh báo có thể high, điều kiện qua hai câu có thể need_context.
Không dùng mock để kết luận chất lượng AI. Gemini two_pass đã trả high/clear/clear
trên ba ca thử, nhưng mẫu rất nhỏ, không chứng minh độ chính xác tổng quát.
