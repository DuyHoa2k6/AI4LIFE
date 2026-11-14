# PhoBERT cục bộ — báo cáo thực nghiệm 14/11/2026

**Đã triển khai và chạy pipeline nghiên cứu; chưa đạt chất lượng để thay backend mặc định.** Không có suy luận Gemini/API mô hình ngoài. Chỉ bước chuẩn bị tải thư viện, checkpoint và RDRSegmenter dùng mạng.

## Máy và checkpoint

- CPU: 12th Gen Intel(R) Core(TM) i5-12500H; 16 logical CPU; RAM 15.70 GiB; cấu hình thí nghiệm 2 thread, batch 1, float32.
- GPU Intel Iris Xe tích hợp; CUDA không có. AdapterRAM báo 1 GiB không phải VRAM CUDA dùng được. Không giả định có NVIDIA.
- Python 3.12.5, PyTorch 2.6.0+cpu, Transformers 4.57.1. Đĩa trống lúc audit 183.2 GiB.
- Checkpoint `vinai/phobert-base`, revision `01daacda68afe13d83023d16ec647239e344a1e6`; PhoBERT base 135M, MIT, giới hạn 256 token. [Model card](https://huggingface.co/vinai/phobert-base), [config](https://huggingface.co/vinai/phobert-base/raw/main/config.json), [giấy phép](https://github.com/VinAIResearch/PhoBERT/blob/master/LICENSE). Dùng bản gốc MIT, không tự chuyển sang base-v2 hoặc mô hình khác.
- [preparation.json](../../artifacts/phobert/preparation.json) lưu URL, revision và SHA-256 mọi asset. Model card và LICENSE nằm cùng checkpoint. Tokenizer thực là PhobertTokenizer slow; không có offset_mapping/word_ids để dùng như fast tokenizer.

## Dữ liệu

- Canonical v2: 70/70 ca và 356 span là weak_label; manifest ghi 0 ca đủ điều kiện supervised. Không đổi chúng thành gold hoặc dùng kết quả rulebook tự chấm rulebook.
- Bộ smoke: 20 ca nháp tổng hợp, 10 cặp đối chiếu (không phải tất cả chỉ đổi một biến); 7 clear, 3 need_context, 4 suspicious, 6 high. Bổ sung 10 đầu vào ở minimal_pairs_unlabelled.jsonl cho đúng năm nhóm cặp tối thiểu; tất cả task ở file này unannotated, không dùng làm negative hoặc đưa vào train. Chưa có người rà độc lập. Bộ smoke có 14 quan hệ: same_transaction 8, before 1, obstructs_verification 1, prerequisite_for 2, controls_during 1, threatens_unless 1.
- Chia theo nhóm liên thông family/conversation/template/source và near-duplicate: 12 train, 4 validation, 4 test_locked. Không coi test nghiên cứu này là holdout độc lập: các mẫu do agent biên soạn và công khai trong repo. Chưa chạy đánh giá file test. Holdout cũ không được mở.
- Mọi task đều có trạng thái gán nhãn; span còn có coverage từng nhãn. Chỉ action có coverage hoàn thiện; nhãn span khác partial hoặc unannotated. Null thuộc tính bị mask; role/quan hệ partial không sinh negative từ phần chưa gán nhãn.
- [Hướng dẫn](../../../data/phobert/ANNOTATION_GUIDE.md), [schema](../../../data/phobert/schema.json), [phân bố](../../../data/phobert/audit.json), [hash/split](../../../data/phobert/splits/manifest.json). Log bất đồng rỗng vì chưa rà, không phải đồng thuận 100%.

## Những phép chạy đã hoàn tất

| Phép chạy | Phạm vi | Thời gian | Kết quả |
| --- | --- | ---: | --- |
| Head smoke | 12 train, chọn epoch bằng 4 validation; encoder đóng băng | 13.95 s | Head có học, encoder không đổi |
| Overfit chẩn đoán | 4 mẫu train; cùng mẫu để kiểm khả năng ghi nhớ | 12.47 s | Action F1 resubstitution 1.000; risk Macro-F1 0.667 |
| Fine-tune encoder thật | 2 mẫu, 1 epoch, một bước optimizer, task span | 5.29 s | Encoder probe thay đổi: True; checkpoint chỉ cho stage span |

Fine-tuning dùng checkpoint pretrained, không phải huấn luyện mô hình nền từ đầu. Bản fine-tune một bước có các head khác chưa học nên loader từ chối dùng nó làm pipeline API đầy đủ. Head smoke và overfit đều là nghiên cứu, không có checkpoint được duyệt production.
RAM working set cao nhất của bước fine-tune: 2.70 GiB. Chưa chạy khóa encoder mở trong nhiều epoch trên dữ liệu đủ lớn; chưa thử class weights/AMP/multi-task chung. Các task được huấn luyện riêng tuần tự.

## Validation: chất lượng thực tế

Chỉ **4 ca nháp**, không phải bằng chứng khái quát. Action span: precision 0.500, recall 0.250, F1 0.333. Thuộc tính action_type đúng 0/8 sự kiện gold khi tính cả lỗi trích đầu vào. Offset hợp lệ không chứng minh đúng ngữ nghĩa.

| Phương án | Risk Macro-F1 |
| --- | ---: |
| Rulebook hiện tại | 0.167 |
| PhoBERT baseline phân loại bốn mức | 0.125 |
| PhoBERT span dự đoán + quan hệ + quy tắc | 0.167 |
| Cấp span gold cho các head phía sau | 0.100 |
| Bỏ quan hệ | 0.167 |
| Bỏ role | 0.167 |

Cấp span gold còn kém hơn trong phép nhỏ này: head thuộc tính/quan hệ và quy tắc vẫn lỗi; chưa có bằng chứng cải thiện từ PhoBERT. Hai ablation bằng nhau không chứng minh các thành phần vô ích; tập quá nhỏ và quan hệ đầu ra sai/chưa tạo được khác biệt. Không sửa cấu hình theo tám ca công khai để gọi đó là kết quả độc lập.

Ma trận thực của pipeline (hàng gold, cột dự đoán; kết quả unsupported/error đếm riêng):

| Gold \ Pred | clear | need_context | suspicious | high | unsupported/error |
| --- | ---: | ---: | ---: | ---: | ---: |
| clear | 2 | 0 | 0 | 0 | 0 |
| need_context | 0 | 0 | 0 | 0 | 0 |
| suspicious | 2 | 0 | 0 | 0 | 0 |
| high | 0 | 0 | 0 | 0 | 0 |

Hỗ trợ theo nhãn tham chiếu: {'clear': 2, 'need_context': 0, 'suspicious': 2, 'high': 0}. Nhãn có hỗ trợ 0 chưa đo được recall; số 0 trong JSON dùng quy ước zero_division=0, không phải chứng minh không bỏ sót. Macro-F1 báo trên danh sách bốn nhãn cố định, không phải accuracy hoặc xác suất đúng ngoài thực tế.

Precision/recall/F1 từng nhãn span/quan hệ/rủi ro, đúng từng thuộc tính, role, hướng cạnh, no_relation và trạng thái xử lý nằm trong [validation_report.json](validation_report.json). Nhãn không có annotation hoàn thiện ghi not_measured; số hỗ trợ bằng 0 không phải bằng chứng chất lượng.

## Độ trễ và tài nguyên

- Inference trực tiếp, n=4: p50 482.92 ms, p95 nearest-rank 509.53 ms; nạp model trong process 997.21 ms; RSS quan sát 839.9 MiB.
- Toàn route ASGI /api/analyze, n=8: p50 547.46 ms, p95 nearest-rank 561.41 ms; startup process + lifespan 4051.55 ms. Chưa đo từ lúc bấm ở browser/extension, tải dài, disk cold hoặc nhiều mức tải.
- Đồng thời 3 request vào Runtime một slot, không hàng đợi ẩn: ['complete', 'busy_rejected', 'busy_rejected']. Hai lượt bận bị từ chối, không biến thành clear/need_context. Public API ánh xạ trạng thái bận sang 503 PHOBERT_BUSY.
- RDRSegmenter hiện khởi chạy Java theo request, góp phần lớn thời gian tiền xử lý; chưa triển khai segmenter persistent. Chi tiết preprocessing/inference/verification_reasoning/total từng ca ở predictions JSON. Không hứa thời gian trên nội dung khác.

## Tám ca công khai trước đó — chỉ hồi quy

| Ca | Backend luật trước | PhoBERT thử nghiệm | Nhận xét rà |
| --- | --- | --- | --- |
| 01 | need_context | suspicious | Sai cơ chế: giải thích chung về quyền/giấy tờ/tài chính, chưa nhận đúng giả người quen. |
| 02 | need_context | suspicious | Chưa nhận điều kiện nộp thêm để rút; cơ chế giải thích lệch. |
| 03 | need_context | clear | False-clear nghiêm trọng: nội dung có yêu cầu mã đăng nhập. |
| 04 | need_context | suspicious | Chưa giải thích đúng việc trung gian tiền và khai sai nguồn. |
| 05 | need_context | HTTP 503 | 503: không đủ đầu ra có cấu trúc để quyết định; không đổi thành need_context. |
| 06 | suspicious | suspicious | Chỉ cảnh báo chung, chưa nối đúng điều khiển từ xa với ngân hàng. |
| 07 | need_context | high | High nhưng giải thích sai cơ chế sang giao mã đăng nhập; không tính là đúng chỉ vì trùng mức. |
| 08 | suspicious | high | Có đầu ra high theo cơ chế giữ giấy tờ/khả năng trở về; cần người rà kiểm tra toàn bộ evidence. |

[api_eight_predictions.json](api_eight_predictions.json) giữ response và ms từng ca; [api_smoke.json](api_smoke.json) ghi kiểm tra nạp một lần, 422 đầu vào sai, 503 thiếu checkpoint và chặn mô hình chưa duyệt. Các lỗi trên là lý do không bật PhoBERT làm mặc định.

## Ví dụ chuỗi và bằng chứng

Xem [overfit_predictions.json](overfit_predictions.json): đầu vào, span có quote/offset, sáu thuộc tính từng sự kiện, vai, cạnh, rule_id, cơ chế, giới hạn và quyết định đều từ lần chạy thật trên bốn mẫu đã học. Đây là ví dụ resubstitution, không phải ca mới độc lập. Một quote chỉ xác nhận vị trí chữ; không xác nhận action_type/role mô hình suy ra là đúng.

## Tích hợp và nghiệm thu

- `SCAMSHIELD_REASONER=phobert` chọn pipeline riêng; mặc định legacy giữ nguyên. Runtime nạp một lần qua lifespan và cache, chỉ local_files_only; xác minh hash asset, heads, preprocessing và label mapping. Không có fallback sang Gemini, mock hoặc quy tắc trích cũ.
- Backend đọc sự kiện/quan hệ đã kiểm tra để quyết định; classifier bốn mức chỉ dùng đối chứng và ghi bất đồng. Không có bitmask hoặc cộng điểm trùng bằng chứng.
- 18 trường dùng kiểu hiện có, tổng hợp những dữ kiện có căn cứ, còn lại unknown. Các trường quan hệ/phạm vi lỗi bị loại trước quyết định. Quote, ID, speaker và transaction kiểm riêng. Không suy từ high thành phạm tội.
- RAG/URL tiếp tục nhánh enrich hiện có sau mô hình. Chế độ chạy offline mẫu tắt HTTP HEAD; không thêm nguồn chính thống chưa duyệt. Nội dung OCR vẫn phải qua cơ chế xác nhận cũ.
- Chưa hỗ trợ context_facts/bổ sung bối cảnh trong pipeline ML nháp: trả unsupported/503, không âm thầm bỏ qua hoặc hỏi người dùng điều đã có. Không thay khả năng này của reasoner mặc định.
- Đã chạy toàn bộ pytest backend và kiểm Node popup/worker/OCR; log chính xác tại final_tests.log và commands.json. Có thêm kiểm chặn checkpoint chỉ học stage span, speaker metadata nhiều người và RDR emoji/xuống dòng.

## Phần chưa hoàn thành để dùng thực tế

Chưa có gold độc lập hoặc đo test độc lập; chưa được hai người rà bất kỳ ca mới nào; chưa huấn luyện đủ span entity/object/condition/benefit/consequence, vai đối tượng nhắc gián tiếp và đồng tham chiếu; chưa nghiệm thu nhiều giao dịch/hội thoại dài bằng mô hình học; chưa có resolver quan hệ xa cửa sổ; chưa hiệu chuẩn điểm; chưa huấn luyện encoder đầy đủ qua các stage trên dữ liệu đủ; chưa có kiểm chứng giải thích ngữ nghĩa quy mô lớn, cân bằng lớp hoặc multi-task. Full fine-tuning path đã chạy một bước thật, không được gọi đó là mô hình hoàn chỉnh.

Mã, cấu hình và lệnh tái lập: [README_PHOBERT.md](../../README_PHOBERT.md).
