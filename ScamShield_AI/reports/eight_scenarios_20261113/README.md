# Chạy tám tình huống người dùng — 13/11/2026

Đã chạy nguyên văn tám đoạn qua **POST /api/analyze**, bằng FastAPI ASGI TestClient, backend thật và cấu hình hiện hành; không override provider, không mock kết quả, không sửa quy tắc. Chỉ gửi `{"text": "..."}`, không gửi tiêu đề, điểm cần nhận ra hay nhãn kỳ vọng. Lưu toàn bộ dự đoán trước khi rà nghĩa.

## Kết quả thực tế

Mode `local_rules`, cấu hình reasoner `legacy`, context/RAG/URL enabled; phiên bản quyết định thực trả `local-situation-1.0-support`. Không gọi Gemini. Không có URL trong tám đầu vào; trace URL ghi 0 ms. `rule_conflicts=0` ở cả tám ca: đây không phải phép chạy có xung đột Gemini/regex.

| Ca | Tình huống | HTTP | Mức thực trả | Thời gian qua API (ms) | Rà từ dữ liệu trả về |
| --- | --- | --- | --- | ---: | --- |
| 01 | Tài khoản nhắn tin mới, chuyển bên thứ ba, ngăn gọi số cũ | 200 | need_context | 86.87 | Đã trích chuyển tiền và avoid_verification nhưng chưa ghép thành cảnh báo; hỏi mục đích thanh toán |
| 02 | Nộp thêm mới được trả tiền, bỏ dở mất khoản cũ | 200 | need_context | 41.46 | Có nộp tiền và khoản rút, nhưng không có liên kết tình huống cho điều kiện trả thêm → được nhận lại |
| 03 | Hoàn phí nhưng xin mã đăng nhập | 200 | need_context | 25.22 | Nhận provide_code nhưng chưa xác định công dụng đăng nhập; còn trích “chuyển” trong “vận chuyển” thành transfer_funds |
| 04 | Nhận/chuyển tiền hộ, khai sai với ngân hàng | 200 | need_context | 37.58 | Có receive_funds, third_party_payee và misstate_origin nhưng chưa nối thành cơ chế lợi dụng tài khoản; “giữ hoa hồng” thành hold_asset |
| 05 | Đứng tên vay, giữ bí mật, gây sức ép tình cảm | 200 | need_context | 29.31 | Findings chỉ còn giữ bí mật; bỏ sót hành động đứng tên vay và chuyển nghĩa vụ tài chính |
| 06 | Điều khiển từ xa trong lúc mở ngân hàng | 200 | suspicious | 40.68 | Có cấp quyền và mở dữ liệu tài chính nhưng không ghép chúng; một finding remote_control bị gán speech_role=denial dù câu trích là yêu cầu bật/cấp quyền |
| 07 | Chuyển tiền để không phát tán ghi hình | 200 | need_context | 25.44 | Chỉ giữ yêu cầu chuyển tiền, không biểu diễn được quan hệ đe dọa phát tán → buộc trả tiền |
| 08 | Đi theo xe, giữ hộ chiếu, trả khoản chưa xác định mới được về | 200 | suspicious | 36.66 | Có giữ giấy tờ, bí mật và travel, nhưng không ghép với điều kiện hạn chế trở về |

Tổng: **8/8 HTTP 200; 6 need_context, 2 suspicious, 0 high, 0 clear**. Thời gian trung bình **40.40 ms**, khoảng **25.22–86.87 ms**. Mỗi ca chạy một lần, ca đầu có thể chịu khởi tạo; đây không phải đo tải, cold/warm có kiểm soát, độ trễ browser hay extension. Không chuyển thành tỷ lệ chính xác từ tám ca chỉ thuộc nhóm đáng ngờ.

## Đối chiếu ngữ nghĩa thủ công sau khi chạy

Các ca 01, 02, 03, 04, 06, 07, 08 có tổ hợp hành động và điều kiện đủ rõ để rà theo hướng **high** về nguy cơ, không phải khẳng định người gửi chắc chắn phạm pháp. Ca 05 tối thiểu cần **suspicious**, đồng thời cần đặc tả rõ tiêu chí lên high cho đứng tên vay kèm bí mật và sức ép tình cảm. Đây là nhận xét rà thủ công, không phải nhãn chuẩn đã được hội đồng duyệt.

Ca 06 và 08 đã phát cảnh báo nhưng mới thể hiện một phần cơ chế. Sáu ca need_context đều trả tóm tắt chung “Chưa đủ dữ kiện trong phạm vi bộ phân tích để kết luận.” Một số câu hỏi lệch trọng tâm: hỏi mục đích thanh toán ở ca 03 thay vì bảo vệ mã đăng nhập, hoặc ở ca 07 thay vì nhận diện đe dọa.

## Nhận định kỹ thuật

- Cả tám response có `grounded_relation_count=0`. `situation_links=0` ở ca 02–08, ca 01 có 2 liên kết nhưng vẫn không thành cảnh báo kết hợp. Trace này chỉ chứng minh kết quả biểu diễn trong lần chạy; không tự xác định chính xác dòng mã gây mọi lỗi.
- Các findings cho thấy giới hạn ở bóc tách cụm nghĩa, phân vai lời nói và nối hành động–điều kiện–hậu quả. Không có căn cứ quy lỗi cho Gemini trong lần chạy này vì `live_status=not_used`.
- Hướng sửa tiếp: chống nhận nhầm động từ nằm trong cụm danh từ; xác định công dụng mã từ câu liên quan; tránh phủ định câu sau làm sai vai trò câu trước; biểu diễn điều kiện nhận tiền, đe dọa, nghĩa vụ vay và quyền tự do rời đi; quyết định theo tổ hợp có bằng chứng. Chưa áp dụng sửa trong yêu cầu kiểm tra này.
- Tám ca đã được xem khi chẩn đoán: nếu dùng để sửa sau này, phải coi là hồi quy, không tính là đánh giá độc lập.

## Tệp và lệnh chạy lại

- [inputs.json](inputs.json): nguyên văn đầu vào, không có expected.
- [predictions.json](predictions.json): HTTP, thời gian, hash dữ liệu, cấu hình công khai và response đầy đủ từng ca.
- Script: `tests/run_user_eight.py`.

Từ thư mục repo ngoài:

```powershell
$env:PYTHONIOENCODING='utf-8'
python ScamShield_AI/tests/run_user_eight.py
```

Script chạy route API trong tiến trình riêng, không cần server 8000 đang mở và không sửa cấu hình backend. Thời gian lần chạy lại có thể khác.
