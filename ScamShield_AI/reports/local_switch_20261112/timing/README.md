# Đo 12 câu qua backend local — 2026-11-12

Chế độ thực tế: `local_rules`. Đo 10 lượt/câu, tổng 120 HTTP POST tuần tự qua TCP localhost; dùng lại kết nối. Tính thời gian từ trước POST đến sau giải mã JSON. Không gọi Gemini (0 lần gọi provider, 0 request async ra ngoài).

- HTTP 200: 120/120; không ghi nhận lỗi.
- HTTP p50: 4.8731 ms; p95: 8.1271 ms; min/max: 2.9268/20.7478 ms.
- Engine p50: 3.1722 ms; p95: 6.3685 ms. Engine không gồm adapter, tuần tự hóa và HTTP.
- 12/12 ca giữ cùng mức rủi ro và mức khẩn qua 10 lượt, khớp tham chiếu phát triển. Đây không phải kiểm định chất lượng độc lập.
- Với 10 lượt/câu, p95 theo nearest rank bằng giá trị lớn nhất của câu đó. Lượt HTTP đầu tiên 20.7478 ms; chưa chứng minh cold start đầy đủ.

## Chi tiết và dữ liệu gốc

- [Câu, hành vi, quan hệ, quy tắc, câu hỏi và thời gian từng ca](DETAILS.md).
- [Đầu vào, phản hồi API và cấu trúc BE đầy đủ từng ca](predictions.json).
- [120 phép đo](measurements.json), [tổng hợp](summary.json), [hash cấu hình và mã nguồn](lock.json).

## Luồng xử lý và vị trí mã nguồn

1. `backend/main.py::analyze`: nhận `/api/analyze`; kiểm tra nguồn OCR nếu có.
2. `backend/schemas.py::AnalyzeRequest`: xác thực text/messages, ID và giới hạn đầu vào.
3. `backend/providers.py::get_provider`: chọn LocalRulesProvider theo cấu hình đang có.
4. `backend/local_reasoning/adapter.py::LocalRulesProvider.extract`: đổi request sang CaseInput, giữ ID/người nói/văn bản/bối cảnh.
5. `backend/local_reasoning/engine.py::analyze_local`: nạp quy tắc/template, chạy kiểm tra an toàn ban đầu. Tín hiệu khẩn hợp lệ đi đường urgent_precheck; các ca khác đi full_local.
6. `backend/local_reasoning/extract.py`: trích hành vi, vai trò, trạng thái và quan hệ; tái sử dụng `backend/local_observation/analyzer.py`, `text.py`, `abbreviations.py`, `segmentation.py` để chuẩn hóa, phân giải viết tắt, chia đoạn và nhận diện hành động. `data/abbreviations_vi.json` là từ điển viết tắt.
7. `backend/local_reasoning/validation.py`: kiểm tra tham chiếu và đoạn trích trên văn bản gốc. `engine.py::apply_rules` áp điều kiện/ngoại lệ trong `data/v2/rulebook.json`, dùng `data/v2/templates.json` dựng nội dung. Trích an toàn dùng `data/v2/extraction_rules.json`.
8. Với nhánh không khẩn, `backend/retrieval.py` tìm nguồn chính thống đủ điều kiện. Hiện chưa có nguồn được duyệt; phép đo này không đánh giá RAG có tài liệu thực.
9. `adapter.py::to_public`: chuyển kết quả v2 sang schema API chung, trả HTTP JSON. Không có Gemini lượt 1/lượt 2 trong chế độ này.

## Giới hạn quan trọng

P08 “Mây bay trên núi.” trả need_context do ngoài phạm vi quy tắc; không có hành vi đáng ngờ được trích. Đây là hạn chế độ bao phủ, không phải phát hiện lừa đảo. Một số căn cứ hành vi trong graph chỉ là động từ ngắn; xem spans và quan hệ trong JSON, không coi mọi nhãn đúng là bằng chứng đã đầy đủ ngữ nghĩa.

Chưa đo thời gian từ thao tác trên website/extension, mạng Internet, tải đồng thời, cold/warm được kiểm soát hoặc chất lượng trên dữ liệu thực. Chế độ local hiện không thực hiện kiểm tra mạng URL/redirect. Không dùng số liệu này để tuyên bố độ chính xác 98%.

## Chạy lại

Từ thư mục ứng dụng `ScamShield_AI`:

```powershell
python benchmark_local_switch.py --rounds 10 --output reports/local_switch_timing_rerun
```

Dùng thư mục đầu ra mới. Script ghi dự đoán trước khi đọc tham chiếu kỳ vọng và tự dừng server đo khi hoàn tất.
