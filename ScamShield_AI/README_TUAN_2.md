# ScamShield AI — website và extension tuần 2

Renderer hiện hỗ trợ two_pass, nguồn thực sự dùng và trạng thái fallback. Bật theo [TWO_PASS.md](TWO_PASS.md), reload extension/tab; client chờ tối đa 55 giây, không thay chỉ tiêu trải nghiệm dưới 2 giây. Số liệu tuần 2 dưới đây là snapshot local/mock, kết quả mới ở reports/two_pass; chưa xác nhận mạng xã hội thực.

## Chạy đơn giản

Nếu server tuần 1 còn chạy, nhấn Ctrl+C ở terminal của server đó rồi chạy lại để nạp website mới. Từ thư mục gốc repo:

```powershell
python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log
```

Hoặc mở `ScamShield_AI/chay_he_thong.cmd`. Truy cập **http://127.0.0.1:8000/**. Máy đã có các dependency Python; máy mới cài `python -m pip install -r ScamShield_AI/requirements.txt`. Website là HTML/CSS/JavaScript thuần, được FastAPI phục vụ cùng origin; không cần Node/npm hoặc bước build để sử dụng. Node chỉ dùng chạy kiểm thử tự động. Đây là lựa chọn triển khai cho demo local, thay vì bộ React/Vite gợi ý tại 02.

1. Dán văn bản; hoặc chọn “Hội thoại” và dán mảng `[{"id":"m1","speaker":"sender","text":"..."}]` theo thứ tự.
2. Thêm bối cảnh/câu hỏi nếu cần. Bấm **Xem lại trước khi gửi**: chưa gọi API phân tích.
3. Sửa JSON bản gửi để che dữ liệu hoặc chọn đoạn rồi bấm **Che đoạn đang chọn**. Giữ JSON hợp lệ.
4. Rà nơi xử lý rồi bấm **Phân tích nội dung**. Kết quả gồm mức cảnh báo, đúng bản đã gửi với đoạn tô sáng, hành động, hướng xác minh và tám câu trả lời.
5. Nếu có câu hỏi bổ sung, nhập bối cảnh rồi bấm xem lại/phân tích bổ sung. Giữ nguyên nội dung gốc và nối bối cảnh mới. Sửa bản nhập sẽ hủy lượt đang chờ, kết quả cũ không ghi đè lượt mới.

Chế độ mặc định **mock**, bộ quy tắc tích hợp chưa đại diện chất lượng mô hình. Live dùng cấu hình tuần 1, website/extension hiện tên máy chủ provider trước khi gửi. Không nhúng API key vào client. Backend không lưu hội thoại; client chỉ giữ trong bộ nhớ phiên, không localStorage. Việc chuyển sang live chưa được kiểm chứng với provider thật trong lượt này.

## Cài Chrome Extension unpacked

1. Chạy backend ở cổng 8000.
2. Mở `chrome://extensions`, bật **Developer mode / Chế độ dành cho nhà phát triển**.
3. Bấm **Load unpacked / Tải tiện ích đã giải nén**, chọn đúng thư mục **ScamShield_AI/extension** có `manifest.json`.
4. Mở http://127.0.0.1:8000/fixture và bấm biểu tượng extension → **Chọn vùng quét**.
5. Bấm vào **phần nền xanh** của khối bình luận để chọn cả danh sách, tránh bấm riêng một tin nếu muốn theo dõi nhiều tin. Rà viền, phạm vi và nơi xử lý trong thanh điều khiển.
6. Bấm **Bật quét vùng này**. Nhãn xuất hiện ở đúng mục; bấm nhãn để xem bằng chứng và hướng xác minh. Khi cuộn trong khối hoặc tải thêm, mục mới hiển thị được xếp hàng tự động.
7. Dùng **Tạm dừng**, **Tiếp tục**, **Đổi vùng**, **Dừng quét**. Đổi vùng luôn cần bật lại. Bấm Escape để hủy chọn. Sau khi điều hướng/gỡ vùng, chọn lại vùng. Mục lỗi không tự retry; để thử lại sau khi có mạng, dừng và chọn/bật vùng mới.

Fixture có bài hợp lệ, bình luận đáng ngờ trong vùng, bài cảnh báo, ca thiếu bối cảnh, mục ngoài vùng, nội dung hidden/opacity=0, input/mật khẩu, contenteditable, tải thêm, sửa nội dung, đổi tuyến, gỡ vùng và thêm 35 mục. Dữ liệu đều tổng hợp.

## Cách giữ đúng phạm vi

- Manifest V3 chỉ yêu cầu `activeTab`, `scripting` và host loopback `http://127.0.0.1/*`; không xin quyền tất cả website, lịch sử hay cookie. Chrome host permission theo host không giới hạn port; service worker cố định URL `http://127.0.0.1:8000/api/analyze`.
- Content script chỉ chèn vào main frame sau thao tác popup. API gọi qua worker; kiểm tra extension ID, tab, frame, document, URL và session. Không nhận URL API tùy ý từ nội dung trang. Payload API chỉ `{text}`; mã phiên/mục/version giữ tại client.
- Tách đơn vị theo `[data-ss-item]`, `article`, `[role=article]`, `li`, chọn đơn vị trong cùng không gộp cha/con. Không thấy ranh giới thì xử lý khối đã chọn như một đơn vị. Từ chối body/html, trường nhập và khối quá rộng; mỗi mục tối đa 10.000 code point.
- Chỉ lấy text node đang hiển thị trong vùng nhìn thấy, có kiểm tra ancestor ẩn và vùng cuộn; bỏ trường nhập, editor, script, iframe, UI của tiện ích. Kiểm tra lại text, viewport và membership ngay trước gửi và trước gắn nhãn. Không đọc HTML toàn trang hoặc input.value.
- Debounce 120 ms, polling 500 ms kết hợp MutationObserver/IntersectionObserver, một request đồng thời, hàng chờ tối đa 20. Mục dư hiển thị số bị hoãn và được xét lại khi có chỗ; không mở hàng chờ vô hạn. Khử trùng theo đối tượng DOM và phiên bản text trong phiên; DOM được tái sử dụng với text mới được phân tích lại.
- Tạm dừng hủy hàng chờ và phiên worker; tiếp tục mở session mới và chỉ giữ kết quả của text không đổi. Đổi vùng/dừng xóa badge và các bản ghi. Worker restart không tự khôi phục quyền quét: báo cần chọn lại.

## Kiểm thử và giới hạn nghiệm thu

Chạy từ repo gốc:

```powershell
$env:PYTHONPATH = 'ScamShield_AI'
python -m unittest discover -s ScamShield_AI/tests -v
node ScamShield_AI/tests/worker_security.mjs
node ScamShield_AI/tests/browser_week2.mjs
python ScamShield_AI/week2_manifest.py
```

Browser test yêu cầu Node 24 và Chrome hỗ trợ CDP `Extensions.loadUnpacked`. Đổi `SCAMSHIELD_CHROME`/`SCAMSHIELD_PYTHON` nếu đường dẫn khác. Dùng profile test riêng, Chrome headless, API mock tại cổng 18762; sao chép extension và đổi **chỉ port** API trong worker bản test để tránh server của người dùng ở 8000. Không dùng profile Chrome cá nhân. Nếu sandbox Windows chặn khởi động Chrome thì cần cho phép tiến trình kiểm thử riêng. Script không cài dependency npm hoặc thay cấu hình Chrome cá nhân.

Kết quả thực, danh sách assertion và phiên bản trình duyệt ở `reports/week2/browser.json`; kiểm tra worker cô lập ở `worker_security.json`; hồi quy Python ở `python_tests.txt`. Ảnh giao diện ở `web.png`. Dự đoán mock tuần 1 và baseline tuần 3 vẫn được giữ nguyên. Không chấm hoặc mở nội dung holdout để chỉnh giao diện.

Kết quả lượt nghiệm thu: 12 kiểm thử Python, 10 assertion worker và 29 assertion trình duyệt đều đạt. Lượt 35 mục cùng hiển thị gửi đúng 35 request, đồng thời tối đa 1; hàng đợi giới hạn 20, có ghi nhận mục hoãn rồi được xử lý tiếp. Đây là kiểm tra tải chức năng, chưa phải báo cáo hiệu năng p50/p95. Các file thay đổi theo nhiệm vụ:

| Mã | Mã nguồn và đầu ra |
| --- | --- |
| W2-01 | `web/index.html`, `web/style.css`, `web/app.js`, renderer `extension/shared.js`, static/config routes trong `backend/main.py` |
| W2-02 | `extension/manifest.json`, popup, bộ chọn và panel trong `content.js`, fixture `/fixture` |
| W2-03 | Reader visible text, observer, hàng đợi/version trong `content.js`; ranh giới mạng `worker.js`; kiểm thử browser/worker |
| W2-04 | Điều khiển pause/resume/stop/reselect, bỏ phản hồi cũ, lỗi; `chay_he_thong.cmd`, báo cáo/hashes và hướng dẫn này |

Các ca trình duyệt bao gồm WEB-01, Unicode, che dữ liệu, hội thoại, bổ sung bối cảnh, bỏ phản hồi web cũ; EXT-01–07, PRIV-01 và E2E-01 trong phạm vi fixture. Nạp **worker MV3 thật và content script isolated world thật**, không shim chrome.runtime. Bộ chọn được gọi bằng Chrome API giống popup, sau đó chọn vùng bằng sự kiện chuột CDP; các nút trong shadow DOM được bấm tự động. Cần thử tay thao tác biểu tượng toolbar và kiểm tra từng mạng xã hội trước khi công bố hỗ trợ nền tảng đó.

Các lỗi 429, mất mạng và AbortError được **chủ động chèn tại fetch của worker/client thật** để kiểm tra đường xử lý lỗi; không gọi đó là một lần provider live lỗi hoặc ngắt mạng vật lý. Timeout API thật theo ngân sách async đã được kiểm ở tuần 1. Kết quả cuối còn phụ thuộc mock/live của backend, không có suy luận hành vi mới ở client.

Giới hạn: chưa thử Facebook/Zalo/Gmail, iframe, shadow DOM của trang, DOM ảo tái tạo nhiều node giống nhau, CSS che khuất phức tạp hoặc nội dung ngoài main document. Kiểm tra visibility không chứng minh phần tử không bị một lớp phủ khác che. Text dài qua nhiều vùng cuộn có thể chỉ gửi phần đang hiển thị; cần chọn đơn vị nhỏ hoặc dùng web để cung cấp cả hội thoại. Dedupe theo DOM/version không ngăn bản sao cùng nội dung ở hai DOM node khác nhau, nhằm giữ đúng đối tượng bình luận. Không kiểm tra OCR/URL/RAG. Chưa đo p50/p95 trải nghiệm; tuần 3 thực hiện phép đo riêng.

**Cổng tuần 2 chỉ xác nhận luồng local/mock trên fixture và các ca lỗi giả lập đã chạy. P0 live và phạm vi mạng xã hội thật còn mở.** Tiếp theo cấu hình provider và rà live; chỉ tích hợp RAG sau khi P0 và kho nguồn đã duyệt đạt cổng.

Nguồn kỹ thuật: [Chrome network requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests), [message passing](https://developer.chrome.com/docs/extensions/develop/concepts/messaging?hl=en), [permissions](https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions?authuser=41).
