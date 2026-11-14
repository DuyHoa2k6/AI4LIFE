# 16 tình huống suy luận — kết quả backend ngày 14/11/2026

**Chạy backend đang cấu hình: local_rules + legacy-event-rules. Không phải phép đo PhoBERT hoặc Gemini.** Không thay backend, luật, cấu hình riêng hoặc trọng số trong đợt này. Tập do người dùng cung cấp đã công khai, tổng hợp, 0 ca được hai người rà độc lập; không huấn luyện trên đáp án.

## Kết quả chính

- 16 request `/api/analyze` độc lập, **16 HTTP 200**, không lỗi giao thức. Có thêm 16 lượt `/api/analyze-local` chẩn đoán riêng; mức trùng API chính cả 16. Không trộn hai loại thời gian.
- **3/16 = 18.75% khớp mức draft**, Macro-F1 **0.1500**. Không gọi đây là độ chính xác ngoài thực tế.
- Cả **8/8 ca kỳ vọng high bị bỏ sót**: 6 need_context, 1 suspicious, **TH04 bị clear**. Không có dự đoán high; precision high không xác định vì mẫu số 0, recall high so draft là 0/8.
- Ba ca khớp mức: TH02, TH14, TH16. Cả ba còn có dữ kiện trích sai trong trace; không được tính là ba ca đúng toàn bộ. Theo rà agent hiện tại chưa có ca nào được chấp nhận đúng đầy đủ mọi tầng; semantic_accuracy đo bằng người vẫn **chưa đo**.
- Tự động đối chiếu 143 lượt quote ở findings và risk_indicators: **0 lỗi quote/offset hoặc nhãn speaker của finding**. Điều này không chứng minh actor/affected, loại hành động hoặc phạm vi phủ định đúng. Nhiều quote đúng nguyên văn nhưng dùng sai nghĩa.
- Trace có 1 relation tổng cộng, chỉ TH06 có một same_object; 15/16 không có relation. Tất cả cơ chế semantic-graph được ghi nhận đều rỗng. Trạng thái báo từ backend: {'complete': 15, 'unsupported': 1}; chữ complete không chứng minh hiểu đúng toàn bộ.

## Từng ca

| Ca | Tình huống | Kỳ vọng draft | API thực tế | ms |
| --- | --- | --- | --- | ---: |
| TH01 | Khóa học biến thành nghĩa vụ vay | high | **need_context** | 141.98 |
| TH02 | Học bổng yêu cầu giấy tờ quá sớm | suspicious | **suspicious** | 76.71 |
| TH03 | Tình cảm gắn với chuyển quyền tài sản | high | **need_context** | 66.92 |
| TH04 | Công việc đổi thành nợ và hạn chế nghỉ | high | **clear** | 60.66 |
| TH05 | Xác nhận nhận hàng trước khi được kiểm tra | high | **need_context** | 74.98 |
| TH06 | Đóng góp nhưng thông tin người nhận không nhất quán | suspicious | **need_context** | 68.35 |
| TH07 | Hồ sơ nhận tiền chứa quyền chuyển tài sản | high | **need_context** | 106.31 |
| TH08 | Lương đi qua tài khoản do người khác điều khiển | high | **need_context** | 62.81 |
| TH09 | Quà số yêu cầu quyền không tương xứng | high | **suspicious** | 54.33 |
| TH10 | Đặt cọc chỗ ở nhưng thiếu căn cứ về quyền cho thuê | suspicious | **need_context** | 69.54 |
| TH11 | Hoàn khoản “chuyển dư” trước khi tiền tới | high | **need_context** | 99.86 |
| TH12 | Thu nhập được dùng để thuyết phục bảo lãnh | suspicious | **need_context** | 49.42 |
| TH13 | Đối chứng hợp lệ về hợp đồng đào tạo | clear | **need_context** | 70.94 |
| TH14 | Chưa biết nội dung văn bản cần ký | need_context | **need_context** | 78.11 |
| TH15 | Hai người nhận thuộc hai giao dịch khác nhau | clear | **need_context** | 113.28 |
| TH16 | Tham chiếu chưa đủ để nối điều kiện | need_context | **need_context** | 82.31 |

Toàn bộ đầu vào, nội dung API trả, câu hỏi, căn cứ quan sát, lỗi đầu tiên và đối chứng đề xuất: [CASES.md](CASES.md). Dữ liệu máy đọc: [predictions.jsonl](predictions.jsonl), [debug_traces.jsonl](debug_traces.jsonl), [diagnostic_summary.json](diagnostic_summary.json), [agent_review.jsonl](agent_review.jsonl), [metrics.json](metrics.json).

## Ma trận nhầm lẫn

Hàng = tham khảo draft, cột = thực tế:

| Tham khảo / dự đoán | high | suspicious | need_context | clear |
| --- | ---: | ---: | ---: | ---: |
| high | 0 | 1 | 6 | 1 |
| suspicious | 0 | 1 | 3 | 0 |
| need_context | 0 | 0 | 2 | 0 |
| clear | 0 | 0 | 2 | 0 |

## Tầng gây lỗi

1. **Trích sai cụm hành động/đối tượng**: đồng trong hợp đồng → chuyển tiền; giao trong giao dịch → giao tài sản; giao thông tin đăng nhập → handover_asset; bỏ sót ký nghĩa vụ/ủy quyền/bảo lãnh. Đây là quan sát trực tiếp trong trace; pattern sau chuẩn hóa thiếu phân giải nghĩa là nguyên nhân được mã nguồn hỗ trợ.
2. **Scope phủ định và speech act**: “chưa có yêu cầu chuyển tiền hay gửi mã” thành yêu cầu gửi mã; báo “tôi chưa gọi được” hoặc hỏi xem xác nhận thành avoid_verification. Mẫu verification_delay trong clause_context.py có token chuẩn hóa “toi”, có thể nhầm “tôi” với “tối”. Không phải xung đột regex–Gemini vì Gemini không được dùng.
3. **Vai và nguồn**: có câu tự thuật được gán actor là người bên kia; metadata speaker trên finding vẫn đúng vì adapter ghép lại theo message ID. Kiểm quote và speaker vì vậy không bắt hết lỗi người thực hiện/người chịu tác động.
4. **Thiếu graph/transaction**: yêu cầu chính và quan hệ điều kiện bị bỏ, nên không có chuỗi đủ điều kiện cho high. Tách A/B và cập nhật xác minh chưa đáp ứng TH15.
5. **Policy fallback**: khi không match luật, phần lớn trả need_context vì thiếu dữ kiện trong cấu trúc của BE, dù đầu vào đã có căn cứ. TH04 nghiêm trọng hơn: parser chỉ giữ thanh toán lương phủ định, nhánh clear do không còn active event làm bỏ qua ký nợ/giữ lương/hạn chế nghỉ.

Đề xuất ưu tiên: sửa tiêu chuẩn coverage trước clear và phân biệt unsupported với thiếu dữ kiện thật; phân giải cụm danh từ, phủ định phối hợp và speech act; bổ sung kiểu ký nghĩa vụ/ủy quyền/quyền tài sản với nhãn được duyệt; sau đó mới nối graph và hiệu chỉnh policy. Không sửa bằng cách ép mọi yêu cầu tiền/quyền lên high. Chưa triển khai các sửa này trong phép đo hiện tại, nên không có con số cải thiện trước/sau.

## Hiệu năng và phạm vi

- 16 lượt tuần tự, mỗi ca một lần qua ASGI TestClient: p50 **70.94 ms**, p95 nearest-rank **141.98 ms**. Lượt đầu **141.98 ms**; 15 lượt còn lại p50 **70.94 ms**. Không đo bấm gửi ở browser/extension, tải đồng thời hay cold start được kiểm soát.
- Cấu hình hiện hành có RAG và URL bật; không có URL trong 16 input, mọi url_analysis rỗng. Tất cả source_matches rỗng; knowledge_status no_approved_sources ở 13 ca, no_match ở TH03/TH04/TH12. Không đo chất lượng RAG với tài liệu thật và không có kiểm tra redirect trong tập này.
- Công tắc timeout đang là `1` theo cấu hình hiện tại, không bị đổi trong lần chạy. Không lấy việc 16 request không lỗi làm bằng chứng đã kiểm timeout hoặc provider.
- TH02 giữ nguyên hai nhãn người phụ trách như tài liệu, không khẳng định họ là hai tài khoản hay tự xác minh họ cùng người. TH16 giữ một message người dùng thuật lại hai người khác; không tách lời được kể thành tin nhắn trực tiếp giả.
- Chỉ đo backend legacy đang dùng. Checkpoint PhoBERT không được nạp, chưa chạy huấn luyện/so sánh PhoBERT ở đây. Số đo trên báo cáo ML trước không thể đem so trực tiếp với bộ mới và pipeline này.

## Lệnh chạy và dữ liệu

Chạy từ thư mục ứng dụng có backend và .venv-phobert. Đầu vào đã chuẩn bị tại [fixtures/reasoning_document_20261114](../../fixtures/reasoning_document_20261114/inputs.jsonl); expected draft lưu tách. `run` chỉ đọc inputs, lưu tất cả prediction trước debug và trước `score`. Agent đã nhìn tài liệu công khai; không gọi đây là blind đánh giá.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv-phobert\Scripts\python.exe tests/run_reasoning_document.py run --out reports/reasoning_document_new_run
.\.venv-phobert\Scripts\python.exe tests/run_reasoning_document.py score --out reports/reasoning_document_new_run
```

Chọn thư mục mới cho mỗi lần chạy. Script từ chối ghi đè prediction đã có. `tests/inspect_reasoning_document.py` và `tests/report_reasoning_document.py` dựng lại phần chẩn đoán của đợt này từ dữ liệu đã lưu, không gọi model. Manifest lưu cấu hình cho phép công khai, hash input/mã/asset; không xuất private settings hoặc khóa.

Input SHA256: `65715ca9cb1a8ec5d30f964cb1a91176e14cea8da23832e3b5c9228967d844bb`. [run_manifest.json](run_manifest.json) và [data_manifest.json](../../fixtures/reasoning_document_20261114/data_manifest.json). Không tự chuyển 16 ca thành train/gold hoặc đổi nhãn cho khớp kết quả.
