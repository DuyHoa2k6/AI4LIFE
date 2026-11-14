# Sửa tầng ngữ nghĩa và suy luận — 13/11/2026

Đã triển khai, đo trên hội thoại đầu vào thật qua API local, không thay bằng
fixture đầu ra đã định sẵn. Không dùng API mô hình, bitmask hoặc huấn luyện ML.
Xem [thiết kế/module/giới hạn](../../SEMANTIC_GRAPH.md).

## Kết quả cuối

| Phép kiểm tra | Kết quả |
|---|---|
| 10 hội thoại gốc theo kỳ vọng high của người dùng | 1/10 → 10/10 khớp mức |
| 42 đối chứng cấu trúc A–G | 42/42 thỏa điều kiện: 12 high, 30 not_high |
| Cảnh báo high trên 30 đối chứng not_high | 0/30 trong bộ development này |
| Các bộ cũ | 31/31, 24/24, 8/8 qua; bộ 8 dùng phiên bản kỳ vọng mới cho quy tắc G |
| Kiểm thử Python | 244 tests qua |
| Lỗi HTTP, lời gọi HTTP bên ngoài trong các bài đo | 0 |

“Khớp” không phải độ chính xác độc lập: tất cả các câu đã được dùng để phát
triển hoặc do cùng phiên làm việc tạo. Không cộng các bộ thành số mẫu độc lập.
Không khẳng định đạt 98% trên dữ liệu thật. `not_high` cho phép clear,
need_context hoặc suspicious; các ca đối chứng không được ép tất cả clear.

## Từng tầng

- [Rà từng tầng của 10 ca](verified_after/LAYERS.md) và
  [số liệu chi tiết](verified_after/layer_review.json).
- 30/30 loại hành động bắt buộc theo chú giải sparse được tìm thấy.
- 16/16 loại quan hệ bắt buộc theo chú giải sparse được tìm thấy.
- Kiểm tra ID, quote, scope và liên hệ người: không lỗi cấu trúc trên 10 ca.
- 585/585 quote trong 30 lượt API công khai khớp message_id/Unicode offset.
  Các lượt lặp và quote trùng không phải những mẫu độc lập mới.
- Kiểm thử riêng speaker/requester/performer, lời thuật lại, tên người được
  gọi khác nhau, phủ định, điều kiện “còn không”, tham chiếu ảnh mơ hồ, mã kết
  nối so với mã xác thực, input vào trang so với gửi credentials cho bên khác.
- Kiểm thử cập nhật mỗi nhóm A–G làm thay đổi kết luận; G còn được thử qua
  clarification có case/version thật, tăng revision và từ chối revision cũ.
- Câu hỏi về nhiệm vụ có chi tiền khi chưa có căn cứ; không hỏi lại mục đích
  nộp khi điều kiện trả thêm/nhận vốn đã được xác định.

Đây là kiểm tra độ phủ yêu cầu và toàn vẹn cấu trúc, chưa phải precision đầy
đủ của bộ trích hoặc đánh giá đúng mọi đại từ. Bộ 31 còn một required event
chưa được trích dù mức cảnh báo cuối khớp (20/21 event yêu cầu, 8/8 quan hệ
yêu cầu). Không đánh đồng schema hợp lệ với hiểu đủ ngữ nghĩa hay 18 trường đúng.

## Nguyên nhân 0 quan hệ và sửa thực tế

Linker cũ chạy, ID/validator/serializer không làm rơi một loạt quan hệ. Các
quan hệ không được tạo chủ yếu do thiếu/sai đầu mút, giới hạn cùng câu/cùng
nguồn và thiếu cấu trúc điều kiện/đối tượng. Một lỗi scope coi từ thường sau
“hợp đồng” là mã giao dịch cũng được sửa. Chi tiết trong đặc tả.

Ca 09 còn có alias người nói của harness (“Tài khoản mới nhắn”/“Tài khoản
mới”) từng bị tách. Đã sửa trước phép đo đối chiếu cuối. Script layer_review
assert payload trước/sau giống nhau. Bản graph tắt với payload sửa alias vẫn
chỉ 1/10 high, nên kết quả không phải chỉ do sửa harness.

Không nâng ngưỡng chung: cơ chế mới đọc các cấu trúc sự kiện/quan hệ. Ví dụ:

```text
“Bạn chuyển thêm tiền bảo chứng. Hệ thống sẽ trả cả vốn...”
→ payment(request) + promised_return(claim)
→ prerequisite_for có bằng chứng hai đầu, cùng nguồn/scope/người bị tác động
→ trạng thái có điều kiện nhận tiền sau khoản nộp
→ nguy cơ tiếp tục mất tiền, không xác minh số dư là thật
→ high
```

Yêu cầu giao thông tin đăng nhập có thể được cảnh báo bằng một sự kiện đúng
đối tượng/hướng, không bắt buộc tạo quan hệ để làm đẹp số đếm.

## Các lỗi phát hiện trong quá trình sửa

Giữ nguyên các thư mục chạy thử để kiểm tra lại lịch sử:

- Bản `first` mới 8/10 high: “còn không tôi gửi” bị coi nhầm là phủ định, và
  alias speaker ca 09 tách sai. Đã phân biệt phủ định hành động với điều kiện
  không làm; sửa alias tường minh của harness.
- `controls_first` 40/42: thời gian “trong lúc tôi thao tác” tự bị coi là đủ
  quyền điều khiển; “gửi cho chỗ làm” chưa giải quyết đối tượng lọt vào luật
  coercion cũ. Đã yêu cầu có hành động truy cập từ xa riêng và trì hoãn phân
  loại threaten_disclosure cho tới khi có tham chiếu/điều kiện hợp lệ.
- Các hồi quy ban đầu: graph thêm payment trùng nhưng không kế thừa mục đích
  mua hàng; quyền lợi trong câu phủ định bị coi là claim có hiệu lực; khoản
  vốn của công ty bị coi như khoản người dùng nhận. Đã sửa điều kiện/ngữ nghĩa,
  không sửa các nhãn đó để che lỗi.
- Một kỳ vọng cũ về giả người quen/khác tài khoản/đừng xác minh là suspicious
  được giữ trong lịch sử, bản kỳ vọng graph riêng chuyển high theo tiêu chí G
  người dùng vừa chốt. Ca hóa đơn đổi tài khoản chưa đủ tổ hợp vẫn suspicious.

## Độ trễ đối chiếu

Đầu vào và alias giống nhau, chạy tuần tự hai tiến trình cùng code cuối;
khác cờ bật/tắt graph. Mỗi ca 3 lượt, 30 request công khai mỗi chế độ; không
tính 10 request debug vào phân vị công khai.

| Cấu hình | p50 | p95 nearest-rank |
|---|---:|---:|
| Graph tắt | 49,680 ms | 103,553 ms |
| Graph bật | 73,953 ms | 97,232 ms |

Lớp mới tăng p50 khoảng 24 ms trong lần đo này. p95 dao động với mẫu nhỏ,
không kết luận cải thiện tốc độ. Không có kiểm soát cold start, tải đồng thời,
browser/extension, OCR hoặc mạng URL. Nguồn RAG thực chưa được đánh giá ở đây.
Hash code/config/dữ liệu và cấu hình hiệu lực trong summary hai thư mục đo.

## Artifact và lệnh

- [Kết quả từng hội thoại](verified_after/CASES.md).
- [Dự đoán trước](verified_before/predictions.json),
  [dự đoán sau, graph và trace](verified_after/predictions.json).
- [42 đối chứng](controls_verified/CASES.md).
- [31 ca](regression31_verified/CASES.md), [24 ca](regression24_verified/CASES.md).
- Trace không có văn bản/khóa/mật khẩu, chỉ ID/count/method/reason; quote raw
  debug vẫn chứa đầu vào giả lập đã được chủ động đưa vào báo cáo này.

Từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests -q
python check_graph_controls.py --output reports/graph_controls_new
python check_user_scenarios10.py --source "C:\Users\nhoa4\.codex\attachments\c23e52f9-f527-4757-9ba6-4a4c9ffd89d1\Pasted text.txt" --output reports/graph_user10_new --rounds 3
```

Không sửa dev/validation/holdout cũ hoặc key. Chưa chạy lại Chrome E2E và chưa
chấm độc lập trên dữ liệu thật. Các cách nói ngoài mẫu, đại từ đa nghĩa, tên
riêng phức tạp và nhiều đối tượng vẫn có thể chưa hiểu; giữ unknown hoặc
need_context thay vì tự clear hoặc bịa liên hệ. Không tự tuyên bố thành công
mọi cách diễn đạt của cùng một quan hệ.
