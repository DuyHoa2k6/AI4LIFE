# Đồ thị sự kiện và cơ chế nguy cơ cục bộ — 13/11/2026

Luồng mặc định vẫn `local_rules`, reasoner `legacy`, context bật. Lớp đồ thị
ngữ nghĩa mới bật bằng `SCAMSHIELD_SEMANTIC_GRAPH_ENABLED=1` (mặc định). Không
gọi Gemini/OpenAI/API mô hình khác, không bitmask, không mô hình đã huấn luyện.

## Truy vết nguyên nhân cũ

Đường thực tế: `/api/analyze` → `LocalRulesProvider` → `engine.py` dispatch
`legacy_engine.py` → extract/interaction/context_updates → sanitize →
prepare_interpretation → apply_rules/risk_assessor → support → adapter → response.

Các linker cũ **được gọi**, ID và span qua validator; adapter lấy trực tiếp
`len(annotations.relations)` làm `analysis.situation_links`, không làm mất
quan hệ. Những ca nhiều hành vi vẫn 0 quan hệ vì:

- Tên hành động bị nhận sai: “gửi thông tin đăng nhập” thành login, “gửi cho
  chỗ làm” không có đối tượng nên chưa thành đe dọa phát tán.
- Quan hệ yêu cầu cả hai đầu mút, nhưng “trả cả vốn”, “nhiệm vụ 3 triệu”,
  hạn chế tự rời chỗ ở hoặc tiền qua trung gian chưa được biểu diễn đủ.
- Một số linker chỉ tìm cùng message/cùng nguồn, không dùng dữ kiện hợp đồng
  do người dùng nói trong message khác. Các trường hợp xuyên câu không có
  đối tượng tham chiếu chung chưa tạo được quan hệ.
- `scope_for` từng coi từ sau “đơn/hợp đồng” là mã giao dịch, kể cả danh từ
  thông thường. Hiện chỉ mã tường minh như A/B/A12 tạo transaction namespace.
- Script kiểm thử từng coi “Tài khoản mới nhắn” và “Tài khoản mới” là hai
  speaker khác nhau ở ca 09. Đã sửa alias trong harness; payload trước/sau của
  phép đo đối chiếu cuối được kiểm tra giống nhau. Chỉ sửa alias vẫn không
  giải quyết các lỗi suy luận, vì bản graph tắt vẫn chỉ 1/10 ca high.

## Biểu diễn và phân vai

`Event.semantic` bổ sung thuộc tính có phiên bản phương pháp, tương thích với
Event cũ: message/context ID, situation, speaker, requester, performer, bên
bị tác động, hành động chuẩn hóa, loại đối tượng, nguồn/đích chuyển giao,
phạm vi phủ định, dấu mốc điều kiện/thời gian và information_status.

Speaker không mặc định là người yêu cầu hoặc người làm. “Bên hỗ trợ bảo tôi
gửi thông tin đăng nhập” giữ người kể, nguồn yêu cầu được nhắc và bên được
yêu cầu là các vai khác nhau. Đây là lời thuật lại chưa xác minh. “Chị/em”
không tạo quan hệ gia đình đã xác minh. Nhãn người được gọi tên tường minh
chỉ là tham chiếu trong văn bản, không phải danh tính thật.

Nguồn cục bộ: `semantic_graph_patterns.json` chứa mẫu động từ + đối tượng/
hướng/điều kiện. Không chứa 10 đoạn kiểm thử, nhãn dự đoán hoặc mã ca. Bộ mẫu
có giới hạn, không tương đương khả năng hiểu ngôn ngữ tổng quát.

Phân biệt tự login, gửi thông tin cho bên khác, gửi vào trang, mã kết nối từ
xa và mã đăng nhập. Không biến mọi mã kết nối thành OTP. Không tự biến nhiệm
vụ có số tiền thành yêu cầu nộp nếu chưa có ngữ cảnh nộp/khóa rút hỗ trợ.

## Quan hệ và quyết định

Quan hệ giữ ID, loại, hai đầu mút, scope, span, trạng thái và method. Các kiểu
bổ sung: same_object, obstructs_verification, transfer_via, promised_after,
threatens_unless, controls_during, supersedes. Kiểu được khai báo chưa đồng
nghĩa mọi cách diễn đạt của kiểu đó đã được hỗ trợ; các phép thử ghi rõ kiểu
và phương pháp thực sự tạo ra.

Linker kiểm tra hoạt tính lời nói, phủ định, nguồn, vai bị tác động, scope và
điều kiện ngôn ngữ. Không lấy thứ tự thu thập DOM làm thời gian thực. Phạm vi
chung là điều kiện cần, chưa đủ: phải có đối tượng và cấu trúc bổ sung như
chuyển tiếp, điều kiện nhận lại, hoặc cùng lúc thao tác/mở ngân hàng.

Tham chiếu “gửi cho chỗ làm” chỉ gắn ảnh/video khi có ứng viên phù hợp cùng
nguồn, cùng người và scope. Nhiều đối tượng hoặc khác người giữ unresolved;
không cho sự kiện chưa giải quyết lọt vào luật coercion cũ. Tương tự, thời
gian “trong lúc tôi thao tác” không tự chứng minh đã có quyền điều khiển từ xa.

`Interpretation.mechanisms` được tạo **trước quyết định cuối**, mang sự kiện,
quan hệ, bằng chứng, tài sản/quyền và cơ chế có thể gây hại. Các cấu trúc tổng
quát: thay nơi nhận tiền + trái thỏa thuận/cản xác minh; tiền qua trung gian
+ che giấu; giấy tờ + hạn chế rời đi; nộp thêm để mở quyền lợi; quyền thiết bị
+ dữ liệu ngân hàng; đòi tiền bằng đe dọa phát tán; danh tính tự nhận + người
nhận tiền khác + ngăn xác minh. Yêu cầu giao credentials còn hiệu lực có thể
đủ cảnh báo cao bằng một sự kiện, không bắt buộc tạo quan hệ giả.

Không cộng điểm 18 trường. Không nâng tất cả suspicious; một luật cũ vẫn có
thể trả suspicious khi chỉ có cài ứng dụng hoặc đổi tài khoản chưa đủ tổ hợp.
Giữ nguy cơ mạnh đã có bằng chứng. Không khẳng định deepfake, biên lai giả,
mua bán người, mã độc hay tiền đã bị chuyển từ các phát hiện nguy cơ.

## Trạng thái, bổ sung và câu hỏi

Situation giữ phiên bản, người, đối tượng, yêu cầu còn hiệu lực, trạng thái
được báo, điều kiện, xác nhận độc lập do người dùng kể, mâu thuẫn và mechanism.
18 trường chỉ tổng hợp lại IDs/span từ cấu trúc này.

Context phải gắn đúng scope và message; context mơ hồ hoặc sai scope bị loại
có mã lý do. Context dùng span `context_id`, không giả làm văn bản của người
gửi. Bổ sung qua API giữ case_id/situation_id/revision/content_version và chặn
revision cũ. Xác nhận qua kênh cũ vẫn là user_reported, không phải system-verified.
Nó chỉ tác động tới nguy cơ danh tính/tài khoản liên quan; không xóa yêu cầu
giao mật khẩu khác. Trạng thái cũ được giữ, liên kết state_update, không xóa.

Câu hỏi dựa vào trường còn thiếu: nhiệm vụ có phải chi tiền không; tài khoản
đã đối chiếu chưa; hỗ trợ từ xa có mở nội dung nhạy cảm không. Tối đa hai câu;
high cảnh báo ngay. Không hỏi mã thật/mật khẩu, không hỏi lại mục đích nộp khi
đã có chuỗi trả thêm để nhận vốn. Câu hỏi tự do ngoài mẫu vẫn còn giới hạn.

## Trace phát triển và an toàn dữ liệu

`/api/analyze-local` → `annotations.graph_trace`: số cụm/sự kiện, rules_run,
ứng viên, quan hệ giữ, lý do loại, tham chiếu chưa giải quyết, validator loại
gì và IDs thực sự dùng quyết định. Trace chứa mã/ID/count, không lưu khóa,
mật khẩu hay toàn văn vào log. Quote vẫn ở phần annotations khi gọi debug
API tường minh; không dùng debug API để ghi dữ liệu người thật hàng loạt.
`/api/analyze` và giao diện mặc định không thêm graph_trace hoặc suy luận thô.

## Kiểm thử và chạy

Xem [báo cáo nghiệm thu](reports/semantic_graph_20261113/README.md). Các ca gốc
và 42 đối chứng đều là development, không phải holdout độc lập. Tập 42 có
mỗi cấu trúc A–G: diễn đạt mới, hợp lệ, thiếu dữ kiện, phủ định/cảnh báo,
hai giao dịch, và bổ sung thay đổi kết luận. `not_high` không mặc định clear.

Từ thư mục ứng dụng:

```powershell
python -m unittest discover -s tests -q
python check_graph_controls.py --output reports/graph_controls_new
```

Khởi động lại backend:

```powershell
$env:SCAMSHIELD_MODE="local_rules"
$env:SCAMSHIELD_REASONER="legacy"
$env:SCAMSHIELD_CONTEXT_ENABLED="1"
$env:SCAMSHIELD_SEMANTIC_GRAPH_ENABLED="1"
python -m uvicorn backend.main:app --app-dir "C:\AI4Life\AI4LIFE\ScamShield_AI\ScamShield_AI" --host 127.0.0.1 --port 8000
```

Đặt cờ graph bằng 0 để so sánh có kiểm soát với lớp trước; không cần tắt RAG/URL
trong sử dụng thông thường. Phép đo trong báo cáo tắt URL network vì đầu vào
không có URL. Không đổi key, không cài thêm công cụ.

Giới hạn còn lại: mẫu và đại từ chưa phủ ngôn ngữ tổng quát; tên riêng chỉ
nhận một số cấu trúc tường minh; đối tượng đa nghĩa giữ unknown; không có
bộ chấm đầy đủ mọi thực thể, coreference hoặc độ đúng 18 trường. Chưa chạy
lại toàn bộ Chrome E2E, dữ liệu thật, OCR hoặc redirect mạng trong lần sửa này.
