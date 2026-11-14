# Kiểm thử OCR — 10/11/2026

## OCR thật + Gemini thật

Ảnh tổng hợp render bằng font Arial tiếng Việt trên nền trắng, không phải ảnh
người dùng thật. Kỳ vọng đặt trước, dự đoán ghi trước khi đọc references.

| Ca | Nội dung | OCR | Gemini two_pass | OCR API | Phân tích |
| --- | --- | --- | --- | --- | --- |
| O1 | Chuyển phí trước để nhận lại cọc | Khớp chữ | high | 0,565s | 14,034s |
| O2 | Ảnh lời dụ, DOM là bài cảnh báo | Khớp chữ | clear | 0,530s | 10,892s |
| O3 | Tự nhập mã, không giao mã cho người khác | Khớp chữ | clear | 0,571s | 12,932s |
| O4 | Ảnh trắng | no_text | Không gọi Gemini | 0,518s | — |

Ba ảnh chữ khớp toàn bộ sau chuẩn hóa khoảng trắng; không sửa text trước khi gửi
model. O1 có một lần sửa nhất quán trong lượt rà, O2/O3 không sửa. Trích rủi ro đúng
message ảnh; O2 giữ quoted_warning/denial thay vì coi người đăng đang yêu cầu chuyển
tiền. Phản hồi có nguồn OCR và nhắc đối chiếu ảnh. Không suy ra mọi ảnh đều đọc đúng.

Cả ba ca no_approved_sources, không phải phép đo RAG có tài liệu thật. Chưa chấm
độc lập tám answers, chưa đo tải đồng thời/cold-warm có kiểm soát hoặc dữ liệu thật.
Không tuyên bố đạt 98%. Dự đoán và số liệu tại `two_pass/predictions.json`,
`two_pass/summary.json`; ảnh và references tại `fixtures/ocr_checks` trong ứng dụng.

## Mock báo riêng

OCR vẫn thật nhưng phân tích là quy tắc: O1 need_context (chưa nối điều kiện đúng),
O2 high (chưa hiểu lời dẫn cảnh báo ngoài ảnh), O3 clear, O4 no_text không phân tích.
Không giấu hai ca mock sai mức hoặc lấy kết quả Gemini thay thế. Xem `mock/summary.json`.

## Phần mềm và Chrome

- **120 unittest backend đạt**, gồm source/text bị sửa, nguồn giả/hết hạn, tham
  chiếu sai/trùng, body/định dạng/pixel quá lớn và DOM/OCR cùng tới hai lượt model.
- **10 worker security checks đạt**, **7 OCR worker checks đạt** với Chrome/canvas
  mô phỏng: crop ngoài viewport, che input, đổi tab/session, chỉ gửi bytes ảnh cắt.
- **10 kiểm tra Chrome thật đạt**: website chọn ảnh không gửi, OCR thật, xem trước,
  nguồn và ảnh trắng; extension unpacked chụp/cắt và OCR thật, không có chữ ngoài
  vùng/giá trị input trong OCR/request, chỉ gọi sau xác nhận. Browser dùng API mock.

Chrome **157.0.8103.50**, profile riêng, API thử cổng 18766. Bản extension **chỉ trong
test** thêm `<all_urls>` để kiểm tra capture API trong headless. Manifest phân phối
vẫn activeTab/scripting và origin backend. Chưa nghiệm thu việc cấp activeTab bằng
nút toolbar trong Chrome tương tác thật; không suy rộng hỗ trợ mọi Facebook/Zalo
hoặc overlay phức tạp. Kết quả `browser/report.json`, ảnh `browser/web.png` và
`browser/extension.png`. Profile thử đã đóng và xóa đúng đường dẫn.

Hai lần debug harness trước khi đạt lỗi chọn worker/cú pháp async của test, không
phải kết quả OCR/Gemini; giữ mẫu `browser/harness_debug.json`.

## Tái lập

Thiết lập theo [README_OCR.md](../../README_OCR.md), chạy từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests -q
node tests/worker_security.mjs
node tests/ocr_worker.mjs
python ocr_check.py --mode mock
python ocr_check.py --mode two_pass
node tests/browser_ocr.mjs
```

ocr_check yêu cầu output chưa tồn tại để không ghi đè; đổi đường dẫn trong script
khi chạy phiên mới. Bộ thử do `create_ocr_checks.py` tạo, không đọc/chỉnh holdout
hoặc đưa ảnh thử vào kho tình huống phục vụ người dùng.
