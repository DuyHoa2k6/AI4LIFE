# Rà kết quả phân tích — 10/11/2026

Rà kỹ thuật bởi người triển khai trên 24 ca tổng hợp, không phải hội đồng gán nhãn
độc lập. Không sửa prompt/quy tắc hoặc chạy lại ca chưa đạt trong phiên này.

## Ca chưa cảnh báo đúng mức: NW-02

Đầu vào:

> Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang
> tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.

Kỳ vọng đã chốt trước: **high** vì việc chuyển tiền trước là điều kiện nhận khoản
hoàn lớn hơn. Thực tế: **need_context**, dù vẫn khuyên không chuyển tiền khi chưa rõ.
Không gọi đây là clear hoặc hoàn toàn không đưa khuyến cáo; điểm chưa đạt là không
nâng cảnh báo đúng mức theo hành vi và quan hệ đã thể hiện trong đầu vào.

1. Gemini trích đúng request chuyển 1,2 triệu và điều kiện khoản hoàn 12 triệu.
2. Lượt rà đầu vừa có risk_link vừa gán bất định relation cho support, nên backend
   phát hiện `risk_link_and_blocking_uncertainty` và yêu cầu sửa một lần.
3. Sau sửa, Gemini xóa risk_link, chuyển sang uncertain_relations và giữ relation
   chưa rõ. Kết quả đã nhất quán về cấu trúc nhưng vẫn đánh giá thiếu chắc chắn so
   với kỳ vọng của người viết ca. Backend vì thế trả need_context.

Đây là minh chứng: kiểm tra nhất quán giúp ngăn JSON tự mâu thuẫn, nhưng không tự
chứng minh suy luận ngữ nghĩa đúng. Không được diễn giải một lần sửa thành một lần
nhận diện thành công. Có thể cần thêm ca validation về diễn đạt thay thế, liên hệ
đại từ “dấu này” và điều kiện thanh toán; phải đo trên dữ liệu độc lập sau khi chỉnh.

## Quan sát theo nhóm

| Ca | Vai/người nói/quan hệ đã rà |
| --- | --- |
| NW-01–03 | Cả ba có request chuyển tiền và điều kiện nhận tiền. NW-03 giữ đúng người nói quan_ly xuyên hai tin. NW-02 là ca bỏ lỡ mức high nêu trên. |
| NW-04 | Yêu cầu trả tiền ăn có context quote hợp lệ; clear phù hợp trong thông tin cung cấp. Không chứng nhận người nhận thật. |
| NW-05–07 | Đọc chuỗi đăng nhập, giao mật khẩu, giao cụm khôi phục: đều là yêu cầu giao bí mật cho người khác, không phải tự nhập. |
| NW-08 | Người dùng tự thao tác và phủ định việc giao mã, clear. |
| NW-09–11 | Quyền điều khiển, quản trị toàn quyền, chia sẻ ngân hàng gắn với quyền lợi; high. NW-11 giữ speaker hotro đúng cả hai tin. |
| NW-12 | Quyền thông báo lịch với context giới hạn rõ, clear. |
| NW-13–15 | Cài phần mềm ngoài nguồn đã biết, trợ năng/điều khiển hoặc tắt bảo vệ để nhận tiền; có request và điều kiện. NW-13/15 trích cả cài đặt lẫn cấp quyền. |
| NW-16 | Trích lời dụ trong bản tin và lời khuyên không cài; quoted_warning/denial, không thành request. |
| NW-17–19 | Tiền giữ suất sau nhiệm vụ nhỏ, áp lực giả cơ quan, bảo lãnh để rút lợi nhuận; high. NW-17 gắn yêu cầu với người tuyển dụng, không gắn vào lời ứng viên. |
| NW-20 | Quà thư viện không yêu cầu tiền/mã/ngân hàng, clear. |
| NW-21–23 | Xác nhận nhận hàng trước, ký quyền chi tiêu token, giao bộ giấy tờ/video qua kênh riêng để nhận quyền lợi; high theo chính sách và kỳ vọng đã đặt. |
| NW-24 | Chỉ xác nhận sau khi kiểm tra và phủ định xác nhận trước/ngoài sàn, clear. |

51/51 quote của phản hồi thành công khớp code point và khoảng vị trí; 0 sai
message/speaker reference. Rà vai chính của các ca cho kết quả như bảng. Chưa chấm
đầy đủ ngữ nghĩa mọi câu trong tám answers; không lấy quote đúng làm chứng minh
toàn bộ giải thích đúng.

## Giới hạn còn quan sát được

- NW-06 có một finding other/unknown dư trên đoạn đã nhận ra là yêu cầu giao mật
  khẩu. NW-10 có finding transfer_funds/unknown cho lời người gửi hứa chuyển tiền
  tài trợ. Hai ca vẫn high đúng nhưng cách trích có nhiễu; cần phân biệt ai là người
  được yêu cầu thực hiện với ai chỉ hứa thực hiện.
- NW-18 không giữ riêng finding danh tính tự nhận “cán bộ xử lý hồ sơ” trong kết
  quả cuối. Mức high đúng nhưng chi tiết tám câu hỏi có thể thiếu thông tin vai trò.
- Một số ca high vẫn hỏi danh tính/mục đích khá chung; phiên này không chấm điểm
  riêng tính hữu ích của câu hỏi. Chưa triển khai tính năng hỏi linh hoạt mới.
- NW-23 cố ý mô tả gửi giấy tờ/video riêng cho người đề nghị vay chưa xác minh.
  Kỳ vọng high là phán đoán tác giả về nguy cơ dữ liệu; không chứng minh mọi quy
  trình KYC hoặc mọi điều kiện duyệt vay là lừa đảo. Cần đối chứng thêm KYC chính
  thức, kênh xác minh và mục đích hợp lệ trước khi suy rộng tỷ lệ báo nhầm.
- Sáu ca normal không đủ đại diện cho ngân hàng, hỗ trợ kỹ thuật, thanh toán hợp
  pháp và các ca ranh giới thực tế. High precision 100% trên mẫu này không phải
  độ chính xác tổng quát 100%.

## Hiệu năng và nguồn

API thành công 24/24. Có một HTTP 503 từ provider nhưng retry hữu hạn đã hồi phục;
không có lỗi cuối cùng ở API. Các thời gian chờ của ứng dụng đang tạm tắt theo yêu
cầu trước, không phải đã nghiệm thu timeout.

Hai lượt model chiếm phần lớn thời gian: median lượt đầu khoảng 3,252 giây, lượt
rà khoảng 3,404 giây; truy xuất local median 2,714 ms. Không có dữ liệu để tách riêng
thời gian mạng và thời gian suy luận phía Google. API p95 9,592 giây, chưa đạt mốc
2 giây nếu dùng mục tiêu cũ. Không đo độ trễ web/extension hoặc tải nhiều người dùng.

Cả 24 ca có official_sources=no_approved_sources. Đây là phép đo phân tích văn bản
và đối chiếu local của cấu hình hiện tại; không phải đánh giá RAG có nguồn thật.
