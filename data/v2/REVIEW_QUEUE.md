# Hàng chờ rà nhãn trước huấn luyện

Tất cả 70 ca hiện là weak_label, cần hai người rà. Các mục ưu tiên:

1. **legacy-SS-001**: input nhiệm vụ/ứng tiền nhiều tin nhắn hiện trả need_context.
   Bộ nối cục bộ chưa chắc nối đúng điều kiện đảo thứ tự “muốn rút … chuyển thêm”.
   Đây là hạn chế đã quan sát, không phải mẫu gold need_context. Cần sửa nhãn sự kiện/
   quan hệ bằng rà thủ công trước khi cải thiện extractor; không đưa nhãn tự sinh
   này vào train như đáp án chuẩn.
2. Toàn bộ relation inferred, đặc biệt travel_conditioned_on_secrecy, nợ/rời đi và
   work_differs_from_agreement: rà có thật cùng người/sự việc, có đủ căn cứ điều kiện
   hay mới đồng xuất hiện. Không lấy rule IDs làm chứng cứ ngữ nghĩa.
3. actor_id/affected_party_id/recipient_id và đồng tham chiếu: hiện nhiều actor null
   hoặc đối tượng chưa rõ danh tính. Không tính nối metadata là đúng vai ngữ nghĩa.
4. Urgent trên lời báo trực tiếp và lời đe dọa: rà thời điểm, người báo, giả định,
   phủ định, trích dẫn. Không dùng mất liên lạc/đi nước ngoài để suy thân thể bị hại.
5. OCR minh họa dưới bài cảnh báo so với bình luận độc lập; phân biệt loại nội dung
   có thể đổi cách hiểu dù chữ giống nhau. Nguồn OCR chưa chứng minh OCR đọc đúng.
6. Câu hỏi/hướng hỗ trợ cần rà bởi người am hiểu an toàn người dùng, không đòi dữ
   liệu nhạy cảm hoặc gây đối đầu. Danh bạ liên hệ vẫn chưa có nguồn xác minh.

Hai ca dev còn lại: legacy-SS-002 trả clear, legacy-SS-003 trả need_context. Ba ca
này không được tính trong 67 target nghiệm thu mới, và đã được dùng phát triển nên
không phải đánh giá độc lập. Kết quả 67/67 không xóa hạn chế legacy-SS-001.
