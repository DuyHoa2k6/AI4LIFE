# Kiểm chứng ngữ nghĩa trước suy luận — grounding 2.0

Cập nhật 13/11/2026, luồng mặc định `local_rules/legacy`, context và graph bật.
Python cục bộ, không API mô hình, bitmask, trọng số hoặc huấn luyện mới.
Tài liệu này thay phần gán vai/đối tượng cũ trong CLAUSE_ROLES/SEMANTIC_GRAPH.

## Luồng và file chịu trách nhiệm

1. `local_observation/segmentation.py`: cụm câu và offset gốc.
2. `local_observation/syntax.py`: đối tượng ngay sau động từ, phạm vi lời nói,
   mã giao dịch tường minh cả trước và sau động từ.
3. `local_observation/analyzer.py`: không tạo nhận tiền từ phụ lục, hướng dẫn
   hoặc cụm danh từ “tài khoản nhận tiền”; giữ khác biệt lời báo/phủ định.
4. `local_reasoning/extract.py`, interaction, semantic_graph: trích và tạo ứng viên.
5. `local_reasoning/grounding.py`: kiểm chứng chéo các bộ trích, sửa thuộc tính,
   gán giao dịch/vai, loại dữ kiện sai và phụ thuộc, hợp nhất bản sao, tạo quan
   hệ có căn cứ, chọn câu hỏi, dựng lại 18 trường từ dữ kiện còn hiệu lực.
6. `fact_validation.py`/`validation.py`: kiểm ID, span, scope, người, mention,
   phủ định và tham chiếu hậu quả.
7. situation/rulebook/semantic_graph: đánh giá từ sự kiện và quan hệ hợp lệ.
8. adapter/support: API chung, nguồn/URL bổ trợ theo cấu hình hiện hành.

Không có nhánh khớp nguyên văn hoặc mã của 24 ca kiểm thử trong runtime.

## Năm nhóm sửa

### Động từ và đối tượng

“Nhận phụ lục” → receive_document; “nhận đủ tiền” → receive_funds. “Gửi hướng
dẫn đăng nhập” → send_document, không login hoặc giao credentials. Đối tượng
chưa rõ giữ action tổng quát/object unknown, không mặc định tiền.

Chặn “ứng” trong “ứng dụng” thành hành động ứng tiền, “nhận” trong danh từ
“tài khoản nhận tiền” thành sự kiện nhận. Chặn “dụng” bị bỏ dấu thành “đừng”.
Đây là sửa cấu trúc và ánh xạ về nguyên văn, không tăng danh sách từ rủi ro.

Hợp nhất các bộ trích khi cùng vị trí hành động, loại, vai, polarity và giao
dịch. Remap ID và quan hệ, không cộng số bản sao thành bằng chứng mạnh hơn.
Hai hành động khác đối tượng như giao giấy tờ và giao credentials vẫn riêng.

### Phủ định, điều kiện và lời nói

| Cấu trúc | Biểu diễn |
|---|---|
| Đừng gửi mã | denial/prohibition, negative |
| Tôi chưa gửi mã | claim/report, negative, pending |
| Không cần nộp thêm | phủ định sự cần thiết, không phải yêu cầu nộp |
| Tôi không yêu cầu bạn gửi mã | phủ định yêu cầu, không tạo request đang có hiệu lực |
| Nếu không nộp thì mất khoản cũ | antecedent negative; consequence riêng, modality threat/hypothetical, có quan hệ |
| Họ dọa: nếu không nộp thì mất tiền | speaker là người kể, requester/actor bên được thuật lại, không gán người kể là bên đe dọa |

`Event.semantic` có speech_act, condition, consequence_refs. Không phủ định
toàn câu chỉ vì có “không”; không để phủ định lan qua “thì”. Điều kiện về
chi phí để được về liên kết giấy tờ/hạn chế rời đi khi có bối cảnh; đứng riêng
không chứng minh đã giam giữ. Lời cảnh báo/trích dẫn vẫn không là request thật.

### Giao dịch và trạng thái

Nhận “đơn A” cả trong đối tượng sau động từ. Giao A dùng thanh toán A, không
lấy trạng thái B. Giữ lịch sử, nguồn và state_update cũ khi đúng phạm vi.
“Giữ lại đơn B chưa trả” khác yêu cầu giao B trước thanh toán.

Tham chiếu chưa rõ như “khoản kia”/“đơn này” không tự tạo cùng giao dịch.
Trường transaction_reference/transaction_binding nói rõ binding có mã hay
chưa giải quyết. Chưa xử lý tổng quát mọi đại từ hoặc mã đơn bị lược.

### Người và lần nhắc

`annotations.mentions`: mỗi lần nhắc có mention_id riêng, span, scope,
participant_id nếu giải được và candidate_ids nếu mơ hồ. Một tiền ngữ Nam có
thể nối “anh ấy”; Nam và Bình cùng phù hợp thì giữ unresolved. Hai người không
tên được nhắc riêng không trở thành một người chỉ vì chưa biết danh tính.

Sau hòa giải, sự kiện/frames/clause_roles/salient_actions dùng binding người
thực tế hoặc vai được neo trong cuộc hội thoại, không dùng `recipient:unknown`
làm khóa chung. Các extractor cũ vẫn có placeholder tạm thời trước bước này;
nó không được dùng làm chứng minh cùng người tại quyết định cuối. Identity
status vẫn unknown/claimed/user_reported, không tự system-verified.

ID mention/name/role sinh cục bộ mỗi lần phân tích. Không dùng các ID này để
theo dõi hay gộp người qua hai request. Phiên bổ sung vẫn dùng case_id/revision
riêng theo hợp đồng API; IDs sự kiện/mention không phải định danh con người.

### Câu hỏi và trạng thái xử lý

`grounding_trace.field_needs` ghi field đã biết/đã trả lời, scope và bằng chứng;
question_bindings ghi field còn thiếu. Chỉ hỏi mục đích nếu chưa có; mục đích
đã rõ có thể hỏi bên thụ hưởng. Không dựng giả thuyết rút tiền cho mọi khoản
chuyển. Không hỏi nhận tiền A chưa khi câu đã báo nhận A và yêu cầu giao A.

Sentinel coverage phát hiện một số dữ kiện tường minh bị mất, như báo nhận đủ
tiền hoặc nhận phụ lục. Khi sentinel bắt lỗi: partial, không hỏi lại dữ kiện
đã có; vẫn giữ high nếu có bằng chứng độc lập khác. Lỗi module trả error/503;
ngoài khả năng nhận diện trả unsupported và mô tả giới hạn của BE, không tự
clear. Sentinel có giới hạn, không phát hiện được mọi lỗi hiểu nghĩa.

## Kiểm chứng giải thích

Sự kiện bị loại → quan hệ phụ thuộc bị loại → không tham gia đánh giá. Các
view 18 trường được dựng lại từ IDs/span còn hiệu lực; frame điều kiện bị bỏ
nếu quan hệ hỗ trợ không còn. Một câu trả lời đúng mức nhưng sai đối tượng,
vai, scope hoặc câu hỏi vẫn thất bại ở tầng tương ứng.

Trace phát triển: `annotations.grounding_trace` và graph_trace ở
`/api/analyze-local`. Không thêm trace này vào UI công khai hoặc ghi toàn văn
nhạy cảm vào log. Báo cáo lưu các input tổng hợp được chủ động kiểm thử.

## Chạy và phạm vi nghiệm thu

```powershell
python -m unittest discover -s tests -q
python check_grounding.py --output reports/grounding_repeat
python score_grounding.py reports/grounding_repeat
```

Từ thư mục ứng dụng, hoặc khởi động backend từ bất kỳ đâu:

```powershell
$env:SCAMSHIELD_MODE="local_rules"
$env:SCAMSHIELD_REASONER="legacy"
$env:SCAMSHIELD_CONTEXT_ENABLED="1"
$env:SCAMSHIELD_SEMANTIC_GRAPH_ENABLED="1"
python -m uvicorn backend.main:app --app-dir "C:\AI4Life\AI4LIFE\ScamShield_AI\ScamShield_AI" --host 127.0.0.1 --port 8000
```

Schema công khai 2.0 và bốn risk_status giữ nguyên. Schema raw thêm mentions,
grounding_trace và thuộc tính semantic. Schema Python là nguồn chuẩn, đã xuất
lại các JSON schema. Nhánh facts thử nghiệm không được bật và chưa áp dụng
toàn bộ hòa giải mới; object guard của observer là dùng chung.

Xem [báo cáo và lỗi còn lại](reports/grounding_v2_20261113/README.md). Các tập
24/8 ca đều tổng hợp, không phải holdout độc lập. Tập 8 được đo sau khi sửa
cấu trúc chính, không dùng cách diễn đạt của nó để tinh chỉnh nhận diện.
Chưa chạy lại Chrome E2E, OCR, redirect mạng, tải đồng thời hoặc dữ liệu thật.
