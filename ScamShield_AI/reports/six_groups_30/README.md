# Kiểm thử 30 ca / 6 nhóm hành vi — 09/11/2026

Đã chạy một lượt phân tích cho mỗi ca trên cấu hình khóa; không sửa prompt/model/quy tắc trong phiên, không chọn lại dự đoán đẹp nhất. Sáu nhóm là nhóm hành vi, không phải sáu mức cảnh báo. verified_match chưa triển khai.

## Kết quả theo nhóm

| Nhóm | Dự kiến | Đã gửi | API thành công | Đúng trạng thái + quote | Lỗi | Chưa gửi | p50/p95 API (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Chuyển tiền | 5 | 5 | 4 | 2 | 1 | 0 | 16.82 / 31.85 |
| Giao mã/mật khẩu | 5 | 5 | 5 | 5 | 0 | 0 | 13.35 / 31.41 |
| Cấp quyền | 5 | 5 | 4 | 2 | 1 | 0 | 10.30 / 21.89 |
| Cài ứng dụng | 5 | 5 | 4 | 4 | 1 | 0 | 15.62 / 16.17 |
| Lời dụ/điều kiện | 5 | 5 | 4 | 4 | 1 | 0 | 6.85 / 17.48 |
| Hành vi khác | 5 | 5 | 4 | 3 | 1 | 0 | 13.81 / 23.67 |

Tổng: 30/30 ca gửi API, 25 thành công, 5 lỗi, 0 chưa gửi. Đúng trạng thái kỳ vọng kèm đối chiếu quote/speaker: 20/30 (66.7%). Không gọi tỷ lệ này là độ chính xác độc lập trên người dùng thật.

## Ma trận theo nhãn kỳ vọng

| Nhóm kỳ vọng | high | suspicious | need_context | clear | error | not_run |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| scam | 5 | 0 | 2 | 0 | 2 | 0 |
| suspicious | 0 | 1 | 0 | 0 | 2 | 0 |
| normal | 0 | 0 | 2 | 9 | 1 | 0 |
| uncertain | 0 | 1 | 5 | 0 | 0 | 0 |

High: TP=5, FP=0, FN tính cả lỗi/chưa gửi=4; precision=100.0%, recall toàn tập ca high=55.6%.
Cảnh báo high/suspicious nhầm trên normal: không ghi nhận.
Normal bị yêu cầu thêm bối cảnh: SG-13, SG-14.
Ca scam không nhận high: SG-31, SG-51, SG-61, SG-12.
Ca thiếu thông tin có API 200 nhưng không có câu hỏi: không ghi nhận.

Lỗi theo mã: `{"PROVIDER_UNAVAILABLE": 2, "PROVIDER_TIMEOUT": 2, "EVIDENCE_INVALID": 1}`. Bước lỗi: `{"observation": 1, "review": 3, "pipeline": 1}`.
Lỗi/chưa gửi không được tính là clear hoặc phân tích đúng. Không suy ra hết credit từ 503; diagnostic chỉ cho biết lỗi HTTP/network/timeout/schema và bước liên quan.

## Hiệu năng và số request

| Phép đo | Số lượt | p50 (s) | p95 (s) |
| --- | ---: | ---: | ---: |
| API gồm cả lỗi | 30 | 13.75 | 31.41 |
| API chỉ ca thành công | 25 | 13.35 | 25.11 |
| Các lượt sau lượt đầu, chưa chứng minh provider warm | 29 | 13.75 | 31.41 |

Lượt đầu: 16.82 s; tổng thời gian batch gồm nghỉ chủ động 3 s và I/O báo cáo: 537.18 s.
Provider có 63 attempt, kể cả retry/lỗi mạng. Các HTTP nhận được: `{"200": 55, "503": 6}`. Một request API có hai lượt logic; retry không phải thêm ca độc lập.

| Bước trên ca API thành công | n | p50 (s) | p95 (s) |
| --- | ---: | ---: | ---: |
| first_provider | 25 | 3.55 | 16.94 |
| retrieval_parallel | 25 | 0.00 | 0.01 |
| second_provider | 25 | 4.73 | 12.94 |
| verification_render | 25 | 0.00 | 0.00 |

Đo ASGI TestClient + HTTP Gemini thật, tuần tự đồng thời 1; không gồm mạng browser→API, thời gian chờ extension hoặc hiển thị. Provider time gồm truyền mạng, xử lý dịch vụ và parse; chưa tách được mạng khỏi model. p95 nearest-rank, n=5/nhóm rất nhỏ; không phải SLA. Không cộng các p95 bước thành p95 tổng. Mục tiêu p95 dưới 2 s vẫn cần đối chiếu số đo này, không dùng deadline thay mục tiêu.

Usage cộng từ phản hồi có usage: `{"prompt_tokens": 102040, "completion_tokens": 45279, "total_tokens": 147319}`. Lỗi/timeout có thể không báo usage; không suy ra hóa đơn hoặc xác nhận Free Tier.

## Bằng chứng và nguồn

Phản hồi cuối có 43/43 quote khớp theo code point. ID refs answers được đối chiếu với findings. Đây là kiểm tra máy móc, chưa chứng minh diễn giải/vai lời trích hoặc tám câu trả lời đúng đầy đủ.
Ca còn thiếu action kỳ vọng theo taxonomy: không ghi nhận trên ca có kết quả.
Nguồn thực sự trả: 0; trạng thái nhánh nguồn trên ca có phản hồi: `{"no_approved_sources": 25}`.
Kho nguồn còn candidate, không tự duyệt. Không có nguồn không nghĩa an toàn. Chưa đo chất lượng RAG trên tài liệu nhà nước thật đủ phê duyệt; ví dụ runtime không được tính như nguồn chính thống.

## Cấu hình và giới hạn

`{"model": "gemini-3.5-flash-lite", "mode": "two_pass", "timeout_s": "20", "total_timeout_s": "45", "retries": 1, "output_format": "auto", "inter_request_pause_s": 3.0, "service_error_limit": 30}`
Cấu hình riêng/key không được chép vào báo cáo. Prompt/code/kho/input/expected khóa theo hash trước khi gọi; lock đã được kiểm tra lại. Không đặt seed/temperature, dùng mặc định provider; chưa khóa được revision nội bộ dịch vụ. Mẫu gồm ca thay chữ/cách tiếp cận, bình thường, trích cảnh báo và thiếu thông tin; không gọi đây là phương thức lừa đảo hoàn toàn mới được phát hiện ngoài thực tế.
Input/expected tách file; runner chỉ gửi input, lưu dự đoán rồi mới đọc expected. Nhãn do người triển khai viết, chưa có hai người rà độc lập. Không đọc holdout hoặc đưa nhãn vào kho runtime. 30 ca không đủ để chứng minh mục tiêu trên 98%, ngay cả khi tất cả ca đúng. Không dùng các ca này như holdout nếu tiếp tục chỉnh theo lỗi.

## Bàn giao

[Rà nguyên nhân từng ca chưa đạt](MANUAL_REVIEW.md): phân biệt lỗi dịch vụ, quote bị viết sai,
khác biệt taxonomy giữa hai lượt và việc model đánh dấu quan hệ chưa rõ.

- [CASES.md](CASES.md): đủ 30 nội dung cụ thể, kỳ vọng/thực tế, bằng chứng, thời gian và câu hỏi.
- [cases.csv](cases.csv): bảng UTF-8 BOM để mở bằng Excel, gồm input JSON và lỗi từng ca.
- `live/predictions.json`: kết quả từng ca, đầu ra các lượt model hợp lệ và diagnostic.
- `live/lock.json`, `summary.json`, `case_results.json`: cấu hình/hash và số đo chi tiết.
- `../../fixtures/six_groups_30/`: input và reference judgments riêng.

Chạy từ thư mục ứng dụng, chọn output mới (không ghi đè):
```powershell
python mixed_check.py --mode two_pass --output reports/six_groups_30_new --fixtures-dir fixtures/six_groups_30 --pause 3 --service-error-limit 30
```
Lệnh gọi provider thật; tối đa 60 lượt logic, tối đa 120 attempt với cấu hình retry=1. Dừng ngay nếu HTTP 400/auth/model/quota; lỗi dịch vụ được thử qua tối đa 30 ca theo yêu cầu, không gọi lại ca đã chấm để chọn đáp án đúng. Cấu hình phân tích không thay đổi trong phiên này. 87 unit test đã đạt trước khi chạy, không dùng số test làm độ chính xác mô hình.
