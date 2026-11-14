# Rà kết quả 10 hội thoại — 13/11/2026

Đây là nhận xét phát triển sau khi đã lưu dự đoán. Tệp người dùng có lời nhắc
về nhãn kỳ vọng nhưng không chứa bảng đáp án cuối cùng. Mức đề xuất dưới đây
do người thực hiện bài kiểm thử đặt để thảo luận, chưa phải nhãn chuyên gia.
Không tính accuracy/precision/recall khi chưa chốt nhãn độc lập.

| Ca | Thực tế | Mức đề xuất để rà | Lỗi hoặc điều đã nhận ra |
|---|---|---|---|
| 01 | need_context | suspicious | Có yêu cầu chuyển tiền và đừng gọi xác minh, nhưng 0 quan hệ. Chưa chuẩn hóa việc “đổi sang tài khoản nhận tiền mới”/tài khoản cá nhân so với tài khoản công ty thành dữ kiện đổi nơi nhận có liên hệ. |
| 02 | need_context | suspicious, cần rà ngưỡng high | Nhận ra chuyển tiếp tiền, nhưng chưa biểu diễn chuỗi nhận tiền không rõ nguồn → chuyển cho bên khác → giữ một phần → khai mục đích khác khi ngân hàng hỏi. Không được khẳng định tiền phạm pháp. |
| 03 | suspicious | high | Luật R-CONTROL nhận ra giữ hộ chiếu, nhưng chưa nối đầy đủ việc đi theo nhóm, chưa biết địa chỉ/hợp đồng, không được tự rời chỗ ở và muốn về phải trả chi phí chưa xác định. Không được tự xác nhận đã bị mua bán người. |
| 04 | need_context | high | Trích được yêu cầu chuyển tiền bảo chứng, nhưng “hệ thống sẽ trả cả vốn lẫn tiền bảo chứng” chưa được nối thành quyền lợi/điều kiện, 0 quan hệ. Không phải thiếu câu trả lời của người dùng về mục đích nộp. |
| 05 | suspicious | high | R-ACCESS nhận ra cài ứng dụng/cấp quyền; chưa dùng chuỗi kiểm soát từ xa → mở ngân hàng làm căn cứ kết hợp mức cao. Mã kết nối từ xa không phải mã OTP; không được tự gán app là mã độc. |
| 06 | need_context | high | Chỉ nhận ra yêu cầu chuyển tiền; chưa trích lời đe dọa từ “gửi cho chỗ làm” với đối tượng ảnh/danh sách bạn bè. Ảnh bị người dùng phủ nhận là thật không làm mất hành vi đe dọa phát tán. |
| 07 | high | high | R-CODE-IDENTITY đã nối yêu cầu đọc mã với lời người dùng xác định đó là mã đăng nhập; không cần xác minh người gửi có thật là nhân viên. |
| 08 | need_context | high | Nhận ra trạng thái rút tiền nhưng chưa hiểu “hoàn tất nhiệm vụ 3 triệu” là bước chi trả có điều kiện trong chuỗi đã nộp tiền, 0 quan hệ. Việc đã trả thưởng ít ban đầu không chứng minh nhóm đáng tin. |
| 09 | need_context | suspicious | Nhận ra chuyển tiền/đừng gọi, nhưng không nối được danh tính tự nhận, tài khoản mới, khác người đứng tên và trì hoãn xác minh qua các lượt nói. Chỉ có lời mô tả bản ghi âm, không có phân tích âm thanh/deepfake. |
| 10 | suspicious | high | R-DATA nhận ra yêu cầu giấy tờ; “thông tin đăng nhập ứng dụng” bị trích thành login, chưa thể hiện yêu cầu giao thông tin truy cập cho bên khác. Phí trước và ngăn xác minh chưa được liên kết đầy đủ. |

Các sai sót nằm chủ yếu trước hoặc tại tầng liên kết ngữ nghĩa, không phải lỗi
HTTP, timeout hoặc xung đột Gemini. Bộ phân tích đang chạy Python cục bộ.
Các câu hỏi chung về “nộp để nhận/rút tiền” không phù hợp với một số tình huống
vì bộ chọn câu hỏi đang thiếu loại hành vi tương ứng.

## Giới hạn của bước rà

- Chưa có đối chứng bình thường xen kẽ trong chính bộ 10 này; không đo được
  cảnh báo nhầm, specificity hoặc precision thực tế từ một bộ chỉ gồm ca nghi ngờ.
- So khớp quote chỉ kiểm tra chứng cứ đúng ký tự, không chứng minh ngữ nghĩa,
  vai trò hoặc quan hệ đều đúng. Có thể trích nhiều hành động không phù hợp.
- Mức `complete` chỉ nói pipeline chạy xong, không khẳng định hiểu đầy đủ hội thoại.
- Nhãn vai người nói được chuyển thành speaker_1/2/3 và giữ nhất quán. Tên
  phương thức, tiêu đề và mục tiêu kiểm tra không được gửi API. Các mô tả người
  nói như “tự nhận kỹ thuật viên” nằm ở metadata; không biến thành sự thật đã xác minh.
- Chưa dùng 10 câu để sửa bộ diễn giải trong lượt kiểm thử này. Nếu dùng sửa
  tiếp, phải coi chúng là development, không tái dùng làm holdout độc lập.
