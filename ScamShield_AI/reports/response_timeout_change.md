# Tạm tắt thời hạn chờ phản hồi

Cập nhật ngày 09/11/2026. Không thay đổi chính sách phân loại rủi ro.

- `backend/local_settings.py`: đã đặt `SCAMSHIELD_DISABLE_RESPONSE_TIMEOUTS = "1"`.
  Backend không áp thời hạn toàn lượt 45 giây (trần 50 giây), thời hạn 20 giây
  mỗi lần gọi provider hoặc timeout HTTP do ứng dụng thiết lập.
- `web/app.js`, `extension/worker.js`: comment timer hủy phân tích sau 55 giây
  và phần dọn timer tương ứng. Vẫn giữ hủy khi đổi nội dung, dừng hoặc đổi phiên.
- Giữ giới hạn truy xuất local 0,8 giây và tải cấu hình extension 5 giây:
  đây không phải thời hạn chờ kết quả phân tích Gemini.
- Giữ số lần retry hữu hạn. Lỗi 503, ngắt kết nối, JSON sai hoặc bằng chứng sai
  vẫn trả lỗi; bỏ timeout không tự sửa các lỗi này. Chrome, mạng và provider
  có thể có thời hạn riêng. Request treo có thể giữ hàng đợi chờ lâu.

Khởi động lại backend, Reload extension trong `chrome://extensions`, tải lại tab.
Để khôi phục: đổi cấu hình trên thành `"0"` (biến môi trường cùng tên có ưu tiên
cao hơn), bỏ comment hai timer và phần dọn timer của hai client, rồi khởi động lại.
Các kết quả benchmark trước thay đổi vẫn là phép đo cấu hình cũ.

## Vì sao high thành need_context trong bộ 30 ca

`SG-31` và `SG-61`: Gemini cuối vừa tạo `risk_links` vừa đánh dấu request/support
chưa rõ quan hệ (`relation`). `two_pass.finalize` giữ loại bất định này làm yếu tố
chặn. `hybrid.adjudicate` bỏ link có một đầu bất định, nên không còn cơ sở high
theo chính sách hiện tại và trả `need_context`. Đây là bất nhất suy luận của model
kết hợp với chính sách backend thận trọng; không phải RAG không tìm thấy nguồn.
Không phải mọi thiếu thông tin đều buộc hạ mức: một link khác hợp lệ hoặc yêu cầu
giao OTP đủ căn cứ vẫn có thể làm kết quả high.

Hai ca bình thường `SG-13`, `SG-14` cũng thành need_context vì so khớp sơ bộ đòi
cùng action. Khi Gemini đổi nhãn hành vi giữa hai lượt, cùng đoạn có thể bị ghi
thành xung đột. Đây là lỗi giới hạn điều phối cần xử lý riêng.

Hướng sửa tiếp theo: phân biệt thiếu danh tính với thiếu bản chất hành vi; kiểm tra
nhất quán giữa risk_links và relation uncertainty; đối chiếu lại với câu gốc và
giải quyết đổi nhãn cùng bằng chứng. Không tự chọn mức cao nhất giữa hai lượt.
Nếu dùng 30 ca này để sửa, chỉ dùng chúng làm hồi quy và đo chất lượng cuối trên
tập độc lập mới. Chi tiết tại `six_groups_30/MANUAL_REVIEW.md`.
