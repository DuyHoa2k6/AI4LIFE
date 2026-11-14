# Phân tích cụm câu, vai trò và hành động chủ chốt — 13/11/2026

Bản thử cục bộ bằng Python, tiếp tục nhánh `SCAMSHIELD_REASONER=legacy` và
`SCAMSHIELD_CONTEXT_ENABLED=1`. Không thêm công cụ/mô hình bên ngoài, không huấn
luyện từ dataset. Nhánh `facts` vẫn không dùng mặc định.

## Luồng hiện hành

1. Giữ nguyên text/messages, Unicode offset và thứ tự đầu vào.
2. `segmentation.py` tạo cụm có ranh giới và bối cảnh; `interaction.py` trích
   khung yêu cầu/điều kiện/quyền lợi, không chỉ lấy động từ.
3. `clause_context.py:extend_clause_context` bổ sung yêu cầu nói lược về chuyển
   tiền, đổi tài khoản, trì hoãn xác minh, di chuyển, bỏ qua hợp đồng, giữ bí mật,
   giữ giấy tờ và cập nhật thanh toán có căn cứ.
4. Kiểm chứng quote/offset/ID. Chỉ dựng quan hệ đúng phạm vi, nguồn lời nói,
   vai trò bị tác động và các đầu mút còn hiệu lực.
5. `situation.py` dựng hành vi, tình huống, giả thuyết, hậu quả.
6. `add_role_and_salience` ghi `clause_roles` và `salient_actions` trong
   `interpretation` của `/api/analyze-local`.
7. Áp rulebook hiện hành và `assess_contextual_choices`, giữ cảnh báo mạnh hơn
   đã có bằng chứng. Tầng mới không hạ high hoặc tín hiệu khẩn.
8. RAG/URL tiếp tục bổ trợ. `/api/analyze` giữ schema công khai; không đưa các
   trường diễn giải nội bộ mới vào khối kết quả người dùng.

## Vai trò khi chưa biết danh tính

| Trường | Cách hiểu |
|---|---|
| requester_id | Nguồn đưa ra yêu cầu, có thể chỉ là speaker hoặc nhãn Người gửi. |
| performer_id | Vai trò được yêu cầu thực hiện; `recipient:unknown` không phải tên thật. |
| affected_party_id | Vai trò chịu tác động khi có căn cứ; không mặc định mọi người là nạn nhân. |
| affected_status | `textual_role` nếu xác định được vai trò từ yêu cầu; `unknown` nếu chưa xác định. |
| unresolved_roles | Giữ `real_identity`; thêm `affected_party` nếu chưa biết ai bị tác động. |
| role_labels | Mô tả vai trò, không tự điền tên hoặc quan hệ gia đình. |

Ví dụ giao giấy tờ có ba vai: bên yêu cầu, người giao và bên đón giữ. Bên giữ
được gán `custodian:unknown:<scope>`; chưa biết tên không làm mất dấu hiệu giữ
giấy tờ. Đây vẫn là vai trò trong văn bản, không phải xác minh người thật.
Nếu không xác định được vai trò bị tác động, không dùng suy đoán đó để kích
hoạt luật mức 3–4. Danh tính chưa rõ đơn lẻ không phải căn cứ tăng mức.

## Hành động chủ chốt

`salient_actions` có event/quan hệ hỗ trợ, hậu quả có thể xảy ra, lý do chọn và
`is_primary`. Một hành động chính trên mỗi scope. Quan hệ hạn chế quyền chủ
động/giữ giấy tờ được ưu tiên hơn chi tiết thúc giục phụ trợ. Nộp thêm để nhận
lại tiền khác với chuyển tiền đơn lẻ. Giao tài sản trước thanh toán khác với
giao sau khi người liên quan đã báo nhận đủ.

Nếu chưa có quan hệ, có thể chọn yêu cầu tác động trực tiếp làm điểm cần rà,
nhưng **chọn hành động chính không tự tạo kết luận nguy hiểm**. Không cộng số
từ khóa hoặc số lần lặp động từ. Thứ tự chọn hiện là chính sách theo loại hậu
quả, chưa phải khả năng so sánh ngữ nghĩa tổng quát mọi hành động.

## Mức 3–4 và lựa chọn bất lợi

Mức 1 `clear`, mức 2 `need_context`, mức 3 `suspicious`, mức 4 `high`.
Mức nguy cơ và `safety_urgency` độc lập; kế hoạch chưa diễn ra không tự là khẩn.

| Luật | Điều kiện bắt buộc | Mức |
|---|---|---|
| R-CLAUSE-PAYMENT-VERIFY | Chuyển tiền + tài khoản đổi/khác tên + trì hoãn xác minh; hai quan hệ gắn cùng yêu cầu, nguồn và scope | 3 |
| R-CLAUSE-TRAVEL-CUSTODY | Đi gặp tuyển dụng + giấu gia đình + giao giấy tờ cho bên đón giữ, các quan hệ gắn cùng chuyến đi | 3 |
| R-CLAUSE-TRAVEL-CONTROL | Tất cả điều kiện trên + đi trước khi xem hợp đồng | 4 |

Mức 4 cảnh báo lựa chọn có thể khiến người dùng mất quyền chủ động và tìm hỗ
trợ, không phải đợi thiệt hại xảy ra. Không suy ra đã mua bán người, bắt giữ
hoặc cưỡng ép. Không dùng lời trích cảnh báo, phủ định, giả định hoặc nguồn bị
loại. Giữ hộ có quyền lấy lại hoặc chỉ đi gặp tuyển dụng chưa đủ kích hoạt tổ
hợp mức 4 này. Các luật an toàn hiện hành vẫn chạy độc lập.

## Cập nhật theo thời gian

“Lúc sáng chưa thấy tiền” → “vừa kiểm tra lại, đã vào đủ” của **cùng người bán**,
cùng giao dịch tạo `state_update`; giữ bằng chứng cũ để rà, không xóa lịch sử.
Xác nhận mới có thể hỗ trợ `clear` cho yêu cầu giao hàng sau đó. Lời người mua
không thay lời người bán; đơn A không cập nhật đơn B. Xuất hiện sau trong văn
bản đơn lẻ không đủ thay thế mọi lời khai trước.

Hiện hỗ trợ mẫu cập nhật tường minh và nhãn người nói thông dụng trong cùng
message. Cập nhật tự nhiên qua nhiều message, tên riêng, đại từ mơ hồ, giao
dịch không có mã, câu thiếu dấu ngắt hoặc cách nói ngoài mẫu vẫn cần kiểm thử
thêm. Khi chưa chứng minh được liên hệ, giữ `need_context`.

## Chạy thử

Khởi động lại backend từ thư mục bất kỳ:

```powershell
$env:SCAMSHIELD_MODE="local_rules"
$env:SCAMSHIELD_REASONER="legacy"
$env:SCAMSHIELD_CONTEXT_ENABLED="1"
python -m uvicorn backend.main:app --app-dir "C:\AI4Life\AI4LIFE\ScamShield_AI\ScamShield_AI" --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000`. `/docs` → `/api/analyze-local` để xem vai trò và
hành động chính; đầu vào mẫu:

```json
{"messages":[{"id":"m1","scope_id":"case","text":"Nội dung cần kiểm tra"}]}
```

Không cần API key. `/api/analyze` vẫn dành cho website/extension. Từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests -q
python check_clause_roles.py
python evaluate_local_pipeline.py --output reports/clause_roles_20261113/regression31_new
```

`SCAMSHIELD_CONTEXT_ENABLED=0` tắt toàn bộ lớp ngữ cảnh để so với event cũ, không
chỉ tắt riêng thay đổi hôm nay.

Xem [tám ca trước/sau](reports/clause_roles_20261113/CASES.md) và
[báo cáo](reports/clause_roles_20261113/README.md). Đây là ca phát triển đã biết,
không chứng minh độ chính xác độc lập hoặc mục tiêu 98%. Không chỉnh holdout.
Chưa kiểm thử lại toàn bộ thao tác trình duyệt trong lần sửa này. Chưa đề xuất
công cụ mới để bạn chạy thử ý tưởng trước.
