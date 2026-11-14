# Ghép văn bản, RAG và URL trong luồng local

Phiên bản quyết định `local-rules-2.1-support`; không cần key hoặc model. Dataset đánh giá không được dùng làm chỉ mục truy xuất.

## Thứ tự

1. `backend/main.py` xác thực request, `local_reasoning/adapter.py` giữ văn bản/ID/người nói rồi gọi lõi BE.
2. `engine.py` trích, kiểm chứng và áp rulebook trên bằng chứng từ nội dung. Lõi đồng bộ này không truy xuất hoặc mở URL.
3. `local_reasoning/support.py::enrich` nhận kết quả có căn cứ, chạy hai nhánh song song bằng asyncio.gather: `retrieval.branch` và `url_network.inspect_urls`.
4. Ghép nguồn/URL với sự kiện đủ điều kiện, cập nhật cảnh báo, chỉ dẫn và risk_indicators; chuyển qua adapter sang schema API chung. Nhánh khẩn bỏ qua cả hai để ưu tiên an toàn.

## URL đóng góp thế nào?

Đọc URL trong text/OCR và href do client gửi. Phân tích PSL, IDN/Punycode, tên gần giống miền tham chiếu, miền phụ giả tên và khác biệt nhãn/href. Nếu bật mạng, HEAD theo từng redirect, kiểm tra cả miền cuối. Không tải body, chạy JavaScript hoặc xác minh danh tiếng/mã độc.

`R-URL-GROUNDED-REQUEST` yêu cầu **hành động đang được yêu cầu**, không phủ định/trích cảnh báo/giả định, cùng message và cùng đoạn với nhãn/URL xác định được vị trí. Chỉ chấp nhận loại yêu cầu và tín hiệu tên miền mạnh đã liệt kê trong support.py. Không lấy URL của người khác hoặc câu khác làm bằng chứng cho yêu cầu này. Phạm vi ghép cố ý hẹp; có thể bỏ sót liên kết giữa nhiều câu.

Ngoại lệ ghép DOM: khi client xác nhận href và văn bản bị tách node bằng xuống dòng, cho phép nối yêu cầu đứng ngay trước nhãn qua cụm liên kết ngắn như “tại/qua/vào/theo đường dẫn”; không vượt qua câu hoàn chỉnh hoặc người nói khác. Phần hỗ trợ chỉ xét tối đa 50 sự kiện đầu, cùng giới hạn findings của adapter công khai.

- Đủ yêu cầu + dấu hiệu mạnh: có thể nâng clear/need_context lên suspicious; không nâng high chỉ vì URL.
- High từ nội dung được giữ; URL hỗ trợ lời giải thích và hành động tiếp theo.
- URL đứng riêng, HTTP 404, DNS/TLS lỗi, timeout, đổi miền hoặc HTTP đơn lẻ không tự chứng minh lừa đảo.
- HEAD tối đa 3 URL/request, tối đa 3 redirect (4 HEAD mỗi URL), khoảng 6 giây/URL, không cookie/đăng nhập; giữ chặn SSRF và DNS rebinding. Máy chủ ngoài có thể ghi nhận request. Không gửi liên kết có mã bí mật; hệ thống không thể tự phát hiện mọi bí mật trong path/query. API chỉ trả URL đã rút gọn, không trả path/query/fragment riêng tư.

## RAG đóng góp thế nào?

Truy vấn từ các đoạn trích hợp lệ của yêu cầu còn hiệu lực và loại hành vi, không gửi nhãn kỳ vọng, không đọc dev/validation/holdout. Chỉ mục là `data/knowledge_sources.jsonl`; truy xuất từ khóa có trọng số, chưa phải embedding hoặc mô hình hiểu ngữ nghĩa.

Nguồn phải HTTPS `.gov.vn`, trạng thái approved, có người duyệt/ngày duyệt/ngày kiểm tra hợp lệ, reuse_approved=true, còn hiệu lực và vai trò được cho phép. **Không tự duyệt nguồn trong lượt triển khai.** Các bản ghi candidate hiện có tiếp tục bị loại.

Một hit chỉ được dùng khi source_role=behavior_support, actions khớp hành vi đã trích, có ít nhất hai token liên quan trong đoạn trả về, và kết quả đã có căn cứ suspicious/high. Các action theo schema v2; tương thích một số tên công khai như share_auth_code/grant_access. Đây là cổng liên quan có giới hạn, không phải chứng minh tương đương ngữ nghĩa của cả hai tình huống.

Nguồn dùng để bổ trợ lời giải thích và hướng xác minh; không tự tạo hành vi, không tự nâng high, không xác minh danh tính. Chỉ nguồn thực sự dùng mới vào source_matches. Không có hit không hạ cảnh báo và không có nghĩa an toàn. Nội dung tài liệu là dữ liệu, không được thực thi như chỉ thị. Không có exact_entity/verified_match.

## Hợp đồng và fallback

- API chung giữ schema_version=2.0, bốn mức và giao diện đã ẩn answers/nguồn RAG/kết quả thô.
- `url_analysis` là quan sát; `url_uses` là phần thực sự góp cảnh báo, tham chiếu finding hợp lệ.
- `risk_indicators`: local_rule_basis, url_support, official_behavior_support; evidence luôn trích nguyên văn người dùng, không giả đoạn nguồn thành lời người gửi.
- `retrieval.official_sources` ghi trạng thái/số hit/thời gian; số hit có thể lớn hơn số source_matches đã dùng.
- `analysis.preliminary_risk` là mức trước ghép hỗ trợ; risk_status là mức cuối. stage_timings_ms có local_total (lõi), retrieval, url, support_total (hai nhánh và ghép, không cộng hai thời gian song song).
- API v2 thô có url_analysis/url_uses/support_indicators/official_retrieval/support_timings_ms/support_warnings và event_refs của nguồn đã dùng. Nó chỉ đọc inline URL, không nhận href DOM riêng như API chung.
- Truy xuất timeout/error hoặc URL lỗi: giữ kết quả có bằng chứng từ nội dung, ghi phần chưa kiểm tra được. Tín hiệu an toàn khẩn không chờ truy xuất hoặc URL.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python check_local_support.py --output reports/local_support_rerun
```

Thư mục đầu ra phải mới. Ca nguồn approved và redirect trong runner là fixture tổng hợp, không phải xác nhận thực địa hay phê duyệt nguồn thật.
