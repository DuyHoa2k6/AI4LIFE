# HTTP redirect và căn cứ URL — 10/11/2026

## Phạm vi đã làm

Thư viện chuẩn Python (`http.client`, `socket`, `ssl`) gửi HEAD, lấy status/Location,
theo tối đa 3 chuyển hướng, ghim kết nối vào IP public đã kiểm tra. Nhánh này chạy
song song RAG/quy tắc sau Gemini 1. Gemini 2 nhận quan sát cấu trúc + `network`;
backend chỉ chấp nhận sử dụng tín hiệu thật gắn với finding có bằng chứng hợp lệ.
Không đọc body/JS, không kiểm tra danh tiếng, không tự nâng high/verified_match.

API schema 1.8 thêm url_analysis.network; UI website/extension hiển thị trạng thái,
chuỗi status/origin và origin cuối. Không trả path/query/fragment hoặc Location thô.
Người dùng được báo trước HEAD sẽ được gửi tới máy chủ đích. Extension 0.5.0.

## Đã đo thực tế

- `live_network.json`: HTTP HEAD thật tới dịch vụ công khai httpbin, quan sát
  `/redirect/2`: 302 → 302 → 200; `/status/404`: phản hồi 404 được lưu riêng.
  Thử IP loopback: blocked/non_public_address, không có HTTP hop.
  Thời gian cụ thể từng lần chạy nằm ở elapsed_ms; dịch vụ bên ngoài có thể thay đổi.
- `live_pipeline.json`: ASGI TestClient + HTTP tới Gemini và httpbin thật, chế độ
  two_pass, HTTP API 200/schema 1.8, risk_status clear cho bài đọc tài liệu thử nghiệm
  không yêu cầu giao mã/tiền, tổng 15,8176 giây. Input lưu riêng `live_input.json`.
  Đây là kiểm tra tích hợp một ca bình thường, không phải kiểm định chất lượng 98%.
  Phép thử này thực hiện trước bổ sung timer ngắt socket và đóng response; sau sửa
  đã chạy lại HEAD thật và toàn bộ unit test, không chạy lại Gemini cho thay đổi tài nguyên.

## Hồi quy sau sửa

- 157 unittest đạt, gồm 17 ca mới kiểm tra network/pipeline: địa chỉ nội bộ,
  IPv6 transition, mixed DNS, userinfo, port, redirect loop/limit, HEAD 405, 404,
  lỗi mạng/TLS/DNS, ghim IP, không cookie/auth/body, giới hạn URL, dấu hiệu đích cuối,
  và lỗi mạng không xóa cảnh báo văn bản. Các ca này dùng network giả lập có kiểm soát.
- 14 kiểm tra Chrome đạt: extension unpacked thật, backend mock; thẻ redirect
  minh họa được kiểm tra hiển thị bằng dữ liệu cố định. Không coi đó là HTTP thật.
- 13 kiểm tra worker và 4 kiểm tra phiên bản popup đạt.

## Lệnh chạy từ thư mục ứng dụng

```powershell
python -m unittest discover -s tests
node tests/worker_security.mjs
node tests/popup_version.mjs
node tests/browser_url.mjs
python tests/check_url_redirects.py
python tests/check_url_redirects.py --live
```

Hai lệnh cuối cần internet; --live gọi Gemini theo key/model cấu hình backend.
Script ghi lại báo cáo cùng tên khi chạy lại, không đọc nhãn đánh giá/holdout.

## Giới hạn và sử dụng

Mặc định bật trong live/hybrid/two_pass, mock không ra mạng. Tắt bằng
SCAMSHIELD_URL_NETWORK_ENABLED="0". Tối đa 3 URL/request, 4 HEAD/URL, 6 giây/chuỗi,
8 slot/từng tiến trình; có trạng thái deferred khi quá giới hạn. Giới hạn mạng độc
lập với cấu hình tắt timeout Gemini. HEAD 405/501 không tự thử GET; redirect bằng
JS/meta-refresh/cookie/browser có thể khác chuỗi quan sát. DNS hệ điều hành không
thể hủy ngay, nhưng tác vụ nền bị giới hạn slot và không gửi HTTP sau ngân sách.

HTTP 200 không chứng nhận an toàn, 404 không chứng minh lừa đảo; timeout/DNS lỗi
không đủ kết luận tên miền không tồn tại. `reachable=true` chỉ là đã có phản hồi
HTTP. Chuyển miền bình thường không tự tăng mức. Chưa đo tải đồng thời ngoài slot
giới hạn hoặc tỷ lệ phát hiện lừa đảo trên dữ liệu người dùng thật.

Khởi động lại backend, Reload extension 0.5.0 ở chrome://extensions rồi tải lại tab.
Không cần API key mới, thư viện mới hoặc cài thêm công cụ.
