# Hướng dẫn gán nhãn Case 2.0

## Grounding 2.0 — không nghiệm thu chỉ theo risk_status

Gán riêng đối tượng trực tiếp, polarity, speech_act, temporal_state, condition
và consequence. “Nhận phụ lục” không phải nhận tiền; “chưa gửi” không phải
“đừng gửi”; “nếu không nộp thì mất khoản cũ” có hai mệnh đề khác vai. Giữ nguồn
người thuật lại khác bên đưa lời đe dọa.

Mã đơn trong đối tượng sau động từ vẫn thuộc sự kiện đó. Không dùng đơn A
thanh toán để xác nhận B. Nếu “nhận đủ” không nêu đối tượng và chỉ có tiền của
giao dịch khác, giữ chưa rõ. Các đính chính nhãn yếu phải có phiên bản riêng,
không sửa holdout để làm đẹp chỉ số.

Mỗi lần nhắc người có mention_id riêng. Unresolved có candidate_ids, không
dùng một recipient:unknown chung làm chứng minh cùng người. Cùng tên/đại từ
trong hai request không tự gộp danh tính. View và giải thích chỉ lấy IDs/span
còn hợp lệ sau hòa giải; 18 trường không cộng điểm.

Xem [đặc tả](../../ScamShield_AI/GROUNDING_V2.md) và
[kết quả, kể cả ca chưa đạt](../../ScamShield_AI/reports/grounding_v2_20261113/README.md).

## Đồ thị ngữ nghĩa 1.0

Trong `Event.semantic`, phân biệt speaker/requester/performer/affected_party;
normalized_action phải gắn động từ với đối tượng và hướng chuyển, không gán
“login” cho lời yêu cầu gửi credentials cho người khác. Mã kết nối hỗ trợ từ
xa khác mã đăng nhập. Điều kiện phủ định “nếu không trả” không phải lời ngăn
trả tiền; “đừng gửi” mới là phủ định yêu cầu trong ví dụ tương ứng.

Quan hệ phải có hai đầu mút hợp lệ, scope, bên bị tác động, bằng chứng và
phương pháp. Đối tượng bị lược chỉ nối khi có căn cứ, không lấy ảnh/người/tài
khoản từ giao dịch khác. Không coi mọi cặp gần nhau là cùng tình huống. Lời
khẳng định chưa xác minh là claimed/user_reported, không system-verified.

`Interpretation.mechanisms` mô tả cơ chế nguy cơ từ các sự kiện/quan hệ, không
là suy đoán tội phạm. Một sự kiện giao mật khẩu có thể đủ cảnh báo mà không
cần tạo quan hệ giả. 18 trường là bản tổng hợp, không cộng điểm. Bộ 10 ca đã
công khai và 42 đối chứng ở `ScamShield_AI/fixtures/semantic_graph` đều thuộc
development, không dùng lại làm holdout. Chi tiết [đặc tả và giới hạn](../../ScamShield_AI/SEMANTIC_GRAPH.md).

## Biến thể nghĩa tương đương trong ngữ cảnh khác

Xem [bộ 24 ca bổ sung](semantic_variants/README.md). Gán nhãn theo quan hệ ý
nghĩa và lời nói, không chỉ theo từ đồng nghĩa. “Mua gói để nhả vốn” khác với
mua tùy chọn không ảnh hưởng hoàn tiền; cho người lấy hàng khi chưa báo có
khác với giao sau khi báo nhận đủ tiền. Dùng ca phủ định, cảnh báo trích dẫn,
khác giao dịch và khác bên hưởng lợi để kiểm tra liên kết sai.

Chú giải mục tiêu phải nêu hành động, vai thực hiện/bị tác động, quan hệ và
span nguyên văn. Mục không được nói rõ giữ unknown. Không suy số tiền, ý định
chiếm đoạt hoặc danh tính thật từ một cụm tương đương. Các ca dùng sửa bộ
trích thuộc development; không tái sử dụng làm bằng chứng chất lượng độc lập.

## Bổ sung 13/11/2026: vai trò và hành động chủ chốt

Trong đầu ra máy, `interpretation.clause_roles` phân biệt bên yêu cầu, bên thực
hiện và bên bị tác động. Chưa biết tên vẫn gán nhãn vai trò, ví dụ
`recipient:unknown` hoặc `custodian:unknown:<scope>`; không coi đó là danh tính
đã xác minh. Nếu chưa xác định vai trò bị tác động, giữ `affected_status=unknown`
và ID null; không tự bổ sung nạn nhân hoặc quan hệ gia đình.

`interpretation.salient_actions` ghi hành động chủ chốt, quan hệ hỗ trợ, hậu quả
có thể xảy ra và lý do chọn. Một `is_primary=true` trên mỗi scope khi có yêu cầu
đủ căn cứ. Việc chọn hành động không đồng nghĩa đã đủ căn cứ tăng mức rủi ro.

Mức 3–4 cần yêu cầu có hiệu lực và quan hệ dẫn tới lựa chọn bất lợi. Ví dụ đi
tuyển dụng trước hợp đồng + giấu gia đình + giao giấy tờ cho bên đón giữ có thể
được mức 4 do nguy cơ mất quyền chủ động; không gán nhãn vụ án đã xác minh.
Không nâng chỉ vì có từ “nước ngoài”, “giấy tờ” hoặc không biết tên người gửi.

Khi rà cập nhật thanh toán, kiểm tra cùng người báo/cùng giao dịch và dấu mốc
thời gian tường minh. Lời người mua không thay lời người bán. Giữ cả sự kiện
cũ lẫn mới, nối `state_update`; không xóa lời khai cũ hay lấy câu sau làm đúng
mặc định. Lời cảnh báo, phủ định, giả định và khả năng lấy lại giấy tờ là ca
đối chứng bắt buộc. Các nhãn máy vẫn cần người rà, không tự đổi thành reviewed.

Chi tiết: [thiết kế bản thử](../../ScamShield_AI/CLAUSE_ROLES.md),
[tám ca trước/sau](../../ScamShield_AI/reports/clause_roles_20261113/CASES.md).

Bộ fact TRUE/FALSE/UNKNOWN đã tạm ngừng dùng mặc định; luồng hiện tại quay lại event/rulebook + RAG/URL (`SCAMSHIELD_REASONER=legacy`). Các file [fact_catalog.json](fact_catalog.json), [fact_rules.json](fact_rules.json) chỉ giữ để đối chiếu thử nghiệm, không phải nhãn chuẩn tự sinh. Không sửa annotations/expected để ép khớp runtime. Mapping và lịch sử: [FACT_REASONER.md](../../ScamShield_AI/FACT_REASONER.md).

## Quy trình

1. Chỉ đọc input. Xác định nguồn từng message: text/post/comment/email/ocr, parent,
   speaker_id và thứ tự. Timestamp message khác thời gian sự kiện được nhắc.
2. Chọn phạm vi sự việc/giao dịch; nếu hai việc không có căn cứ chung thì giữ riêng.
3. Gán span từ nguyên văn, Unicode code point, end loại trừ. Không sửa chính tả hoặc
   mở rộng viết tắt trong quote. Dùng ánh xạ chuẩn hóa của bộ trích nếu khớp luật.
4. Gán participant, event và attribution; trường chưa rõ dùng null/unknown.
5. Nối relation khi có căn cứ cho cả hai đầu mút, đúng người và scope. Quan hệ chỉ
   suy từ đồng xuất hiện phải inferred và cần rà lại, không coi như nguyên văn khẳng định.
6. Điền 18 trường từ IDs/span đã kiểm chứng. technical_checks unknown nếu chưa có
   kết quả mô-đun thật. Nhận định không thay thế dữ kiện quan sát.
7. Áp rulebook rồi chọn risk_status và safety_urgency độc lập, ghi bằng chứng khẩn.
8. Hai người rà riêng, ghi bất đồng, người thứ ba/nhóm chuyên môn phân xử. Chỉ khi
   hoàn tất mới đổi reviewed và ghi reviewers; không tự chấp nhận nhãn máy.

## Phân biệt các lớp thông tin

| Câu | Gán đúng | Không được suy ra |
|---|---|---|
| “Anh là người quen của em” | Quan hệ claimed, loại có thể unknown | Đã xác minh quan hệ gia đình |
| “Người gửi là anh trai tôi” trong context | user_reported, unverified | Hệ thống kiểm chứng danh tính |
| “Tôi là công an” | identity_claim, sender_claim | Có thẩm quyền thật |
| “Chưa thấy tiền về” | receive_funds negative/pending, claimed | Chưa ai chuyển hoặc biên lai giả |
| Không nhắc tiền | Thiếu dữ kiện thanh toán | Tự sinh sự kiện chưa nhận tiền |
| “Đừng gửi OTP” | Phủ định/ngăn yêu cầu | Request dương tính |
| Bài cảnh báo trích “gửi OTP” | quoted_warning | Người viết đang đòi mã |
| “Họ nói sẽ giữ hộ chiếu” | reported/planned | Đang bị giam hoặc urgent |
| “Họ đang giữ hộ chiếu của tôi và tôi không được rời đi” | Lời báo trực tiếp/current, ưu tiên an toàn | Vụ án đã được xác minh |
| Đòi tiền để thả người | demand_release_payment, nguồn lời đòi chưa xác minh | Đã chứng minh có bắt giữ thật |
| Đi nước ngoài rồi mất liên lạc | Ngoài độ phủ/thiếu dữ kiện | Suy lấy nội tạng |

## Span và vai

Gán verb/action/object/negation/state/time/condition/purpose/participant/organization/
url/account/application/quotation/reported_speech/persuasion/statement. Có thể nhiều
span chồng nhau nhưng mỗi span phải có lý do. Emoji dùng code point; JS kiểm tra
bằng Array.from, không chỉ số UTF-16. URL và 500.000,50 không tách như dấu chấm câu.

Các nhãn tag do luật sinh chỉ là weak_label. Ví dụ “đã” là state, không tự chứng minh
hoàn tất nếu ở trong trích dẫn hoặc phủ định kép. “gia đình” không phải “giả định”
sau bỏ dấu. Nguồn OCR vẫn cần đối chiếu ảnh, không xem quote khớp OCR là OCR chắc đúng.

## Vai giao dịch và quan hệ ngoài đời

buyer/seller/requester/recipient/affected_party chỉ mô tả tương tác. family/friend/
colleague/online_only phải có câu nêu hoặc context; không suy từ anh/chị/em.
Participant có thể unknown; không chế tạo tên hoặc danh tính thật. attribution giữ
người thuật lại riêng với người được nói là đã làm hành động.

OCR dưới bài cảnh báo được đọc cùng parent khi parent thực sự là lời cảnh báo.
Bình luận độc lập dưới bài cảnh báo không tự được miễn: bình luận có yêu cầu gửi mã
vẫn là lời của người bình luận, không phải lời trích của tác giả bài.

## Thời gian, scope và mâu thuẫn

state_update cần cùng người/giao dịch và căn cứ thời gian mới: hôm qua chưa nhận /
hôm nay nhận đủ. Hai lời khẳng định trái nhau mà không có thời gian rõ là contradiction,
không tùy chọn câu thuận lợi hơn. Trạng thái bên người mua tự nói đã trả không thay
cho bên người nhận cho biết đã kiểm tra tiền. Yêu cầu tiền để rút cần quan hệ điều kiện,
không chỉ hai từ “tiền” và “rút” ở nơi khác nhau.

Khi không biết hai yêu cầu có cùng sự việc, không tạo same_transaction chỉ vì cùng
message. Dùng scope_id rõ hoặc ghi unknown/rationale cần rà. Mỗi quan hệ phải có
evidence_refs bao phủ cả hai event; người và phạm vi phải nhất quán.

## An toàn con người và câu hỏi

Chỉ urgent khi có lời báo nguy hiểm đang/sắp xảy ra đủ căn cứ. Không cần đầy đủ quá
trình tiếp cận ban đầu. Câu kể quá khứ, ví dụ giả định, bài tuyên truyền và phủ định
không tự thành nguy hiểm hiện tại. Nếu chưa rõ thời điểm/vai, giữ phần không biết.

Với lời mời: hỏi đầu mối/địa điểm/công việc có thể đối chiếu và có yêu cầu giấu/giao
giấy tờ không. Với nguy hiểm hiện tại: ưu tiên hướng hỗ trợ ngay, chỉ hỏi có trao đổi
an toàn không, có thể bỏ qua. Không đòi giấy tờ/ảnh riêng tư/mô tả tổn hại chi tiết.
Không yêu cầu vị trí chính xác để mới được hỗ trợ. Không tự tạo hotline hoặc URL.

## Những việc người rà phải làm tiếp

Rà actor/recipient/entity, quan hệ implied vs explicit, ràng buộc nợ/giữ giấy tờ,
mức khẩn cấp và câu hỏi an toàn trước khi đưa dữ liệu vào huấn luyện. 70 mẫu hiện
chưa qua quy trình hai người; không lấy nhãn weak làm gold hoặc chấm extractor bằng
chính nhãn extractor sinh rồi tuyên bố độ chính xác.
