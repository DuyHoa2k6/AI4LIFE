# Bộ suy luận fact — kết quả thực tế 12/11/2026

**Báo cáo lịch sử thử nghiệm.** Theo yêu cầu sau đó, bộ fact đã ngừng dùng mặc định; luồng hiện tại quay lại event/rulebook + RAG/URL. Xem [xác minh khôi phục](../restore_event_flow_20261112/README.md). Các số đo dưới đây vẫn giữ nguyên cho phiên bản đã đo.

## Đã thay đổi

Giữ bộ bóc tách Python, event/relation/evidence/18 trường. Bộ quyết định cũ được lưu nguyên phần logic trong `backend/local_reasoning/legacy_engine.py`, có chú thích ngừng dùng mặc định; `engine.py` nay chạy fact ba trạng thái. Không comment tắt bộ bóc tách, RAG hoặc URL vì chúng vẫn cần cho luồng hiện hành.

`SCAMSHIELD_REASONER=facts` là mặc định; `legacy` chỉ để đối chiếu/quay lại. Đã kiểm tra cấu hình hiệu lực là local_rules + facts. Không gọi mô hình hoặc huấn luyện dataset trong lượt này.

Các fact có trạng thái, nguồn, phạm vi, phiên bản, bằng chứng và phụ thuộc; UNKNOWN không đồng nghĩa FALSE. Xử lý state_update cùng nguồn/phạm vi, lưu claim mâu thuẫn, cập nhật theo bối cảnh người dùng tự báo xác minh, bảo toàn high độc lập, và tách complete/partial/error. Rule evaluator không nhận văn bản gốc. Cache cấu hình theo dấu phiên bản file; không dùng bitmask.

Thêm quy tắc screen-share + mở thông tin ngân hàng có liên hệ trình tự. Bộ trích có bước bổ sung cho hành vi này; sửa nhận diện “ứng dụng” bị nhầm thành “ứng tiền”. RAG/URL giữ cơ chế hỗ trợ đã có, đồng thời lưu technical/derived facts vào trace khi sử dụng.

## 12 câu cũ — so sánh cuối

Đo **30 lượt/câu/phiên bản = 720 HTTP request**, cộng 24 lượt khởi động kết nối/làm ấm. Luân phiên cũ/mới trên cùng server, một request tại một thời điểm, HTTP TCP localhost có giải mã JSON. Cùng chỉ mục RAG thực hiện, tắt mạng URL; 12 câu không có liên kết. Không đọc expected trước khi ghi dự đoán.

| Chỉ số | Cũ | Fact mới | Nhận xét |
|---|---:|---:|---|
| HTTP p50 | 4,8539 ms | 4,5690 ms | Giảm **5,87%**, khoảng **0,2849 ms** |
| HTTP p95 | 7,4677 ms | 7,5365 ms | Tăng 0,0688 ms; **không cải thiện p95** |
| Lõi BE p50 | 2,9172 ms | 2,6764 ms | Giảm khoảng 8,25% |
| Lõi BE p95 | 5,4564 ms | 5,5262 ms | Hầu như tương đương, hơi tăng |
| Bóc tách p50 | 1,9725 ms | 2,1417 ms | Bản mới có thêm trích ngân hàng và kiểm tra/prune |
| Tạo fact p50 | Không có pha riêng | 0,1096 ms | Chi phí mới |
| Đánh giá luật p50 | 0,0969 ms | 0,1295 ms | Bản mới thêm trạng thái và audit; không chứng minh phép đánh giá luật nhanh hơn |
| Ca khớp risk + urgency tham chiếu | 12/12 | 12/12 | **Không tăng tỷ lệ phân loại trên 12 ca này** |
| Lượt lỗi HTTP trong phép đo | 0 | 0 | 720/720 HTTP 200 |
| Lượt gọi mô hình / bộ URL | 0 | 0 | Không dùng mạng ngoài để tạo số đo này |

Lợi ích thời gian tổng quan sát chủ yếu gắn với cache tài nguyên và bỏ đánh giá đầy đủ ở precheck rỗng; nó không đến từ phép bit. Các median của từng pha không cộng thành median tổng; pha luật cũ có kiểm chứng trong apply_rules, bản mới tách phần này sang tạo fact/kiểm tra. Không so hai pha như cùng một lượng công việc hoàn toàn giống nhau.

**11/12 câu có p50 giảm; P11 viết tắt tăng khoảng 2,35%** (7,419 → 7,594 ms). Bảng đầy đủ câu, mức và số đo: [verified_final/CASES.md](verified_final/CASES.md). JSON từng ca có fact/18 trường/phản hồi API: [predictions.json](verified_final/predictions.json). [720 số đo gốc](verified_final/measurements.json), [tổng hợp](verified_final/summary.json), [hash cấu hình và mã nguồn](verified_final/lock.json).

Đây là **12 ca phát triển đã biết**, không phải accuracy độc lập 100% hoặc chứng minh mục tiêu 98%. P08 “Mây bay trên núi” vẫn trả need_context do ngoài phạm vi bộ trích; không phải phát hiện lừa đảo. Một batch nhỏ có nhiễu GC/lập lịch và outlier; chưa chứng minh cải thiện có ý nghĩa thống kê trên tải thực.

Các lần đo trước được giữ: `comparison` (bản đầu HTTP p50 chậm khoảng 0,41%), `comparison_optimized` (sau bỏ precheck thừa, giảm khoảng 7,16%), `final_comparison` (giảm khoảng 6,07%), `verified_comparison` (giảm khoảng 5,63%, trước sửa partial khi không còn event). **Số bàn giao là verified_final sau các sửa cuối**, không chọn lần có phần trăm tốt nhất. Baseline là bộ quyết định cũ chạy lại trong repo, chia sẻ bộ trích chung hiện tại, không phải toàn bộ binary lịch sử trước mọi thay đổi.

## Các cải thiện ngoài 12 ca

Chín ca phát triển bổ sung: [bảng](verified_examples/CASES.md), [input → facts → rules → kết quả](verified_examples/predictions.json).

- Chỉ yêu cầu giao máy: cả hai need_context; bản mới có payment_confirmed UNKNOWN và hỏi đúng “Bạn đã kiểm tra và xác nhận khoản tiền vào tài khoản chưa?”, thay vì câu hỏi chung chung.
- Chưa nhận tiền + giao trước: giữ suspicious; đã báo nhận đủ + giao máy: giữ clear; lời phủ định: giữ clear.
- Chia sẻ màn hình rồi mở thông tin ngân hàng có căn cứ nối chuỗi: cũ suspicious → mới high.
- Người dùng bổ sung đã tự kiểm tra và nhận đủ tiền, gắn duy nhất giao dịch: cũ vẫn suspicious → mới clear với câu “theo thông tin bổ sung”, không nói BE đã xác minh ngân hàng.
- Lời người mua, bối cảnh phủ định/trích dẫn hoặc phạm vi khác không ghi đè xác nhận của người nhận.

Các ca mở rộng dùng để triển khai/hồi quy, không tính như kiểm định chất lượng độc lập. Kiểm thử update/xung đột còn có ma trận fact/annotations tổng hợp để tách lỗi suy luận khỏi lỗi bóc tách.

## Kiểm thử đã chạy

- **180/180 backend tests pass**, gồm 18 test mới. [Log](backend_tests.txt).
- Mỗi **16 quy tắc** có ca fact đủ điều kiện, phủ định, thiếu dữ kiện và trích cảnh báo; thêm các tổ hợp TRUE/FALSE/UNKNOWN của luật nhỏ. Có 39 tổ hợp phép AND 1–3 đầu vào, kiểm tra không nhập nhằng FALSE/UNKNOWN.
- Kiểm tra khác giao dịch/người nói, state_update phiên bản, claim người mua không ghi đè người bán, không dùng observed_at làm event_time, chứng cứ sai bị loại cùng phụ thuộc, partial không thành clear, high độc lập không bị hạ, lỗi không thành clear, dependency không chu trình và cấm biểu thức Python tùy ý.
- **Chrome thật + extension unpacked: 12/12 checks pass**, bốn mức, khẩn cấp, URL, nội dung ẩn và phạm vi gửi: [browser/report.json](browser/report.json).
- **14 worker security checks pass**, có mô phỏng phản hồi về muộn sau đổi phiên → STALE_SESSION: [worker_security.json](worker_security.json). Popup version: 4 checks pass.
- Compile Python và xuất schema thành công. Không chạy/chỉnh theo legacy holdout hoặc validation. Không đổi nhãn để làm đẹp kết quả.

## File bàn giao

- `backend/local_reasoning/engine.py`, `legacy_engine.py`: luồng mới và bản cũ đã ngừng dùng mặc định.
- `fact_schema.py`, `facts.py`, `fact_validation.py`, `fact_decision.py`: kiểu dữ kiện, trạng thái/phiên bản, kiểm chứng, điều kiện/ngoại lệ và tổng hợp.
- `semantic_events.py`: trích ngân hàng/trình tự có căn cứ; `local_observation/rules.json`: sửa nhầm ứng dụng/ứng tiền.
- `support_facts.py`, `support.py`: liên kết bằng chứng kỹ thuật/RAG vào fact trace; không khôi phục Gemini.
- `schema.py`, `backend/schemas.py`, `adapter.py`, `extension/result_view.js`: trạng thái partial, trace và tương thích hiển thị.
- `data/v2/fact_catalog.json`, `fact_rules.json`, `fact_templates.json`, các schema fact/rulebook/output và ghi chú ANNOTATION_GUIDE/README.
- `backend/settings.py`, cấu hình mẫu: SCAMSHIELD_REASONER; không cần key/model.
- `benchmark_fact_reasoner.py`, `check_fact_examples.py`, các test mới và cập nhật công cụ khóa phiên bản. Validator nhãn pilot vẫn ghi rõ dùng rulebook gốc để grounding, đồng thời kiểm tra cấu hình mới.

Mapping, chi tiết các luật/ngoại lệ, cấu hình và giới hạn: [FACT_REASONER.md](../../FACT_REASONER.md).

## Chạy lại

Từ thư mục ứng dụng:

```powershell
$env:SCAMSHIELD_REASONER="facts"
python -m unittest discover -s tests -v
python benchmark_fact_reasoner.py --rounds 30 --output reports/fact_comparison_rerun
python check_fact_examples.py --output reports/fact_examples_rerun
```

Thư mục đầu ra mới. Khởi động lại backend và tải lại extension để dùng mã mới. Chỉ đặt `SCAMSHIELD_REASONER=legacy` khi cần đối chiếu/quay lại.

## Giới hạn còn lại

Bộ trích vẫn dựa trên quy tắc, có thể bỏ sót biến thể hoặc nối sai sự kiện. Fact engine không tự học từ dataset và không tự khắc phục mọi lỗi ngữ nghĩa của bộ trích. Phạm vi/người bị tác động có thể chỉ là tham chiếu hội thoại chưa xác minh. Các quan hệ thời gian yếu cần người rà.

FactStore không có cơ sở dữ liệu bền qua nhiều request; version và lịch sử cập nhật nằm trong snapshot input hiện tại. Client gửi lại hội thoại+bối cảnh để tính lại; bảo vệ phiên/phản hồi cũ vẫn ở client/worker. Chưa có bitmask, embedding, mô hình huấn luyện hoặc bộ suy luận tổng quát.

Kho thật chưa có nguồn chính thống được duyệt. Các thời gian mili giây này **không đo redirect Internet hoặc hàng chờ extension**, không chứng minh đã giải quyết thời gian 8–20 giây quan sát trước đó. Ngân sách URL hiện hành vẫn có thể chiếm khoảng 6 giây; cần tối ưu/chia giai đoạn mạng riêng nếu muốn chặn toàn luồng ở 1–5 giây.
