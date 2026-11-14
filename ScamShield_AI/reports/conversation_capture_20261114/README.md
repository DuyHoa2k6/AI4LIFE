# Thu thập hội thoại — báo cáo 14/11/2026

Đã chạy **38/38 kiểm tra qua trên Chrome/157.0.8103.51**, extension unpacked thật, HTTP fixture tổng hợp và tải file thật. Không chạy backend hoặc mô hình trong bộ kiểm thử thu thập. Phạm vi hỗ trợ đã xác minh: fixture của dự án; chưa kiểm tra Messenger, Zalo Web hoặc website đăng nhập thực tế.

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

Kiểm tra thuần Node: **16 model/export + 7 popup/cách ly**. Hồi quy cũ: **4 popup version + 14 worker security + 7 OCR worker**, và **39 kiểm tra Chrome bảng quét cũ** qua. Backend/rulebook không bị sửa; không chạy lại Python hoặc benchmark mô hình vì phạm vi này là thu thập phía extension.

## Mạng và dữ liệu

CDP ghi nhận 2 request sau bật quan sát, **0 POST**, **0 HTTP ngoài fixture**. Worker fetch probe và page fetch/XHR probe đều 0. Kiểm tra tĩnh bốn module không có fetch/XHR/WebSocket/sendBeacon/runtime.sendMessage hoặc lưu storage. Đây là quan sát trong fixture, không phải chứng nhận hành vi của website bên thứ ba.

Snapshot mẫu có 18 tin, 1 participant, 1 segment. [conversation_sample.json](conversation_sample.json) và [conversation_sample.txt](conversation_sample.txt) được tải qua nút trên UI; đối chiếu TXT đúng bằng renderer của snapshot JSON. [snapshot.png](snapshot.png), [narrow.png](narrow.png). Nội dung hoàn toàn tổng hợp.

## Thời gian và bộ nhớ quan sát

- 17 lần chốt thành công, tuần tự: p50 **21.52 ms**, p95 nearest-rank **33.50 ms**. Đo từ thao tác nút qua CDP đến state frozen; gồm overhead tự động hóa, không phải độ trễ phân tích rủi ro hoặc cam kết trên website thực tế.
- Ca loading được thử riêng: chờ tối đa khoảng 1,2 giây rồi báo thử lại, không tính là lần chốt thành công trong p50/p95.
- Phiên cuộn mẫu 18 tin: 8 batch; tổng xử lý Store 6.50 ms, batch lớn nhất 1.40 ms. Chỉ đo chuẩn hóa/lưu/kiểm ngân sách của Store, không bao gồm mọi công đoạn đọc DOM, preview hoặc Blob.
- Dữ liệu session/participants/messages ước tính 10764 byte. Không bao gồm toàn bộ JS heap, DOM, graph, snapshot và Blob.
- CDP Runtime heap trước inject: 446012 byte JS; sau toàn bộ kiểm thử: 2348148 byte JS và 40075632 byte embedder heap. Bao gồm trang/UI và ca stress tạo văn bản 2,2 triệu ký tự, không kiểm soát GC, không được quy toàn bộ mức tăng cho bộ thu thập hoặc gọi là RAM riêng của extension.
- Sau chốt: 0 observer thu thập, 0 interval giám sát, 0 listener scroll/pagehide đang hoạt động. Listener UI để mở/đóng/kéo bảng vẫn tồn tại trong tab.

## Giới hạn

Không biết đầy đủ lịch sử; không tự đọc media; không xác minh danh tính. Thiếu ID/anchor có thể giữ bản nghi trùng thay vì xóa nhầm. Không có đoạn giao nhau thì thứ tự giữa segment chưa rõ. Adapter chỉ chấp nhận DOM contract của fixture. Chuyển chat không đổi ID/URL/root chưa phát hiện chắc được. Chưa đo thiết bị khác, iframe, Shadow DOM của ứng dụng chat, tải thực tế hoặc hành vi Chrome khi hệ điều hành thiếu RAM.

Cách cài/chạy, hợp đồng DOM và các file mã nguồn: [README_CONVERSATION_CAPTURE.md](../../README_CONVERSATION_CAPTURE.md). Dữ liệu kiểm tra chi tiết: [report.json](report.json); hồi quy cũ: [panel_regression.json](panel_regression.json).
