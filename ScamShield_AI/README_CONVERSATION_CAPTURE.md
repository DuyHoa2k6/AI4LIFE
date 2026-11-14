# Thu thập hội thoại đang hiển thị — thử nghiệm 0.9.0

Chế độ này thu thập các tin đã nhìn thấy trong vùng người dùng chọn, xem trước và tải JSON/TXT. Nút **Phân tích · Xuất dữ liệu thử** chỉ chốt dữ liệu, chưa suy luận rủi ro. Không cần backend, API key hoặc mô hình. Quy trình phân tích rủi ro cũ không thay đổi.

**Đã kiểm chứng trên Chrome thật với trang chat giả lập của dự án. Chưa kiểm tra Messenger, Zalo Web hay website có tài khoản thực.** Không nên bật chế độ này trên một website bất kỳ rồi kỳ vọng có adapter tương ứng. Khung không đúng hợp đồng DOM sẽ bị từ chối, không chuyển sang đọc toàn trang.

## Cài và chạy thử

1. Mở `chrome://extensions`, bật **Developer mode**. Với bản đã cài, bấm **Reload**; nếu chưa cài, bấm **Load unpacked** và chọn thư mục `ScamShield_AI/extension` bên trong repo, nơi có `manifest.json`.
2. Tải lại tab web sau khi cập nhật extension để bỏ content script cũ. Bản popup mới chặn tab còn giữ build cũ.
3. Từ thư mục ứng dụng có `extension` và `fixtures`, chạy:

```powershell
python -m http.server 8877 --bind 127.0.0.1 --directory fixtures
```

4. Mở `http://127.0.0.1:8877/conversation_capture.html`.
5. Bấm icon extension → **Thu thập hội thoại đang hiển thị · Thử nghiệm**.
6. Bấm nền trắng trong khung chat viền xanh, rồi bấm **Bắt đầu**. Chọn vùng chưa thu thập dữ liệu. Có thể kéo bảng bằng thanh tiêu đề nếu bảng che khung.
7. Tự cuộn khung để tải/hiện những tin muốn giữ. Nút **Tải tin cũ phía trên** của fixture giả lập việc tải lịch sử; extension không tự bấm nút này hoặc tự cuộn.
8. Bấm **Xem trước**, rồi **Phân tích · Xuất dữ liệu thử**. Extension hoàn tất hàng đợi, chốt bản sao và tạm dừng thu thập. Bấm **Tải JSON** hoặc **Tải TXT**; file vào vị trí tải xuống do Chrome quản lý.
9. Muốn ghi nhận tiếp, bấm **Tiếp tục thu thập**, rồi chốt lại. **Tạm dừng** ngắt theo dõi. **Đóng** dừng thu thập và ẩn bảng; mở lại chế độ để xem phiên còn trong tab. **Xóa dữ liệu phiên** xóa bộ nhớ của phiên, không xóa file đã tải.

Không cần sửa request hoặc đọc console. Python chỉ phục vụ fixture HTTP; nội dung chat không được gửi cho HTTP server. Trang thật được hỗ trợ trong tương lai sẽ không cần server fixture này. Node chỉ dùng cho kiểm thử phát triển.

## Phạm vi và adapter

Các thành phần tách riêng:

| File | Trách nhiệm |
| --- | --- |
| `extension/conversation_adapter.js` | Nhận diện khung, scroll container, tin hiển thị, tác giả, quote, media, thời gian theo DOM contract |
| `extension/conversation_model.js` | Chuẩn hóa, định danh, chống trùng có điều kiện, giữ tin khi DOM bị gỡ, ghép đoạn và tạo snapshot |
| `extension/conversation_export.js` | Dựng TXT và tải JSON/TXT từ snapshot bằng Blob cục bộ |
| `extension/conversation_capture.js` | Bộ chọn vùng, MutationObserver, hàng đợi, scroll/debounce, điều khiển phiên và UI |
| `extension/popup.js` | Mở riêng chế độ thu thập; không inject bộ quét rủi ro cho chế độ này |

Adapter duy nhất hiện có là `scamshield-dom-fixture-v1`, với hợp đồng:

- Khung: `[data-ss-conversation][data-conversation-id]`. Wrapper được chọn phải chứa đúng một khung; không đọc tiêu đề hoặc danh sách chat bên ngoài.
- Tin: `[data-message-id]` hoặc `[data-chat-message]`; nội dung trong `[data-chat-text]`. Thứ tự DOM của adapter là thứ tự hội thoại trong cửa sổ quan sát. Chưa hỗ trợ DOM đảo chiều hoặc DOM riêng của nền tảng khác.
- Tác giả: `data-sender-id`, `data-sender-name`, `data-sender-role="self"`. Chỉ kế thừa trong nhóm có `[data-sender-group]` tường minh; không kế thừa theo người đứng trước hoặc vị trí trái/phải.
- Tên giống nhau không gộp tài khoản. Chỉ có tên, thiếu ID/nhóm/vai xác nhận được thì giữ `sender_id=null`, tên hiển thị riêng và unresolved reference theo tin.
- `data-kind="system"`, `data-edited="true"`, `data-deleted="true"` là metadata tường minh. Có thể bổ sung nhãn tác giả/thời gian sau khi tải.
- Reply: `data-reply-to` và `[data-chat-quote]`. `[data-chat-forward]`/`[data-link-preview]` được giữ làm nội dung tham chiếu riêng, không trộn vào lời đang viết. Đích reply chưa quan sát được không tự nối theo câu giống nhau.
- Thời gian: `<time>` hoặc `data-time`; chỉ chuẩn hóa `datetime` đầy đủ ngày/giờ/múi giờ. Không đoán năm hoặc múi giờ từ nhãn “09:10”.

Chỉ lấy tin giao với viewport và vùng clipping của các ancestor, loại nội dung hidden, ô soạn, trường nhập, nút và DOM của extension. Tìm scroll container thật từ khung lên ancestor; chỉ dùng viewport tài liệu khi không có khung cuộn. Không tự tải media, OCR, mở URL hoặc đọc tệp. Link chỉ giữ nhãn và href HTTP/HTTPS; ảnh chỉ giữ loại/nhãn với `content_not_extracted`.

Manifest giữ `activeTab`, `scripting` và origin local đã có cho chế độ quét cũ; không thêm quyền storage/downloads hoặc đọc toàn bộ website. Chế độ thu thập không gửi runtime message chứa hội thoại và không gọi worker/API. Khi chuyển giữa hai chế độ, chế độ cũ được dừng trước.

## Snapshot và giới hạn đã biết

Schema `scamshield-conversation-1.0` có session, capture_scope, conversation_reference, participants, messages, segments, coverage và diagnostics_summary. ID nội bộ khác ID đọc từ nền tảng. Metadata tự nhận/hiển thị không xác minh danh tính ngoài đời.

Message có nội dung gốc/xuống dòng/emoji, tác giả hoặc unresolved reference, quote, reply, attachment, links, thời gian hiển thị/chuẩn hóa, thời điểm ghi nhận đầu/cuối, trạng thái sửa/thu hồi và cảnh báo trích xuất. Tin thu hồi không xuất văn bản/quote/attachment/link cũ mặc định; đây không phải công cụ khôi phục tin.

Ưu tiên message ID ổn định. Khi không có ID, chỉ đối chiếu bản tải lại bằng người gửi + thời gian + nội dung + quan hệ lân cận với một tin có ID ổn định. Không gộp chỉ vì cùng chữ “OK”. Khi thiếu căn cứ, giữ bản có thể trùng và ghi warning; số tin có thể cao hơn thực tế trong trường hợp này. Cùng node không thay đổi có thể được nhận diện, nhưng không thể phân biệt chắc một tin mới hoàn toàn giống tin cũ khi nền tảng tái sử dụng node mà không có metadata.

Ghép thứ tự bằng các cặp liền kề đã quan sát trong DOM. Cuộn lên có thể nối tin cũ vào trước tin mới nhờ phần giao nhau. Hai cửa sổ không có căn cứ nối giữ thành hai segment; không dùng `first_seen_at` làm thứ tự lịch sử. Đồ thị có vòng hoặc rẽ nhánh được đánh dấu thứ tự chưa xác định. `complete_history` luôn false trong adapter thử nghiệm; không biết đã tới đầu lịch sử hay có khoảng trống.

Dừng cuộn sau 700 ms chỉ cập nhật trạng thái, không tự chốt. Nút chốt flush mutation và đọc phần đang hiển thị để không bỏ đuôi debounce. Nếu `aria-busy`/`data-chat-loading` còn bật, chờ tối đa khoảng 1,2 giây rồi báo thử lại. Khi đã chốt, thay đổi DOM không làm thay đổi file snapshot.

Đổi conversation ID, URL, khung bị gỡ: dừng thu thập, giữ phiên cũ để xuất; chọn khung mới tạo phiên mới. Không phát hiện chắc việc đổi chat nếu nền tảng không thay ID, URL hoặc root — đó là phần phải kiểm thử khi thêm adapter thật. Đổi vùng có xác nhận trước khi bỏ dữ liệu cũ. Điều hướng/tải lại trang làm mất bộ nhớ phiên; tải file trước nếu cần giữ.

Giới hạn: 1000 tin, khoảng 2 MiB dữ liệu session/participants/messages đã tuần tự hóa, 4000 quan hệ thứ tự, hàng đợi tối đa 1000 node. Chạm giới hạn thì tạm dừng và thông báo. Con số byte là ước tính dữ liệu, **không phải giới hạn RAM của Chrome**; DOM trang, string tạm, graph, bản sao snapshot/Blob và preview cũng sử dụng bộ nhớ.

## Kiểm thử và mẫu xuất

[Báo cáo thực tế](reports/conversation_capture_20261114/README.md) có kết quả A–O, số đo và giới hạn. [JSON mẫu](reports/conversation_capture_20261114/conversation_sample.json) và [TXT mẫu](reports/conversation_capture_20261114/conversation_sample.txt) được tải thật từ Chrome trên fixture tổng hợp.

```powershell
node tests/conversation_model.mjs
node tests/conversation_popup.mjs
node tests/browser_conversation.mjs
```

Browser test cần Chrome cài ở đường dẫn Windows trong script và Node có WebSocket. Nó tự mở HTTP server loopback, Chrome headless, load unpacked và thao tác UI qua CDP; không chạy backend. Profile chứa file xuất được giữ tại `.browser-profile-conversation-*` để kiểm tra. Không sử dụng cookie hoặc profile cá nhân. Chưa có kiểm tra đăng nhập website thực tế, thiết bị di động, iframe, Shadow DOM của ứng dụng chat hoặc chat trong canvas.
