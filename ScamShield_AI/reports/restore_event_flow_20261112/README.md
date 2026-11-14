# Khôi phục luồng event/rulebook + RAG/URL — 12/11/2026

Theo yêu cầu, ngừng dùng bộ fact ba trạng thái làm mặc định và quay lại luồng trước thử nghiệm này. Không xóa dữ liệu/nhãn hay số đo cũ, không khôi phục Gemini.

Luồng hiện hành:

```text
Văn bản / OCR được người dùng yêu cầu
  → bộ bóc tách Python
  → kiểm chứng event, relation và evidence
  → rulebook gốc + ngoại lệ
  → RAG và URL/redirect song song nếu phù hợp
  → ghép bằng chứng hỗ trợ
  → clear / need_context / suspicious / high
```

## Cấu hình và thay đổi

- `engine.py` mặc định chọn legacy; `legacy_engine.py` được dùng cho quyết định theo event gốc.
- Cấu hình riêng backend và các cấu hình mẫu đặt `SCAMSHIELD_REASONER=legacy`. Không in key hoặc các giá trị riêng khác.
- Giữ bộ fact trong repo chỉ để đối chiếu; không tạo fact_trace trong luồng hiện tại. Các schema tùy chọn và dữ liệu thử nghiệm giữ tương thích.
- Giữ RAG, URL/redirect, bỏ kiểm tra URL khi không có link, các cơ chế phiên và phản hồi cũ, bốn mức và nhánh khẩn.
- Cập nhật README, hướng dẫn dữ liệu và API để không tiếp tục khuyên dùng facts mặc định.

## Xác minh

- Cấu hình hiệu lực: legacy; engine legacy-event-rules; fact_trace=null; decision_version local-rules-2.1-support. [Kết quả](active_pipeline.json).
- **12/12 ca phát triển** khớp risk/urgency tham chiếu qua API chính: [tổng hợp](api/summary.json), [dự đoán](api/predictions.json).
- 10 ca văn bản/RAG/URL trả HTTP 200: [bảng](support/CASES.md). Nguồn approved và redirect trong runner là fixture đã ghi rõ, không phải duyệt nguồn thật.
- **180/180 backend tests pass**, bao gồm kiểm thử legacy hoạt động và kiểm thử nhánh fact được bật tường minh để bảo toàn bản đối chiếu: [log](backend_tests.txt).
- Worker security 14 checks pass, popup version 4 checks pass.
- Smoke URL yêu cầu đăng nhập + tên miền gần giống vẫn trả suspicious và used_url_evidence=1; không coi đó là kiểm định danh tiếng website.

Khôi phục luồng không phải sửa hai lỗi đã phát hiện ở câu giao điện thoại và nộp tiền bảo chứng. Chưa có bằng chứng cải thiện chất lượng của hai ca đó sau khôi phục. Kho thật vẫn chưa có nguồn chính thống được duyệt.

## Chạy

Tắt backend cũ bằng Ctrl+C, sau đó từ thư mục ứng dụng:

```powershell
$env:SCAMSHIELD_MODE="local_rules"
$env:SCAMSHIELD_REASONER="legacy"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Nếu PowerShell trước đó đã đặt SCAMSHIELD_REASONER=facts, phải thay bằng legacy như trên vì biến môi trường ưu tiên hơn cấu hình file. Tải lại extension và trang đang quét sau khi khởi động lại backend.
