# Mục tiêu cảnh báo đúng trên 98%

Mục tiêu người dùng là kết quả phân tích đúng trên các nội dung gửi vào. Phải đo toàn
luồng: ca lỗi/timeout/chưa chạy không được tính là dự đoán đúng. Primary metric là mức
cảnh báo khớp nhãn đã rà và quote/speaker đối chiếu được. Chấm riêng độ đủ hành động,
vai lời trích, giải thích/tám answers và câu hỏi; tỷ lệ đúng nhãn không đại diện tất cả.
Precision/recall high là cổng an toàn bổ sung, tránh tập nhiều nội dung bình thường làm
điểm tổng cao trong khi bỏ sót lừa đảo. Mốc 98% là mục tiêu kiểm chứng, không phải cam kết
cho mọi nội dung ngoài phạm vi, phương thức hoàn toàn mới hoặc tài khoản free tier.

## Các sửa đã triển khai

1. Sửa mâu thuẫn prompt cũ yêu cầu ba khóa gốc nhưng schema thực tế cần năm; bản mới
   có sáu khóa theo FinalReviewV2, gồm uncertainty_reasons có loại identity/purpose/action/relation.
2. Gửi response_format=json_schema cho host Gemini, inline $ref và nullable fields
   required. Thử nghiệm cho thấy endpoint hiện tại từ chối schema Pydantic đầy đủ và
   biến thể có ràng buộc mảng với HTTP 400; dùng schema cấu trúc tương thích. Backend vẫn
   kiểm tra toàn bộ giới hạn Pydantic, quote, speaker và refs. Không tự đổi sang JSON mode
   sau lỗi để che tình trạng không hỗ trợ. Adapter khác giữ json_object hoặc chọn cấu hình rõ.
3. Bỏ trùng và lấy tối đa hai question_topics hợp lệ trước validation; enum lạ vẫn bị từ
   chối, không thay finding/quote/risk_links để làm đầu ra trông đúng.
4. Chưa rõ identity/purpose không tự phủ nhận hành động rõ. Yêu cầu cấp quyền/cài đặt
   có thể suspicious đồng thời có câu hỏi. Tiền thiếu mục đích vẫn need_context; action
   hoặc relation chưa rõ vẫn chặn nâng mức. Request/support bất định thật đều được xét.
5. Claim/cảnh báo/phủ định bị model gán benign thừa không cần context exemption. Request
   thực sự hoặc ID không hợp lệ vẫn qua kiểm chứng cũ. Không xóa bất định chưa phân loại.
6. Ghi diagnostic an toàn stage/kind/attempts/output_format/issue path/type, không ghi
   input, error message, ctx, URL key hoặc tên trường lạ do model tạo. Client API có thể
   xem lỗi ở bước observation/review để chẩn đoán; giao diện vẫn báo chưa kiểm tra được.
7. Hai lượt dùng chung HTTP session theo context request và đóng trong finally. Có một
   retry cho 503/mất mạng khi cấu hình, trong ngân sách cũ; không retry 429/auth/schema,
   không tăng timeout hoặc gọi lại đến khi ra đáp án mong muốn. Sơ đồ hai lượt không đổi.

## Cách đánh giá không làm tăng điểm giả

`quality_gate.py` chỉ chấm offline, không gửi dữ liệu tới model. Nạp dự đoán trước nhãn;
ID trùng/ngoài tập bị từ chối. Thiếu dự đoán và lỗi tính là không đạt; ca high lỗi tính FN.
Quote đúng nhưng hành động/vai sai vẫn cần chấm ngữ nghĩa riêng, không suy từ exact match.

Thiết lập cổng đề xuất, không phải chuẩn thống kê bắt buộc cho mọi dự án:

- Ít nhất 500 ca, có ít nhất 50 mỗi nhóm scam/normal/suspicious/uncertain. Số này chỉ là
  mức tối thiểu vận hành; không tự bảo đảm đủ dữ liệu cho mọi họ hoặc mọi phân bố ngoài đời.
- Cận dưới Wilson 95% của overall, precision high và recall high phải trên 98%, không
  chỉ nhìn tỷ lệ điểm. Nếu quá ít dự đoán high thì chưa đủ chứng cứ để vượt cổng.
- Hai người rà nhãn độc lập, tập ngoài phiên chỉnh cấu hình/kho runtime. Manifest ghi
  independent=true, reviewers=[hai người khác nhau], references_sha256 khớp file nhãn.
  Manifest chỉ là khai báo của người vận hành; script không chứng nhận tính độc lập.
- Không chấm các ca đã dùng để chỉnh như holdout độc lập. Chia theo họ/chiến dịch để
  tránh gần trùng, thêm dữ liệu được phép dùng và các trường hợp chưa có trong kho.
- Báo riêng group counts, các ca lỗi và recall high có lỗi. Thử lặp với cấu hình khóa
  để quan sát độ ổn định; không chọn lần chạy đẹp nhất. Không dùng một nhóm toàn bình
  thường để công bố độ chính xác chung cho hệ thống chống lừa đảo.

```powershell
python quality_gate.py --predictions <predictions.json> --references <expected.json> --review-manifest <review.json> --output <quality_gate.json>
```

Định dạng input prediction giống mixed_check.py; refs có cases[{id,group,acceptable}].
Manifest không có thông tin độc lập đầy đủ hoặc thiếu số mẫu thì gate không đạt, kể cả
vài ca đúng 100%. Cổng chưa chấm đủ ngữ nghĩa/tám answers nên cũng không thay nghiệm thu sản phẩm.

## Lộ trình thực tế

Ưu tiên lỗi giao thức và bất định trước; rồi hoàn thiện nhãn, đo lỗi theo họ, chọn cấu
hình trên validation và chấm tập khóa độc lập. Duyệt nguồn RAG thật, đo retrieval/citation;
không nguồn không nghĩa an toàn. Chỉ so model khác hoặc fine-tune khi có dữ liệu chứng minh
giới hạn còn lại thuộc model; không coi đổi model hoặc thêm RAG tự động đạt 98%.

Độ ổn định provider và giới hạn free tier phải được đo riêng. Một retry không khắc phục
được lỗi dịch vụ kéo dài hoặc timeout đã hết ngân sách. Không thể công bố đạt chỉ tiêu
toàn luồng khi ca nguy hiểm không nhận được cảnh báo do các lỗi này.

Kết quả các lần thử ở `reports/quality_v2/`; chỉ là hồi quy công khai, không đánh giá độc lập.
Khởi động lại backend để nạp mã và SCAMSHIELD_RETRIES mới. Không cần đổi key/model.
