# Sửa nền tảng chất lượng và cổng mục tiêu 98%

Đã giữ nguyên sơ đồ hai lượt Gemini/hai nhánh song song. Mục tiêu trên 98% **chưa đạt**.
Đây là phiên sửa giao thức/quyết định và thử hồi quy công khai, không phải đánh giá độc lập.

## Đã thay đổi

- Provider gửi structural json_schema cho Gemini; inline tham chiếu, required rõ các
  trường nullable. Schema đầy đủ và biến thể có bounds mảng đã bị endpoint hiện tại
  trả 400. Không tự fallback để che lỗi; backend vẫn áp đầy đủ Pydantic và kiểm chứng.
- Prompt cũ nói chỉ ba khóa gốc trong khi schema cần thêm trường. Prompt mới ghi đúng
  sáu khóa của FinalReviewV2. Không khẳng định mâu thuẫn này là nguyên nhân duy nhất
  của các lỗi lịch sử vì trước đó chưa ghi đường dẫn validation.
- Chỉ question_topics hợp lệ được deduplicate/giới hạn hai. Không sửa facts, quote hoặc
  risk_links để làm đầu ra vượt kiểm tra. Enum lạ vẫn lỗi.
- uncertainty_reasons tách identity/purpose khỏi action/relation. Có thể suspicious
  và hỏi thêm; bất định quan hệ thực vẫn chặn high, kể cả bất định nằm ở support.
- Claim/cảnh báo/phủ định không cần context exemption. Không bỏ kiểm chứng benign của
  request thực hoặc ID chưa hợp lệ. Giữ nguyên bảo vệ thông tin xác thực.
- Error diagnostic chỉ chứa stage/kind/attempts/output_format/field path/type. Không
  lưu input, error message/ctx hoặc key. Đường dẫn trường ngoài schema được che.
- Hai lượt tái sử dụng HTTP session riêng của request rồi đóng. Cấu hình private bật
  một retry cho 503/mất mạng trong deadline sẵn có, không retry quota/auth/schema/timeout.
  Key/model không đổi, không tăng giới hạn thời gian.
- `quality_gate.py` chấm offline, tính lỗi/chưa chạy là không đạt, high lỗi là FN;
  chống duplicate ID, yêu cầu mẫu/nhóm và khai báo rà độc lập, xét cận dưới Wilson 95%.
  Đây là cổng kỹ thuật, chưa thay rà ngữ nghĩa đầy đủ của tám answers.

## Kiểm chứng

87 unit test và 10 worker security check đạt. Test mới gồm schema gửi thật qua transport
giả lập, lọc diagnostic không lộ secret, không fallback khi HTTP 400, một retry 503 và
không retry 429, đóng session, không nâng mức khi quan hệ chưa rõ, cảnh báo kèm câu hỏi,
không coi vài mẫu đúng 100% là đạt 98%. Không cộng test chạy lặp thành độ chính xác AI.
Browser không chạy lại trong phiên này; kết quả 32 fixture check của two_pass trước đó là lịch sử.

## Gemini thật: không chọn lần đẹp nhất

Các thư mục giữ riêng từng lần, cùng bốn ca hồi quy khó; không cộng chúng thành mẫu độc lập:

| Lần | Diễn biến |
| --- | --- |
| regression | Full schema bị 400; 3 ca thử trước khi circuit breaker dừng, 1 chưa gửi |
| structured_portable | 2/4 API thành công; Q1 suspicious đúng; S4 503, S5 quá nhiều question_topics, N3 need_context |
| final_regression | Biến thể schema có bounds mảng bị 400, dừng sau 1 ca |
| checked | Sau bỏ bounds wire/cap questions: Q1 suspicious; S5 need_context; S4/N3 503 |
| retry_checked | Bản cuối có retry một lần: 3/4 API thành công, 1/4 đúng trạng thái kỳ vọng |

Bản cuối `retry_checked`:

| Ca | Kỳ vọng | Kết quả | Phân tích |
| --- | --- | --- | --- |
| TP-Q1 quyền điều khiển | suspicious | 503 | Lượt review vẫn 503 sau hai attempt; không có cảnh báo bàn giao |
| TP-S4 phí hoàn cọc | high | need_context | Model vẫn đánh dấu support là relation chưa rõ, backend giữ thận trọng |
| TP-S5 tự xưng người quen | high | need_context | Model vẫn đánh dấu yêu cầu là relation chưa rõ |
| TP-N3 lịch hẹn | clear | clear | Các claim bị gán benign thừa không còn làm yêu cầu thêm context |

Không gọi 1/4 trên bốn ca chọn từ lỗi đã biết là độ chính xác chung. Những lần Q1 trả
suspicious trước đó cho thấy phân biệt bất định hoạt động được, nhưng lỗi dịch vụ khiến
không thể cam kết độ ổn định. Retry một lần không giải quyết dịch vụ 503 kéo dài.

Điểm chưa giải quyết là phán đoán ngữ nghĩa của model, nhãn cần rà độc lập và độ ổn định
provider. Không ép bỏ relation uncertainty hoặc bỏ ca lỗi để đạt số đẹp. Chưa rõ HTTP 503
do hạ tầng/model hay điều kiện tài khoản; không kết luận hết credit từ mã này.

## Cổng đánh giá và bước tiếp theo

`quality_gate.json` trả NOT ESTABLISHED. Chỉ có bốn ca hồi quy đã biết, thiếu mẫu/nhóm/
rà độc lập; các lỗi còn tồn tại. Dự đoán lưu trước khi đọc expected, lock của bản cuối
được đối chiếu trong `verification.json`. Báo cáo không ghi key hoặc hội thoại thật.

Thực hiện tiếp theo: hai người rà nhãn và ranh giới suspicious/need_context, thu tập
được phép dùng theo họ/chiến dịch, chọn cấu hình trên validation rồi chấm tập khóa độc lập.
Cổng mặc định đề xuất 500 ca/ít nhất 50 mỗi nhóm và cận dưới overall/precision/recall trên
98%; đây không phải số mẫu bảo đảm thành công. Tách tỷ lệ lỗi kỹ thuật khỏi suy luận,
vẫn tính cả hai vào hiệu quả toàn luồng. Không dùng nguồn RAG tương tự như xác minh đối tượng.

Chi tiết tại `../../QUALITY_98.md`. Từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests -q
node tests/worker_security.mjs
python quality_gate.py --predictions reports/quality_v2/retry_checked/predictions.json --references reports/quality_v2/regression_references.json --output reports/quality_v2/another_gate.json
```

Lệnh gate không gọi model. Không tiếp tục gọi model hàng loạt chỉ để tìm lần trả đúng.
Khởi động lại backend để nạp phiên bản mới. Nguồn runtime vẫn chưa được duyệt;
không có số liệu RAG trên tài liệu chính thống đủ duyệt trong lần sửa này.
