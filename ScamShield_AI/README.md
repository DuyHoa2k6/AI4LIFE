# ScamShield AI — phân tích tại backend

Thử nghiệm 0.9.0: [thu thập hội thoại đang hiển thị và xuất JSON/TXT](README_CONVERSATION_CAPTURE.md), chạy riêng trong extension, không gửi hội thoại tới backend. Đã kiểm chứng trên fixture chat; chưa xác nhận hỗ trợ Messenger/Zalo Web.

Mới nhất: [grounding 2.0 — đối tượng, phủ định, giao dịch, người và câu hỏi](GROUNDING_V2.md).
[Báo cáo trước/sau và phần chưa hỗ trợ](reports/grounding_v2_20261113/README.md)
tách riêng mức cảnh báo với độ đúng của dữ kiện.

Mới: [đồ thị sự kiện và cơ chế nguy cơ cục bộ](SEMANTIC_GRAPH.md), có trace phát
triển và [kiểm thử 10 ca + 42 đối chứng](reports/semantic_graph_20261113/README.md).

Bổ sung [dataset biến thể ngữ nghĩa](../data/v2/semantic_variants/README.md) và
bộ diễn giải tương ứng; xem [kết quả kiểm thử](reports/semantic_variants_20261113/README.md).

Cập nhật 13/11: thêm [phân tích cụm câu, vai trò và hành động chủ chốt](CLAUSE_ROLES.md),
cùng [bảng tám ca trước/sau](reports/clause_roles_20261113/CASES.md).
Mức 3–4 xét quan hệ giữa yêu cầu và bất lợi có thể xảy ra; danh tính chưa rõ
không tự tăng hoặc hạ cảnh báo. Luồng vẫn cục bộ, không thêm API mô hình.

**Đã quay lại bộ quyết định theo event/rulebook trước khi thử fact ba trạng thái.** Cấu hình hiện tại: `SCAMSHIELD_REASONER=legacy`. Giữ RAG, URL/redirect và bốn mức cảnh báo, không gọi Gemini. Nhánh fact chỉ giữ để đối chiếu, không dùng mặc định. Xem [xác minh khôi phục](reports/restore_event_flow_20261112/README.md).

Nhánh gọi Gemini và các mô hình bên ngoài đã được gỡ theo yêu cầu. Hiện chỉ hỗ trợ `local_rules` (phân tích BE) và `mock` (kiểm thử tích hợp). Không cần model hoặc API key. Cấu hình `live`, `hybrid`, `two_pass` trả lỗi `EXTERNAL_MODEL_REMOVED`, không tự chuyển sang một kết quả an toàn.

## Chạy hệ thống

Tại thư mục ứng dụng, nơi có `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
$env:SCAMSHIELD_MODE="local_rules"
$env:SCAMSHIELD_REASONER="legacy"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Mở http://127.0.0.1:8000. Extension: Chrome → chrome://extensions → bật Developer mode → Load unpacked → chọn thư mục `extension` chứa manifest.json. Khởi động lại backend sau khi cập nhật mã.

## Luồng hiện hành

`POST /api/analyze` → xác thực đầu vào → LocalRulesProvider → chuẩn hóa/viết tắt/chia đoạn → trích sự kiện và quan hệ → kiểm chứng đoạn trích → áp rulebook và ngoại lệ → **song song truy xuất nguồn đã duyệt + phân tích URL/redirect** → ghép dữ kiện có liên hệ → dựng giải thích → trả schema API chung. Cùng luồng bổ trợ được dùng bởi `/api/analyze-local`; `/api/observe` vẫn chỉ trích dữ kiện, không gọi mạng.

Ca có bằng chứng khẩn được xử lý ưu tiên. Nhánh thông thường có đối chiếu nguồn chính thống đủ điều kiện tại backend; hiện chưa có nguồn chính thống được duyệt. Không có Gemini lượt 1, lượt 2 hay bước gọi mô hình khi BE khó kết luận. Trường hợp thiếu dữ kiện có thể trả `need_context` và câu hỏi bổ sung.

- Quy tắc BE: `../data/v2/rulebook.json`, `../data/v2/extraction_rules.json`.
- Câu giải thích: `../data/v2/templates.json`.
- Viết tắt: `../data/abbreviations_vi.json`.
- `/api/observe`: xem cấu trúc trích xuất đầu tiên; `/api/analyze-local`: xem kết quả v2 đầy đủ; `/local`: giao diện xem BE.
- Giữ bốn mức `clear`, `need_context`, `suspicious`, `high`. Quy tắc có phạm vi giới hạn; chưa bảo đảm hiểu hành vi/cách diễn đạt mới.
- OCR chỉ chạy khi người dùng yêu cầu; cần cài công cụ OCR riêng theo hướng dẫn OCR.
- URL: phân tích tên miền và HTTP HEAD/redirect tối đa 3 liên kết, 3 lần chuyển hướng, ngân sách khoảng 6 giây/liên kết; chặn IP nội bộ và kiểm tra từng chặng. Có thể tắt mạng bằng `SCAMSHIELD_URL_NETWORK_ENABLED=0`; đối chiếu tên miền vẫn chạy. Máy chủ đích có thể ghi nhận yêu cầu HEAD.
- RAG: `SCAMSHIELD_RAG_ENABLED=1`, giới hạn tối đa 3 đoạn và `SCAMSHIELD_RETRIEVAL_TIMEOUT` (mặc định 0,8 giây, trần 2 giây). Chỉ nguồn đã duyệt có hành vi tương ứng mới bổ trợ giải thích. Kho thực hiện chưa có nguồn được duyệt; không tự nâng candidate.
- Quy tắc ghép dữ kiện và giới hạn: [LOCAL_SUPPORT.md](LOCAL_SUPPORT.md). Ví dụ kiểm thử: [báo cáo](reports/local_support_20261112/README.md).

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python check_local_switch.py --output reports/local_after_gemini_removal
```

Thư mục đầu ra phải mới. Các số liệu trong `reports/` là lịch sử, gắn với phiên bản đã đo, không mô tả luồng gọi mô hình hiện hành. Các bài kiểm thử chuyên biệt cho nhánh mô hình đã gỡ cùng nhánh đó; không tính chúng như các ca đã vượt qua của BE.
