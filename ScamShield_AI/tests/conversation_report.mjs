import fs from 'node:fs';import vm from 'node:vm';
const out=new URL('../reports/conversation_capture_20261114/',import.meta.url),r=JSON.parse(fs.readFileSync(new URL('report.json',out),'utf8'));
if(!r.completed||r.checks.some(c=>!c.passed))throw Error('Browser run is incomplete');
const panel=JSON.parse(fs.readFileSync(new URL('../reports/extension_panel_20261113/report.json',import.meta.url),'utf8'));
if(!panel.completed||panel.checks.some(c=>!c.passed))throw Error('Panel regression run is incomplete');
fs.writeFileSync(new URL('panel_regression.json',out),JSON.stringify(panel,null,2));
const ctx=vm.createContext({});vm.runInContext(fs.readFileSync(new URL('../extension/conversation_export.js',import.meta.url),'utf8'),ctx);
const s=JSON.parse(fs.readFileSync(new URL('conversation_sample.json',out),'utf8')),txt=fs.readFileSync(new URL('conversation_sample.txt',out),'utf8');
if(ctx.SSConversationExport.toText(s)!==txt)throw Error('Downloaded TXT differs from downloaded JSON snapshot');
const n=r.timings.length,fmt=x=>Number(x).toFixed(2);
const body=`# Thu thập hội thoại — báo cáo 14/11/2026

Đã chạy **${r.checks.length}/${r.checks.length} kiểm tra qua trên ${r.browser}**, extension unpacked thật, HTTP fixture tổng hợp và tải file thật. Không chạy backend hoặc mô hình trong bộ kiểm thử thu thập. Phạm vi hỗ trợ đã xác minh: fixture của dự án; chưa kiểm tra Messenger, Zalo Web hoặc website đăng nhập thực tế.

## Kết quả

| Ca | Kiểm tra đã qua |
| --- | --- |
| A | Hai người xen kẽ: giữ tin và tác giả riêng |
| B | Chỉ kế thừa tác giả trong nhóm DOM được đánh dấu; tin ngoài nhóm chưa rõ người gửi |
| C | Nhóm ba người giữ ba participant |
| D | Cùng tên hiển thị, khác ID: giữ hai participant |
| E | Các lần gửi “OK” thật không bị gộp theo chữ |
| F | Tải lại ID cũ không nhân bản; cuộn lên nối trước tin mới bằng đoạn giao nhau |
| G | Một node tái sử dụng cho ID khác giữ cả hai tin |
| H | Lời trích tách khỏi văn bản người trả lời, reply_to đúng ID |
| I | Giữ xuống dòng/emoji/nhãn ảnh/href; không đọc nội dung media; chuyển tiếp giữ riêng |
| J | Chỉnh sửa cập nhật cùng ID; thu hồi không xuất văn bản cũ |
| K | Conversation ID đổi làm dừng trước khi lấy tin phiên khác |
| L | Thiếu người gửi/thời gian được ghi rõ; unresolved theo từng tin |
| M | Chốt ngay sau thêm tin/cuộn không bỏ phần đuôi chờ debounce |
| N | Vượt giới hạn byte làm tạm dừng, coverage ghi giới hạn; không tạo participant giả cho tin bị từ chối |
| O | Không đọc bảng extension, nội dung hidden hoặc trường soạn tin |

Kiểm tra bổ sung: popup mở đúng chế độ riêng; chưa bắt đầu không có dữ liệu; định danh dự phòng cần metadata và anchor lân cận; tạm dừng/tiếp tục; thông báo sau 700ms dừng cuộn; timeout tải hữu hạn; ancestor sở hữu scrollbar; snapshot không đổi theo DOM sau chốt; vùng không hỗ trợ bị từ chối; khung 390×650 không tràn; xóa phiên; dọn observer/interval/listener.

Kiểm tra thuần Node: **16 model/export + 7 popup/cách ly**. Hồi quy cũ: **4 popup version + 14 worker security + 7 OCR worker**, và **${panel.checks.length} kiểm tra Chrome bảng quét cũ** qua. Backend/rulebook không bị sửa; không chạy lại Python hoặc benchmark mô hình vì phạm vi này là thu thập phía extension.

## Mạng và dữ liệu

CDP ghi nhận ${r.network.observed_requests} request sau bật quan sát, **${r.network.post_requests} POST**, **${r.network.external_http_requests} HTTP ngoài fixture**. Worker fetch probe và page fetch/XHR probe đều 0. Kiểm tra tĩnh bốn module không có fetch/XHR/WebSocket/sendBeacon/runtime.sendMessage hoặc lưu storage. Đây là quan sát trong fixture, không phải chứng nhận hành vi của website bên thứ ba.

Snapshot mẫu có ${s.messages.length} tin, ${s.participants.length} participant, ${s.segments.length} segment. [conversation_sample.json](conversation_sample.json) và [conversation_sample.txt](conversation_sample.txt) được tải qua nút trên UI; đối chiếu TXT đúng bằng renderer của snapshot JSON. [snapshot.png](snapshot.png), [narrow.png](narrow.png). Nội dung hoàn toàn tổng hợp.

## Thời gian và bộ nhớ quan sát

- ${n} lần chốt thành công, tuần tự: p50 **${fmt(r.p50_finalize_ms)} ms**, p95 nearest-rank **${fmt(r.p95_finalize_ms)} ms**. Đo từ thao tác nút qua CDP đến state frozen; gồm overhead tự động hóa, không phải độ trễ phân tích rủi ro hoặc cam kết trên website thực tế.
- Ca loading được thử riêng: chờ tối đa khoảng 1,2 giây rồi báo thử lại, không tính là lần chốt thành công trong p50/p95.
- Phiên cuộn mẫu 18 tin: ${r.memory.batches} batch; tổng xử lý Store ${fmt(r.memory.total_processing_ms)} ms, batch lớn nhất ${fmt(r.memory.max_batch_ms)} ms. Chỉ đo chuẩn hóa/lưu/kiểm ngân sách của Store, không bao gồm mọi công đoạn đọc DOM, preview hoặc Blob.
- Dữ liệu session/participants/messages ước tính ${r.memory.estimated_session_bytes} byte. Không bao gồm toàn bộ JS heap, DOM, graph, snapshot và Blob.
- CDP Runtime heap trước inject: ${r.heap_before_injection.usedSize} byte JS; sau toàn bộ kiểm thử: ${r.heap_after_tests.usedSize} byte JS và ${r.heap_after_tests.embedderHeapUsedSize} byte embedder heap. Bao gồm trang/UI và ca stress tạo văn bản 2,2 triệu ký tự, không kiểm soát GC, không được quy toàn bộ mức tăng cho bộ thu thập hoặc gọi là RAM riêng của extension.
- Sau chốt: ${r.cleanup.observers} observer thu thập, ${r.cleanup.intervals} interval giám sát, ${r.cleanup.capture_listeners} listener scroll/pagehide đang hoạt động. Listener UI để mở/đóng/kéo bảng vẫn tồn tại trong tab.

## Giới hạn

Không biết đầy đủ lịch sử; không tự đọc media; không xác minh danh tính. Thiếu ID/anchor có thể giữ bản nghi trùng thay vì xóa nhầm. Không có đoạn giao nhau thì thứ tự giữa segment chưa rõ. Adapter chỉ chấp nhận DOM contract của fixture. Chuyển chat không đổi ID/URL/root chưa phát hiện chắc được. Chưa đo thiết bị khác, iframe, Shadow DOM của ứng dụng chat, tải thực tế hoặc hành vi Chrome khi hệ điều hành thiếu RAM.

Cách cài/chạy, hợp đồng DOM và các file mã nguồn: [README_CONVERSATION_CAPTURE.md](../../README_CONVERSATION_CAPTURE.md). Dữ liệu kiểm tra chi tiết: [report.json](report.json); hồi quy cũ: [panel_regression.json](panel_regression.json).
`;
fs.writeFileSync(new URL('README.md',out),body);console.log('Report written; actual downloaded JSON/TXT pair matches.');
