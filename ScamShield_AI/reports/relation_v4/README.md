# Bằng chứng quan hệ và rà liên kết có thể bỏ sót — 10/11/2026

## Thay đổi

- `backend/schemas.py`: `FinalReviewV3` thêm `relation_assessments` cho từng cặp;
  trạng thái supported / uncertain / not_supporting_risk, loại quan hệ, quote,
  kết luận ngắn và khoảng trống thông tin cụ thể.
- `backend/relation_grounding.py`: dùng lại bộ kiểm chứng Unicode/quote/người nói
  để kiểm tra cả quan hệ; không lấy context, nguồn kho hoặc câu bịa làm quote.
  Kiểm tra quan hệ khớp danh sách risk_links/uncertain_relations, không trùng cặp,
  không cấp căn cứ rủi ro bằng loại ordinary_transaction/unrelated/unknown.
- Tìm request + inducement cùng người nói và cấu trúc điều kiện trong văn bản gốc
  như tín hiệu có thể bị bỏ sót. Tối đa 12 gợi ý trên finding đã kiểm chứng; từ khóa
  đơn lẻ, lời cảnh báo/phủ định, hai người nói khác nhau hoặc request có context
  benign hợp lệ không tự thành tín hiệu. Đây không phải quy tắc tự kết luận high.
- `backend/two_pass.py`, `review_prompt.txt`: sửa chỉ dẫn cân bằng. Đọc lại đầu vào,
  đối chiếu cả giữ/bác quan hệ, tên gọi thay thế và đại từ. Nếu có quan hệ rõ, giữ
  liên kết và bỏ bất định không phù hợp; nếu thiếu thật, nêu khoảng trống cụ thể;
  nếu giao dịch thường/không liên quan thì bác liên kết bằng đánh giá có căn cứ.
  Dùng tối đa một lần sửa trong lượt rà cuối, thường 2/max 3 lời gọi model trước
  retry HTTP. Không chọn mức cao nhất hoặc dùng kết quả trước làm bằng chứng.
- API `schema_version=1.5`, `decision_version=two-pass-4`; thống kê grounded links,
  tín hiệu đã rà và tín hiệu vẫn còn. Giao diện vẫn nhận contract kết quả chính;
  không công bố assessment_note chưa kiểm chứng như lời giải thích đã xác minh.
- Cập nhật bộ fixture/unit test và khóa hash module mới trong script đo live.

Giữ nguyên model và API key, nguồn candidate chưa duyệt, tập holdout, cấu hình
tạm bỏ response timeout và các báo cáo cũ. Chưa thêm tính năng hỏi linh hoạt mới.

## Kiểm thử

`python -m unittest discover -s tests -q`: **112 kiểm thử đạt**; 12 ca mới gồm
bỏ sót nhất quán vẫn cần rà, cue không tự nâng high, quote quan hệ bịa/nguồn sai,
thiếu assessment, giao dịch hợp pháp, warning, khác người nói, khoảng trống thiếu
cụ thể, Unicode/câu lặp, đánh giá bác bỏ rõ ràng cho hai người nói khác nhau và
phản hồi chỉ rõ ID finding có quote không nguyên văn.
`node tests/worker_security.mjs`: **10 kiểm thử đạt**.
Đây là kiểm thử đầu ra giả lập; không phải tỷ lệ đúng của Gemini.

Kiểm thử Gemini thật tách input và nhãn tham chiếu; ghi mọi dự đoán trước khi đọc
expected. Tám ca nhắm đích: NW-02 là hồi quy đã biết, bảy ca mới gồm biến thể,
giao dịch hợp pháp, lời cảnh báo, khác người nói và thực sự thiếu thông tin.
Không phải tập gán nhãn độc lập hoặc phép đo chất lượng toàn hệ thống.

```powershell
python mixed_check.py --mode two_pass --output reports/relation_v4/live --fixtures-dir fixtures/relation_v4 --pause 3 --service-error-limit 6
```

Lệnh từ thư mục ứng dụng. Khi chạy phiên khác phải đổi output để không ghi đè.
Không chỉnh prompt/quy tắc trong phiên đo; lưu cấu hình/hash, dự đoán, ma trận,
thời gian và trường hợp chưa chạy trong thư mục `live`.

### Phiên validation đầu — không gộp với phiên cuối

`live/` ghi phiên prompt v4 đầu: 8 ca, 7 API thành công, 6/8 khớp mức kỳ vọng.
NW-02 vẫn need_context. Model đã nêu điều kiện rõ nhưng đặt thiếu thông tin về
bản chất khoản hoàn vào missing_information của quan hệ, rồi bỏ liên kết khi sửa.
Một bài cảnh báo bị EVIDENCE_INVALID vì model tự đặt speaker là “kẻ gian”/“Bản tin”
thay vì metadata unknown. Rà ca khác cũng phát hiện bộ kiểm tra ban đầu bắt cả đánh
giá bác bỏ quan hệ khác người nói phải cùng người nói, gây một yêu cầu sửa thừa.
Hash được kiểm tra không đổi trong phiên, lưu `live/hash_verification.json` trước
khi chỉnh phiên tiếp theo. Không bỏ hoặc thay thế các dự đoán chưa đạt này.

Đã sửa prompt thành v4.1 để định nghĩa status là quan hệ **được nêu trong tin**, không
phải chứng minh giao dịch hợp pháp/lừa đảo; đưa thông tin thiếu về danh tính/pháp lý
sang câu hỏi chung nếu không làm đổi quan hệ đã nêu. Bổ sung ý nghĩa trường ngay
trong phản hồi sửa, nhắc metadata speaker của text ở lượt đầu. Đánh giá bác bỏ có
thể đối chiếu hai người nói khác nhau; quote của mỗi đầu vẫn phải đúng speaker.

### Phiên cuối

`checked/` dùng `fixtures/relation_v4_checked`: 1 hồi quy NW-02 và 7 đầu vào mới,
đặt nhãn trước khi gọi. Các ca validation đầu đã dùng để chỉnh không được coi ca
độc lập. Nhãn mới vẫn do người triển khai đặt, không có người gán nhãn độc lập.

```powershell
python mixed_check.py --mode two_pass --output reports/relation_v4/checked --fixtures-dir fixtures/relation_v4_checked --pause 3 --service-error-limit 6
```

Không đổi production code/prompt/index/config trong phiên cuối. Kết quả tổng hợp
và nội dung từng ca được lưu riêng; không lấy kết quả tốt nhất giữa hai phiên.

Trong `checked/`, 6/8 API thành công, 5/8 khớp mức kỳ vọng. Hai biến thể nguy hiểm
mới high, hai normal clear và một ca thiếu tham chiếu need_context. NW-02 không còn
bỏ liên kết do thiếu danh tính nhưng bị lỗi quote ghép `[...]` ở finding support;
backend từ chối với `PROVIDER_INCONSISTENT_OUTPUT`. Một normal lỗi provider 503,
một ca chưa biết quyền nào vẫn suspicious thay vì need_context. Không loại các ca
này khỏi mẫu số để báo chất lượng tốt hơn. p95 API thành công khoảng 44,820 giây;
provider/mạng không ổn định, response timeout đang tắt.

### Bổ sung phản hồi lỗi bằng chứng cụ thể

Sau phiên checked, `evidence_feedback` chỉ rõ từng finding sai cùng mã lỗi
quote_not_verbatim/speaker_metadata_mismatch/quote_offsets_mismatch/... trong yêu
cầu sửa riêng gửi model. Không tự sửa dấu, không chấp nhận `[...]`, không tự thêm
link hoặc thêm vòng gọi. Nếu model tiếp tục không sửa thì vẫn trả lỗi. Một unit
test xác nhận quote gốc không bị backend viết lại.

`focused/` là kiểm tra nhắm đích sau bổ sung này, chỉ NW-02 và một bài cảnh báo.
Hai ca đã biết nên đây là hồi quy, không phải tập cuối độc lập; không gộp với
checked hoặc lấy kết quả thay thế cho các ca lỗi trước. Chi tiết mọi phiên xem
[RUNS.md](RUNS.md), [CASES.md](CASES.md) và JSON gốc. Phiên focused có 1/2 API thành
công: bài cảnh báo clear; NW-02 lỗi 503 ở provider sau retry. Không khẳng định NW-02 đã được giải quyết ổn định chỉ vì
prompt/model trả đúng quan hệ ở một đầu ra trung gian.

## Giới hạn

Quote khớp và các trường nhất quán chưa chứng minh quan hệ đúng ngữ nghĩa. Việc
nêu thông tin thiếu là kết luận model; backend chỉ kiểm tra cấu trúc và loại các
câu thiếu thông tin rỗng/quá chung đã định. Cue có thể bỏ sót cách diễn đạt ngoài
phạm vi; nếu model không trích được hai đầu, cue không tự phát hiện. Không lấy
việc sửa riêng NW-02 làm bằng chứng đạt 98%. Chưa có nguồn RAG thực đủ duyệt.
