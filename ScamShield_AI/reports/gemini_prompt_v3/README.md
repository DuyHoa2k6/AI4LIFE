# Prompt Gemini v3 — 08/11/2026

Đã triển khai prompt theo hợp đồng backend và kiểm thử bằng Gemini thật. 18/18 lần gọi
trả kết quả API 200 trong phiên này; điều đó chưa bảo đảm chất lượng hoặc độ trễ thực tế.

## Thay đổi

- `backend/hybrid_prompt.txt`: chia nhiệm vụ, đầu vào, trích dẫn, action/vai người nói,
  review, hình dạng tám answers và kiểm tra trước khi xuất. Chỉ cho phép enum/field có trong
  schema; ID phải tồn tại; lời cảnh báo không dùng benign; request đã đủ căn cứ không tự động uncertain.
- `backend/extraction_prompt.txt`: thống nhất hợp đồng trích xuất ở chế độ live riêng.
  Phiên gọi thật này dùng hybrid; chất lượng chế độ live riêng chưa được đo lại.
- Quote nguyên văn duy nhất luôn dùng `start=null, end=null`. Backend tự tìm offset
  code point; quote lặp không phân biệt được, quote sửa chữ/ghép đoạn vẫn bị loại.
- `backend/providers.py`: thêm hint nội bộ cho nguyên văn context với vị trí backend
  tính sẵn. Model có thể sao chép vào context_evidence khi phù hợp. Không thêm trường API công khai.
- `backend/hybrid.py`: tính số finding bị loại trước khi thêm rule-conflict, sửa bộ đếm âm.
  Không thay thứ tự quyết định cảnh báo hoặc bỏ kiểm chứng bằng chứng.
- Thêm bốn kiểm thử cho giao thức null quote, Unicode/context hint, lời cảnh báo và
  quote lặp/bộ đếm. Tổng 53 unit test và 10 worker security check đều đạt.

Bản trước của hai prompt và hai file nguồn nằm ở `before/`; không lưu key/cấu hình riêng.
Không đổi key/model/timeout. Không sửa regex, prompt hoặc thuật toán quyết định giữa hai
lượt kiểm thử v3. Lock xác nhận hash backend giống nhau.

## Hồi quy 8 ca từng lỗi

| Ca | Trước chỉnh | Sau chỉnh |
| --- | --- | --- |
| MX-S01 — phí nhận thưởng | need_context | need_context, chưa đạt high |
| MX-N01 — bài cảnh báo | need_context | clear |
| MX-N04 — trả nợ có bối cảnh | need_context | clear |
| MX-S06 — yêu cầu mật khẩu | EVIDENCE_INVALID | high |
| MX-N06 — tự đổi mật khẩu | need_context | need_context, chưa đạt clear |
| MX-S09 — APK để hoàn tiền | need_context | high |
| MX-N10 — thuê nhà có bối cảnh | need_context | clear |
| MX-N11 — ví dụ chỉ thị nhúng | EVIDENCE_INVALID | clear |

6/8 đúng trạng thái mong đợi, 8/8 trả kết quả API. Trước chỉnh cả tám ca này chưa đạt
trạng thái mong đợi, trong đó hai ca lỗi API. Đây là tập hồi quy chọn từ lỗi đã biết,
không phải so sánh độ chính xác độc lập trên toàn bộ 28 ca. Chưa chạy lại 20 ca còn lại.

Hai giới hạn đã rà trực tiếp:

- MX-S01: model vẫn ghép hai đoạn với `[...]` trong một quote support. Backend loại
  support không nguyên văn nên trả need_context. Không nới kiểm chứng để cho quote này qua.
- MX-N06: model phân biệt đúng phủ định yêu cầu mật khẩu nhưng coi hướng dẫn tự đổi
  mật khẩu là request `other`; còn xung đột với regex. Backend trả need_context.
  Chỉnh prompt không tự giải quyết mọi giới hạn hợp đồng/luồng quyết định.

## Mười ca mới sau khi khóa v3

| Nhóm | Số ca | Kết quả |
| --- | ---: | --- |
| Lừa đảo | 4 | 4 high |
| Bình thường | 4 | 4 clear |
| Thiếu bối cảnh | 2 | 2 need_context, đều có câu hỏi |

10/10 khớp trạng thái phán đoán chức năng. Các ca mới gồm giả điện lực cài APK,
phí trả ví, lấy mã đăng nhập, chỉ thị nhúng để lấy phí hoa hồng, lịch hẹn bình thường,
thanh toán thợ sửa có context, bài tập huấn trích lời dụ, tự nhập mã và hai ca thiếu bối cảnh.
Với hội thoại, speaker của yêu cầu mã được giữ là hỗ trợ, không gán cho thành viên.

Đây là mẫu nhỏ tổng hợp do người triển khai viết, không phải dữ liệu thực hoặc tập holdout
được người độc lập quản lý. Input và expected tách file; dự đoán lưu trước khi chấm;
không gửi nhãn cho Gemini và không chỉnh prompt theo kết quả mới trong phiên này.
Đúng trạng thái chưa chứng minh trích đủ mọi hành động: ví dụ PV-S1 chưa tách riêng
finding cấp quyền dù đã có finding cài app và liên kết lợi ích. Chưa đo recall từng hành động.

## Tính hợp lệ và hiệu năng

- Tổng 18 ca: 0 lỗi API. Tất cả 28 quote raw có start/end=null. Một quote ghép đoạn
  bị loại; phản hồi cuối gồm cả quan sát rule-conflict có 29/29 quote khớp và không sai
  tham chiếu speaker theo phép kiểm tra máy móc. Không suy ra vai ngữ nghĩa đều chính xác.
- p50 toàn bộ 18 lượt: **3,300 giây**; p95 nearest-rank: **17,242 giây**.
- Riêng 10 ca mới: p50 **3,173 giây**, p95 **5,593 giây**.
- Ca MX-S09 mất khoảng 17,24 giây nhưng vẫn trong timeout 20 giây. Không có cơ sở tuyên bố
  prompt mới nhanh hơn; p95 vẫn chưa đạt mục tiêu dưới 2 giây. Không tăng timeout.
- Đo ASGI API + HTTP provider thật, tuần tự một request, nghỉ 3 giây, không retry.
  Không đo p95 web/extension, tải đồng thời, cold provider hoặc mạng tách khỏi xử lý model.

Chưa nghiệm thu toàn hệ thống. Cần bộ độc lập lớn hơn và khắc phục hai lớp lỗi còn lại
trước khi dùng số liệu như cam kết sản phẩm. Không coi 53 unit test hoặc 10/10 mẫu mới
là bằng chứng hệ thống có độ chính xác 100% trên nội dung ngoài đời.

## File và lệnh

- `summary.json`: tổng hợp v3; `regression/` và `new_cases/` chứa lock, từng dự đoán,
  review model, câu hỏi, bằng chứng, thời gian và expected sau chấm.
- `../../fixtures/prompt_v3_new/`: mười input mới và expected riêng.
- `before/`: nguồn trước sửa; số liệu trước sửa ở `../mixed_check/`.

Chạy từ thư mục ứng dụng `ScamShield_AI` bên trong repo, dùng đường dẫn output mới:

```powershell
python -m unittest discover -s tests -q
node tests/worker_security.mjs
python mixed_check.py --mode hybrid --output reports/v3_new_run/regression --pause 3 --case-ids MX-S01 MX-N01 MX-N04 MX-S06 MX-N06 MX-S09 MX-N10 MX-N11
python mixed_check.py --mode hybrid --output reports/v3_new_run/new_cases --fixtures-dir fixtures/prompt_v3_new --pause 3
```

Hai lệnh cuối gọi API thực, tiêu thụ quota của dự án. Cấu hình mẫu và cách khởi động lại
backend tại `../../README_GEMINI.md`. Các fixture đã kiểm tra sẽ là regression công khai,
không dùng làm số liệu độc lập nếu tiếp tục chỉnh prompt dựa vào chúng.
