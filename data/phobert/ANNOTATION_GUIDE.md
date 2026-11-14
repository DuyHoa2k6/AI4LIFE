# PhoBERT Structured 1.0 — hướng dẫn gán nhãn

Bộ 20 ca smoke hiện tại là **nháp tổng hợp do agent biên soạn**, không phải gold hoặc dữ liệu người dùng thực. Đây là 10 cặp đối chiếu; không phải mọi cặp chỉ thay đúng một biến. File `minimal_pairs_unlabelled.jsonl` bổ sung đúng năm nhóm cặp tối thiểu theo yêu cầu, gồm 10 đầu vào chưa gán nhãn; không dùng làm negative hay supervised train. Không đổi nhãn tự động từ rulebook thành nhãn chuẩn. 70 ca v2 cũ vẫn giữ weak_label, không nhập làm supervised gold. Các ca đã dùng sửa quy tắc hoặc đã xuất hiện trong trao đổi là regression công khai.

## Đơn vị và bằng chứng

Mỗi dòng là một tình huống/hội thoại. Bản gốc trong messages là nguồn duy nhất để đối chiếu quote. `start/end` dùng Unicode code point của Python, end loại trừ. Không sửa bản gốc để khớp nhãn; không dùng offset của chuỗi có dấu gạch dưới từ RDRSegmenter.

Span classification dùng ứng viên biên từ, tối đa `max_span_words` trong một cửa sổ; nhiều nhãn và span lồng nhau có thể cùng được gán, không dùng BIO một lớp. `action` là cụm hành động tối thiểu có nghĩa, có thể gồm bổ ngữ được tách từ thành một đơn vị như “rút tiền”; không lấy chữ “chuyển” bên trong cụm “vận chuyển”. Với biên không trùng từ RDR, dừng và rà nhãn/thiết kế biểu diễn; không mở rộng offset âm thầm. Decoder smoke hiện chỉ xuất action, loại trùng chồng lấn trong cùng nhãn; entity/object/condition và span lồng cùng loại chưa được nghiệm thu.

Nhãn span: entity, action, object, condition, purpose, time, negation, benefit, consequence. Gán riêng `span_label_status` từng nhãn. Nhãn complete: toàn bộ ứng viên còn lại của đúng nhãn đó có thể làm negative. Partial: chỉ dùng positive đã đánh dấu, không coi phần còn lại là negative. Unannotated: không chấm hoặc phạt missing labels. Phần smoke hiện action hoàn thiện trong từng câu nháp; các nhãn khác chỉ partial hoặc chưa có nhãn.

## Sự kiện và vai

Mỗi sự kiện có action_type, object_type, speech_act, polarity, temporal_state, modality riêng. `null` là thuộc tính chưa gán nhãn, bị mask loss. Giá trị `unknown` là nhãn bất định có chủ ý, khác với null.

- Nhận phụ lục: receive + document; chưa nhận là not_completed, không phải receive_funds.
- Gửi hướng dẫn đăng nhập: handover + document; gửi thông tin đăng nhập: disclose_credentials + credentials.
- Lời cảnh báo trích lời dụ: quoted_warning; không chuyển thành request của người cảnh báo.
- “Nếu không nộp thì mất khoản cũ”: điều kiện phủ định của việc nộp và hậu quả bị đe dọa. Không phủ định toàn bộ lời yêu cầu hoặc lời đe dọa.
- Trạng thái đã xảy ra khác lời đề nghị thực hiện. Không suy ra lời tự nhận là sự thật đã xác minh.

speaker lấy từ metadata ứng dụng, không huấn luyện đoán lại tên. Các vai requester, performer, recipient, affected_party, transfer_source, transfer_destination liên kết với từng sự kiện. Mention phải có entity span; người chưa xác định dùng placeholder unknown, không tạo danh tính thật. Vai chưa gán nhãn trong task partial bị mask; trong task complete, thiếu liên kết nghĩa là annotator đã xác nhận không xác định được đích liên kết (null), không phải người đó không tồn tại.

## Quan hệ và giao dịch

same_transaction đối xứng, lưu một cạnh không phân biệt thứ tự. before, after, prerequisite_for, promised_after, threatens_unless, contradiction, state_update, obstructs_verification, transfer_via, controls_during có hướng. Có thể cùng tồn tại nhiều quan hệ trên một cặp. Ví dụ nộp → rút là prerequisite_for; đe dọa → hành động bị ép là threatens_unless; sự kiện cũ → mới là state_update.

Mỗi quan hệ phải tham chiếu cả anchor của hai đầu mút và có thể thêm condition/consequence span. Không coi tất cả cặp chưa được gán nhãn là negative: chỉ complete mới huấn luyện vector toàn 0 thành no_relation; partial chỉ học các loại positive đã ghi. Cặp ngoài cửa sổ không coi là no_relation.

Hai đơn A/B có transaction ID riêng. Đã nhận tiền A không xác nhận B. Cập nhật chỉ thay trạng thái đúng đối tượng/giao dịch; không tự dùng bản ghi phía sau cho mọi đơn. Metadata giao dịch của tập gold không được đưa vào input runtime; runtime chỉ có nhận dạng định dạng ID rõ trong câu và quan hệ do mô hình dự đoán. Đồng tham chiếu giao dịch ngầm còn cần dữ liệu riêng.

## Rủi ro tham chiếu

high: yêu cầu và cơ chế gây hại có căn cứ; suspicious: có dấu hiệu liên quan nhưng chưa đủ high; need_context: có dữ kiện người dùng thực sự còn thiếu có thể thay đổi đánh giá; clear: phân tích thành công trong phạm vi hỗ trợ và chưa thấy dấu hiệu.

Không dùng need_context để che lỗi mô hình, không dùng clear khi checkpoint/căn chỉnh lỗi. partial/unsupported/error là trạng thái xử lý riêng. Softmax/sigmoid chưa hiệu chuẩn không phải xác suất lừa đảo. Bộ quy tắc đọc sự kiện/quan hệ, không phải mô hình đã học.

## Rà độc lập và bất đồng

Hai người rà riêng bản gốc, chưa xem dự đoán mô hình hoặc nhãn của nhau. Ghi từng nhiệm vụ chưa hoàn thiện. Sau đó đối chiếu span, thuộc tính, vai, quan hệ và cơ chế rủi ro. Lưu bất đồng theo mẫu:

```json
{"sample_id":"...","task":"relations","reviewer_a":"...","reviewer_b":"...","label_a":{},"label_b":{},"resolution":null,"adjudicator":null,"evidence_refs":[]}
```

Chỉ chuyển independently_reviewed khi hai người thực sự đã rà; adjudicated khi bất đồng đã giải quyết và lưu lý do. Validator kiểm hai reviewer khác nhau, không thể tự chứng minh họ đã làm việc độc lập. Hiện có **0 ca được rà độc lập**, log bất đồng rỗng không có nghĩa đồng thuận 100%.

## Chia và khóa tập

Gộp nhóm liên thông theo family, hội thoại nguồn, template và source_group; thêm cạnh cho bản gần trùng, sau đó mới chia. Không tách tin nhắn/hai bản diễn đạt lại sang hai tập. Bộ smoke: 12 train, 4 validation, 4 test_locked theo nhóm. Đây đều là dữ liệu tổng hợp công khai do agent biết khi biên soạn, không phải holdout độc lập có giá trị chứng minh khái quát. File test không được dùng chọn checkpoint/ngưỡng; chưa chạy đánh giá test. Holdout cũ và holdout độc lập bên ngoài repo không được nạp.

## Dữ liệu còn thiếu

Cần gold được rà độc lập cho entity/object/condition/purpose/time/benefit/consequence, các vai bên thứ ba, đối tượng chịu tác động, nhiều người và nhiều giao dịch; cùng các quan hệ promised_after, after, contradiction, state_update, transfer_via. Cần nhiều nguồn độc lập, ca không có hành vi, ca không dấu/lỗi chính tả, lời cảnh báo và phủ định phức tạp, quan hệ xa, bối cảnh bổ sung. Không tăng số lượng bằng đổi tên/số tiền rồi coi là đa dạng mới.
