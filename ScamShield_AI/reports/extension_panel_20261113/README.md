# Panel extension ScamShield 0.8.0 — 13/11/2026

Đã thay giao diện panel được chèn vào trang, giữ nguyên backend và quyết định bốn mức. Đã đọc `04_API.md`, `backend/schemas.py`, renderer hiện tại và luồng content script/service worker trước khi sửa. Website và schema API không đổi.

## Kết quả hiển thị

- Panel rộng tối đa 370px, tự giới hạn theo viewport, Shadow DOM đóng và CSS riêng. Header, nút điều khiển và tiến độ đứng ngoài vùng cuộn kết quả.
- Mỗi cảnh báo mặc định có mức, tóm tắt từ `display_summary`, hành động từ `display_action`, nút mở chi tiết. Không dựng kết luận mới từ keyword ở frontend. Bản API thiếu trường hiển thị được báo thiếu tóm tắt, không tự suy diễn.
- Bốn nhãn: **Nguy cơ cao**, **Cần xác minh**, **Cần thêm thông tin**, **Chưa thấy dấu hiệu**. Các mục clear gộp một dòng trong panel, kèm “Trong nội dung đã kiểm tra”. Bài viết giữ badge nhỏ để nhận diện mục tương ứng.
- Chi tiết tối đa ba đoạn trích nguyên văn, kiểm lại message và vị trí Unicode code point; tối đa hai giải thích của backend và hai câu hỏi backend cung cấp. Bằng chứng giả, kể cả giải thích đi kèm, bị bỏ. Đoạn quá dài không được tự cắt thành một quote mới; giao diện báo chưa có đoạn phù hợp.
- Không hiển thị answers, source_matches, nguồn RAG, prompt, rule/event ID, trace, JSON hoặc kết quả mô hình thô. Các khối dài trước đây trong badge được thay bằng thẻ ngắn và chi tiết mở riêng.
- Bổ sung thông tin gửi đúng `case_id`, `situation_id`, `revision`, `content_version`, `question_id`, `answer`; phiên cũ bị từ chối. Chỉ hiện form khi backend có câu hỏi và khóa liên kết hợp lệ.
- Mất mạng là trạng thái chưa kiểm tra được, không phải một mức rủi ro. Nút **Thử lại** kiểm tra kết nối và gửi lại mục lỗi trong vùng còn hợp lệ, không buộc chọn lại vùng.
- Nút **Ảnh trong vùng (N)** chỉ hiện khi có ảnh đang hiển thị trong vùng. Xem trước, đọc chữ và phân tích vẫn là các thao tác riêng; không tự OCR khi quét văn bản.

## Cách dùng bản mới

1. Mở `chrome://extensions`, tìm ScamShield AI và bấm **Tải lại**. Nếu chưa cài, chọn **Load unpacked** tới thư mục `ScamShield_AI/extension` trong repo.
2. Tải lại tab muốn kiểm tra, mở extension và chọn vùng. Chỉ bắt đầu gửi nội dung sau **Bật quét vùng này**. Bản 0.8.0 phát hiện content script cũ và yêu cầu tải lại tab.
3. Kéo phần đầu panel để di chuyển. Khi focus phần đầu, phím mũi tên dịch 10px, Shift + mũi tên dịch 40px; Home đặt lại vị trí. Có nút **Đặt lại vị trí** trong **Thông tin hàng chờ**. Tọa độ lưu trong sessionStorage của trang, luôn giới hạn lại theo viewport.
4. Nút **−** thu gọn thành nút nổi, vẫn tiếp tục quét. Bấm nút nổi để mở lại; nút nổi cũng kéo được. **×** hoặc **Dừng quét** dừng phiên, bỏ hàng đợi và đóng panel. Tạm dừng giữ kết quả nhưng gắn nhãn lịch sử.

## File thay đổi

| File | Thay đổi |
| --- | --- |
| `extension/panel_view.js` | Mới: bố cục, CSS cô lập, kéo/thu gọn, giới hạn vị trí, thẻ kết quả và form bổ sung |
| `extension/content.js` | Nối panel mới với phiên/quét có sẵn; badge gọn; retry; ảnh theo thao tác; dọn listener khi đóng |
| `extension/popup.js` | Inject thêm panel_view.js và kiểm phiên bản 0.8.0 |
| `extension/manifest.json` | Phiên bản 0.8.0, giữ quyền hiện tại |
| `tests/browser_panel.mjs` | Mới: kiểm thử Chrome thật và chụp ảnh |
| `tests/popup_version.mjs` | Kiểm phiên bản mới |
| `tests/browser_week2.mjs`, `browser_url.mjs`, `browser_ocr.mjs`, `browser_local_provider.mjs` | Đồng bộ danh sách script inject với dependency mới; không báo các bộ lịch sử này đã được chạy lại |

## Kiểm thử đã chạy

Chrome **157.0.8103.51**, extension unpacked thật, chạy headless và điều khiển bằng CDP. **39/39 kiểm tra qua**. [report.json](report.json) lưu từng kết quả.

- Một ca rủi ro cao đi qua API/backend thật. Các ca bốn mức, mất mạng và phản hồi trễ dùng response được kiểm soát trong service worker để kiểm giao diện, không gọi mô hình ngoài.
- Chưa bật quét: 0 request. Nội dung ngoài vùng và chữ của chính panel không có trong request phân tích.
- Kéo thật tới bốn góc, kiểm vị trí thay đổi và không phát sinh request; viewport 1280×900 và 390×650; bàn phím, focus, chọn chữ không kéo panel; click điều khiển không kích hoạt kéo.
- Thu gọn vẫn gửi phân tích khi nội dung trong vùng thay đổi. Kết quả mới không đóng chi tiết của mục khác. Cuộn bằng bánh xe trong danh sách không di chuyển trang ngoài; quét nền không đặt lại scrollTop.
- Bốn nhãn, clear gộp, câu trích đúng và câu trích giả bị loại; không có các marker dữ liệu nội bộ trong cả thẻ lẫn chi tiết.
- Hiện nút ảnh theo ảnh thực trong vùng; trước thao tác ảnh không có OCR tự động. Bộ kiểm OCR worker riêng: **7/7** qua.
- Bổ sung từ phiên cũ bị từ chối; ca hiện tại gửi đủ sáu trường liên kết, không gửi thêm trường nội bộ của case_context.
- Mất mạng/thử lại vẫn giữ vùng. Nội dung đổi khi request cũ chưa về không giữ kết quả cũ. Hai chu kỳ dừng/bật không nhân bản panel.
- Đóng bằng ×: panel và nút nổi thực sự `display:none`. Probe trong isolated world đo **0 observer quét và 0 listener UI toàn cục còn hoạt động**. Listener runtime dùng để mở lại extension được giữ.
- Bộ popup version **4/4**, worker security **14/14**, OCR worker **7/7**; kiểm tra cú pháp content.js và panel_view.js qua.

Lệnh chạy từ thư mục ứng dụng `ScamShield_AI` bên trong repo:

```powershell
node tests/browser_panel.mjs
node tests/popup_version.mjs
node tests/worker_security.mjs
node tests/ocr_worker.mjs
```

Browser test cần Node có WebSocket, Python cùng dependency backend, Chrome tại đường dẫn trong script và quyền khởi chạy Chrome/local server. Test dùng cổng 18773 và profile riêng; không sửa cấu hình/key backend của người dùng.

## Ảnh nghiệm thu

- [Panel mở, chờ bật quét](open.png)
- [Panel có cảnh báo và chi tiết](warnings.png)
- [Nút nổi thu gọn](minimized.png)
- [Khung hẹp 390×650](narrow.png)

## Giới hạn

Đây là nghiệm thu giao diện trên trang fixture, không chứng minh độ chính xác phân tích hay tương thích mọi website. Các response được kiểm soát không thay cho phép đo chất lượng backend. Chưa kiểm toàn bộ quá trình nhận dạng ảnh thật trong đợt UI này; OCR worker và điều kiện kích hoạt thủ công đã được kiểm. Không thêm chức năng OCR/RAG/URL mới. Frontend không tự tạo câu hỏi thiếu hay giải thích ngữ nghĩa khi backend không cung cấp; backend phải trả các trường hiển thị và liên kết câu hỏi phù hợp.
