# Từ điển nhãn và hướng quan hệ

Danh sách máy đọc đầy đủ nằm ở labels.json, được kiểm tra bằng labels.schema.json.
EventType/RelationType là enum Pydantic, có other kèm description cho hành vi chưa có.

## Hành vi

Giữ các nhóm tài chính/dữ liệu: transfer_funds, receive_funds, withdraw_funds,
handover_asset, provide_code, provide_credentials, provide_documents, open_link,
login, install_app, share_screen, grant_control, change_channel, keep_secret,
avoid_verification, identity_claim, relationship_claim, code_identity.

| Nhãn an toàn mới | Định nghĩa và điều không đủ |
|---|---|
| build_trust | Làm thân/tự nhận đáng tin; riêng lẻ chưa là tội phạm |
| invite_travel_or_meeting | Mời đi/gặp; không lấy quốc gia làm đặc trưng rủi ro |
| offer_employment | Đề nghị việc làm, tách lời hứa khỏi điều kiện thực |
| change_destination_or_terms | Đổi nơi/công việc; cần căn cứ thỏa thuận cũ để nói lệch |
| impose_debt | Tạo nghĩa vụ nợ; nợ riêng lẻ không chứng minh mất tự do |
| request_secrecy | Yêu cầu giấu người thân/đầu mối; khác quyền riêng tư hợp lệ |
| restrict_communication | Ngăn liên lạc/giữ điện thoại; cần phân biệt tự nguyện |
| retain_identity_documents | Giữ giấy tờ, chưa đồng nghĩa không cho nhận lại |
| restrict_movement | Ngăn rời đi có câu nêu; không suy từ mất liên lạc |
| threaten_harm | Lời đe dọa gây hại, chưa chứng minh đã xảy ra tổn hại |
| threaten_disclosure | Đe dọa phát tán riêng tư; không yêu cầu nạn nhân đưa ảnh |
| demand_release_payment | Đòi tiền để rời đi/thả người; chưa xác minh bắt giữ |
| compel_work | Ép lao động; không đồng nhất hợp đồng tự nguyện |
| compel_illegal_activity | Ép làm việc trái pháp luật có lời gốc |
| bodily_integrity_threat | Đe dọa/cưỡng ép thân thể trực tiếp, không suy từ giữ giấy tờ |

Helper labels return_documents_available/free_to_leave/consent_and_exit_available
ghi căn cứ đối chứng. Không dùng một câu “tự nguyện” để xóa nguy hiểm hiện tại rõ ràng.

## Quan hệ giữa sự kiện

| Nhãn | Hướng from → to / căn cứ |
|---|---|
| prerequisite_for | Hành động điều kiện → kết quả/lợi ích; cần điều kiện có lời gốc |
| before | Sự kiện trước → sự kiện sau, có thứ tự được nêu |
| after | Sự kiện sau → sự kiện trước |
| reason_given_for | Lý do được nêu → hành động được biện minh; không chứng minh lý do đúng |
| contradiction | Hai mệnh đề không tương thích trong cùng thời điểm/phạm vi |
| state_update | Trạng thái cũ → mới, cần thời gian/thứ tự, không chọn tùy ý |
| reported_by | Sự kiện được kể → người thuật lại |
| warning_about | Người cảnh báo → sự kiện được trích để phòng tránh |
| same_transaction | Hai sự kiện cùng giao dịch có căn cứ định danh, không suy từ đồng xuất hiện |
| travel_conditioned_on_secrecy | Lời mời đi → yêu cầu giấu, cùng người/sự việc; luật hiện có thể inferred |
| movement_restricted_by_debt | Khoản nợ → hạn chế rời đi |
| document_retention_limits_exit | Giữ giấy tờ → hạn chế rời đi |
| threat_used_to_compel_action | Đe dọa → hành động bị ép |
| release_conditioned_on_payment | Điều kiện trả tiền → được thả; một event ghép có thể dùng self-edge, cả hai vế phải nằm trong quote |
| work_differs_from_agreement | Lời mời → điều kiện thực tế thay đổi có căn cứ |

Không có relation không có nghĩa quan hệ bị phủ định. Status unknown khác negative.
Một tên thủ đoạn chỉ là nhãn tham khảo, không là điều kiện ra cảnh báo.

## Vai và trạng thái

speech_role: request/claim/reported/quoted_warning/denial/hypothetical/unknown.
modality: request/assertion/report/conditional/threat/possibility/unknown.
temporal_state: requested/completed/pending/ongoing/imminent/planned/hypothetical/past/unknown.
attribution.kind: sender_claim/self_report/reported/quoted_warning/hypothetical/user_report/unknown.
Observed là đã quan sát thấy câu, không khẳng định câu đúng ngoài đời. Claimed là
lời tự nhận/tuyên bố; user_reported giữ ở quan hệ/context với verification_status.

Mức rủi ro vẫn clear/need_context/suspicious/high. Safety urgency riêng:
undetermined (chưa đủ dữ kiện), preventive (cần phòng ngừa), urgent (nguy hiểm trực
tiếp đang/sắp xảy ra có căn cứ). Urgent không chứng minh tội danh và không đòi đủ 18 ô.
