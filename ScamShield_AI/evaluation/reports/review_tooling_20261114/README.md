# Bổ sung công cụ rà soát — 14/11/2026

Prompt đánh giá sau huấn luyện đã được thực hiện tại [20261114_rounds/final_report.md](../20261114_rounds/final_report.md). Đợt bổ sung này xử lý điều kiện còn thiếu để chuẩn bị fine-tune: nhận và quản lý bản gán nhãn của con người. Không chạy lại model hoặc báo tăng độ chính xác từ thay đổi công cụ.

## Đã làm và chạy thực tế

- `evaluation/review.py`: export chỉ đầu vào; submit với input hash/attestation; reconcile hai bản rà; approve sau quyết định của người phụ trách, xuất dataset mới kèm audit manifest. Không tự train, không lấy dự đoán làm nhãn.
- Không xuất family/template/source group có tên có thể tiết lộ nhãn. Dataset vẫn công khai, không được gọi là blind holdout.
- Chấp nhận bản rà partial chưa chọn mức cảnh báo, nhưng chặn xuất thành mẫu đã duyệt khi hai bản rà chưa đầy đủ. Quote/offset phải khớp Unicode code point.
- Chặn ghi đè gói, một reviewer nộp trùng ca, thay đổi hash đầu vào/dataset/bản ghi; so graph theo cấu trúc thay vì tên ID hoặc câu giải thích giống nguyên văn. Đồng thuận cấu trúc vẫn cần con người rà ngữ nghĩa.
- `evaluation/training.py` chặn dùng trực tiếp family còn mang split validation/locked làm train. Cần chuyển phiên bản có lịch sử và tập validation thay thế.
- Export thật 35 ca vào `evaluation/review_packs/public_20261114`; reconcile thật cho kết quả **35 needs_two_independent_reviews, 0 approved**. Chưa có submission hoặc resolution thật; không tạo file training đã duyệt giả.
- Hướng dẫn có lệnh thực tế: [REVIEW_WORKFLOW.md](../../REVIEW_WORKFLOW.md).

## Kiểm thử

`tests/test_review_workflow.py`: **26 passed**. Mô phỏng nhận bản rà, bất đồng, partial, ghi đè, hash sai, trích dẫn bịa, thiếu xác nhận và duyệt có điều kiện trong thư mục tạm. Reference `unit-fixture-*` chỉ là dữ liệu kiểm thử, không được tính là người rà thật.

Hồi quy Python đầy đủ: **358 passed, 1 warning in 32.63s**; log [tests.log](tests.log). Warning là deprecation của anyio/Starlette TestClient. Lần chạy sandbox ban đầu bị lỗi quyền thư mục tạm Windows; đã chạy lại với quyền thực thi phù hợp. Các test không chứng minh độ chính xác ngữ nghĩa ngoài thực tế. Không sửa frontend/extension và không đo lại browser trong đợt bổ sung.

## Bảo toàn dữ liệu và mô hình

SHA256 kiểm tra sau thay đổi:

- Dataset `evaluation/data/novel_cases.jsonl`: `a7c858a932555ff6ea1c8980756e980e7281de81ea0ca1d8297982016fbfed9a`, trùng hash nguồn gói review.
- `artifacts/phobert/smoke_heads/heads.pt` và bản rollback: cùng `72527397e1e914e9c67ef4441f3a2a5d4cab98bb2abc63f13b6519b383d7cff5`, trùng model manifest đã khóa.
- Không đổi trọng số, mapping, lựa chọn policy hoặc backend production mặc định.

Điểm thực nghiệm trước vẫn giữ nguyên: 51 ca/vòng (35 draft mới + 16 regression); Macro-F1 baseline 0.3087, candidate 0.2860; đúng mức kèm cấu trúc 9/51 cả hai; candidate bị từ chối. Đây là chẩn đoán trên draft công khai. Oracle graph tăng điểm chỉ phản ánh policy khi được cung cấp dữ kiện tham chiếu, không phải chất lượng end-to-end.

Chưa đủ 84 ca mục tiêu, chưa có hai người rà thật, chưa có fine-tune trên nhãn mới hoặc đánh giá holdout độc lập. Phần mềm ghi lời xác nhận và lịch sử; không thể tự xác minh hai reference thực sự là hai người đã làm độc lập. Đã có nhãn được duyệt cũng còn cần replay/validation và xử lý nhãn mới ngoài mapping trước khi huấn luyện.
