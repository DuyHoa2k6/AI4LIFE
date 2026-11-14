# Biến thể ngữ nghĩa và ngữ cảnh — phiên bản 1.0

24 ca tổng hợp bổ sung; **tất cả thuộc development**, không phải mẫu độc lập,
chưa được người rà độc lập/chuyên gia duyệt. Không sửa dataset cũ hoặc holdout.
Các ca gần nghĩa/cùng họ phải được giữ cùng nhóm khi xây tập đánh giá độc lập
trong tương lai, tránh rò rỉ qua các câu chỉ đổi tên vật hoặc cách diễn đạt.

## Các file

- `inputs.jsonl`: ID, họ tình huống, nhóm biến thể và đầu vào `text`. API chỉ
  nhận đối tượng `input`; không gửi ID, nhãn hoặc câu trả lời mong đợi vào BE.
- `expected.jsonl`: mức kỳ vọng, vai trò lời nói, quan hệ ngữ nghĩa, vai thực
  hiện/bị tác động và span gán thủ công. Offset tính theo Unicode code point,
  end loại trừ; `identity_verified=false`.
- `manifest.json`: số lượng, phiên bản, nguồn tổng hợp, phạm vi và SHA-256.

Đây là định dạng regression bổ sung, không giả làm bộ CaseInput/Annotations
đầy đủ. Các trường quan hệ và vai trò là chú giải mục tiêu, chưa phải nhãn
chuyên gia và chưa được chấm ngữ nghĩa tự động toàn diện.

## Ý nghĩa được đối chiếu

| Ý nghĩa | Dạng diễn đạt | Cần kiểm tra ngữ cảnh |
|---|---|---|
| Yêu cầu chi thêm | nộp phí, bổ sung khoản đảm bảo, mua gói xác thực | Có bắt buộc để nhận/rút tiền không? |
| Quyền lợi được hứa | nhận lại tiền, nhả lại vốn, giải phóng số dư | Khoản của ai, lời hứa của ai, chưa xác minh khả năng trả |
| Giao tài sản | giao máy, cho người mang đàn đi, để tài xế lấy tủ | Đã nhận tiền, chưa nhận, hay không có thông tin? |
| Chưa xác nhận tiền | chưa thấy tiền vào, chưa báo có, chưa ghi nhận thanh toán | Lời người nhận hay giả định/cảnh báo, có cùng giao dịch không? |

Có ca yêu cầu nguy hiểm, mua tùy chọn, mua hàng thông thường, lời tự kể, lời
cảnh báo trích dẫn, phủ định, thiếu bối cảnh, giao sau khi báo nhận đủ tiền,
khác giao dịch, khác bên hưởng lợi và emoji. Hai ca M/NOVEL-ASSET đã biết là
ca lỗi được đưa vào development, không được gọi là ca độc lập sau khi sửa.

## Liên hệ với runtime

Backend **không quét các câu/nhãn trong dataset để quyết định** và không có
huấn luyện mô hình. Runtime tải `../semantic_phrases.json`, dùng các nhóm mẫu
để đề xuất ý nghĩa; bộ phân vai, điều kiện, quan hệ, phủ định và rulebook vẫn
phải kiểm tra trước khi chọn cảnh báo. Từ “mua”, “tài xế” hoặc “nhả vốn” riêng
lẻ không đủ để gán high. Mẫu config không có nhãn risk_status của từng ca.

Thay đổi config cần khởi động lại backend vì biểu thức được nạp theo tiến trình.
Không dùng nhãn máy để tự đổi trạng thái dữ liệu thành reviewed.

## Lệnh kiểm tra

Từ thư mục ứng dụng `ScamShield_AI`:

```powershell
python -m unittest tests.test_semantic_variants -q
python check_semantic_variants.py --output reports/semantic_variants_20261113/run_new
```

Script gửi input và lưu tất cả dự đoán trước khi đọc expected. Đo mức cảnh báo
và tính chính xác ký tự của bằng chứng; không coi đó là đánh giá độc lập về
toàn bộ vai trò, ý nghĩa và quan hệ. Thư mục đầu ra phải chưa tồn tại.
