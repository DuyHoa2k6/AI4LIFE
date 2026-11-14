# Bộ suy luận ba trạng thái — bản 12/11/2026

**Đã tạm ngừng dùng mặc định theo yêu cầu mới.** Hệ thống hiện chạy `SCAMSHIELD_REASONER=legacy`, giữ luồng event/rulebook + RAG/URL. Phần dưới là tài liệu của thử nghiệm fact được lưu để đối chiếu, không phải hướng dẫn chạy mặc định.

Tại thời điểm thử nghiệm, cấu hình là `SCAMSHIELD_MODE=local_rules`, `SCAMSHIELD_REASONER=facts`. Hiện đã quay lại legacy như thông báo trên. Bộ bóc tách vẫn là Python/quy tắc, không phải mô hình được huấn luyện. Không gọi Gemini hoặc API mô hình ngoài.

## Trạng thái và nguồn

`Truth` là Enum TRUE/FALSE/UNKNOWN. Thiếu dữ kiện là UNKNOWN; FALSE đòi hỏi bằng chứng phủ định. Điều kiện dùng so sánh Enum tường minh, không dùng `not value` để gộp FALSE/UNKNOWN.

FactRecord gồm fact_id, fact_type, value, participant_ids, scope_id, transaction_id, source, evidence_refs, event_time, observed_at, version; thêm dependency_refs/rule_id cho dữ kiện suy ra và superseded_by cho lịch sử. Attributes giữ vai câu nói, trạng thái thời gian, nguồn phát ngôn đã chuẩn hóa.

Nguồn: observed_content (quan sát văn bản), sender_claim (bên gửi hoặc lời được thuật lại), user_report (người dùng bổ sung/tự thuật), technical_check (kết quả kiểm tra), derived (suy ra từ fact khác). TRUE mô tả điều được nguồn đó hỗ trợ, **không mặc nhiên là sự thật ngoài đời**.

Danh mục máy đọc: [fact_catalog.json](../data/v2/fact_catalog.json). Ví dụ payment_confirmed=TRUE là lời báo đã nhận đủ tiền, FALSE là lời báo chưa nhận, UNKNOWN là chưa có thông tin đủ rõ. Authentication_meaning của “sáu số” là UNKNOWN nếu chưa biết đó là loại mã gì. “Đừng gửi mã” giữ phủ định và direct_request=FALSE.

## Bảng ánh xạ

| Dữ liệu đã bóc tách | Fact/thuộc tính chuẩn hóa |
|---|---|
| handover_asset | handover_requested |
| transfer_funds | transfer_requested |
| receive_funds | payment_confirmed; positive nhưng chưa completed vẫn UNKNOWN |
| provide_code / provide_credentials | code_requested / credentials_requested; thêm authentication_meaning |
| provide_documents | documents_requested |
| install_app / share_screen / grant_control | install_requested / screen_share_requested / control_requested |
| Vai request/denial/quoted_warning/unknown | direct_request, denial, quoted_warning và thuộc tính speech_role |
| Quan hệ before/after/prerequisite_for/state_update/same_transaction… | Fact relation:* có dependency_refs của các sự kiện |
| Sự kiện an toàn con người | Giữ các nhãn restrict_movement, compel_work, retain_identity_documents… |
| Bước trích mở thông tin ngân hàng | bank_information_requested; quan hệ after chỉ khi có căn cứ nối chuỗi |
| Danh tính/quan hệ tự nhận | identity_claim / relationship_claim; không trở thành identity_verified |
| Bối cảnh người dùng | user_context_provided, nguồn user_report, chỉ gắn phạm vi đủ rõ |
| Mâu thuẫn thanh toán | Giữ từng claim; payment_resolution=UNKNOWN và danh sách conflicts |
| Chất lượng/độ phủ | analysis_coverage: có sự kiện trong phạm vi/giới hạn đã biết/không xác định; không chứng minh hiểu hết ngữ nghĩa |
| URL đã kiểm tra và nguồn đã dùng | Technical facts và derived support facts; bằng chứng ngoài nằm trong fact_trace.external_evidence |

## Pipeline và file

1. `engine.py`: gọi bộ trích an toàn, giữ nhánh khẩn; chỉ chạy bộ trích đầy đủ nếu cần. Bản quyết định cũ không còn được gọi mặc định, có chú thích chỉ tới `legacy_engine.py`.
2. `extract.py`, `local_observation/*`: bộ trích đang có. `semantic_events.py` bổ sung một lượt trích yêu cầu mở thông tin ngân hàng và nối chuỗi có dấu chỉ trình tự. Không đặt việc đọc lại văn bản trong từng quy tắc.
3. `fact_validation.py`: loại quote sai và annotations phụ thuộc trước khi tạo fact; xóa lời giải thích mất căn cứ. Dữ liệu còn sai không được coi là clear.
4. `facts.py`: chuẩn hóa một lần, tạo fact và chỉ mục theo loại, giữ người/phạm vi/quan hệ. Mã xác thực và bối cảnh được phân tích ở bước tạo fact, không lặp ở mỗi luật.
5. `fact_decision.py`: chỉ nhận FactStore, rulebook và template; không nhận văn bản gốc. Kiểm tra điều kiện, quan hệ, ngoại lệ và tổng hợp mức mạnh nhất đủ căn cứ.
6. `support.py` giữ hai nhánh RAG/URL đã triển khai. `support_facts.py` ghi các quan sát kỹ thuật và phụ thuộc vào fact audit. URL đơn lẻ không tạo high; nguồn không dùng không tự thành bằng chứng.
7. `adapter.py`: giữ API công khai và tám answers hiện có; 18 trường vẫn giữ. Trace fact chỉ có ở API thô `/api/analyze-local`; website/extension không hiển thị fact, bảng câu hỏi hoặc dữ liệu suy luận nội bộ.

## Quy tắc

Rulebook mới: [fact_rules.json](../data/v2/fact_rules.json), được kiểm tra bởi FactRulebook. Mỗi luật có ID/version/scope/required_conditions/required_relations/exclusion_conditions/conclusion/evidence_requirements/missing_information/follow_up_template/explanation_template.

- MATCHED: đủ điều kiện TRUE (hoặc đúng trạng thái FALSE được yêu cầu, như chưa nhận tiền), đủ quan hệ và không có ngoại lệ được xác định áp dụng.
- NOT_MATCHED: có điều kiện quyết định được xác định không thỏa, hoặc có ngoại lệ áp dụng.
- UNDETERMINED: thiếu điều kiện, loại mã chưa rõ, hoặc chưa nối đúng người/phạm vi/quan hệ.

Không thực thi biểu thức Python từ cấu hình. Loại fact, quan hệ, template và phạm vi không hợp lệ bị từ chối. Không triển khai bitmask: dùng Enum làm bản tham chiếu, chưa có bằng chứng cần tối ưu bit và không đánh đổi kho bằng chứng để lấy tốc độ.

| Luật | Tổ hợp chính | Mức |
|---|---|---|
| R-HANDOVER | Yêu cầu giao + payment_confirmed FALSE + before + same_transaction + cùng phạm vi/người | suspicious |
| R-CREDENTIAL | Yêu cầu cung cấp mật khẩu hoặc mã có authentication_meaning TRUE | high |
| R-CODE-IDENTITY | Dãy số được tin liên quan xác định là mã đăng nhập, có quan hệ rõ | high |
| R-PAY-TO-WITHDRAW | Chuyển tiền là điều kiện nhận/rút tiền | high |
| R-SCREEN-BANK | Yêu cầu chia sẻ màn hình + mở thông tin ngân hàng + trình tự after có căn cứ | high |
| R-DATA | Yêu cầu cung cấp giấy tờ nhạy cảm | suspicious |
| R-ACCESS | Yêu cầu cài ứng dụng/chia sẻ màn hình/cấp quyền | suspicious |
| R-TRAVEL-SECRET | Di chuyển gắn giữ bí mật | suspicious |
| R-DEBT-EXIT / R-DOC-EXIT | Khoản nợ hoặc giữ giấy tờ gắn với hạn chế rời đi | high |
| R-CONTROL | Hạn chế liên lạc/giữ giấy tờ, xét ngoại lệ có thể lấy lại/tự do | suspicious |
| R-CHANGE-WORK | Lời mời việc và thay đổi điều kiện có quan hệ | suspicious |
| R-RELEASE | Yêu cầu tiền để thả/rời đi theo lời bên đòi tiền | high, không chứng minh bắt cóc |
| R-COERCION | Dữ kiện cưỡng ép/đe dọa phù hợp luật | high |
| R-URGENT-CURRENT / R-URGENT-THREAT | Nguy hiểm hiện tại/sắp xảy ra đủ điều kiện nguồn, vai, thời gian | high + urgent |

Với ngoại lệ UNKNOWN, luật cũ chuyển sang chính sách `limit_claim`: cảnh báo về yêu cầu/dấu hiệu **trong nội dung hiện có**, không khẳng định vụ án, sự việc ngoài đời hoặc tương lai không có cập nhật. Luật chọn `undetermined` sẽ không MATCH khi ngoại lệ còn UNKNOWN. Mâu thuẫn được giữ riêng và hỏi làm rõ; không lấy UNKNOWN ở một nhóm khác để hạ high đã có căn cứ.

Nếu không có luật nguy cơ MATCH: chỉ clear khi có căn cứ thuộc phạm vi hỗ trợ, không còn yêu cầu đáng ngờ và độ phủ không bị báo thiếu. Trường hợp ngoài phạm vi/thiếu quan hệ giữ need_context; “Mây bay trên núi” vẫn need_context, là hạn chế chưa khắc phục.

## Cập nhật và phiên

Một claim chỉ bị thay thế khi có state_update cùng phạm vi/người bị tác động và cùng nguồn phát ngôn, hoặc bối cảnh người dùng báo tự kiểm tra và nhận đủ tiền được gắn **duy nhất một phạm vi**. Lời người mua không tự ghi đè lời người bán. Bối cảnh phủ định, trích lời, giả định hoặc giao dịch khác không được dùng như xác nhận thanh toán.

Giữ claim cũ bằng superseded_by; phiên bản mới có version và dependency_refs. Tránh chu trình phụ thuộc khi relation đã tham chiếu chính observation mới. observed_at là thời điểm BE tiếp nhận, không dùng để suy ra event_time hoặc thứ tự thanh toán.

FactStore hiện **không lưu bền qua các request**. Phiên bản là lịch sử được tái dựng trong một snapshot input; phải dùng input_sha256/lần phân tích để phân biệt fact_id giữa các request. Khi bổ sung thông tin, chạy lại từ hội thoại + bối cảnh; extension vẫn giữ cơ chế phiên/phiên bản mục để bỏ phản hồi cũ. Chưa có cơ sở dữ liệu lịch sử fact hay đồng bộ thời gian sự kiện ngoài đời.

## Trạng thái chạy và tương thích

- complete: hoàn tất phạm vi xử lý đang chọn; urgent_precheck có chủ ý giữ phần còn lại unknown.
- partial: loại được bằng chứng/tham chiếu sai hoặc nhận diện phần vượt giới hạn; high độc lập vẫn được giữ, không tạo clear từ phần thiếu.
- error: lỗi xử lý/cấu hình; risk_status không được tạo thành clear. API chung trả lỗi 503 khi không có kết luận hợp lệ.

API công khai vẫn schema_version=2.0, bốn risk_status. AnalysisTrace.decision_version=`facts-1.0-support`, thêm extraction/fact_build/rule_evaluation vào stage_timings_ms. API thô có fact_trace và core_timings_ms. JSON schema mới được xuất vào data/v2/output.schema.json, fact_record.schema.json và fact_rulebook.schema.json. Schema bộ ca gán nhãn giữ nguyên; không tự sửa nhãn dataset để khớp bộ suy luận mới.

## Chạy và đối chiếu

```powershell
$env:SCAMSHIELD_MODE="local_rules"
$env:SCAMSHIELD_REASONER="facts"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Đối chiếu bản cũ: đổi SCAMSHIELD_REASONER sang `legacy` rồi khởi động lại. Không dùng legacy làm kết quả mặc định hoặc gộp hai bộ bằng bỏ phiếu.

```powershell
python -m unittest discover -s tests -v
python benchmark_fact_reasoner.py --rounds 30 --output reports/fact_comparison_rerun
python check_fact_examples.py --output reports/fact_examples_rerun
```

Thư mục đo phải mới. Benchmark dùng cùng 12 ca dev, luân phiên cũ/mới, HTTP TCP localhost, tắt mạng URL và không gọi mô hình, lưu dự đoán trước khi đọc expected. Không đo độ trễ redirect thực, tải đồng thời hoặc độ chính xác độc lập. `validate_v2_dataset.py` vẫn rà grounding của nhãn pilot theo rulebook gốc có chỉ rõ trong báo cáo; nó đồng thời xác thực cấu hình fact mới, không tự đổi nhãn để làm đẹp kết quả.

Kết quả và giới hạn đo: [báo cáo](reports/fact_reasoner_20261112/README.md).
