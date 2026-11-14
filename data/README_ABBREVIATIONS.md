# Dataset viết tắt tiếng Việt — 12/11/2026

Hai file riêng, không thay dev/validation/holdout:

- **abbreviations_vi.json**: kho quy tắc phân giải dùng lúc chạy Python. 29 cách hiểu,
  23 dạng viết tắt khác nhau, có cả đối chứng bình thường và từ đa nghĩa.
- **abbreviations_examples.jsonl**: 29 mẫu phát triển, input/expected/provenance/
  review_status=draft_reference/risk_label_reference=null. Không dùng nhãn này làm
  kết luận rủi ro hoặc đưa vào runtime. Cần rà ngôn ngữ độc lập trước huấn luyện.

## Cấu trúc một cách hiểu

```json
{
  "id": "AB-CK-TRANSFER",
  "aliases": ["ck"],
  "canonical": "chuyển khoản",
  "context_any": ["tiền", "phí", "stk", "tk", "ngân hàng", "nh", "$amount"],
  "exclude_any": [],
  "note": "Nếu nhiều nghĩa cùng phù hợp thì giữ mơ hồ."
}
```

- id ổn định để truy vết; aliases là token đầy đủ, không khớp giữa một mã dài.
- canonical là cách viết đầy đủ có dấu; chỉ được dùng trên bản khớp luật.
- context_any: cần ít nhất một từ/cụm trong cửa sổ tối đa 60 ký tự chuẩn hóa mỗi
  bên, cùng câu và cùng message. $amount là mẫu số có đơn vị k/tr/nghìn/triệu/đồng;
  chỉ dùng nhận ngữ cảnh, không tự đổi số tiền hoặc tiền tệ.
- left_any/right_any tùy chọn: xét cụm liền trước/liền sau, ví dụ k + “cần”.
- exclude_any: các cụm loại trừ. Mọi nhóm điều kiện có khai báo đều phải thỏa.
- Tất cả từ/cụm là literal được escape trước khi khớp; không nhận regex người dùng.

Nếu đúng một nghĩa được hỗ trợ, trả resolved và expansion. Nếu nhiều nghĩa có căn
cứ hoặc thiếu ngữ cảnh, giữ nguyên từ, trả ambiguous/unresolved cùng alternatives,
rule_ids và câu hỏi. Không chọn nghĩa bằng cách ưu tiên mức cảnh báo cao hơn.
Resolved là lựa chọn từ vựng theo luật, không chứng nhận đúng nghĩa hoặc danh tính ngoài đời.

## Các nhóm khởi đầu

| Dạng | Cách hiểu hỗ trợ | Ràng buộc chính |
|---|---|---|
| ko, k0, hok | không | Không khớp trong mã/URL/email; chỉ dạng cấu hình |
| k | không | Cần động từ/chỉ dẫn ngay sau; không phải 500k/500 k hoặc Đơn K |
| ck | chuyển khoản / chồng / chứng khoán | Ngữ cảnh tiền / gia đình / đầu tư; có xung đột thì hỏi |
| tk | tài khoản / thiết kế / TikTok | Dựa ngữ cảnh, không mặc định tài khoản ngân hàng |
| dc, đc | được / địa chỉ | Từ ngay trước hoặc ngữ cảnh giao nhận |
| kh | khách hàng / kế hoạch | Không tự đổi thành không |
| cs | chia sẻ / chính sách | Màn hình/mã hoặc quy định/bảo hành |
| mh | màn hình / mô hình | Hiển thị hoặc học máy |
| mk | mật khẩu / mình | Ngữ cảnh giao thông tin hoặc chủ thể; thiếu thì giữ mơ hồ |
| stk | số tài khoản | Không xác minh người sở hữu |
| cccd, cmnd | căn cước công dân / chứng minh nhân dân | Giữ đúng loại giấy tờ |
| sdt, sđt | số điện thoại | Không đổi số thực |
| cskh | chăm sóc khách hàng | Vai trò tự nhận, không verified |
| nh | ngân hàng | Cần ngữ cảnh tài khoản/giao dịch |
| app | ứng dụng | Không tự xác nhận nguồn chính thức |
| ib, inbox | nhắn tin riêng | Không tự thành chuyển kênh hoặc lừa đảo |
| bh | bảo hành / bảo hiểm / bây giờ | Phải có ngữ cảnh, không đoán mọi trường hợp |

Không tự thay a/c/e/t thành đại từ, không khôi phục dấu toàn bộ tiếng Việt,
không đổi mọi k/tr thành nghìn/triệu. Từ ngoài kho hoặc viết dính như ck500k chưa
được phân giải tự động; không tách mã định danh để cố tìm từ viết tắt.

## Nối vào bộ phân tích

Chỉ áp dụng cho **POST /api/observe**, không đổi luồng Gemini /api/analyze.
`local_observation/abbreviations.py` được gọi từ normalize trước khi tách mệnh đề,
trích hành động/phủ định/đối tượng và adapter. Mỗi ký tự của từ mở rộng ánh xạ về
token gốc; quote vẫn là “ck”, “ko”, “CCCD”, không biến thành câu trích bịa.
Không thay text/messages, speaker, ID, context gốc hoặc giá trị URL/OTP/số tài khoản.

Ví dụ `ko ck tiền` có bản khớp luật `khong chuyen khoan tien`. Negation span vẫn
trích `ko`; verb span vẫn trích `ck`. API trả abbreviation_version,
abbreviation_sha256 và abbreviation_resolutions với nguồn message/context,
start/end/quote/status/expansion/alternatives/rule_ids/basis.

Không dùng context/question/tin nhắn khác để âm thầm quyết định nghĩa của một từ
trong message. URL, email, chuỗi backtick và tên mã rõ ràng được bảo vệ; các đoạn
đó cũng không được dùng làm ngữ cảnh hỗ trợ. Lời trích cảnh báo vẫn được phân giải
từ vựng nhưng giữ đúng vai cảnh báo, không biến thành request của người viết.

Sửa kho cần restart backend để nạp lại cache. Khi bổ sung từ, thêm nghĩa cạnh tranh,
đối chứng không mở rộng và fixture riêng. Không dùng đáp án validation/holdout để
thêm luật. Đây là bộ quy tắc được kiểm soát trong dự án, không phải từ điển đã có
cơ quan chuyên môn phê duyệt hoặc mô hình đã học mọi cách viết tắt.

[Báo cáo, các ví dụ và lệnh kiểm thử](../ScamShield_AI/reports/abbreviations_20261112/README.md).
