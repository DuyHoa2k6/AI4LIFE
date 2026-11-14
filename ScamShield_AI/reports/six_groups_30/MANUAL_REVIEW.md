# Rà kỹ thuật các ca chưa đạt

Đây là rà của người triển khai trên 30 ca tổng hợp, không phải rà nhãn độc lập.
Không chỉnh model/prompt/quy tắc theo các lỗi trong phiên chạy này.

## 5 ca có kết quả nhưng khác kỳ vọng

| Ca | Kỳ vọng → thực tế | Điều quan sát được |
| --- | --- | --- |
| SG-31 điều khiển ngân hàng để hoàn phí | high → need_context | Model trích đúng quyền điều khiển, mở ngân hàng và điều kiện giải ngân, có risk_links; nhưng đồng thời đánh dấu các request là relation chưa rõ. Backend giữ bất định và không nâng high. |
| SG-61 xác nhận hàng chưa tới để hoàn tiền | high → need_context | Nhận ra yêu cầu và điều kiện hoàn tiền nhưng đánh dấu request/support đều bất định relation. Cơ chế bị hạ mức dù câu gốc nêu điều kiện trực tiếp. |
| SG-13 trả khoản vay đã đối chiếu | clear → need_context | Model lượt cuối trả benign có context quote hợp lệ (end=121 đúng độ dài 121), không yêu cầu thêm thông tin. Tuy nhiên lượt đầu gán action=other, lượt cuối gán transfer_funds. So khớp sơ bộ bắt buộc cùng action nên tạo rule-conflict cho cùng câu. Đây là hạn chế điều phối/taxonomy, không phải context quote sai. |
| SG-14 bài cảnh báo về phí hoàn cọc | clear → need_context | Lượt cuối đã có quoted_warning/denial, nhưng một quan sát sơ bộ chưa ghép được với finding cuối có action khác. rule_conflicts=1 khiến cần làm rõ. Đúng vai cuối chưa đủ để giải quyết khác biệt taxonomy giữa các bước. |
| SG-35 chưa biết loại quyền | need_context → suspicious | Model gán grant_access/request rồi chỉ ghi bất định identity/purpose. Bộ quyết định cho phép suspicious đồng thời hỏi thêm. Kỳ vọng của ca là cần biết quyền gì trước vì quyền thông báo và điều khiển khác nhau. Cần rà lại ranh giới nhãn và cách biểu diễn loại quyền chưa biết; đây là phán đoán chức năng của người viết, chưa phải lỗi được hai người độc lập xác nhận. |

## 5 ca lỗi

| Ca | Mã | Bước |
| --- | --- | --- |
| SG-51 nhiệm vụ miễn phí rồi ứng vốn | PROVIDER_UNAVAILABLE | Observation HTTP 503 sau hai attempt |
| SG-12 đệm số dư để nhận tiền công | PROVIDER_TIMEOUT | Review, có retry rồi hết ngân sách |
| SG-32 đòi quyền quản trị trang | PROVIDER_UNAVAILABLE | Review HTTP 503 sau hai attempt |
| SG-62 tắt cảnh báo ví và ký chấp thuận | PROVIDER_TIMEOUT | Review |
| SG-44 bài cảnh báo APK | EVIDENCE_INVALID | Đã có hai đầu ra model; quote của lượt cuối không khớp bản gốc, backend loại toàn bộ finding cuối |

SG-44 có các lỗi như đổi “với” thành “vối”, “người” thành “ngưối” và thay dấu mở lời
trích. Null offset chỉ giúp tìm vị trí của quote nguyên văn; không sửa được quote bị
model viết sai. Backend trả chưa kiểm tra được thay vì chấp nhận đoạn không tồn tại.

Không suy ra 503 là hết credit hoặc do một nguyên nhân tài khoản cụ thể. Không có dữ
liệu để khẳng định model không hiểu các ca dịch vụ lỗi; hệ thống vẫn không bàn giao
được cảnh báo nên các ca này phải nằm trong tỷ lệ chưa đạt toàn luồng.

## Điểm đã làm được trong phạm vi thử

- Hai ca đòi OTP/chuỗi sáu số trong SMS được cảnh báo high; tự nhập và lời cảnh báo trả clear.
- APK kèm quyền để nhận trợ cấp trả high; APK chưa rõ lý do trả suspicious, không tự bịa thêm yêu cầu tiền.
- Nhiều tình huống bình thường trả clear; không ghi nhận high/suspicious trên 12 ca normal,
  nhưng hai ca normal bị need_context và một ca lỗi, nên không thể tuyên bố xử lý normal hoàn hảo.
- 43/43 quote trong các phản hồi thành công khớp. Đây không phải điểm đúng ngữ nghĩa hoàn toàn;
  các ca sai mức vẫn có quote đúng và một quote sai ở ca lỗi bị loại khỏi phản hồi cuối.
- Cả sáu ca thiếu thông tin có câu hỏi; một ca trong số đó nhận suspicious khác kỳ vọng.
- Không có nguồn chính thống đủ duyệt nên không có citation hoặc verified_match.

## Ưu tiên sửa sau khi kết thúc phép đo

1. Biểu diễn rõ quan sát đến từ regex hay Gemini đầu; giải quyết reclassification khác
   action khi cùng câu/người nói mà không cho phép mất request nguy hiểm im lặng.
2. Tách chưa biết loại quyền/loại mã khỏi chỉ thiếu danh tính/mục đích. Rà nhãn suspicious
   và need_context bằng hai người trước khi đổi chính sách để khớp ca riêng.
3. Cải thiện tính nhất quán giữa điều kiện nêu rõ, risk_links và relation uncertainty.
   Không bỏ mọi uncertainty hoặc ưu tiên nhãn cao nhất để tăng điểm.
4. Nâng độ ổn định provider và giảm thời gian hai lượt. Nhánh local chỉ mất vài ms,
   chưa có dữ liệu để quy riêng mạng hay model là nguyên nhân thời gian provider cao.
5. Giữ tập này làm regression công khai nếu dùng để sửa. Chấm tập độc lập khác cho số liệu cuối.
