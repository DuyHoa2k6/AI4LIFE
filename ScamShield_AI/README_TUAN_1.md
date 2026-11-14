# ScamShield AI — backend tuần 1

Luồng hiện hành: [TWO_PASS.md](TWO_PASS.md), response 1.2/mode two_pass, hai lần gọi Gemini với hai nhánh đối chiếu song song giữa hai lượt. Mock/live/hybrid giữ để đối chứng; phần tuần 1 dưới đây là snapshot lịch sử, kết quả mới ở reports/two_pass.

**Cập nhật hiện hành:** mock đã nâng lên `mock-behavior-2.0.0`; xem [MOCK_RULES.md](MOCK_RULES.md) cho registry, liên kết bằng chứng, kiểm thử và giới hạn mới. Báo cáo `reports/week1` và các số liệu 11/12 bên dưới là snapshot tuần 1 trước nâng cấp; kết quả phát triển hiện tại lưu riêng tại `reports/mock_v2`. Adapter live vẫn chưa được xác minh với mô hình thật.

API văn bản FastAPI dùng chung cho web/extension tại `POST /api/analyze`. Có schema OpenAPI, mock xác định, adapter live, kiểm chứng câu trích và bảng quyết định ở backend. Website/extension thuộc tuần 2.

## Chạy từ thư mục gốc repo

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r ScamShield_AI/requirements.txt
.\.venv\Scripts\python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log
```

Mở `http://127.0.0.1:8000/docs` để gửi thử hoặc dùng PowerShell:

```powershell
$payload = @{ text = 'Ứng tiền để nhận hoa hồng.' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/analyze -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($payload))
```

Mặc định mock, không gửi dữ liệu ra ngoài. `.env.example` là danh sách biến mẫu, ứng dụng đọc biến môi trường, không tự nạp file .env. Để chạy live, đặt biến trong terminal chạy backend:

```powershell
$env:SCAMSHIELD_MODE = 'live'
$env:SCAMSHIELD_PROVIDER_URL = '<URL HTTPS đầy đủ tới endpoint chat completions>'
$env:SCAMSHIELD_MODEL = '<tên model của dịch vụ>'
$env:SCAMSHIELD_API_KEY = '<khóa chỉ lưu tại backend>'
$env:SCAMSHIELD_TIMEOUT = '20'
```

Adapter dùng HTTP chat-completions-compatible: gửi model/messages/response_format=json_object; đọc choices[0].message.content và kiểm tra theo Extraction schema. Có thể dùng dịch vụ cục bộ tại localhost. Không có cấu hình model mặc định hoặc tự hạ từ live xuống mock. Dịch vụ không hỗ trợ giao thức này cần adapter riêng. Mỗi lần gửi live có thể phát sinh phí và chuyển nội dung tới provider đã cấu hình. Không đưa dữ liệu bí mật vào ca thử.

## Kiểm thử và tạo lại hồ sơ

```powershell
python data/validate_dataset.py
$env:PYTHONPATH = 'ScamShield_AI'
python -m unittest discover -s ScamShield_AI/tests -v
python ScamShield_AI/week1_artifacts.py
```

Dùng Python trong .venv thay `python` nếu đã tạo môi trường. Môi trường triển khai đã có đúng phiên bản dependency nên kiểm thử bằng Python 3.12.5 đang cài; lệnh cài mới từ mạng chưa được chạy. Script artifacts ghi đè báo cáo tuần 1, chỉ dùng dev để dự đoán; không gọi mô hình với validation/holdout. Nếu cấu hình live đầy đủ, script thử một đầu vào tổng hợp tiếng Việt qua adapter thật. Bản hiện tại ghi `attempted=false` do chưa cấu hình.

Ba fixture ở `fixtures/inputs.json`, đáp án tách tại `fixtures/expected.json`: SS-001 dẫn dụ nhiều bước; SS-002 bài cảnh báo trích lời dụ; SS-003 thiếu bối cảnh. `reports/week1/dev_predictions.json` lưu response thật từ TestClient của API; `timeout_example.json` là lỗi timeout chủ động giả lập. OpenAPI ở `/openapi.json` và bản xuất trong báo cáo là schema chuẩn cho client.

## Kết quả và cổng W1-01–05

| Mã | Đã làm và bằng chứng | Phần còn thiếu |
| --- | --- | --- |
| W1-01 | `data/validate_dataset.py`; audit 36 mẫu/13 họ, 12 mỗi tập; schema/quote/tách họ/trùng chuẩn hóa qua; ba fixture tách nhãn; requirements | Hai người rà nhãn; trùng ngữ nghĩa; cách ly vật lý holdout |
| W1-02 | Pydantic strict; endpoint text/messages; giới hạn và lỗi; mock/live; OpenAPI; API-01–03 qua kiểm thử | Lượt live thật chưa chạy |
| W1-03 | Prompt tám câu hỏi; xác nhận speaker, ID, quote, offset code point; xử lý câu lặp; loại finding sai và dựng lại giải thích | Không chứng minh tự động vai trò lời trích đúng về ngữ nghĩa khi live; cần rà bằng mô hình thật |
| W1-04 | Backend gán risk; nguồn rỗng; không verified_match; tối đa 2 câu hỏi; câu hỏi riêng trả theo finding hợp lệ; ba fixture và biến thể qua mock | Chất lượng suy luận live và trả lời câu hỏi riêng theo ngữ nghĩa chưa đo |
| W1-05 | Năm seed và năm đoạn nguồn đã đăng ký, đều candidate; người duyệt null; không đưa vào chỉ mục | Duyệt nguồn/hiệu lực/quyền dùng; RAG chưa tích hợp |

Xem log `reports/week1/tests.txt`, audit/hash, dự đoán từng ca, manifest nguồn và live_smoke. Baseline từ khóa tuần 3 giữ ở tools.py/config.json, tách biệt mock API. Không sửa baseline hoặc dùng validation để chỉnh backend trong tuần này.

Mock khớp nhãn 11/12 ca dev; SS-007 kỳ vọng high nhưng trả suspicious vì chưa nhận ra điều kiện nhận quà là dấu hiệu dẫn dụ. Giữ lỗi này trong báo cáo, không gọi tỷ lệ dev là độ chính xác độc lập. Ba ca fixture đạt mức kỳ vọng high/clear/need_context. Mười kiểm thử tự động đều qua. Các ca dev chạy bằng TestClient ASGI trong tiến trình. Ngoài ra đã khởi động uvicorn và gửi fixture SS-001 qua HTTP loopback thật: 200/high/mock, lưu `reports/week1/http_smoke.json`. Chưa đo trình duyệt hoặc mạng bên ngoài.

Giới hạn đã biết: mock dùng quy tắc từ ngữ, có thể phân loại sai câu nhiều vai hoặc diễn đạt mới; bước kiểm chứng chuỗi không chứng minh đúng ngữ nghĩa hành động. Tám answers từ provider được kiểm tra cấu trúc, nhưng đầu ra công khai được dựng lại bằng mẫu và giữ unknown cho phần không kiểm chứng được. Đặc biệt danh tính, mạo danh, chuỗi và nội dung tự nhận chưa được diễn giải chi tiết. `answer_to_user` hiện tóm tắt hành vi/rủi ro, chưa trả lời linh hoạt mọi câu hỏi. Không có RAG, truy cập URL đầu vào, danh sách chặn, lưu hội thoại, OCR hoặc rate limiter. Origin mặc định localhost:5173; đổi qua SCAMSHIELD_ALLOWED_ORIGINS. Chỉ dùng local khi chưa bổ sung xác thực/rate limit cho public deployment.

Holdout: audit đọc bằng chương trình xác thực cố định và chỉ xuất số mẫu/họ/hash, không hiển thị hội thoại hoặc nhãn holdout. Nội dung holdout không đưa vào provider, prompt, fixture hay chỉ mục. File vẫn nằm trong workspace ban đầu; chưa thể tuyên bố đã cách ly ngoài môi trường phát triển. Người giữ dữ liệu cần giữ tập cuối độc lập ngoài workspace. Không tự di chuyển file ra ngoài vùng ghi được cấp quyền.

**Cổng tuần 1: tích hợp mock đạt ba ca chuẩn, kiểm chứng và xử lý lỗi; nghiệm thu live còn mở.** Bước tiếp theo là cấu hình provider, chạy live_smoke rồi rà thủ công hành vi/người nói trên dev; tiếp tục W2-01 cho website. Chưa đủ điều kiện tích hợp RAG theo W3-01.

## Chuẩn bị nguồn

Đã mở và đối chiếu cấu trúc bài [Cổng Thông tin điện tử Bộ Công an](https://www.bocongan.gov.vn/bai-viet/nang-cao-canh-giac-truoc-25-kich-ban-lua-dao-tren-khong-gian-mang-nam-2026-1788865614) ngày 08/11/2026. Bài có năm nhóm hành vi; knowledge_sources.jsonl chỉ lưu diễn giải ngắn và vị trí nhóm, không dùng như bản ghi xác minh đối tượng. Đây là rà kỹ thuật của người triển khai, chưa phải phê duyệt của người phụ trách. Seed thiếu URL vẫn giữ thiếu; không gán nguồn mới để tạo cảm giác đã xác minh.

Đề xuất bổ sung 04 khi bắt đầu RAG (chưa áp vào runtime): retrieval_status=disabled/used/no_match/timeout/error; fallback_reason; source_id/version/url/publisher/section/quote/approved_at/valid_until và used_finding_ids. Backend chỉ xuất đoạn thực sự dùng, từ chỉ mục approved; không nâng đối tượng tương tự thành verified_match. Chạy RAG-01–07 theo 06 khi tích hợp, gồm candidate/hết hiệu lực/không phù hợp/timeout/chỉ thị nhúng/nguồn bịa; RAG-06 chỉ khi có đối chiếu URL cụ thể.

Tham khảo triển khai schema và lỗi: [FastAPI](https://fastapi.tiangolo.com/tutorial/handling-errors/) và [Pydantic strict mode](https://pydantic.dev/docs/validation/2.12/concepts/strict_mode/).
