# Đánh giá và cải tiến có kiểm soát — 14/11/2026

**Đạt tầng A (pipeline chạy thật). Chưa đạt B hoặc C. Candidate không được chọn.**

## Dữ liệu và điều kiện ban đầu

- Checkpoint thực: `artifacts/phobert/smoke_heads`, PhoBERT base + head đã học với encoder đóng băng. Bản fine-tune encoder một bước trước đây chỉ học task span, không đủ head để chạy toàn luồng. Không gọi Gemini/API mô hình ngoài.
- 35 ca draft đa lĩnh vực: khóa học, tình cảm, tài chính/quyền sở hữu, việc làm, dịch vụ, dữ liệu/quyền truy cập và đóng góp. Trong đó 5 ca khóa học/biến thể đã có nền từ ví dụ prompt nên đánh dấu seen_development; 30 nhánh draft công khai mới được biên soạn. Không gọi bất kỳ mẫu nào là holdout mù.
- 16 regression từ train/validation cũ đã biết; không mở test_locked/holdout cũ. Tổng mỗi vòng 51 ca, tất cả draft, 0 human-reviewed. Có 1 ca cập nhật dịch vụ còn mơ hồ được đưa vào review queue, không sửa nhãn để khớp mô hình.
- Chia trước inference: 25 diagnostic, 10 validation, 16 regression. Cùng family/template/source ở cùng split; kiểm near-duplicate bằng mã. 35 ca không đáp ứng mục tiêu biên soạn 84, chưa có đủ biến thể và rà độc lập để tăng quota một cách có ý nghĩa.
- Baseline source, checkpoint, tokenizer/label mapping, cấu hình acceptance và hash dữ liệu đã khóa. File expected không đi vào Runtime; mọi E2E prediction được lưu xong trước khi chấm hoặc chạy oracle.

## Trước/sau

| Chỉ số, mẫu số 51 trừ khi ghi khác | Baseline | Candidate 01 |
| --- | ---: | ---: |
| Risk Macro-F1 (draft, không phải accuracy ngoài thực tế) | 0.3087 | 0.2860 |
| Thành công cấu trúc + đúng mức | 9/51 | 9/51 |
| Đúng mức nhưng sai căn cứ theo kiểm tra cấu trúc | 9 | 6 |
| Coverage có mức trong bốn nhãn | 0.9412 | 0.7059 |
| Clear bị high | 2 | 2 |
| High bị bỏ sót (kể cả không xử lý được) | 9 | 9 |
| Oracle annotations → reasoner Macro-F1 | 0.3720 | 0.8937 |
| Oracle trigger spans → model heads → reasoner Macro-F1 | 0.2872 | 0.3004 |
| p50 toàn wrapper inference/policy (ms) | 868.67 | 841.31 |
| p95 nearest-rank (ms) | 1700.26 | 1699.47 |

Oracle là debug với tham chiếu draft, không là kết quả sản phẩm. Bộ suy luận nhận được cấu trúc tốt hơn đã cải thiện, nhưng head PhoBERT vẫn không tạo được đúng cấu trúc trên nhiều nhánh. Chưa có bằng chứng cải thiện end-to-end. Không đưa đầu ra oracle vào fallback API.

## Theo nhóm (bao gồm regression thuộc nhóm đó)

| Nhóm | n | Macro-F1 trước | Sau | Thành công cấu trúc trước/sau |
| --- | ---: | ---: | ---: | ---: |
| contributions | 5 | 0.0000 | 0.0000 | 0/0 |
| data_access | 11 | 0.4542 | 0.5125 | 5/5 |
| education | 5 | 0.0000 | 0.0000 | 0/0 |
| employment | 7 | 0.3667 | 0.3667 | 2/2 |
| finance | 13 | 0.3929 | 0.3409 | 2/2 |
| relationships | 5 | 0.1667 | 0.0000 | 0/0 |
| services | 5 | 0.2500 | 0.2500 | 0/0 |

## Tách đúng phạm vi đo

| Tập | n | Macro-F1 trước | Sau | Thành công cấu trúc trước/sau |
| --- | ---: | ---: | ---: | ---: |
| diagnostic | 25 | 0.0833 | 0.0625 | 0/0 |
| regression | 16 | 0.5809 | 0.5536 | 9/9 |
| validation | 10 | 0.1667 | 0.1667 | 0/0 |

Phạm vi label map checkpoint: 17/51 ca biểu diễn được toàn bộ thuộc tính tham chiếu; các ca còn lại có ít nhất một nhãn cơ chế mới chưa được head huấn luyện. Đây là giới hạn schema/coverage, không tự chứng minh encoder không hiểu ngôn ngữ. JSON có within_checkpoint_vocabulary riêng; không đổi nhãn tham chiếu thành nhãn cũ để làm đẹp điểm.

Không trộn điểm regression với khả năng khái quát: JSON có by_split riêng cho diagnostic, validation và regression. Tất cả đều công khai; independent_holdout.score=null. Dữ liệu ít và draft nên ưu tiên số đếm. Khoảng bootstrap theo family chỉ mô tả tập công khai, không phải độ chính xác dân số.

## Năm nhóm lỗi tiêu biểu và phần sửa

1. **Khoảng trống label/action-object:** nhiều hành động ký nghĩa vụ, chuyển quyền, xác nhận dịch vụ và kiểm soát lương không có trong label map đã học. Đây là giới hạn biểu diễn đã xác định; không tự nạp checkpoint cũ vào head đổi kích thước. Cần gold được duyệt rồi migration/fine-tune; vòng này không đổi trọng số.
2. **Người chưa rõ dùng ID chung:** baseline có thể giữ recipient:unknown qua nhiều tin nhắn. Candidate tách unknown theo message, giữ speaker metadata và loại vai tham chiếu sai. Không tự đoán danh tính hoặc gộp người không rõ.
3. **Cập nhật trạng thái/phạm vi:** candidate yêu cầu state_update giữa hai báo cáo cùng action/object, cùng giao dịch đã phân giải, hướng cập nhật hợp lệ và không trái vai đã biết. Không cho một yêu cầu mới xóa trạng thái cũ hay cho đơn đã trả xóa rủi ro đơn khác.
4. **Giải thích chung lệch cơ chế:** thay mẫu gộp “thiết bị, giấy tờ hoặc tài chính” bằng mẫu theo action/object tương thích; thêm graph rule có điều kiện cho nghĩa vụ bị che giấu, quyền vượt mục đích, kiểm soát thu nhập/nghỉ việc và xác nhận dịch vụ trước thực hiện. Không dò nguyên văn câu hoặc domain để tăng high.
5. **Lỗi nhãn/thiếu dữ kiện chưa giải quyết:** case cập nhật dịch vụ N33 cần rà mâu thuẫn về quyền khiếu nại; một số placeholder/quan hệ và mục đích hỏi còn cần người xác nhận. Chỉ phát câu hỏi theo dữ kiện có cấu trúc, không dùng độ tự tin thấp thành need_context. Các đánh giá ngữ nghĩa tự động là proxy, không thay người rà.

Chi tiết trước/sau từng case, expected/predicted từng tầng, confirmed/suspected, evidence, origin_module, severity và review_state nằm trong error_log.jsonl, case_diagnostics.jsonl và review/review_queue.jsonl. Label đúng nhưng căn cứ sai bị ghi riêng. Không khẳng định mọi khác biệt với draft là lỗi mô hình.

## Cổng chọn phiên bản và lý do dừng

- acceptance.yaml đóng băng trước vòng đầu: main metric tăng ít nhất 0,05 tuyệt đối, không tăng high nhầm/không tăng bỏ sót high, không giảm coverage, p95 ≤5 giây, RSS ≤4 GiB; tối đa 3 vòng gồm baseline và 2 cấu hình. Đây là ngưỡng nghiên cứu do người triển khai chọn, không phải chuẩn sản phẩm.
- Đã thử 2 cấu hình: baseline và candidate policy-only, 204 lượt gọi model (E2E và oracle spans), không chạy vô hạn. Candidate không tăng main metric và giảm coverage; không được promote. Không có vòng 2 để học thuộc.
- Training gate exit 3: 0 mẫu mới đã được hai người rà, nên không train trên draft hoặc dự đoán, không tạo checkpoint mới giả. Có công cụ strict warm-start/replay và kiểm label mapping cho khi có dữ liệu hợp lệ.
- Comparison exit 2: chất lượng không đạt và hai điều kiện reviewed_validation/independent_holdout chưa xác định. Không tự coi null là pass. Model baseline và bản rollback được giữ, production default legacy không đổi.

## Hiệu năng và kiểm chứng

Cold load model baseline/candidate: 2135.17/1730.15 ms. RSS quan sát: 843.3/842.8 MiB. CPU i5-12500H, RAM 15,7 GiB, 2 torch threads, float32, CUDA/VRAM 0, sequential concurrency=1. Độ dài đầu vào và thời gian từng ca có trong manifest/predictions. Đây là wrapper local, chưa đo browser/extension hoặc tải dài.
- Evidence rate có mẫu số trước và sau verifier trong metrics.json. Offset đúng không chứng minh action/quan hệ đúng. Chỉ số mẫu số 0 là null; không ghi 0%/100% cho phần không đo được.
- Công cụ tập khóa tách predict(inputs only) khỏi score(private labels + attestation); không có dữ liệu độc lập được cung cấp nên chưa chạy chấm mù. Tên thư mục không chứng minh độc lập.

## Bàn giao

Mã và lệnh: [../../README.md](../../README.md). Dữ liệu, schema, acceptance và review queue ở evaluation/. Checkpoint thực giữ tại evaluation/models/rollback_baseline, model_manifest.json ghi lựa chọn. Checkpoint gốc không bị đổi. Logs kiểm thử riêng tại tests.log.

## Kiểm thử cuối

332 passed, 1 warning in 60.89s (0:01:00)
Node popup/version 4, worker security 14, OCR worker 7 đã chạy qua; xem command_results.json.

Ví dụ dữ kiện trước/sau có quote và trạng thái thật: [CASE_REVIEW.md](CASE_REVIEW.md). Coverage theo từng hiện tượng còn thiếu: [inventory.json](inventory.json).
