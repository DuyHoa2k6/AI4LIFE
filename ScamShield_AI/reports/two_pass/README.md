# Bàn giao two_pass theo sơ đồ người dùng — 08/11/2026

Đã triển khai luồng đúng sơ đồ: Gemini lượt 1 → kiểm chứng bằng chứng → hai nhánh
song song → Gemini lượt 2 với văn bản/bối cảnh gốc → kiểm chứng kết quả và nguồn → cảnh báo.
**Cấu trúc đã triển khai; chất lượng và độ trễ chưa đạt nghiệm thu.**

## Mã và tài liệu

- `backend/two_pass.py`: điều phối hai lượt; toàn bộ nhánh regex + tìm tình huống chạy
  song song với nhánh nguồn. Nhánh tình huống nhận cả context gốc; lượt cuối luôn nhận
  input gốc, được bác bỏ giả thuyết đầu. Không có nhánh bỏ lượt hai theo điểm tự tin.
- `backend/retrieval.py`: tìm local bằng từ vựng + action tags; không có embeddings.
  Top-k 3/nhánh, đoạn 1.600 ký tự, timeout mặc định 0,8 giây, file tối đa 2 MB/500 mục.
- `backend/observation_prompt.txt`, `review_prompt.txt`: hợp đồng InitialReview/FinalReview,
  giả thuyết có refs/cách giải thích khác, phân biệt quan sát và kết luận, tài liệu là dữ liệu.
- `schemas.py`, `main.py`, `providers.py`, `settings.py`: mode two_pass/response 1.2,
  metadata retrieval/thời gian, điều phối deadline, nguồn chỉ lấy từ dữ liệu đã cung cấp.
- `knowledge/scenarios.jsonl`: 10 ví dụ tổng hợp runtime viết riêng, có đối chứng bình thường.
  Không đọc dev/validation/holdout, không lấy expected làm nguồn tri thức hoặc đưa vào prompt.
- Renderer chung: mode mới, nguồn thực sự dùng và lý do không có nguồn; worker/web 55 giây.
- README_GEMINI/TWO_PASS, 01–08, prompt điều phối/tuần 1–3 và README liên quan đã cập nhật;
  tài liệu hybrid/tuần trước được phân biệt là đối chứng hoặc snapshot lịch sử.
- Key/model riêng giữ nguyên, chỉ đổi mode thành two_pass. Không chép key vào báo cáo.

## Kho nguồn chưa đủ điều kiện

Nhánh RAG đã có trong pipeline nhưng kho nguồn hiện vẫn candidate, không tự duyệt.
Trong 12 ca live có kết quả cuối, cả 12 báo `no_approved_sources`; không trả nguồn nhà nước.
Chưa đo chất lượng truy xuất/citation trên nguồn chính thống thật. Không dùng ví dụ tổng hợp
để thay nguồn hoặc gọi đó là xác nhận của cơ quan nhà nước.

Source fixture giả lập chỉ dùng trong unit test để kiểm tra duyệt/hết hạn/nguồn được dùng,
không nằm trong runtime. Nguồn hợp lệ phải được người phụ trách kiểm tra trước khi gán
approved/reviewer/date/reuse_approved. Có tài liệu tương tự không xác minh đối tượng;
không có tài liệu không chứng minh an toàn. Không có chức năng exact_entity/verified_match.

## Kết quả Gemini thật trên bản cuối

16 ca tổng hợp gồm biến thể đổi chữ/cách tiếp cận, bình thường, nghi ngờ và thiếu thông tin.
Giữ nguyên model/key/prompt/backend/kho trong phiên cuối. Dự đoán lưu trước khi đọc expected.
Tập này do người triển khai viết; chưa có rà nhãn độc lập và không đại diện dữ liệu người dùng.
Không gọi các biến thể tự viết là phát hiện phương thức lừa đảo hoàn toàn mới.

| Nhóm kỳ vọng | Số ca | high | clear | need_context | Lỗi |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lừa đảo | 6 | 4 | 0 | 1 | 1 |
| Bình thường | 4 | 0 | 2 | 0 | 2 |
| Nghi ngờ | 3 | 0 | 0 | 3 | 0 |
| Thiếu thông tin | 3 | 0 | 0 | 2 | 1 |
| Tổng | 16 | 4 | 2 | 6 | 4 |

- 12/16 API 200, 4/16 lỗi (25%): hai PROVIDER_INVALID_OUTPUT ở lượt đầu và hai
  PROVIDER_TIMEOUT. 8/16 đúng trạng thái chức năng, hoặc 8/12 trên nhóm có kết quả.
- Cả ba ca kỳ vọng suspicious đều về need_context: hệ thống còn quá thận trọng, chưa
  phân biệt tốt mức nghi ngờ với thiếu dữ kiện. Không tính các ca này là đạt.
- Trên hai nhóm scam/normal có kết quả: TP=4, FP=0, FN=1, TN=2; precision high=100%
  với chỉ 4 cảnh báo cao, recall high=80% nếu bỏ ca lỗi. Tính toàn luồng có lỗi như yêu cầu,
  chỉ 4/6 ca scam nhận high = 66,7%, chưa đạt mục tiêu 75%. Không dùng tỷ lệ lọc lỗi để nghiệm thu.
- Không ghi nhận cảnh báo high/suspicious nhầm trong 2 ca bình thường có kết quả, nhưng
  2 ca bình thường còn lại lỗi nên chưa thể kết luận hệ thống xử lý bình thường ổn định.
- Hai ca thiếu thông tin thành công đều có câu hỏi. Một ca còn lại timeout.
- Phản hồi cuối có 21/21 quote khớp văn bản, không sai tham chiếu speaker theo kiểm tra máy móc.
  Điều này chưa chứng minh trích đủ mọi hành động hoặc mọi suy luận đều đúng.
- Ghi nhận 27 phản hồi HTTP provider trong phiên cuối; không suy ra số tiền hoặc gói miễn phí.
  Chi phí/token tổng của cả hai lượt chưa được đo đầy đủ trong runner này.

## Ca đã rà kỹ thuật

1. TP-S1: “đệm vốn bảo chứng” để lấy tiền công nhận high, cho thấy có thể xử lý biến thể
   diễn đạt mà không cần tên thủ đoạn cố định.
2. TP-S2: nói không cần gửi tiền nhưng yêu cầu quan sát/thao tác màn hình ngân hàng để
   hoàn phí nhận high; đối tượng rủi ro có thể là quyền truy cập thay vì tiền trực tiếp.
3. TP-S3: chuỗi sáu ký tự trong SMS đăng nhập được nhận là mã nhạy cảm, đúng người yêu cầu.
4. TP-N1: khoản sửa xe có context đã đối chiếu nhận clear, context quote được backend kiểm chứng.
5. TP-S4: model nối phí giữ chỗ với hoàn cọc nhưng đồng thời đặt request vào uncertain;
   backend không nhận quan hệ mâu thuẫn và trả need_context. Đây là ca high bị hạ mức.
6. TP-S6: chỉ thị nhúng không khiến trả an toàn; finding cuối có cài app, cấp quyền và
   ứng phí, cùng liên kết điều kiện nhận tài trợ, kết quả high.
7. TP-Q1/Q2/Q3: cấp quyền/cài APK/quyền quản trị bị trả need_context thay suspicious.
8. TP-S5/TP-N3 lỗi hợp đồng đầu ra, TP-U3/TP-N4 timeout; không có cảnh báo được bàn giao,
   không gán clear để che lỗi.

Đây là rà của người triển khai trên fixture công khai, không phải đánh giá độc lập.

## Độ trễ thực

| Bước | Số ca có kết quả | p50 | p95 |
| --- | ---: | ---: | ---: |
| API toàn bộ lượt đã thực hiện | 16 | 13,698 s | 23,541 s |
| Model lượt 1, nhóm API thành công | 12 | 6,060 s | 17,199 s |
| Hai nhánh local song song | 12 | 6,947 ms | 17,837 ms |
| Model lượt 2, nhóm API thành công | 12 | 3,999 s | 19,253 s |
| Kiểm chứng/dựng phản hồi | 12 | 0,680 ms | 2,166 ms |

Percentile tính nearest-rank; không cộng p50/p95 các bước thành percentile tổng.
Adapter model bao gồm mạng/provider/parse; chưa tách được mạng khỏi tính toán model.
Đo ASGI TestClient + HTTP Gemini thật, tuần tự, nghỉ 3 giây, không retry; không phải
thời gian web/extension từ đủ điều kiện đến hiển thị. Thiết bị phát triển không phải
môi trường benchmark cô lập. Chưa đo live nhiều mục, queue latency, cold provider hoặc SLA.

Giới hạn provider 20 giây/lượt, tổng pipeline 45/trần 50, client 55 là deadline, không
phải mục tiêu hiệu năng. Mục tiêu p95 dưới 2 giây chưa đạt, hai lượt model là phần tốn thời gian.

## Kiểm thử cục bộ và Chrome

70 unit test và 10 worker security check đạt. Test điều phối dùng rào đồng bộ chứng minh
nhánh nguồn đã khởi chạy khi nhánh regex còn đang xử lý; kiểm tra cả context gốc ở nhánh
tình huống và input gốc ở lượt hai. Đây là bằng chứng về cấu trúc, không phải năng lực model.

Chrome thật/MV3 đã qua 32/32 assertion với provider cục bộ giả lập, key rỗng, không gọi
Gemini thật. Queue thử 35 mục gửi đúng 35 request, đồng thời tối đa 1, sức chứa 20,
ghi nhận 15 mục bị hoãn; thời gian quan sát xả hàng đợi khoảng 43,061 giây. Không dùng
thời gian fixture này thay hiệu năng Gemini thật. Kết quả ở `browser/browser.json`.
Các lần dừng đầu được giữ trong browser_initial/browser_after_stale_fix/browser_before_burst_budget:
đã sửa test để chủ động giữ/thả phản hồi cũ, so sánh E2E bỏ riêng thời gian đo từng request,
và dành ngân sách chờ fixture hai lượt cho hàng đợi 35 mục. Không nới kiểm tra phạm vi,
evidence, số request trùng hoặc đồng thời. Xem file JSON cuối cho số assertion và kết quả thực.

## File và lệnh

- `final/lock.json`: hash bản cuối, input/expected, hai prompt, mã pipeline và hai kho.
- `final/predictions.json`: từng ca, hai đầu ra model khi hợp lệ, HTTP, thời gian và kết quả API.
- `final/cases.json`, `cases.csv`, `summary.json`: chấm sau dự đoán, lỗi và mẫu số riêng.
- `live/`: lượt phát triển trước khi đặt toàn bộ regex trong nhánh song song và thêm context
  cho nhánh tình huống theo sơ đồ người dùng nhắc lại. Không trộn với 16 ca của bản cuối;
  hai lượt dùng cùng 16 input nên không được công bố thành 32 ca độc lập.

Từ thư mục ứng dụng trong repo:

```powershell
python -m unittest discover -s tests -q
node tests/worker_security.mjs
python mixed_check.py --mode two_pass --output reports/two_pass_new --fixtures-dir fixtures/two_pass --pause 3
```

Lệnh cuối gọi Gemini thật tối đa hai lượt/ca, tiêu thụ quota và không ghi đè output cũ.
Để chạy Chrome fixture: đặt SCAMSHIELD_BROWSER_TWO_PASS=1 và SCAMSHIELD_REPORT_DIR là thư
mục báo cáo mới rồi chạy `node tests/browser_week2.mjs`.

Khởi động lại backend và reload extension/tab theo README_GEMINI. Chưa công bố nghiệm thu
P0 hoặc nguồn chính thống. Cần sửa chất lượng đầu ra/phân mức nghi ngờ, giảm độ trễ và có
nguồn duyệt thật cùng tập đánh giá độc lập trước khi dùng số liệu như cam kết sản phẩm.
