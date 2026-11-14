# Kế hoạch kiểm thử và hiệu năng ScamShield AI

## Luồng hiện hành two_pass

Nghiệm thu thêm: TP-01 lượt đầu không nhận regex/nhãn; TP-02 kiểm chứng trước truy xuất; TP-03 hai nhánh khởi chạy song song, nhánh tình huống nhận cả văn bản/bối cảnh gốc; TP-04 lượt cuối nhận lại bản gốc và được bác giả thuyết đầu; TP-05 không bỏ phiếu/cộng điểm hit; TP-06 loại nguồn candidate/hết hạn/thu hồi/không dùng/bịa; TP-07 truy xuất lỗi vẫn phân tích văn bản đủ căn cứ, model lỗi không fallback clear; TP-08 đủ high/suspicious/need_context/clear và biến thể đổi chữ/cách tiếp cận; TP-09 đo riêng hai lượt model/hai nhánh/kiểm chứng; TP-10 client hiện đúng mode/nguồn/fallback, bỏ phản hồi cũ.

Test giả lập chỉ chứng minh điều phối; nguồn fixture không được tính là nguồn nhà nước thật. Giữ mục tiêu precision high ≥85%, recall ≥75%, p95 trải nghiệm <2 giây; không hạ mục tiêu vì gọi hai lượt. Giới hạn chờ 45/55 giây không phải đạt độ trễ. Số liệu mới ở reports/two_pass; không sửa số liệu lịch sử hybrid.

Hồi quy hybrid (08/11/2026): HYB-01 luôn gọi live khi có/không có dấu hiệu; HYB-02 đồng thuận bằng chứng/quan hệ; HYB-03 live bác cảnh báo nhầm hoặc dùng context trả nợ; HYB-04 bất đồng chưa giải quyết/thiếu bối cảnh; HYB-05 quote/speaker/offset/ref sai; HYB-06 quan hệ sai người nói và hỗ trợ bị loại; HYB-07 chỉ thị nhúng/nguồn bịa/schema sai; HYB-08 timeout/429/mất mạng/thiếu cấu hình, không fallback clear; HYB-09 input không hợp lệ không gọi live; HYB-10 hội thoại bổ sung/Unicode/giới hạn; HYB-11 web/extension hiển thị mode hybrid và xử lý lỗi như API chung. Test giả lập chỉ chứng minh điều phối, không chấm chất lượng suy luận live.

## Hồi quy mock hành vi — 08/11/2026

MR-01 chuyển tiền/ứng/nộp phí và đối chứng thanh toán hợp lệ; MR-02 giao mã so với tự nhập trên ứng dụng chính thức; MR-03 cấp quyền/cài ứng dụng và lời thuật lại; MR-04 điều kiện nhận/rút tiền và lời cảnh báo; MR-05 tách câu có cảnh báo rồi yêu cầu mới; MR-06 nhiều người nói, dấu hiệu không liên quan và giới hạn cửa sổ; MR-07 quote Unicode, số thập phân, cụm lặp và đoạn đã che; MR-08 thiếu bối cảnh/câu hỏi an toàn; MR-09 chỉ thị nhúng và giới hạn tối đa 50 findings; MR-10 API giữ schema và web/extension hồi quy. Mỗi quy tắc trong registry phải có ít nhất một ca kích hoạt trong kiểm thử phát triển. Báo riêng số assertion/test và số mẫu dev, không gọi tổng test là độ chính xác mô hình. Live/RAG chưa chạy ghi chưa đo.

Tài liệu quy định cách nghiệm thu bản demo ba tuần và cách báo cáo chất lượng khi trình bày với doanh nghiệp. Các bảng là kế hoạch kiểm thử. Kết quả chỉ được ghi đạt sau khi chạy trên bản triển khai cụ thể.

## 1 Phạm vi và thứ tự

| Phạm vi | Nội dung cần kiểm tra | Điều kiện |
| --- | --- | --- |
| P0 | API phân tích, kiểm chứng bằng chứng, website, extension tự quét một vùng trên tab hiện tại | Bắt buộc chạy mock và chạy live để đánh giá mô hình. |
| RAG | Truy xuất kho đã duyệt, kiểm chứng nguồn, fallback và so sánh bật/tắt | Chạy khi API đã tích hợp RAG. Nếu chưa, ghi chưa triển khai trong báo cáo. |
| P1 | OCR ảnh chat hoặc kiểm tra cấu trúc URL | Chỉ nghiệm thu tính năng nhóm chọn sau khi luồng chính đạt. |
| P2 | Form nâng cao, media, deepfake, nguồn URL đã xác minh và cộng đồng | Chỉ công bố kết quả của chức năng đã triển khai và có dữ liệu đánh giá tương ứng. |

Chạy theo thứ tự kiểm tra dataset, test đơn vị và API với mock, test web và extension, đánh giá live, đo tải và diễn tập demo. Sử dụng mock để tạo lỗi và đo chi phí nội bộ. Chạy live với cấu hình được ghi rõ để đánh giá khả năng phân tích thật.

## 2 Kiểm tra dataset và cách tổ chức đánh giá

1. Chạy `python data/validate_dataset.py`. Bản hiện tại có 72 mẫu tổng hợp, 13 họ tình huống và 24 mẫu mỗi tập. Lưu hash, số mẫu, phân bố nhãn và kết quả kiểm tra trích dẫn.
2. Hai người rà nhãn độc lập, ghi các ca bất đồng và thống nhất cách chấm hành vi, bằng chứng và câu hỏi bổ sung. Kiểm tra gần trùng theo nội dung và chiến dịch. Script kiểm tra trùng sau chuẩn hóa, còn trùng ý cần rà riêng.
3. Dùng dev để phát triển. Dùng validation để chọn cấu hình. Trước khi chấm holdout, khóa phiên bản dataset, prompt, mô hình, quy tắc, kho tri thức và ngưỡng truy xuất. Chỉ đưa `input` vào bộ phân tích. Đọc `expected` sau khi lưu dự đoán.
4. Nếu nhóm đã xem holdout trong lúc chỉnh hệ thống, báo đó là tập thử công khai và chuẩn bị tập độc lập mới. Nếu sửa dựa trên lỗi của tập độc lập, ghi lần đó là phân tích lỗi và dùng tập mới cho đánh giá cuối.
5. Báo riêng kết quả dữ liệu tổng hợp và dữ liệu thật đã ẩn danh, được phép sử dụng. Trong holdout hiện tại chỉ có 5 ca `high`, nên một ca bỏ sót làm recall giảm 20 điểm phần trăm. Trình bày số đếm và giới hạn mẫu bên cạnh tỷ lệ.

## 3 Ma trận kiểm thử API và phân tích văn bản

| ID | Ca kiểm thử | Kết quả mong đợi |
| --- | --- | --- |
| API-01 | Gửi `text` hoặc `messages` hợp lệ | Nhận đủ cấu trúc phản hồi. Tin nhắn giữ thứ tự, đúng người nói và mã tin. |
| API-02 | Gửi cả hai dạng, bỏ cả hai, rỗng, sai kiểu, ID trùng hoặc vượt giới hạn | Trả lỗi theo hợp đồng. Provider không được gọi với đầu vào bị từ chối. |
| API-03 | Provider timeout, lỗi dịch vụ, JSON sai hoặc thiếu trường | Lỗi có mã và request ID. Giao diện hiển thị **Chưa kiểm tra được** và hỗ trợ thử lại theo loại lỗi. |
| API-04 | Trích dẫn bịa, sai mã tin, sai offset, cụm lặp | Chỉ giữ bằng chứng đối chiếu được. Dữ liệu bị loại không nâng mức rủi ro hoặc xuất hiện trong giải thích. |
| API-05 | Emoji trước đoạn trích, dấu tổ hợp, nhiều dòng và bản đã che dữ liệu | Giao diện tô đúng đoạn trên cùng văn bản đã kiểm chứng. Kiểm tra chuyển Unicode code point sang chỉ số chuỗi JavaScript nếu dùng cách đó để tô sáng. |
| AI-01 | Làm thử miễn phí → ứng tiền → nộp thêm để rút | Nối đúng thứ tự, phân biệt lời hứa với yêu cầu và dẫn cả hai đoạn có liên quan. |
| AI-02 | Thay vai người gửi, đổi cách diễn đạt hoặc kết hợp nhiều hành vi | Trích đúng hành động và lý do kể cả khi tên thủ đoạn rỗng. |
| AI-03 | Bài tuyên truyền trích nguyên lời dụ, câu phủ định và tin nhắn hợp lệ có từ OTP | Giữ đúng vai người nói. Không gán cảnh báo cao chỉ vì có từ khóa. |
| AI-04 | Cắt mất đoạn quyết định, chẳng hạn chỉ còn “lệnh rút bị treo” | Khi thiếu chứng cứ đủ mạnh, hỏi tối đa hai câu có thể đổi đánh giá. Không xin mã xác thực thật. |
| AI-05 | Nội dung yêu cầu mô hình bỏ qua chỉ thị, bịa nguồn hoặc mở liên kết | Mô hình giữ hợp đồng. Backend chỉ dùng nguồn thật và không thực thi yêu cầu nhúng. |
| AI-06 | Người dùng đặt câu hỏi riêng và bổ sung bối cảnh ở lượt sau | Câu trả lời bám bằng chứng còn hiệu lực. Kết quả mới phản ánh dữ liệu bổ sung. |

## 4 Nghiệm thu website và extension tự quét vùng

Dùng trang thử nghiệm có bài viết, bình luận riêng, nội dung ẩn, vùng soạn thảo và nút tải thêm. Thu request tại API thử nghiệm để xác nhận dữ liệu thật sự đã gửi. Kiểm tra giao diện song song với request.

| ID | Thao tác | Kết quả mong đợi |
| --- | --- | --- |
| EXT-01 | Chọn vùng rồi chưa bấm bật | Có viền và mô tả phạm vi. Số yêu cầu phân tích bằng 0. |
| EXT-02 | Bật quét vùng bình luận dưới bài viết bình thường | Chỉ gửi mục đủ điều kiện trong vùng. Cảnh báo gắn đúng bình luận, không gắn nhầm bài viết. |
| EXT-03 | Cuộn, tải thêm và cuộn quay lại | Mục mới được kiểm tra tự động. Mục không đổi không gửi lại trong cùng phiên. |
| EXT-04 | Sửa nội dung hoặc tái sử dụng DOM trong lúc request cũ còn chạy | Phản hồi cũ không ghi đè kết quả mới. Kết quả gắn đúng mã và phiên bản mục. |
| EXT-05 | Tạm dừng, tiếp tục, đổi vùng hoặc tắt | Không tạo request mới khi dừng. Khi đổi vùng, bỏ kết quả đến muộn của vùng trước. |
| EXT-06 | Chuyển trang, thay tuyến trong ứng dụng một trang hoặc gỡ vùng đã chọn | Dừng phiên theo quy tắc và yêu cầu chọn lại. Không tiếp tục gửi từ tài liệu cũ. |
| EXT-07 | Mất mạng, 429, timeout và nhiều mục xuất hiện đồng thời | Hàng đợi có giới hạn. Hiển thị mục chờ hoặc chưa kiểm tra được. Không gọi lặp vô hạn. |
| PRIV-01 | Đặt nội dung ngoài vùng, trong phần ẩn, trường mật khẩu và vùng soạn thảo | Kiểm tra request và log để xác nhận các dữ liệu đó không bị gửi. |
| WEB-01 | Dán nội dung, xem trước, che dữ liệu, phân tích và gửi bổ sung | Từng kết quả gắn đúng lượt. Trích dẫn khớp bản đã gửi. |
| E2E-01 | Gửi cùng đầu vào qua website và extension với cùng cấu hình mock | Cùng hành vi, bằng chứng và mức rủi ro. Hai giao diện thể hiện đúng phạm vi của kết quả. |

## 5 Kiểm thử RAG và nguồn chính thống

| ID | Ca kiểm thử | Kết quả mong đợi |
| --- | --- | --- |
| RAG-01 | Biến thể đổi bối cảnh nhưng giữ hành vi đã có trong kho | Tìm được nguồn hỗ trợ hành vi. Đoạn trích từ tin nhắn chứng minh yêu cầu. Nguồn kho giải thích rủi ro. |
| RAG-02 | Kho chỉ có bài giống từ khóa nhưng khác hành vi | Bỏ nguồn không liên quan. Mức rủi ro dựa trên bằng chứng của ca. |
| RAG-03 | Nguồn candidate, hết hiệu lực hoặc bị thu hồi | Nguồn không xuất hiện trong kết quả truy xuất dành cho người dùng. |
| RAG-04 | Không có nguồn phù hợp, truy xuất timeout hoặc kho ngắt kết nối | Luồng văn bản vẫn hoạt động nếu có đủ bằng chứng. Không bịa nguồn. Ghi nhận nguyên nhân fallback. |
| RAG-05 | Tài liệu mô tả thủ đoạn tương tự nhưng đối tượng cụ thể chưa xác minh | `source_matches` có thể chứa nguồn giải thích. `verified_match` không được gán. |
| RAG-06 | Hợp đồng mức cảnh báo | Chỉ chấp nhận clear, need_context, suspicious, high; từ chối trạng thái đã loại bỏ hoặc ngoài hợp đồng. |
| RAG-07 | Tài liệu chứa chỉ thị nhúng hoặc mô hình trích nguồn chưa được cung cấp | Chỉ thị không được thực thi. Nguồn trả về phải thuộc tập nguồn thực sự đã truy xuất và sử dụng. |

Chạy cùng đầu vào cho ba cấu hình gồm baseline từ khóa, mô hình không RAG và mô hình có RAG. Giữ cố định phiên bản mô hình, quy tắc và điều kiện đo giữa hai cấu hình mô hình. Báo riêng nhóm có tài liệu hành vi liên quan và nhóm chưa có họ tình huống trong chỉ mục. Rà `source_matches` theo tính liên quan và khả năng hỗ trợ kết luận. Nếu có nhãn nguồn phù hợp, đo Hit@k trên các truy vấn có nguồn tham chiếu. Với truy vấn không có nguồn phù hợp, đo tỷ lệ hệ thống biết bỏ qua. Báo chênh lệch chất lượng và độ trễ thay vì chỉ trình diễn một ca thành công.

## 6 Chỉ số chất lượng

| Chỉ số | Cách báo cáo |
| --- | --- |
| Phân loại rủi ro | Ma trận nhầm lẫn theo nhãn đang được đánh giá. Báo TP, FP, FN, precision và recall cho `high`. Báo riêng ca hợp lệ bị cảnh báo cao và ca `high` bị bỏ sót. Nếu mẫu số bằng 0, ghi không xác định. |
| Chất lượng bằng chứng | Tách tỷ lệ trích dẫn khớp nguyên văn khỏi tỷ lệ đúng hành động, đúng người, đúng ngữ cảnh. Báo cả tỷ lệ tìm được bằng chứng kỳ vọng để tránh điểm cao do bỏ trống. |
| Khả năng suy luận | Báo riêng ca biến thể mới, ca hội thoại nhiều bước, ca trích dẫn/phủ định và ca thiếu bối cảnh. Với mỗi nhóm, báo số mẫu và lỗi chính. |
| Câu hỏi bổ sung | Chấm câu hỏi có giải quyết đúng thông tin còn thiếu, có thể làm đổi đánh giá và tránh xin dữ liệu nhạy cảm hay không. |
| Nguồn RAG | Báo số nguồn trích đúng, nguồn lệch và số ca không có nguồn nhưng hệ thống xử lý được. Đếm riêng ca gán `verified_match` sai. |

Mục tiêu thử trên tập đủ đa dạng là precision `high` từ 85% và recall `high` từ 75%. Với 24 mẫu holdout khởi tạo, trình bày số đếm và phân tích lỗi trước khi so với mục tiêu. Timeout và lỗi phân tích phải được báo riêng. Khi tính hiệu quả toàn luồng, một ca `high` bị lỗi và không có cảnh báo được tính là bỏ sót, đồng thời vẫn xuất hiện trong thống kê lỗi.

## 7 Hiệu năng và nghiệm thu

| Phép đo | Cách thực hiện |
| --- | --- |
| Website | Từ bấm **Phân tích** đến khi hiển thị kết quả. |
| Extension | Từ lúc mục đủ điều kiện quét xuất hiện đến khi thấy cảnh báo. Ghi riêng thời gian chờ hàng đợi, thời gian API và thời gian hiển thị. |
| Backend | Ghi thời gian kiểm tra đầu vào, provider, truy xuất nếu có, kiểm chứng và tổng thời gian. |
| Tải và chi phí | Thử một mục, một lượt nhiều mục cùng xuất hiện và cuộn lặp. Báo số request mỗi phút, gửi trùng, mục bị hoãn hoặc bỏ, lỗi và chi phí live nếu có. |

Ghi cấu hình máy, mạng, số lượt, kích thước đầu vào, độ đồng thời, mock/live và RAG bật/tắt. Báo p50, p95, số lỗi và tỷ lệ lỗi. Tách khởi động lạnh khỏi lượt đã khởi động. Khoảng 100 lượt mock là điểm bắt đầu cho phép đo nội bộ. Với live, ghi số lượt thực tế và giới hạn ngân sách. Mục tiêu trải nghiệm thử dưới 2 giây cho p95 văn bản khi dịch vụ đã khởi động. Nếu chưa đạt, báo phép đo thật và phần chiếm nhiều thời gian nhất.

Cổng nghiệm thu P0 yêu cầu các ca phạm vi quét, dừng quét, gắn đúng mục, chống trích dẫn sai và báo lỗi đều qua. Demo tối thiểu gồm một ca biến thể đáng ngờ, một bài cảnh báo dễ bị nhầm và một ca thiếu ngữ cảnh. Nếu có RAG, trình diễn thêm một ca có nguồn phù hợp và một ca truy xuất thất bại vẫn trả kết quả dựa trên tin nhắn.

## 8 Kiểm thử chức năng mở rộng và hồ sơ dự thi

| Chức năng | Ca cần kiểm trước khi công bố kết quả |
| --- | --- |
| OCR ảnh | Ảnh rõ, mờ, cắt thiếu và số tiền dễ đọc nhầm. Rà thứ tự chữ, thao tác sửa và đo lỗi ký tự cùng ảnh hưởng lên cảnh báo. |
| URL và form | Tên thương hiệu trong miền phụ, URL sai, liên kết rút gọn, redirect về mạng nội bộ nếu có fetch. Với form, xác nhận giá trị người dùng nhập không bị đọc hoặc gửi. |
| Audio, video và deepfake | Đối chiếu lời nói hoặc chữ theo mốc thời gian, báo đoạn không đọc được. Đánh giá mô-đun giả giọng hoặc khuôn mặt bằng tập riêng. |
| Cộng đồng | Báo cáo chưa duyệt không xuất hiện trong kho truy xuất. Kiểm tra duyệt, thu hồi và lưu dấu vết nguồn. |

Hồ sơ dự thi gồm phiên bản ứng dụng, hash dataset, cấu hình model và RAG, lệnh chạy, bảng từng ca, chỉ số tổng hợp và ít nhất ba lỗi điển hình. Mỗi ca lưu ID, cấu hình, nhãn kỳ vọng, dự đoán, bằng chứng, nguồn nếu có, độ trễ, trạng thái đạt hoặc chưa đạt và lý do. Dữ liệu cá nhân được che khi đưa kết quả vào hồ sơ.
