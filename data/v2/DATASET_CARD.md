# ScamShield Case 2.0 — dataset card

## Mục tiêu và bản đang dùng

Dataset cho bộ trích Python, bộ suy luận có điều kiện và mô hình trích xuất/quan hệ
sẽ huấn luyện sau. Không phải danh sách tên thủ đoạn để so từ khóa hoặc bằng chứng
xác nhận tội phạm. Mỗi dòng JSONL là một ca, giữ message/người nói/nguồn/phạm vi riêng.

`manifest.json` chỉ tới **release_final/pilot.jsonl**, 70 ca. Trong đó 3 ca chuyển từ
input dev cũ; 67 ca có kỳ vọng nghiệm thu biên soạn riêng. Mỗi nhóm an toàn có ca
đối chứng, ca thiếu thông tin và ca có dấu hiệu. Có ca OTP, thanh toán, giao hàng,
OCR dưới bài cảnh báo, bình luận độc lập, nhiều giao dịch, cập nhật trạng thái,
đe dọa, hạn chế liên lạc/tự do, ép làm việc và can thiệp thân thể. Không mô tả đồ họa
hoặc dựng chuỗi tiếp cận nạn nhân có thể đem dùng trực tiếp.

## Nguồn và quyền

- Toàn bộ là synthetic; không phải dữ liệu người dùng thực hoặc bản ghi cơ quan nhà nước.
- Những lời cảnh báo trong mẫu là tình huống biên soạn, không phải nguyên văn nguồn chính thống.
- Không có OTP, tài khoản ngân hàng hoặc URL độc hại đang hoạt động thật.
- Ba mẫu dev giữ source_id để tránh tính như ca độc lập mới.
- license_or_permission ghi phạm vi mẫu dự án; rà quyền sử dụng trước khi phát hành công khai.

## Nhãn và chất lượng

**70/70 bản gán nhãn chi tiết là weak_label**, sinh từ bộ trích/quy tắc, chưa được
hai người rà độc lập. Metadata ghi rõ annotation_version/split/origin/review_status.
Các kỳ vọng ở acceptance_targets.json là nhãn phát triển biên soạn, không phải gold
độc lập. expected_assessment bên trong pilot là kết quả tự động và không dùng làm
bằng chứng accuracy của chính bộ trích. Chưa có mô hình riêng được huấn luyện.

Hiện không có ca đủ điều kiện xuất supervised train/dev/test. Công cụ export chỉ
nhận reviewed kèm ít nhất hai người rà; không tự đổi weak_label thành reviewed.

## Phạm vi và giới hạn

15 nhóm hành vi mới của phần an toàn được giữ riêng với nhóm gian lận tài chính.
Đi nước ngoài, quốc tịch, giới tính, tạo lòng tin hoặc tình cảm riêng lẻ không là
điều kiện kết luận mua bán người. Dữ liệu nêu hành vi quan sát/khai báo; không xác
nhận danh tính hoặc tội danh. Nguy cơ can thiệp cơ thể chỉ xuất hiện khi câu gốc
nêu trực tiếp cưỡng ép/đe dọa tương ứng.

Mô-đun hiện là luật hữu hạn, còn hạn chế từ lóng mới, nhiều chủ thể, đồng tham chiếu,
quan hệ ngầm và thời gian phức tạp. actor_id có thể unknown dù đã nhận được một lời
báo nguy hiểm; không trì hoãn hỗ trợ chỉ để hỏi danh tính tổ chức. Urgent precheck có
thể trả 18 trường với nhiều unknown để ưu tiên an toàn.

## Tách bốn loại dữ liệu

1. Dataset gán nhãn: release_final/*.jsonl và nguồn/vai trò của từng ca.
2. Rulebook/template/nhãn: các JSON ở thư mục này, có schema kiểm tra riêng.
3. Tri thức: ../knowledge_sources.jsonl, qua cổng duyệt hiện có; hiện 0 nguồn đủ điều kiện.
4. Báo cáo cộng đồng: community_reports.jsonl, hiện rỗng; không nạp vào chỉ mục đã duyệt.

support_directory.json hiện rỗng: không có danh bạ hỗ trợ theo khu vực đã được xác
minh. Kết quả không tự tạo số điện thoại hay URL. Hướng hỗ trợ chung không yêu cầu
gửi ảnh riêng tư/giấy tờ/mã thật, không khuyên đối đầu hay tự điều tra.

## Phiên bản và bảo quản

Schema scamshield-case-2.0, đầu ra local-reasoning-2.0. Xem case.schema.json,
output.schema.json, labels.json, rulebook.json và templates.json. Các thư mục
pilot_draft1/pilot/pilot_expanded/pilot_final/release/release_v2 là bản phát triển lưu
đối chiếu, không gộp vào cùng phép đo hoặc tăng số mẫu độc lập. Dữ liệu cũ ngoài
thư mục v2 không bị thay thế. Hash chuẩn ở báo cáo validator; không đọc holdout cũ
để phát triển luật.

[Hướng dẫn gán nhãn](ANNOTATION_GUIDE.md) · [Nhãn](LABEL_DICTIONARY.md) ·
[Chia tập và đánh giá](EVALUATION.md) · [Chuyển đổi](MIGRATION.md).

[Hàng chờ rà và hạn chế đã quan sát](REVIEW_QUEUE.md), gồm legacy-SS-001 chưa nối
chắc điều kiện nộp thêm để rút qua nhiều tin. Không coi nhãn weak của ca này là gold.
