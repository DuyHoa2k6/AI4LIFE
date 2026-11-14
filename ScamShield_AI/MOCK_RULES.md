# Mock theo hành vi 2.0

Phiên bản: `mock-behavior-2.0.0`. Đây là mock xác định cho kiểm thử/demo, không phải mô hình học từ dữ liệu. Không cần thêm thư viện hoặc API key để chạy mock. Khởi động lại backend sau khi cập nhật; website và extension dùng API/schema 1.0 hiện có, không cần thay thư mục cài extension.

```powershell
python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log
```

## Phần thay đổi

| Trước | Sau |
| --- | --- |
| Regex/từ khóa nằm trong MockProvider | Registry có ID, mô tả, phiên bản, pattern trong backend/mock_rules.py |
| Trích toàn tin có từ khóa | Tách câu/đoạn, giữ số 500.000, dấu tổ hợp và offset gốc |
| Một cụm cảnh báo có thể phân vai cả tin | Vai được xét theo đoạn; câu cảnh báo không tự che câu yêu cầu mới |
| Có yêu cầu và lời hứa ở đâu đó trong request có thể nâng high | Chỉ nâng qua mã/mật khẩu được yêu cầu giao hoặc quan hệ bằng chứng đủ điều kiện |
| Chưa nhận dạng “nộp phí…” | Có nộp/đóng phí, nạp tiền, đặt cọc, giao mật khẩu và nhập mã qua link |
| Không truy vết quy tắc | Finding ID có tiền tố quy tắc; báo cáo xuất registry và hash |

## Registry hiện có

| ID | Nhóm nhận diện |
| --- | --- |
| MR-MONEY | Chuyển/ứng/nộp/nạp tiền, phí, đặt cọc, thanh toán |
| MR-CODE | Yêu cầu giao OTP/mã đăng nhập/mã xác thực/mã xác nhận |
| MR-CODE-LINK | Nhập mã vào link/kênh được chỉ định |
| MR-PASSWORD | Yêu cầu cung cấp mật khẩu |
| MR-ACCESS | Chia sẻ màn hình, điều khiển từ xa, quyền truy cập/trợ năng |
| MR-INSTALL | Cài tệp/ứng dụng/phần mềm/APK |
| MR-REWARD | Hoàn gốc/tiền, hoa hồng, nhận quà/ưu đãi |
| MR-UNLOCK | Mở khóa, điều kiện nhận/lấy/rút |
| MR-RECOVER | Nhận/lấy lại tiền, nhận quà |
| MR-SECRECY | Hạn chế gọi/hỏi/kể/báo người khác |
| MR-URGENCY | Thời hạn phút/giờ hoặc áp lực mất quyền lợi |

Đầy đủ pattern nằm trong `reports/mock_v2/rules.json`. Các quy tắc là tín hiệu hành vi; riêng hoa hồng, đặt cọc, thời hạn hoặc một yêu cầu thanh toán không chứng minh lừa đảo.

## Cách liên kết và quyết định

Sau kiểm chứng, chỉ dùng finding request và support claim. Cùng câu/đoạn: yêu cầu và lợi ích phải đi cùng liên từ quan hệ như “để”, “xong”, “rồi”, “thì”, “sẽ”. Hai câu cùng tin: cửa sổ tối đa hai đoạn, 500 ký tự. Khác tin: cùng nhãn speaker cụ thể, cách tối đa hai vị trí tin; yêu cầu có dấu hiệu tài chính, lời hứa có lợi ích và liên từ. Nhãn speaker khác nhau không ghép. Speaker unknown chỉ liên kết trong cùng tin. Bộ lọc chủ đề thuê nhà/hóa đơn/đầu tư/nhiệm vụ/quà/thu hồi tiền loại một số cặp lệch chủ đề; cụm “chuyện khác”, “không liên quan” ngăn liên kết. Đây vẫn là heuristic, không xác minh người thật hoặc quan hệ ngữ nghĩa đầy đủ.

- `high`: yêu cầu giao mã/mật khẩu hoặc yêu cầu có quan hệ lợi ích/điều kiện đủ điều kiện trên.
- `suspicious`: yêu cầu được nhận diện nhưng không có quan hệ đủ để nâng high. Một thanh toán hợp lệ vẫn có thể rơi vào mức này; mock chưa biết đầy đủ thông tin xác minh ngoài đời.
- `need_context`: lời thuật lại/trích dẫn chưa rõ vai hoặc mẫu thiếu thông tin như khoản rút treo, tệp, đổi tài khoản, xác minh, dịch vụ lấy lại tiền. Câu hỏi theo nhóm, không xin mã thật.
- `clear`: chưa nhận ra yêu cầu rủi ro theo các mẫu, không chứng nhận an toàn.

MR-SECRECY/MR-URGENCY không tự nâng high. Có thể bỏ sót kịch bản nguy hiểm chỉ có ép giữ bí mật hoặc diễn đạt mới. Không có verified_match hay nguồn truy xuất trong mock.

`inference.evidence_refs` do backend dựng lại từ cả hai finding còn hợp lệ, không tin tham chiếu tự khai từ provider. ID là opaque với client; không dùng tiền tố để quyết định risk. Không thêm rule_id vào schema công khai. Vượt 50 finding trả 502/MOCK_FINDING_LIMIT để không cắt mất phần cuối rồi báo clear. Live giữ adapter/prompt và đường quyết định live riêng; nâng mock không đồng nghĩa cải thiện live.

## Kiểm thử và báo cáo

```powershell
$env:PYTHONPATH='ScamShield_AI'
python -m unittest discover -s ScamShield_AI/tests -v
python ScamShield_AI/mock_report.py
$env:SCAMSHIELD_REPORT_DIR='ScamShield_AI/reports/mock_v2/browser'
node ScamShield_AI/tests/browser_week2.mjs
```

`reports/mock_v2/python_tests.txt` lưu hồi quy. `dev_predictions.json` lưu response trước khi so nhãn; `summary.json` so với snapshot mock tuần 1; `hashes.json` khóa mã và dev; báo cáo trình duyệt ghi riêng trong thư mục browser. Không ghi đè các báo cáo tuần 1/2 trước đó. Kết quả dev 12/12 khớp nhãn là số liệu phát triển trên 12 ca tổng hợp đã dùng để làm quy tắc, không phải độ chính xác độc lập. Mỗi quy tắc có ca kích hoạt và đối chứng cảnh báo. Chưa chấm độ đúng ngữ nghĩa tự động trên tập độc lập.

Lượt kiểm thử hiện tại: 26 phương thức unittest Python đạt (gồm nhiều subtest đối chứng), 29 assertion trên Chrome 156 headless với worker MV3/content script thật đạt. Hồi quy Chrome dùng fixture local và backend mock; lỗi mạng/429/timeout được chèn có kiểm soát, không phải provider live. Bao gồm một kiểm thử hỗ trợ bịa bị loại không còn nâng high hoặc giữ liên kết suy luận.

## Giới hạn phải giữ khi mở rộng

Chưa đọc context/question để trích hành vi trong mock; không tải dataset hoặc nguồn RAG khi nhận request. NFC chỉ dùng matching; bằng chứng giữ nguyên chuỗi gốc. Tách câu, quote và phủ định không phải bộ phân tích ngữ pháp: câu trích lồng nhau, phủ định phức tạp, không dấu và chủ đề mới có thể sai. Dữ liệu dev/validation/holdout, nguồn candidate và baseline tuần 3 không được sửa trong nâng cấp này. Cần AI live cho đánh giá khả năng hiểu ngữ cảnh; cần P0 và nguồn duyệt trước tích hợp RAG.

Tài liệu 01–07 và prompt tuần 1 đã được đồng bộ vai trò mock/live/RAG. Báo cáo trước đây là lịch sử của phiên bản cũ; sử dụng reports/mock_v2 cho thay đổi này.
