# Gỡ nhánh phân tích mô hình — 12/11/2026

## Thay đổi

- Xóa `backend/two_pass.py`, `backend/hybrid.py`, `backend/rule_hints.py`: bỏ điều phối hai lượt, ghép gợi ý quy tắc vào mô hình, rà lại mâu thuẫn và các quy tắc chuẩn bị gợi ý cho mô hình.
- Xóa bốn prompt runtime: `extraction_prompt.txt`, `hybrid_prompt.txt`, `observation_prompt.txt`, `review_prompt.txt`; xóa bản prompt snapshot trong báo cáo cũ.
- `providers.py` chỉ còn LocalRulesProvider và mock. Không còn client HTTP gọi mô hình, API authorization, model selection hay transport schema cho provider.
- `/api/analyze` bỏ các nhánh finalize/adjudicate cho mô hình; giữ phân tích BE và mock, kiểm tra đầu vào và gắn nguồn OCR. `/api/observe`, `/api/analyze-local` giữ nguyên.
- Mặc định `local_rules`. Giá trị cấu hình cũ `live`, `hybrid`, `two_pass` trả HTTP 503 `EXTERNAL_MODEL_REMOVED`; không gọi mạng và không tạo kết luận clear.
- Schema response chỉ công bố mode `mock`/`local_rules`; AnalysisTrace chỉ công bố pipeline/routing local và live_status not_used. Các trường dữ liệu cấu trúc dùng bởi BE vẫn giữ.
- Bỏ key, model, endpoint và cấu hình định dạng/retry mô hình khỏi file cấu hình riêng mà không in khóa ra log. Cập nhật cấu hình mẫu và README. Bộ đọc cấu hình vẫn chấp nhận tên khóa cũ để tương thích file cũ, nhưng không còn đường sử dụng chúng để gọi mô hình.
- Gỡ runner và bài kiểm thử dành riêng cho nhánh mô hình đã xóa; giữ các kiểm thử local, dữ liệu, OCR, URL offline, API và extension còn áp dụng. Các test cục bộ nay chặn HTTP trực tiếp thay vì patch lớp LiveProvider đã xóa. Browser harness tuần hai không còn khởi động fixture model.

Không đổi rulebook, extraction_rules, templates hoặc dataset. Không thêm khả năng suy luận mới; các hạn chế phân tích local trước đó vẫn tồn tại. Báo cáo số liệu và snapshot mã lịch sử trong reports giữ để truy vết, không được import bởi backend hiện hành. Các hướng dẫn nhiệm vụ gốc trong prompts không phải prompt gửi mô hình và vẫn giữ.

## Xác minh cuối

- `python -m unittest discover -s tests -v`: **144/144 pass**, xem `backend_tests.txt`. Số lượng này loại các bài kiểm thử dành riêng cho nhánh mô hình đã gỡ; không so sánh như cùng bộ 275 ca lịch sử.
- `python check_local_switch.py --output reports/gemini_removed_20261112/final_api`: **12/12** khớp tham chiếu phát triển, 0 HTTP mô hình, 0 request mạng async. Xem [dự đoán từng ca](final_api/predictions.json), [tổng hợp](final_api/summary.json).
- `node tests/worker_security.mjs`: **13 checks pass**.
- `node tests/popup_version.mjs`: **4 checks pass**.
- `node --check tests/browser_week2.mjs`: hợp lệ cú pháp. Chưa chạy lại Chrome toàn luồng trong lượt gỡ này.
- Rà backend runtime: không còn LiveProvider/HybridProvider/TwoPassProvider, tham chiếu prompt.txt hay nhánh gọi finalize/adjudicate.

Đây là kiểm thử hồi quy chức năng; không phải đánh giá độc lập độ chính xác hoặc đo lại độ trễ. Cần khởi động lại backend đang chạy để nạp mã mới. Hướng dẫn chạy: [README](../../README.md).
