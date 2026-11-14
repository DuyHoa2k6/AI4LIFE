# Gán nhãn và quản lý dữ liệu đánh giá

Xuất gói đầu vào, nhận bản gán nhãn và đối chiếu bằng CLI theo [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md). Không dùng nhãn draft hoặc prediction làm bản rà độc lập.

Tái sử dụng [hướng dẫn PhoBERT](../../data/phobert/ANNOTATION_GUIDE.md) và kiểu trong `schema.py`; ontology policy có version riêng với label map mô hình. Các nhãn `draft` hiện tại do agent biên soạn, không phải human_verified. Không lấy prediction làm nhãn.

- Chỉ quote nguyên văn theo Unicode code point, end loại trừ. Không dùng offset bản RDR có `_` để highlight bản gốc.
- Event: anchor/argument refs, action/object, sáu thuộc tính, information_status và scope. Source observed/claimed/user_reported/inferred/unknown không phải bằng chứng sự việc ngoài đời đã thật.
- Participant unknown dùng ID scoped riêng, không dùng `unknown` chung để hợp nhất mọi người/giao dịch. Speaker metadata không được đoán lại hoặc xem là xác minh danh tính.
- Quan hệ có hướng theo loại, source/target/evidence/scope đầy đủ. State_update phải đúng đối tượng/giao dịch và đúng báo cáo cập nhật. Không yêu cầu mọi ca có quan hệ.
- Từng tình huống mới có phản ví dụ hợp lệ và điều kiện làm thay đổi mức; không gán nhãn theo domain hay keyword. Nhận tài liệu khác nhận tiền; kể lại/lời cảnh báo khác yêu cầu đang có hiệu lực.
- Đánh giá ngữ nghĩa cần người rà. Tag/enum mismatch trong harness là chẩn đoán cấu trúc, không tự chứng minh model hiểu sai nếu nhãn quá hẹp hoặc chưa có trong checkpoint.

Hai người rà độc lập bản gốc và gán nhãn trước khi xem prediction của nhau. Ghi reviewer_reference thật và bất đồng từng task. Ca mơ hồ ở review queue không vào train; chỉ adjudicate sau khi lưu lý do. Validator chỉ kiểm có hai reference khác nhau, không thể chứng minh đã rà độc lập. Chưa có người rà thật trong bộ mới.

Chia family/template/source trước chạy. Diagnostic/public regression đã dùng sửa không là holdout. Nếu chuyển validation vào train hoặc viết luật theo một ca validation, chuyển cả family và lưu lịch sử; tạo validation mới. Tất cả 35 ca hiện có là công khai, không blind dù còn để ở split validation.

Khi rà explanation: kiểm câu trích có hỗ trợ đúng hành động, đối tượng, điều kiện và khả năng gây hại; không cần khớp từng chữ với rationale. Một mức đúng nhưng giải thích theo cơ chế khác vẫn ghi lỗi. Không công nhận tội danh, danh tính, hình là thật, tiền đã mất hay tổn hại thân thể nếu không có căn cứ. Câu hỏi chỉ nhắm dữ kiện thực sự còn thiếu, không hỏi lại dữ kiện đã có.

`annotation_completeness` phân biệt complete/partial/unannotated. Không biến unknown/unannotated thành negative. Mọi chỉnh label phải có version/history và lý do từ người rà, không vì candidate đang đoán khác.
