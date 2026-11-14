# Kiểm thử xen kẽ lừa đảo / bình thường — 08/11/2026

**Kết luận: cấu hình hiện tại chưa đảm bảo chất lượng cảnh báo hoặc mục tiêu độ trễ.**
Đã gửi đủ 28 ca khác nhau qua Gemini thật, giữ nguyên prompt/model/quy tắc/backend.
Không sửa bộ phân tích theo lỗi quan sát được trong phiên này.

## Phạm vi và điều kiện

- 12 ca lừa đảo, 12 bình thường, 4 thiếu bối cảnh; xếp xen kẽ để kiểm tra cả từ khóa chung,
  phủ định, bài cảnh báo trích lời dụ, khoản vay có bối cảnh, OTP tự dùng, nhiều người nói và chỉ thị nhúng.
- Toàn bộ là dữ liệu tổng hợp công khai do người triển khai viết. Nhãn là phán đoán chức năng
  của người viết, chưa được người độc lập duyệt; không suy ra độ chính xác trên người dùng thực.
- Không đọc nội dung dev/validation/holdout hoặc dùng nhãn làm đầu vào model. `inputs.json`
  và `expected.json` riêng; runner lưu toàn bộ dự đoán rồi mới đọc expected để chấm.
- Gemini `gemini-3.5-flash-lite`, hybrid always_live, không RAG, timeout 20 giây, đồng thời 1,
  cách nhau 3 giây, không retry, không đổi model, không bật billing. Gói/quota tài khoản chưa được xác minh.
- Windows 11, Python 3.12.5. Đo API bằng ASGI TestClient cộng HTTP provider thực, không bao gồm
  trình duyệt, extension, HTTP socket đến uvicorn hoặc thời gian chờ hàng đợi của client.
- Lượt 1 chạy 12 ca rồi circuit breaker dừng sau 3 lỗi liên tiếp. Lượt 2 chỉ chạy đúng 16 ca chưa gửi.
  Runner lượt 2 tiếp tục sau lỗi bằng chứng từng ca; vẫn dừng nếu lỗi quyền/model/quota hoặc lỗi dịch vụ liên tiếp.
  `comparison.json` xác nhận hash backend/prompt/rules giữa hai lượt giống nhau. Không đếm ca chạy lặp.

## Kết quả thật của Gemini

| Nhóm | Số ca | high | need_context | clear | Lỗi |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lừa đảo | 12 | 3 | 6 | 0 | 3 |
| Bình thường | 12 | 0 | 4 | 0 | 8 |
| Thiếu bối cảnh | 4 | 0 | 3 | 0 | 1 |
| Tổng | 28 | 3 | 13 | 0 | 12 |

- 16/28 trả kết quả phân tích (57,1%); 12/28 lỗi (42,9%). Provider HTTP 200 cả 28 lượt,
  không có lỗi quota/429 hoặc timeout trong phiên này. Thành công HTTP provider chưa đảm bảo đầu ra dùng được.
- 10 lỗi `EVIDENCE_INVALID`; 2 lỗi `PROVIDER_INVALID_OUTPUT` (không đáp ứng hợp đồng đầu ra;
  dữ liệu lưu không đủ để phân biệt chi tiết cú pháp JSON với từng lỗi schema).
- Đúng trạng thái chức năng 6/28 (3 high, 3 need_context), hoặc 6/16 nếu chỉ tính ca API 200.
  Ca lỗi không được tính là clear hoặc là đã phân tích đúng.
- Chỉ số high trên 13 ca có kết quả thuộc hai nhóm scam/normal: TP=3, FP=0, FN=6, TN=4;
  precision=100% (chỉ 3 dự đoán high), recall=33,3%. Bốn ca thiếu bối cảnh nằm ngoài ma trận nhị phân này.
  TN ở đây chỉ nghĩa là không dự đoán high, **không có nghĩa hệ thống trả clear đúng**.
- Tính trên toàn bộ 12 ca lừa đảo dự kiến, chỉ 3/12 (25%) nhận cảnh báo high;
  6/12 bị hạ xuống need_context và 3/12 không phân tích được. Không có ca scam trả clear trong lượt live này.
- Không có cảnh báo high/suspicious nhầm trên nhóm bình thường, nhưng cũng không có ca bình thường
  trả clear: 4 cần bối cảnh và 8 lỗi. Không thể dùng FP=0 để khẳng định hệ thống xử lý tốt nội dung bình thường.
- Ba ca thiếu bối cảnh có kết quả đều trả câu hỏi bổ sung; một ca lỗi. Chưa chấm độc lập chất lượng câu hỏi.

## Bằng chứng và rà kỹ thuật

Đầu ra model đã qua schema có 42 trích dẫn; 20 trích không đạt đối chiếu chính xác
message/range/quote theo Unicode code point. Có trường hợp quote tồn tại nhưng start/end sai,
end vượt độ dài văn bản, hoặc tham chiếu không khớp. `invalid_quotes.json` ghi từng trường hợp.
Các mẫu JSON không qua schema không nằm trong mẫu số 42 này.

Ở phản hồi cuối cùng của 16 ca API 200, 24/24 trích dẫn khớp văn bản và tham chiếu speaker,
không ghi nhận trích giả còn tồn tại. Đây là độ đúng máy móc của quote, chưa chứng minh
vai trò lời trích và kết luận rủi ro đều đúng. Phần rà dưới đây do người triển khai thực hiện,
không phải rà độc lập hay chứng nhận danh tính người gửi.

Các lỗi điển hình đã xem cả input, review của model và phản hồi backend:

1. **MX-S01 — phí nhận thưởng:** model nhận ra yêu cầu tiền và liên kết với quà, nhưng
   hai finding bị loại vì vị trí sai; kết quả chỉ need_context. Đây là hạ mức cảnh báo,
   không phải model hoàn toàn không nhìn thấy hành vi.
2. **MX-N01 — bài cảnh báo:** model ghi đúng `quoted_warning` và `denial`, nhưng cũng đưa
   chúng vào danh sách benign trong khi không có context evidence. Backend yêu cầu làm rõ,
   trả need_context thay clear. Luồng hợp đồng/review cần xử lý vai cảnh báo nhất quán hơn.
3. **MX-S06 — lấy mật khẩu/mã xác thực:** provider trả review với yêu cầu nguy hiểm, nhưng
   bằng chứng sai vị trí bị loại toàn bộ, API 502. Không có cảnh báo high được bàn giao.
4. **MX-N04/MX-N10 — trả nợ/tiền thuê có context:** vẫn need_context dù đầu vào cung cấp
   bối cảnh đã đối chiếu. Kết quả chưa dùng bối cảnh để phân biệt bình thường đủ hiệu quả.
5. **MX-U04 — nhiều người nói:** kết quả need_context, không ghép chủ nhà và người quảng cáo
   thành high; các speaker ở phản hồi được giữ đúng.
6. **MX-N06 — metadata:** `discarded_live_findings=-1` khi thêm một rule-conflict vào danh sách.
   Đây là lỗi bộ đếm cần sửa, không dùng trường này để tính chất lượng trong báo cáo.

## Độ trễ và so sánh mock

| Phép đo | Số lượt | p50 | p95 | Lỗi |
| --- | ---: | ---: | ---: | ---: |
| API hybrid, gồm cả kết quả lỗi | 28 | 3,207 s | 4,065 s | 12 |
| API hybrid, chỉ ca phân tích thành công | 16 | 3,207 s | 4,177 s | 0 trong nhóm đã lọc |
| Adapter provider, nhóm thành công | 16 | 3,205 s | 4,174 s | — |
| API mock, benchmark warm tuần tự | 100 | 1,037 ms | 1,436 ms | 0 |

Benchmark mock gồm 1 lượt đầu (3,341 ms) và 100 lượt warm, luân phiên cùng 28 input.
Mock không gọi model; tốc độ đó không đại diện hiệu năng live hay trình duyệt.
Trên 28 ca chức năng, mock trả high đúng 6/12 scam, suspicious 4/12, bỏ sót hoàn toàn 2/12;
nhóm normal có 10 clear và 2 suspicious nhầm. Nhóm unclear có 2 need_context và 2 suspicious.
Mock không thể thay thế mô hình suy luận dù không có lỗi HTTP trong phép thử.

Trong live, thời gian adapter provider chiếm trung bình khoảng 99,90% thời gian API.
Adapter bao gồm HTTP/network, xử lý phía provider và parse/validate JSON; không tách được
thời gian truyền mạng khỏi thời gian model chạy. Không có truy xuất RAG. Phần ngoài extraction
lớn nhất đo được khoảng 5,53 ms. Chưa có dữ liệu để quy toàn bộ độ chậm cho model thay vì mạng.

Mục tiêu p95 warm dưới 2 giây trong `06_Kiem_Thu.md` chưa được chứng minh đạt;
ngay p50 API đã trên 3 giây. Mỗi đợt tách lượt đầu trong lock/summary, nhưng không xác nhận
provider cold start hoặc trạng thái cache. Với 28 lượt, p95 chỉ là quan sát mẫu nhỏ, không phải SLA.
Chưa đo tải đồng thời live, cuộn/quét nhiều mục, request trùng do extension, thời gian chờ hàng đợi,
web từ bấm gửi, hay p95 trải nghiệm đầu cuối trong phiên này.

Provider báo tổng 58.001 input token, 23.395 output token, 81.396 token cho 28 lượt.
Đây là usage trả về, không phải số tiền đã tính; không xác nhận billing hoặc credit tài khoản.

## Bàn giao và chạy lại

- `comparison.json`: số liệu hai chế độ, ma trận và hash đối chiếu.
- `gemini_cases.csv`, `mock_cases.csv`: bảng từng ca, input ở `../../fixtures/mixed_checks/inputs.json`.
- `gemini/`, `gemini_remaining/`: lock, review model, dự đoán lưu trước khi chấm, thời gian từng lượt.
- `invalid_quotes.json`: trích dẫn bị sai và vị trí đúng tìm được nếu đoạn chỉ xuất hiện một lần.
- `mock_benchmark.json`: toàn bộ 101 thời gian đo mock.
- `verification.json`: 49 unit test và 10 worker security check đều đạt; không đại diện độ chính xác AI.

Từ thư mục ứng dụng `ScamShield_AI` bên trong repo; dùng đường dẫn output mới vì runner từ chối ghi đè:

```powershell
python -m unittest discover -s tests -q
node tests/worker_security.mjs
python mixed_check.py --mode mock --output reports/mixed_check_new/mock
python bench_mixed_mock.py --output reports/mixed_check_new/mock_benchmark.json
python mixed_check.py --mode hybrid --output reports/mixed_check_new/gemini --pause 3
```

Lệnh hybrid gọi API thật và tiêu thụ quota. Bộ mới đã dùng để phát hiện lỗi nên là regression
công khai cho những lần sửa tiếp theo, không dùng làm tập độc lập cuối cùng. Cần bộ độc lập khác
nếu chỉnh prompt/quy tắc/backend theo kết quả này rồi công bố số liệu chất lượng cuối.

Ưu tiên tiếp theo: làm ổn định đầu ra/định vị quote mà vẫn giữ kiểm chứng nghiêm ngặt,
sửa xử lý vai cảnh báo và bối cảnh bình thường, sửa bộ đếm âm; sau đó mới tối ưu latency
và kiểm thử web/extension nhiều mục bằng live. Không tự tăng timeout để che lỗi chất lượng.
