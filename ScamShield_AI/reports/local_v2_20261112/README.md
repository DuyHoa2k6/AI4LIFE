# Bàn giao dataset và suy luận cục bộ v2 — 12/11/2026

Đã triển khai dataset/schema/nhãn/rulebook/template/validator, pipeline Python và
giao diện thử **/local**, API **POST /api/analyze-local**. Nhánh này không gọi hai
lượt Gemini. /api/analyze, cấu hình provider và Chrome Extension cũ giữ nguyên để
đối chiếu, chưa chuyển toàn bộ sản phẩm sang bản cục bộ.

## Đầu ra bàn giao

- [Bộ tài liệu/dữ liệu v2](../../../data/v2/README.md): dataset card, annotation guide,
  từ điển nhãn, migration, kế hoạch chia tập/đánh giá, schema JSON từ Pydantic.
- [70 ca pilot](../../../data/v2/release_final/pilot.jsonl), 3 chuyển từ dev, 67 target
  nghiệm thu riêng; tất cả annotation chi tiết **weak_label**, chưa có hai người rà.
- 15 quy tắc suy luận có điều kiện/ngoại lệ/căn cứ và 18 luật trích an toàn. Mỗi
  rulebook rule đã có test_case_ids, không thực thi biểu thức tùy ý từ dữ liệu.
- 18 câu hỏi nội bộ giữ đủ, unknown khi thiếu. Quyết định risk_status tách khỏi
  safety_urgency; urgent precheck trả thông tin hỗ trợ trước parser đầy đủ/RAG.
- Template có kiểm soát, source gate approved, cộng đồng tách riêng. Danh bạ hỗ trợ
  vùng rỗng nên không tạo số điện thoại/URL; chưa có đối chiếu đối tượng verified.
- [Code/đặc tả backend và cách chạy](../../LOCAL_REASONING_V2.md).

## Kết quả kiểm thử

**271 unittest backend đạt**, bao gồm 26 bài mới cho v2. Kiểm thử điều kiện cần,
scope/người/thời gian, evidence giả, dữ liệu thiếu, bối cảnh chỉ áp đúng message,
urgent không chờ parser, lỗi không trả clear, cổng nguồn, chống biểu thức dữ liệu,
chia nhóm và OCR/bình luận khác vai. Các test provider cũ dùng transport giả lập.

**Validator: 70 ca hợp lệ, 0 lỗi**, 70 weak_label/pilot. Kiểm tra schema/ID/quote/
tham chiếu/scope/đầu mút/urgency, điều kiện rule trước kết luận, trùng input hiệu
dụng, test case của rule và rò scenario/variant/source qua split. Nguồn hiện có
5 candidate, **0 đủ điều kiện approved**. Xem [validator](dataset_validation.json).

Chạy thực qua ASGI TestClient và code Python cục bộ, lưu prediction trước target:

| Target phát triển | Kết quả tương ứng | Số ca |
|---|---|---:|
| clear | clear | 22 |
| need_context | need_context | 17 |
| suspicious | suspicious | 10 |
| high | high | 18 |

**67/67 target phát triển khớp**, ba input dev được ghi riêng. Trong 67 target,
11 urgent, 17 preventive, 39 undetermined đều khớp; không bỏ sót/nhầm urgent trong
bộ nghiệm thu này. High TP=18, FP=0, FN=0 trên target biên soạn. Các tỷ lệ này
**không phải accuracy độc lập**, không chứng minh 98%, vì các ca được dùng chỉnh
quy tắc và nhãn tham chiếu chưa được người độc lập rà.

- 70 request hoàn tất, **356/356 quote đúng offset**, không có lỗi tham chiếu được
  validator phát hiện, **0 provider calls / 0 request mạng**.
- 59 ca chạy full local, 11 ca trả từ urgent_precheck. Chưa đủ 18 trường không chặn
  hướng hỗ trợ khẩn; unknown được thống kê trong summary.
- API p50 **4,46 ms**, p95 **6,11 ms**, 70 lượt; lượt đầu 13,01 ms. Đây là ASGI
  cục bộ, không phải thời gian browser/extension, cold start/tải đồng thời có kiểm soát.
- Chưa đo semantic span/event/relation F1, actor/recipient P/R, mô hình đã huấn luyện,
  dữ liệu thật hoặc chất lượng RAG có tài liệu đã duyệt. Không chấm extractor bằng
  weak labels do chính nó sinh rồi gọi là accuracy.

[Dự đoán/quote/giải thích từng ca](delivery/CASES.md) · [JSON dự đoán](delivery/predictions.json) ·
[Matrix, đếm, unknown, thời gian](delivery/summary.json) · [Hash khóa](delivery/lock.json).

Chrome thật **10/10 kiểm tra đạt** trên giao diện mới: bốn trạng thái, urgent phía
trước câu hỏi, ẩn dữ liệu nội bộ, quote HTML là text, offline không xanh, payload
khẩn với lỗi 503 vẫn hiện hỗ trợ (lỗi mô phỏng), phản hồi cũ bị bỏ. Xem
[report](browser/report.json) và [ảnh urgent](browser/urgent.png). Lượt đầu test
harness có lỗi await ngoài async sau 8 kiểm tra; đã sửa harness và chạy lại đủ 10.
Không chạy lại Chrome Extension vì không sửa client đó trong nhánh v2.

## Dữ liệu, lỗi và giới hạn cần báo rõ

- **legacy-SS-001 hiện need_context**: điều kiện chuyển thêm để rút qua nhiều tin/
  đảo thứ tự chưa nối chắc. Không tính vào 67 target để che thành high đúng; mục này
  được đưa [hàng chờ rà](../../../data/v2/REVIEW_QUEUE.md). legacy-SS-002 clear,
  legacy-SS-003 need_context. Cả ba đã là dữ liệu phát triển cũ.
- Lỗi đầu tiên đã sửa: lời báo “tôi đang nợ … không được rời đi” chưa được gắn đúng
  self_report nên chỉ preventive; đã bổ sung attribution và test tương ứng.
- Lỗi validator đã sửa: cùng chữ OCR minh họa và bình luận độc lập bị coi trùng;
  duplicate check hiện xét source/parent/context, split planner vẫn gom chữ gần
  nhau cùng nhóm để không đưa biến thể sang train/test.
- Còn thiếu coreference/actor và quan hệ ngầm đáng tin. Relation luật inferred chỉ
  là nhãn yếu; chưa chứng minh vụ mua bán người/bắt giữ hoặc can thiệp nội tạng.
- Toàn bộ 70 ca cần người rà; **training export = 0**, status
  not_ready_no_reviewed_cases, chưa huấn luyện mô hình. File train/dev/test rỗng là
  kết quả cổng duyệt, không phải đã huấn luyện. [Trạng thái export](delivery/training_export/status.json).

Các thư mục api/final và các bản pilot nháp là lịch sử phát triển. **delivery** và
manifest → release_final/pilot.jsonl là bản bàn giao; không gộp các lượt để tăng cỡ mẫu.

## Lệnh chạy

Từ workspace gốc, khởi động lại backend:

```powershell
python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log
```

Mở http://127.0.0.1:8000/local hoặc /docs → POST /api/analyze-local. Không cần API key.
Từ thư mục ứng dụng có backend:

```powershell
python validate_v2_dataset.py --output reports/v2_validation_rerun.json
python -m unittest discover -s tests -p 'test_*.py' -q
python evaluate_local_v2.py --output reports/v2_evaluation_rerun
python prepare_v2_training.py --output reports/v2_training_rerun
node tests/browser_local_reasoning.mjs
```

Output đánh giá/export phải là thư mục mới. Đầu ra chỉ gửi input vào bộ phân tích;
annotations/expected không vào runtime. Không đọc hoặc sửa holdout/validation cũ.
