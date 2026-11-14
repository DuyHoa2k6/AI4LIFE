# URL kết hợp phân tích văn bản — 10/11/2026

Triển khai nhánh URL offline trong two_pass, thu href đúng vùng, giữ lời dẫn và
bằng chứng nguồn. Không mở trang, theo redirect, tra DNS/WHOIS hoặc gọi danh sách
độc hại. Phần miền đăng ký là chuỗi theo PSL, không chứng minh đã đăng ký/chủ sở hữu.

## Kiểm thử phần mềm

- **137 unittest backend đạt**, gồm 17 ca URL: PSL/private suffix, IDN/Unicode,
  miền gần giống/miền phụ, userinfo/IP/cổng, cấu trúc sai, nhãn khác đích, không DNS/
  HTTP, lọc tín hiệu bịa, giữ vai warning, nguồn OCR và không tăng mức từ background.
- **8 kiểm tra Chrome thật đạt**, extension unpacked với quyền manifest phân phối,
  chỉ thay origin API sang cổng thử 18767: lấy href ẩn sau nhãn, offset Unicode,
  không gửi trước bật, bỏ link ẩn/ngoài vùng/input, href-only đổi tạo request mới,
  bỏ kết quả cũ và không request trùng. Trang không điều hướng tới URL kiểm tra.
- **10 kiểm tra Chrome OCR hồi quy đạt**; bản copy OCR thử cấp all_urls chỉ để chụp
  headless như báo cáo OCR trước, không đổi manifest phân phối. **10 worker security
  và 7 worker OCR checks đạt**. Browser dùng API mock, không đo chất lượng Gemini.

Profile Chrome thử đã đóng/xóa đúng đường dẫn, không đụng profile người dùng.
`browser/report.json` lưu kết quả, `browser/extension.png` là trang giả lập.

## Gemini thật: giữ hai phiên riêng

| Phiên | Số ca | API thành công | Khớp kỳ vọng trên toàn bộ | Lỗi |
| --- | --- | --- | --- | --- |
| live — validation hợp đồng ban đầu | 6 | 4/6 | 4/6 | 2 |
| checked — hồi quy sau sửa hợp đồng | 6 | 6/6 | 6/6 | 0 |

Phiên đầu: URL-03 lỗi schema vì model dùng background với signal_codes rỗng; URL-06
bằng chứng model không qua kiểm chứng, trả EVIDENCE_INVALID. Đã cho background
mô tả miền tham chiếu không cần tín hiệu rủi ro hoặc finding hành vi. Không nới
kiểm chứng quote, không coi mảng rỗng là căn cứ hỗ trợ request rủi ro. Có unit test
cho hai trường hợp này. Giữ toàn bộ dự đoán lỗi, không lấy kết quả tốt nhất từng ca.

| Ca checked | Kỳ vọng/thực tế | Vai trò URL trong kết quả |
| --- | --- | --- |
| URL-01: yêu cầu OTP, miền gần giống | high | lookalike_reference_domain hỗ trợ request hợp lệ; OTP tự nó đã là căn cứ nguy hiểm |
| URL-02: bài cảnh báo miền gần giống | clear | quoted_warning, không thành request của người đăng |
| URL-03: tự xem nội dung tại miền tham chiếu | clear | background, không tạo tín hiệu chỉ để lấp mảng |
| URL-04: yêu cầu đăng nhập, nhãn/đích khác | suspicious | display_target_mismatch + brand_in_subdomain đi cùng request |
| URL-05: tên miền tiếng Việt | clear | punycode chỉ background, không mặc định độc hại |
| URL-06: cảnh báo link có nhãn/đích khác | clear | quoted_warning, vẫn hiển thị dấu hiệu kỹ thuật |

p50 API **13,860s**, p95 **15,142s** trên sáu ca checked. Gồm hai lượt model và có thể
một lần sửa; không phải riêng thời gian phân tích URL local. Toàn bộ ca checked có
URL được dùng với đúng ID/tín hiệu và vai; không có tín hiệu tự bịa được giữ lại.
URL-04 model gán grant_access cho yêu cầu đăng nhập; mức suspicious khớp kỳ vọng
nhưng taxonomy chi tiết vẫn cần rà thêm, không coi tám answers hoàn toàn đúng.

Hai phiên cùng bộ tổng hợp nhỏ đã biết, nhãn do người triển khai đặt trước. Không
được gộp hoặc coi checked là holdout độc lập/độ chính xác 100%. Không chứng minh
đạt 98%, không xác nhận chủ sở hữu hoặc độ độc hại thực tế của các tên miền ví dụ.
Chưa thử đầy đủ SSO hợp pháp, redirect hợp pháp, link rút gọn, miền thương hiệu
thay thế hay các trang thật. RAG vẫn chưa có nguồn chính thống đủ duyệt.

Các hash mã/prompt/dữ liệu/Unicode/registry không đổi trong từng phiên; checked
khóa thêm phiên bản thư viện và hash PSL. Sau phiên đầu mới sửa hợp đồng, lưu
verification riêng trước khi chỉnh. Dự đoán ghi trước khi đọc expected. Không đọc,
chỉnh hoặc đưa holdout vào runtime. Không sửa API key/model/bật billing.

## Tái lập và bàn giao

Thiết lập theo [README_URL.md](../../README_URL.md), từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests -q
node tests/browser_url.mjs
python mixed_check.py --mode two_pass --output reports/urls/new_run --fixtures-dir fixtures/url_checks --pause 3 --service-error-limit 6
python url_report.py
```

Output mới phải chưa tồn tại; report script tổng hợp hai phiên đã bàn giao.
[CASES.md](CASES.md) chứa input và quan sát/dự đoán từng ca; `checked/lock.json`,
`checked/predictions.json`, `checked/summary.json`, `runs.json`, `summary.json`
giữ cấu hình, dự đoán và số đếm. Dữ liệu URL ở `knowledge/url`, tách kho RAG chính
thống; hai miền tham chiếu YouTube/Google là documented_reference, không giả có
người duyệt độc lập hoặc dùng như allowlist an toàn.
