# Chia tập, chống rò rỉ và kế hoạch đánh giá

## Chia theo nguồn gốc

Không chia ngẫu nhiên từng dòng. backend/local_reasoning/splits.py hợp nhất các
ca có chung scenario_id, variant_group_id, source_group_id hoặc nội dung gốc giống
nhau thành một component; component chỉ vào một split. Nguồn/chiến dịch/hội thoại
liên quan dùng chung source_group_id. Các cặp chỉ đổi một dữ kiện phải cùng nhóm.

Tỷ lệ dự kiến 70/15/15 tính theo hash nhóm ổn định, không bảo đảm tỷ lệ dòng đúng
chính xác trên pilot nhỏ. Independent không được tự chia lại. Khi có gold độc lập,
giữ ngoài workspace phát triển và phiên chỉnh luật/mô hình; không cho công cụ triển
khai đọc labels để sửa luật. Không xuất holdout cũ vào kho runtime.

Tất cả 70 ca hiện ở pilot/weak_label. Dry-run chia nhóm chỉ minh họa thuật toán,
không phải train/test hợp lệ. Export mặc định chỉ lấy reviewed có hai reviewers;
hiện kết quả là 0, không huấn luyện mô hình và không tự nâng nhãn máy thành gold.

## Đánh giá theo bước

1. **Span:** exact và overlap F1 theo nhãn, Unicode offset, tách theo OCR/DOM/text,
   phủ định, viết tắt, câu thiếu dấu và câu lặp. Exact offset đúng không đồng nghĩa
   phân tích ngữ nghĩa đúng.
2. **Event:** type, polarity, speech role, modality, temporal state, attribution;
   báo precision/recall từng loại và ngoài độ phủ. Gold cần người rà độc lập.
3. **Participant:** actor/affected/recipient và coreference; không chấm chỉ nối
   metadata rồi coi là đúng vai ngữ nghĩa.
4. **Relation:** F1 từng nhãn, đúng đầu mút/scope/người/thời gian. Các relation luật
   inferred phải chấm riêng, không đồng nhất với quan hệ explicit.
5. **Rulebook:** kiểm thử điều kiện cần, ngoại lệ, thiếu dữ kiện, trạng thái cập nhật,
   mâu thuẫn, cùng bằng chứng không được cộng lặp.
6. **Risk:** confusion matrix bốn trạng thái, high precision/recall và số đếm, cảnh
   báo nhầm trên ca hợp lệ, ca high bỏ sót, câu hỏi đúng khoảng trống.
7. **Urgency:** precision/recall và số đếm riêng; báo đặc biệt missed urgent,
   false urgent trên bài cảnh báo/quá khứ/tự nguyện, và lỗi phân tích không trả clear.
8. **Giải thích/nguồn:** quote đúng vai, kết luận không vượt bằng chứng, không biến
   lời đòi tiền thành xác nhận bắt giữ, không suy nội tạng. Chấm nguồn hỗ trợ đúng,
   lệch, lỗi cổng duyệt; hiện 0 nguồn đủ điều kiện nên chưa đo chất lượng RAG thực.

## Toàn luồng và báo cáo

Chỉ input được gửi API; lưu predictions trước khi đọc acceptance targets/expected.
Khóa hash mã/quy tắc/template/nhãn/dữ liệu/chỉ mục. Báo riêng lỗi, unknown, các ca đã
dùng chỉnh, dữ liệu synthetic/consented_real/source_based_simulation. Không biến
nhãn extractor tự sinh thành thước đo F1 của chính extractor. Khi có đủ gold, báo
khoảng tin cậy theo nhóm nguồn/biến thể, không chỉ tỷ lệ gộp.

Đo ASGI, browser/extension và throughput riêng; tách cold/warm được kiểm soát,
độ dài đầu vào, xử lý khẩn bỏ qua bước đầy đủ, source lookup và tổng. Không so ms
API cục bộ với giây Gemini trên input khác rồi tuyên bố chất lượng tốt hơn.

Kết quả hiện chỉ là nghiệm thu phát triển 67 target do dự án biên soạn và 3 input
dev chuyển đổi chưa có target độc lập. Đạt cả các ca này chưa chứng minh mục tiêu 98%.
Không có trọng số mô hình được huấn luyện; framework huấn luyện chọn sau khi có
đủ gold, baseline và tài nguyên, không tự tải mô hình/nội dung người dùng lên ngoài.
