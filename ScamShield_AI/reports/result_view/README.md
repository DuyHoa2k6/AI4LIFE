# Giao diện kết quả ScamShield AI — 10/11/2026

Đã đọc hợp đồng 04_API.md, schema backend và renderer/client trước khi sửa.
Không thay prompt, truy xuất, provider, quy tắc hoặc quyết định mức rủi ro.
Backend chỉ thêm route `/result-view.js` để website nhận cùng component với extension.

## Kết quả hiển thị

- Tiêu đề và nhãn một trong 5 mức nằm ngoài vùng cuộn của thẻ.
- Nội dung mở ngay: tóm tắt 1–2 câu, bước xác minh phù hợp và câu hỏi bổ sung nếu có.
- Nút **Xem giải thích** cuộn trong thẻ tới **Vì sao có cảnh báo này?**.
- Mỗi dấu hiệu chỉ có trích dẫn khớp đúng message/người nói/code point và giải thích
  ngắn theo hành vi/vai lời trích. Không phát mô tả, inference hoặc summary tự do.
  Nếu chuỗi số chưa được xác định là mã, giữ “có thể là mã xác thực”. Không có trích
  hợp lệ thì nêu phần còn thiếu, không tạo quote hoặc tự sửa mức rủi ro.
- Không dựng DOM cho answers, source_matches, retrieval hoặc kết quả thô của mô hình.
  Phần URL chỉ có thông tin kỹ thuật người dùng cần, không chứa tài liệu RAG.
- Chiều cao tối đa theo màn hình và vùng cuộn chứa thẻ; nội dung ngắn không bị kéo
  giãn thành khung trống. Website thử ở 390px, thẻ extension thử trong vùng 320px.
- **Bổ sung thông tin** giữ đúng bản đầu vào. Website đưa bản bổ sung vào bước xem
  lại trước khi gửi; extension chuyển vào hàng chờ hiện có sau khi người dùng xác
  nhận. Version/epoch/fingerprint và định danh lần phân tích chặn form hoặc phản hồi cũ.
  Luồng ảnh cũng giữ bản OCR/DOM và nguồn OCR của lần phân tích đó.

## Kiểm thử

| Phép thử | Kết quả | Phạm vi |
| --- | --- | --- |
| browser.json | 42/42 | Chrome thật, website/extension, fixture UI và backend mock |
| regression.json | 29/29 | Website, quét vùng, lỗi mạng, phản hồi cũ, 35 mục và hàng chờ |
| ocr_regression.json | 11/11 | Chrome + OCR local thật, phân tích mock |
| unittest backend | 157/157 | Hợp đồng, trích dẫn, quyết định, URL, OCR và kiểm tra route |
| worker / popup | 13/13 và 4/4 | Quyền gửi, payload, phiên và phiên bản |

Ba mức high/need_context/clear đều được thử trên cả hai client. Fixture cố ý chứa
dấu đánh dấu PRIVATE trong answers, nguồn, summary và mô tả nội bộ; xác nhận chúng
không xuất hiện ở kết quả. Có kiểm tra quote giả, Unicode, câu “có thể”, thao tác
cuộn và form bổ sung đã cũ. Ca dài có 28 dấu hiệu; ca ngắn kiểm tra chiều cao tự co.
Thử 35 mục có thao tác cuộn vì thẻ mở ngay đẩy một số mục xuống ngoài viewport;
35 request, không trùng, đồng thời tối đa 1. Không tính phép thử UI là chất lượng Gemini.

Ảnh xem trước: [website rủi ro cao](web-high.png), [website cần thông tin](web-need_context.png),
[website ngắn](web-clear.png), [extension rủi ro cao](extension-high.png),
[extension cần thông tin](extension-need_context.png), [extension ngắn](extension-clear.png).

## Chạy lại và cập nhật

```powershell
python -m unittest discover -s tests
node tests/browser_url.mjs
node tests/browser_week2.mjs
node tests/browser_ocr.mjs
node tests/worker_security.mjs
node tests/popup_version.mjs
```

Khởi động lại backend để có route JS mới. Reload extension **0.6.0**, rồi tải lại
trang bằng Ctrl+Shift+R. Không cần đổi API key, cài thêm thư viện hoặc sửa cấu hình model.
Ảnh/fixture chỉ dùng dữ liệu tổng hợp công khai; không đọc tập holdout.
