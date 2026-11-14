# Năm ca chẩn đoán: dữ kiện trước/sau

Tham chiếu là draft; nhận xét ở đây do agent chuẩn bị, chưa có người rà độc lập. Không sửa label hoặc huấn luyện theo các kết quả này. Oracle dùng annotation chuẩn bị sẵn, không là output sản phẩm.

## N01 — education

Tham chiếu draft | clear

> advisor: Nội dung học, học phí và quyền hoàn phí đã ghi trong hợp đồng. Bạn đọc kỹ và hỏi đầu mối công khai trước khi quyết định.

| Chế độ | Trước | Sau |
| --- | --- | --- |
| e2e | suspicious | suspicious |
| oracle | None | clear |

Dữ kiện tham chiếu:
- “đọc kỹ” → action=read_terms, object=contract, speech=request, polarity=positive, scope=case:main.
- “hỏi đầu mối” → action=verify, object=information, speech=request, polarity=positive, scope=case:main.

baseline — dữ kiện do model thực sự trả:
- “học, học phí và quyền” → action=grant_control, object=device, speech=request, polarity=positive; roles={'performer': 'recipient:unknown', 'speaker': 'speaker:advisor'}.
- “hoàn” → action=retain_documents, object=money, speech=claim, polarity=positive; roles={'performer': 'recipient:unknown', 'speaker': 'speaker:advisor'}.
- “ghi” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'recipient:unknown', 'speaker': 'speaker:advisor'}.
- Giải thích: Có yêu cầu liên quan đến quyền thiết bị, giấy tờ hoặc nghĩa vụ tài chính cần xác minh.

candidate_01 — dữ kiện do model thực sự trả:
- “học, học phí và quyền” → action=grant_control, object=device, speech=request, polarity=positive; roles={'performer': 'unknown:m1:addressee', 'speaker': 'speaker:advisor'}.
- “hoàn” → action=retain_documents, object=money, speech=claim, polarity=positive; roles={'performer': 'unknown:m1:addressee', 'speaker': 'speaker:advisor'}.
- “ghi” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'unknown:m1:addressee', 'speaker': 'speaker:advisor'}.
- Giải thích: Có yêu cầu cấp quyền điều khiển thiết bị; cần xác minh phạm vi và đầu mối hỗ trợ.

Label chưa có trong head checkpoint: ['read_terms']. Nếu oracle tốt hơn E2E, đây là dấu hiệu lỗi trích/biểu diễn, không chứng minh đã sửa model. Quote khớp chỉ là kiểm chứng vị trí, không xác nhận mọi thuộc tính suy ra đúng nghĩa.

## N04 — education

Tham chiếu draft | high

> advisor: Bạn phải đứng tên vay để đóng học phí ngay. Cứ khai thu nhập cao hơn thực tế; đừng cho gia đình xem hồ sơ. Ký xong mới được xem điều khoản.

| Chế độ | Trước | Sau |
| --- | --- | --- |
| e2e | None | None |
| oracle | suspicious | high |

Dữ kiện tham chiếu:
- “đứng tên vay” → action=borrow, object=money, speech=request, polarity=positive, scope=case:main.
- “khai thu nhập cao hơn thực tế” → action=misstate_information, object=information, speech=request, polarity=positive, scope=case:main.
- “Ký xong mới được xem điều khoản” → action=conceal_terms, object=contract, speech=claim, polarity=positive, scope=case:main.

baseline — dữ kiện do model thực sự trả:
- Không còn sự kiện hợp lệ để kết luận.
- Giải thích: Mô hình chưa xử lý đủ phạm vi đầu vào; chưa có kết luận rủi ro.

candidate_01 — dữ kiện do model thực sự trả:
- Không còn sự kiện hợp lệ để kết luận.
- Giải thích: Mô hình chưa xử lý đủ phạm vi đầu vào; chưa có kết luận rủi ro.

Label chưa có trong head checkpoint: ['conceal_terms', 'misstate_information']. Nếu oracle tốt hơn E2E, đây là dấu hiệu lỗi trích/biểu diễn, không chứng minh đã sửa model. Quote khớp chỉ là kiểm chứng vị trí, không xác nhận mọi thuộc tính suy ra đúng nghĩa.

## N08 — relationships

Tham chiếu draft | high

> partner: Nếu muốn sống chung, em ký giấy chuyển quyền căn nhà cho anh trước. Đừng hỏi người thân hoặc người tư vấn; không ký thì chấm dứt chuyện này.

| Chế độ | Trước | Sau |
| --- | --- | --- |
| e2e | clear | None |
| oracle | None | high |

Dữ kiện tham chiếu:
- “chuyển quyền căn nhà” → action=grant_authority, object=ownership_right, speech=request, polarity=positive, scope=case:main.
- “Đừng hỏi người thân hoặc người tư vấn” → action=avoid_verification, object=information, speech=request, polarity=positive, scope=case:main.
- “không ký thì chấm dứt” → action=pressure_relationship, object=information, speech=claim, polarity=positive, scope=case:main.

baseline — dữ kiện do model thực sự trả:
- “ký” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- “chuyển” → action=disclose_credentials, object=document, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- “ký” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- “chấm dứt” → action=transfer, object=money, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- Giải thích: Trong phạm vi đã phân tích, chưa thấy yêu cầu có cơ chế gây hại được nhận diện.

candidate_01 — dữ kiện do model thực sự trả:
- “ký” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- “chuyển” → action=disclose_credentials, object=document, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- “ký” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- “chấm dứt” → action=transfer, object=money, speech=request, polarity=positive; roles={'performer': 'speaker:partner', 'speaker': 'speaker:partner'}.
- Giải thích: Mô hình chưa xử lý đủ phạm vi đầu vào; chưa có kết luận rủi ro.

Label chưa có trong head checkpoint: ['grant_authority', 'pressure_relationship']. Nếu oracle tốt hơn E2E, đây là dấu hiệu lỗi trích/biểu diễn, không chứng minh đã sửa model. Quote khớp chỉ là kiểm chứng vị trí, không xác nhận mọi thuộc tính suy ra đúng nghĩa.

## N20 — services

Tham chiếu draft | high

> user: Đơn sửa chữa A chưa được thực hiện.
> provider: Bạn bấm đã hoàn tất đơn A và từ bỏ khiếu nại trước để bên tôi mới xếp lịch. Đừng phản ánh lên nền tảng.

| Chế độ | Trước | Sau |
| --- | --- | --- |
| e2e | need_context | None |
| oracle | None | high |

Dữ kiện tham chiếu:
- “chưa được thực hiện” → action=receive_service, object=service_confirmation, speech=claim, polarity=negative, scope=order:A.
- “bấm đã hoàn tất” → action=confirm_completion, object=service_confirmation, speech=request, polarity=positive, scope=order:A.
- “Đừng phản ánh” → action=avoid_verification, object=information, speech=request, polarity=positive, scope=order:A.

baseline — dữ kiện do model thực sự trả:
- “bấm” → action=transfer, object=money, speech=request, polarity=positive; roles={'performer': 'recipient:unknown', 'speaker': 'speaker:provider'}.
- “từ bỏ khiếu nại trước để bên tôi mới xếp” → action=retain_documents, object=money, speech=claim, polarity=positive; roles={'performer': 'recipient:unknown', 'speaker': 'speaker:provider'}.
- Giải thích: Chưa rõ mục đích hoặc trạng thái của yêu cầu chuyển tiền.

candidate_01 — dữ kiện do model thực sự trả:
- “bấm” → action=transfer, object=money, speech=request, polarity=positive; roles={'performer': 'unknown:m2:addressee', 'speaker': 'speaker:provider'}.
- “từ bỏ khiếu nại trước để bên tôi mới xếp” → action=retain_documents, object=money, speech=claim, polarity=positive; roles={'performer': 'unknown:m2:addressee', 'speaker': 'speaker:provider'}.
- Giải thích: Mô hình chưa xử lý đủ phạm vi đầu vào; chưa có kết luận rủi ro.

Label chưa có trong head checkpoint: ['confirm_completion', 'receive_service']. Nếu oracle tốt hơn E2E, đây là dấu hiệu lỗi trích/biểu diễn, không chứng minh đã sửa model. Quote khớp chỉ là kiểm chứng vị trí, không xác nhận mọi thuộc tính suy ra đúng nghĩa.

## N29 — education

Tham chiếu draft | clear

> author: Bài cảnh báo trích lời dụ: “Bạn phải đứng tên vay, khai thu nhập cao hơn thực tế và ký xong mới xem điều khoản”. Đừng làm theo.

| Chế độ | Trước | Sau |
| --- | --- | --- |
| e2e | suspicious | suspicious |
| oracle | None | clear |

Dữ kiện tham chiếu:
- “đứng tên vay” → action=borrow, object=money, speech=quoted_warning, polarity=positive, scope=case:main.
- “khai thu nhập cao hơn thực tế” → action=misstate_information, object=information, speech=quoted_warning, polarity=positive, scope=case:main.
- “ký xong mới xem điều khoản” → action=conceal_terms, object=contract, speech=quoted_warning, polarity=positive, scope=case:main.

baseline — dữ kiện do model thực sự trả:
- “vay, khai” → action=retain_documents, object=money, speech=request, polarity=positive; roles={'performer': 'recipient:unknown', 'speaker': 'speaker:author'}.
- “ký” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'recipient:unknown', 'speaker': 'speaker:author'}.
- Giải thích: Có yêu cầu liên quan đến quyền thiết bị, giấy tờ hoặc nghĩa vụ tài chính cần xác minh.

candidate_01 — dữ kiện do model thực sự trả:
- “vay, khai” → action=retain_documents, object=money, speech=request, polarity=positive; roles={'performer': 'unknown:m1:addressee', 'speaker': 'speaker:author'}.
- “ký” → action=retain_documents, object=identity_document, speech=request, polarity=positive; roles={'performer': 'unknown:m1:addressee', 'speaker': 'speaker:author'}.
- Giải thích: Có yêu cầu giao giấy tờ để bên khác giữ; cần xác minh quyền lấy lại.

Label chưa có trong head checkpoint: ['conceal_terms', 'misstate_information']. Nếu oracle tốt hơn E2E, đây là dấu hiệu lỗi trích/biểu diễn, không chứng minh đã sửa model. Quote khớp chỉ là kiểm chứng vị trí, không xác nhận mọi thuộc tính suy ra đúng nghĩa.
