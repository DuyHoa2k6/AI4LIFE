# Regex gợi ý và ranh giới bốn mức — 10/11/2026

## Thay đổi

- Luồng two_pass không ghép phát hiện regex vào preliminary dùng để áp quyết định.
  Regex chỉ cung cấp tối đa 12 rule_hints, gồm suggested_action/người nói/trích dẫn,
  không kèm nhãn request đã khẳng định hoặc mức rủi ro.
- FinalReviewV5 yêu cầu Gemini rà từng hint: request, claim, denial, quoted_warning,
  not_supported hoặc uncertain. Bằng chứng phải khớp input/người nói và liên quan
  đoạn đang rà. Request phải tham chiếu finding request hợp lệ; claim không được
  gắn ID request chỉ vì cùng chủ đề. Uncertain cần phần thiếu, needs_context và câu hỏi.
- Thiếu/sai review thì gửi phản hồi cụ thể để model đọc lại, tối đa một lần sửa.
  Còn sai trả lỗi; không giả kết quả hoặc coi lỗi provider là need_context.
- Regex đã được bác/phân loại lại không tự giữ need_context. Quan sát request từ
  Gemini lượt đầu chưa được lượt cuối giải quyết vẫn có cổng bảo vệ riêng.
- Prompt bổ sung định nghĩa/ràng buộc bốn mức; backend vẫn đặt risk_status.
  Chi tiết tại [RISK_STATES.md](../../RISK_STATES.md). Mock/hybrid cũ giữ làm đối chứng.
- Thêm chủ đề requested_action/requested_object/action_relation; tối đa hai câu.
  Backend lọc câu hỏi về tiền/quyền điều khiển nếu không có hành vi tương ứng đã
  kiểm chứng, để tránh gợi ý một hành động chưa được nêu. Không xin mã/mật khẩu thật.
- Analysis dùng decision_version=two-pass-5, thêm số hint được rà/phân loại lại/
  chưa rõ. Giao diện giữ bốn màu và phần hiển thị gọn, không đưa audit nội bộ ra UI.

## Kiểm thử tự động

170 unittest đạt, bao gồm các ca mới: lời kể đã cài/tự nhập mã không bị regex phủ
quyết, APK vẫn suspicious khi thiếu nhà phát hành, phải rà đủ hint, sửa một lần,
quote giả hoặc không liên quan bị từ chối, không gán claim vào request, câu hỏi
thiếu đối tượng, không hỏi tiền/quyền ngoài hành vi và giữ high cho OTP/điều kiện tiền.
13 kiểm tra worker và 4 kiểm tra phiên bản popup đạt. Không sửa client trong lần này.

## Gemini thật — giữ riêng từng phiên bản

Tám ca public hồi quy lấy từ phép thử trước, không phải tập độc lập. Không đọc
holdout, không gửi expected cho model. Mỗi lượt khóa prompt/code/hash trước chạy.

1. `live/`, trước làm rõ references: chạy 3/8 rồi dừng theo ngưỡng lỗi. H01/S01
   gặp provider 503; S02 đúng ý nghĩa claim nhưng tham chiếu sai finding request,
   còn lỗi sau lần sửa nên HTTP 502. Không xóa hoặc tính các ca này là thành công.
2. `checked/`, sau làm rõ prompt và phản hồi sửa references: chạy 8/8, HTTP 200 ở
   7 ca, 6/8 khớp nhãn mục tiêu. H03 gặp provider 503; S03 vẫn need_context thay
   vì suspicious. p50/p95 ca thành công 14,22/33,21 giây.
3. `focused/`, sau lọc câu hỏi ngoài hành vi: H03 high, C03 need_context; cả hai
   HTTP 200. H03 22,32 giây, C03 8,13 giây. Không cộng lượt này thành một phép đo
   “8/8 chính xác” của phiên bản khác. Unit test đã chạy lại sau thay đổi lọc câu hỏi.

| Ca | Trước thay đổi | Lượt checked | Nhận xét |
| --- | --- | --- | --- |
| H01 giao OTP | high | high | Giữ cảnh báo nguy hiểm; 1 hint được xác nhận |
| S01 quyền điều khiển, chưa rõ mục đích | high | suspicious | Không còn tạo lợi ích/điều kiện từ câu thiếu mục đích |
| S02 cài APK, thiếu nhà phát hành | need_context | suspicious | Rà 2 hint, phân loại lại 1; câu giải thích không còn ép mức |
| H03 tiền đồng bộ trước khi nhận tiền | high | lỗi 503 | Lượt focused sau đó trả high, lưu riêng |
| N03 bài cảnh báo trích lời dụ | clear | clear | 1 hint được phân loại lại theo vai cảnh báo |
| C03 “gửi cái đó” | need_context | need_context | Focused chỉ hỏi loại thông tin, không hỏi khoản tiền chưa nêu |
| S03 nhãn link khác đích | suspicious | need_context | Còn lệch: model nhận action other nhưng coi dấu hiệu URL là background |
| N04 đã cài từ trước, tự nhập OTP | need_context | clear | Rà 2 hint, phân loại lại cả 2; rule_conflicts=0 |

## Giới hạn

Không bảo đảm model luôn đúng ngữ nghĩa chỉ từ quote đúng. S03 còn lệch nhãn và
dịch vụ đã có 503. Mục đích thay đổi là giảm quyền quyết định sai của regex, không
bỏ kiểm chứng hoặc luôn tin model. Chưa đo chất lượng độc lập/98%, tải đồng thời
hoặc browser latency; RAG vẫn chưa có nguồn chính thống được duyệt trong các ca này.
Các trường nội bộ vẫn bị chặn khỏi giao diện kết quả. Ranh giới action other và
đánh giá quan hệ URL cần kiểm thử tiếp, không tự nâng mức để đạt nhãn mong muốn.

## Chạy và áp dụng

Khởi động lại backend với mode two_pass đang dùng. Không cần thay API key hoặc
cài thêm thư viện. Lệnh kiểm thử từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests
python mixed_check.py --mode two_pass --output reports/advisory_rules_20261110/checked --fixtures-dir fixtures/advisory_rules_20261110 --pause 2 --service-error-limit 5
python mixed_check.py --mode two_pass --output reports/advisory_rules_20261110/focused --fixtures-dir fixtures/advisory_rules_20261110 --pause 2 --service-error-limit 3 --case-ids H03 C03
```

Đổi đường dẫn output khi chạy lại vì script không ghi đè báo cáo. Lock và dự đoán
từng ca trong từng thư mục; verification.json kiểm tra snapshot hiện hành focused.
