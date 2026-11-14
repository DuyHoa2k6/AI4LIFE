# ScamShield AI — quy tắc phối hợp live

## Cấu hình key trực tiếp ở backend (cách mới)

Tài liệu này dành cho mode hybrid một lượt để đối chứng. Luồng hiện hành theo sơ đồ người dùng
chọn là [two_pass](TWO_PASS.md); chạy `chay_hybrid.py --mode two_pass` hoặc uvicorn đọc cấu hình riêng.

Chủ hệ thống điền một lần vào `backend/local_settings.py`:

```python
SCAMSHIELD_MODE = "hybrid"
SCAMSHIELD_PROVIDER_URL = "https://api.openai.com/v1/chat/completions"
SCAMSHIELD_MODEL = "TEN_MODEL_DUOC_CAP_QUYEN"
SCAMSHIELD_API_KEY = "KEY_MOI_CUA_BAN"
SCAMSHIELD_TIMEOUT = "20"
```

Sau đó chạy `chay_he_thong.cmd` hoặc lệnh uvicorn thông thường. Người dùng web/extension không nhập key. Khởi động lại backend sau khi sửa file. File riêng này đã có sẵn với model/key để trống; chưa gọi được AI thật trước khi điền. MODE đặt hybrid; muốn dùng offline đổi thành mock hoặc dùng biến môi trường ghi đè. Biến môi trường được ưu tiên, kể cả giá trị rỗng: nếu terminal còn cấu hình cũ, xóa biến đó hoặc mở terminal mới.

`local_settings.py` bị bỏ qua bởi Git, không được phục vụ bởi các route static, không đưa vào manifest/hash báo cáo; không chia sẻ file này sau khi điền key. Backend đọc các hằng chuỗi bằng AST thay vì import/thực thi file, không tạo pyc chứa key. `local_settings.example.py` là mẫu trống có thể chia sẻ. Khi đóng gói thủ công không dùng thao tác nén cả thư mục chứa key. Dùng key mới, thu hồi key đã gửi trong chat. Các cách nhập ẩn dưới đây vẫn giữ như tùy chọn dành cho người vận hành, không phải yêu cầu đối với người dùng sản phẩm.

Đã có mode `hybrid`: đầu vào → quy tắc sơ bộ → một lần gọi live → kiểm chứng bằng chứng và quan hệ → backend quyết định → web/extension hiển thị. Không coi kết quả quy tắc là đáp án cho live. Không cộng phiếu hoặc chọn mức cao nhất của hai bộ phân tích.

## Bật trên máy của bạn

Nếu API key từng xuất hiện trong chat, thu hồi key đó và tạo key mới. Không dán key mới vào chat, mã nguồn, extension hoặc lệnh được lưu lịch sử. Launcher dưới đây hỏi key bằng getpass (ẩn ký tự), giữ trong bộ nhớ tiến trình, không ghi file và không đặt key lên command line:

```powershell
python ScamShield_AI/chay_hybrid.py --model TEN_MODEL_DUOC_CAP_QUYEN
```

Endpoint mặc định của launcher là `https://api.openai.com/v1/chat/completions`. Có thể cấu hình dịch vụ tương thích bằng `--url` hoặc SCAMSHIELD_PROVIDER_URL; không nhúng key vào URL. Model do bạn chọn từ tài khoản của mình, launcher không tự chọn/nâng model hoặc mua dịch vụ. Nhập key mới khi được hỏi; mỗi request hybrid có thể phát sinh phí. Dừng server cũ cổng 8000 trước, mở http://127.0.0.1:8000/. Reload extension trong chrome://extensions và tải lại tab để nạp renderer mới hiển thị mode hybrid.

Kiểm tra một lượt thật bằng dữ liệu tổng hợp, có thể phát sinh phí:

```powershell
python ScamShield_AI/chay_hybrid.py --model TEN_MODEL_DUOC_CAP_QUYEN --smoke
```

Lệnh smoke đi qua API backend, quy tắc, provider và bộ kiểm chứng; lưu trạng thái/độ trễ/response tổng hợp ở `reports/hybrid/live_smoke.json`. Không gọi đó là đánh giá chất lượng toàn hệ thống. Nếu schema/quote không hợp lệ, provider không khả dụng hoặc timeout, báo lỗi rõ và sửa theo bằng chứng đo. Timeout backend mặc định 20 giây, client chờ 25 giây; chưa đo độ trễ provider/model thật. Không tăng timeout backend vượt client trước khi đồng bộ timeout các kênh.

Nếu dùng biến môi trường có sẵn thay launcher:

```powershell
$env:SCAMSHIELD_MODE='hybrid'
$env:SCAMSHIELD_PROVIDER_URL='https://api.openai.com/v1/chat/completions'
$env:SCAMSHIELD_MODEL='TEN_MODEL_DUOC_CAP_QUYEN'
$secureKey=Read-Host 'API key moi' -AsSecureString
$env:SCAMSHIELD_API_KEY=[System.Net.NetworkCredential]::new('', $secureKey).Password
python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log
```

Sau khi dừng backend, xóa biến key bằng `Remove-Item Env:SCAMSHIELD_API_KEY`; biến chỉ tồn tại trong phiên PowerShell và tiến trình con. `.env.example` là mẫu, không tự nạp file .env. Mặc định repo vẫn mock cho chạy offline; chế độ mock không tự chuyển sang hybrid chỉ vì có key.

## Cách phối hợp

1. Backend xác thực request trước, giữ nguyên văn bản để đối chiếu Unicode code point.
2. Registry mock v2 trích giả thuyết và backend kiểm chứng. Giới hạn đưa vào prompt tối đa 12 finding, mỗi quote tối đa 512 code point; input gốc/context/question vẫn gửi đầy đủ trong giới hạn API. Nếu quy tắc vượt 50 finding, ghi preliminary_status=limited rồi vẫn gọi live, không chặn việc đọc phần còn lại.
3. `hybrid_prompt.txt` hướng dẫn live tự đọc toàn bộ input, bác giả thuyết sai và nhận ra hành vi mới dù quy tắc không phát hiện. Không gửi dataset, expected, holdout hoặc nguồn candidate.
4. Live trả HybridReview gồm findings và review có cấu trúc. Backend kiểm chứng quote/ID/speaker/offset; liên kết và các tham chiếu phải trỏ finding còn hợp lệ. Toàn bộ văn bản giải thích tự do của provider được thay bằng mẫu có căn cứ.
5. Backend đặt risk_status. Quan hệ high phải nối yêu cầu với điều kiện/lời hứa đúng đối tượng người nói. Yêu cầu giao mã xác thực trực tiếp vẫn có thể high; biết người gửi không tự chứng minh thao tác giao mã an toàn.
6. Ngữ cảnh giảm cảnh báo cần finding ID hợp lệ và quote khớp context do người dùng cung cấp. Đây là suy luận trên lời khai, không xác minh danh tính hoặc khoản nợ ngoài đời. Vai unknown hoặc mâu thuẫn chưa giải quyết cần thêm bối cảnh. Một bằng chứng high còn đủ mạnh vẫn có thể kèm câu hỏi về phần chưa rõ.
7. Dấu hiệu quy tắc bị live bỏ qua chưa giải thích được giữ thành finding vai unknown, trả need_context thay vì âm thầm clear. Không nhập dấu hiệu đó như một yêu cầu đã được live xác nhận.
8. Câu hỏi do backend chọn từ tối đa hai topic enum; không nhận câu hỏi tự do yêu cầu OTP/mật khẩu. Với yêu cầu chuyển tiền chưa có bối cảnh, hỏi quan hệ và mục đích trước khi kết luận. Bổ sung ở website gửi lại nội dung gốc và context mới; live đọc context mới ở lượt tiếp theo.

Mode live cũ (không sơ bộ) và mock cũ giữ để đối chứng. Hybrid phase này **always_live**, không có tiết kiệm lượt gọi bằng cách bỏ qua model. Chưa tích hợp RAG; source_matches luôn rỗng, không có verified_match. Chỉ thêm truy xuất sau khi P0/live và nguồn duyệt đạt cổng.

## Những ca đã kiểm thử

| Nhóm | Điều cần bảo đảm |
| --- | --- |
| Đồng thuận | Yêu cầu nộp phí và điều kiện nhận tiền có evidence/ref hợp lệ → high |
| Không có từ khóa | Vẫn gọi live; hành vi mới do live trích được đưa vào quyết định |
| Trả khoản đã mượn | Thiếu xác nhận → need_context; bổ sung context được quote đúng có thể giảm cảnh báo |
| Quy tắc cảnh báo nhầm | Live phân vai bài tuyên truyền → không giữ nhãn high của quy tắc |
| Live bỏ sót dấu hiệu quy tắc | Không âm thầm clear, trả need_context và ghi rule_conflicts |
| Quote/speaker/offset/ID sai | Loại finding, không dùng để nâng rủi ro; tất cả sai trả 502 |
| Quan hệ sai người nói/ref bịa | Không dùng để nâng high, yêu cầu xác minh |
| Context bịa/unknown/nhận định mâu thuẫn | Không âm thầm hạ cảnh báo |
| Model bịa nguồn/verified_match/câu hỏi xin bí mật | Schema nội bộ từ chối, trả lỗi provider |
| Timeout/429/mất mạng/thiếu cấu hình | Trả 502/503/504; không fallback mock/clear giả thành công |
| Input sai | Từ chối trước gọi live |
| Unicode/giới hạn quy tắc | Offset gốc đúng; vượt ngân sách quy tắc vẫn đọc input đầy đủ qua live |
| Web/extension | Hiện đúng hybrid, cùng endpoint, giữ các cổng phạm vi và phản hồi cũ |

Kiểm thử tự động sử dụng phản hồi live **giả lập**, không chứng minh model thật hiểu tiếng Việt hoặc đạt precision/recall. Test doubles được đặt tại tests và không bật ở runtime production. Không dùng key đã gửi trong chat để chạy kiểm thử hoặc ghi vào repo.

```powershell
python ScamShield_AI/hybrid_report.py
$env:SCAMSHIELD_BROWSER_HYBRID='1'
$env:SCAMSHIELD_REPORT_DIR='ScamShield_AI/reports/hybrid/browser'
node ScamShield_AI/tests/browser_week2.mjs
```

Browser test dùng Chrome headless thật, worker MV3/content script thật, API cổng 18762 và provider fixture cổng 18763. Nó xóa API key khỏi env tiến trình test và cố định provider local, không gọi API trả phí. Báo cáo riêng trong reports/hybrid, không ghi đè số liệu tuần trước. Cần Node 24 và Chrome hỗ trợ CDP Extensions.loadUnpacked; Python dependencies không đổi.

Kết quả đã chạy: 49 phương thức unittest Python đạt (có thêm kiểm thử cấu hình riêng và không lộ key); 32 assertion Chrome của lượt hybrid trước thay đổi cấu hình đạt. Ca 35 mục gửi 35 request, tối đa 1 đồng thời và hàng đợi giới hạn 20. Provider fixture local ghi nhận request hybrid thật qua HTTP, nhưng không có mô hình AI đằng sau fixture. Các nhánh suspicious cho yêu cầu cấp quyền/cài phần mềm, high cho quan hệ bằng chứng, need_context cho trả nợ mơ hồ và clear theo bối cảnh đều có kiểm thử. Lượt thật với khóa mới vẫn cần chạy tại máy bằng --smoke; chưa có chỉ số chất lượng model thật.

## File và giới hạn

`backend/providers.py`: điều phối sơ bộ và gọi live; `backend/hybrid.py`: quyết định backend; `backend/hybrid_prompt.txt`: chỉ dẫn; `backend/schemas.py`: schema 1.1/hợp đồng review; `backend/main.py`: route và thông báo nơi xử lý; `extension/shared.js`: hiển thị mode, dùng chung website; `tests/test_hybrid.py`: ca đồng thuận/lỗi/bất đồng; `chay_hybrid.py`: nhập key tại máy.

Tài liệu 01–07, prompt tuần 1 và README đã được cập nhật. 08 giữ nguyên vì không thêm nguồn dữ liệu, quyền extension hay chức năng media. Backend chỉ kiểm chứng cấu trúc và nguồn gốc câu trích, không chứng minh cách model hiểu ngữ nghĩa là đúng. Rà ngữ nghĩa/độ trễ/chi phí và tập độc lập vẫn là bước phải làm với model thật. Hiện không có số liệu chất lượng live hay RAG.

Giao thức adapter hiện dùng JSON mode và Pydantic kiểm schema tại backend. JSON mode tự nó không bảo đảm đúng schema; có thể chuyển sang Structured Outputs cho provider/model hỗ trợ sau khi thử tương thích. Tham khảo [OpenAI Docs về Structured Outputs và JSON mode](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).

