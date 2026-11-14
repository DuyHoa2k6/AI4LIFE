# Giữ dữ liệu cũ và chuyển đổi

Không ghi đè data/dev.jsonl, validation.jsonl, holdout.jsonl, knowledge_seed.jsonl,
knowledge_sources.jsonl hoặc kho tình huống runtime. Không lấy expected cũ làm input.
Ba ca dev được chuyển trong pilot có metadata.source_id và review_status=weak_label;
đã xuất hiện trong phát triển nên không phải tập độc lập mới.

| Dữ liệu/hợp đồng cũ | Case 2.0 |
|---|---|
| id | metadata.case_id, source_id giữ ID cũ |
| split/family_id | metadata.split/family_id, thêm scenario/variant/source_group |
| provenance | metadata.origin_type/license_or_permission/review_status/reviewers |
| input.messages[].speaker | input.messages[].speaker_id, không xác minh danh tính |
| text | Chuyển thành message m1, speaker_id=null |
| context | context_facts có ID, source=user_report, verification_status |
| question | user_question |
| findings/evidence | annotations.events/spans, có actor khác attribution.speaker |
| tám answers | Giữ adapter cũ ở /api/observe; v2 dùng answers_18, không yêu cầu UI hiện 18 ô |
| expected.risk_status | expected_assessment.risk_status, chỉ là reference |
| source_matches | Tri thức đã duyệt, không là annotation của lời dụ |

Đầu ra mới POST /api/analyze-local là LocalResult local-reasoning-2.0, không giả làm
AnalyzeResponse cũ: assessment chứa risk_status/safety_urgency và giải thích có
kiểm soát; annotations giữ nội bộ cho kiểm thử. /local là UI thử nghiệm riêng,
chỉ hiển thị mức rủi ro, thông tin khẩn, tóm tắt, hành động, câu hỏi và quote hợp lệ.
/api/analyze và Chrome Extension hiện tại vẫn giữ luồng/config cũ để so sánh.
Chưa tự bật thay thế cả hai lượt Gemini trong giao diện cũ.

Lộ trình thay dần:

1. Rà nhãn, lấy gold độc lập và đánh giá v2 so với hệ cũ trên cùng input.
2. Thử adapter bộ trích Python ở bước đầu; giữ công tắc/quay lui và ghi phiên bản.
3. Thử backend rule/template thay lượt cuối, đánh giá cả risk và urgency, không chỉ JSON hợp lệ.
4. Khi có đủ dữ liệu reviewed, huấn luyện riêng span/event/actor/relation; giữ bước
   kiểm chứng quote/scope và cổng nguồn như hiện tại. Model không tự xuất tội danh.
5. Chỉ chuyển client cũ sau khi nghiệm thu cả hành vi, riêng tư, phản hồi cũ và lỗi.

Các thư mục bản nháp v2 giữ để đối chiếu. Không huấn luyện trên bản nháp rồi dùng
bản pilot gần trùng làm test độc lập. manifest.json chỉ một bản chuẩn cho validator.
