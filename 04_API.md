# Hợp đồng API

Grounding 2.0: API raw `/api/analyze-local` thêm `annotations.mentions`,
`annotations.grounding_trace`; `Event.semantic` thêm speech_act, condition,
consequence_refs, mention_refs, transaction_reference/transaction_binding.
Các trường cũ giữ tương thích. `/api/analyze` vẫn schema 2.0, bốn mức và trạng
thái xử lý riêng; không thêm debug lên UI mặc định. Partial/unsupported mô tả
giới hạn BE, không tự quy thiếu dữ kiện cho người dùng; lỗi không có kết luận
trả 503. Chi tiết [grounding 2.0](ScamShield_AI/GROUNDING_V2.md).

Lớp semantic-graph-1.0 (13/11/2026) thêm `Event.semantic`, `annotations.graph_trace`
và `interpretation.mechanisms` trong `/api/analyze-local`; Situation thêm tham
chiếu đối tượng, điều kiện và trạng thái được báo. Đây là mở rộng additive,
không đổi request hoặc bốn risk_status của `/api/analyze`. Debug không đưa lên
UI mặc định. Chạy local không dùng API mô hình. Xem
[đặc tả](ScamShield_AI/SEMANTIC_GRAPH.md). Quy tắc G mới nâng tổ hợp danh tính
tự nhận + người nhận tiền khác + cản trở xác minh lên high; không nâng mọi ca
đổi tài khoản. Snapshot kỳ vọng cũ vẫn giữ trong lịch sử báo cáo.

Cập nhật 13/11/2026: `/api/analyze-local` bổ sung trong `interpretation` hai
danh sách `clause_roles` và `salient_actions`. Vai trò được gán từ nguyên văn,
không phải xác minh danh tính; `affected_status` có `textual_role/unknown`.
Hành động chính có event/quan hệ hỗ trợ, hậu quả có thể xảy ra và `is_primary`.
Không đưa các trường này vào UI công khai hoặc đổi enum bốn mức. `/api/analyze`
vẫn trả các trường display/bằng chứng theo hợp đồng cũ. Xem
[mô tả bản thử](ScamShield_AI/CLAUSE_ROLES.md). Các mô-đun RAG và URL vẫn là dữ
kiện bổ trợ theo cấu hình hiện hành; không có lời gọi mô hình bên ngoài.

Hệ thống hiện chỉ có bốn risk_status: clear, need_context, suspicious, high.

Chuyển tạm 12/11/2026: /api/analyze hỗ trợ mode=local_rules (schema response 2.0),
adapter từ CaseInput/LocalResult giữ hợp đồng client text/messages và tám answers.
AnalysisTrace nhận pipeline=local_rules/routing=local_backend/live_status=not_used.
Response thêm safety_urgency, urgency_evidence, analysis_status; UI chỉ hiện banner
khẩn khi urgency quote khớp. Display fields do BE dựng, decision_version=local-rules-2.0.
Mode local không gọi provider hoặc kiểm tra URL mạng; lỗi không có kết luận trả
LOCAL_ANALYSIS_UNAVAILABLE/503, không tự clear. [Cấu hình/hoàn tác](ScamShield_AI/TEMP_LOCAL_MODE.md).

Bổ sung thử nghiệm 12/11/2026: **POST /api/analyze-local** nhận CaseInput v2, trả
LocalResult/local-reasoning-2.0. assessment chứa bốn risk_status và safety_urgency
riêng (undetermined/preventive/urgent), rule/evidence IDs, template và giới hạn kết
luận. Urgent precheck không chờ đủ 18 trường hoặc truy xuất. Lỗi trả HTTP 503 với
analysis_status=error, risk_status=null khi chưa có kết luận; không đổi thành clear.
**GET /local** là giao diện riêng. /api/analyze và extension cũ giữ nguyên.
[Schema và cách chạy](ScamShield_AI/LOCAL_REASONING_V2.md), [dataset](data/v2/README.md).

Trong /api/observe, rules-1.2 thêm abbreviation_version/abbreviation_sha256 và
abbreviation_resolutions: source/message_id/start/end/quote/status/expansion/
alternatives/rule_ids/basis. Status là resolved/ambiguous/unresolved theo ngữ cảnh
từ vựng, không phải mức rủi ro. Bản mở rộng chỉ phục vụ khớp luật, quote vẫn từ
nguyên bản. Kho có cấu trúc và ví dụ ở [dataset viết tắt](data/README_ABBREVIATIONS.md).

Bổ sung 12/11/2026: **POST /api/observe** nhận AnalyzeRequest, trả Observation
schema_version=observation-1.0, mode=python_rules, answers_18, participants/units/
events/relations/evidence, follow_up_questions, limitations, input_sha256,
rules_version/rules_sha256, adapter InitialReview tám answers, elapsed_ms.
Đây là endpoint thử riêng bước đầu, không có risk_status, không gọi provider,
retrieval/URL/OCR và chưa thay bước đầu /api/analyze. Dùng chung giới hạn request,
lỗi 413/422; tối đa 50 event có thông báo phần chưa phân tích. Context có
source=context/provenance=user_report. [Hợp đồng và ánh xạ](ScamShield_AI/README_PYTHON_OBSERVATION.md).

Bản hiện hành two-pass-6 dùng schema response 1.9, kể cả khi có OCR/URL.
Provider dùng InitialReviewDraft/FinalReviewDraftV6, không xuất speaker trong finding;
backend nối tác giả từ message_id đã kiểm tra. Public Finding vẫn giữ speaker.
Tối đa một lần sửa bằng chứng/nhất quán dùng chung observation và review, không quá
ba model calls trước retry HTTP. EVIDENCE_INVALID có diagnostic stage/kind/repairs/
finding_index/types, không có quote hoặc tên trường tùy ý.

FinalReviewV6 thêm situation_facts (16), situation_links (10), information_gaps (5).
Fact gồm id/kind/speech_role/evidence/context_evidence/finding_refs; link gồm kind/
fact_ids/status/evidence/missing_information; gap gồm kind/evidence/finding_refs/
affects_decision. Các evidence đều dùng ID/Unicode offset gốc. Link cần bằng chứng
cho mỗi đầu mút, đúng vai/người nói/phạm vi; không dùng nguồn RAG làm bằng chứng đầu vào.
Bối cảnh bình thường có thể từ hội thoại, không bắt người dùng chép lại vào context.
Response thêm display_summary/display_action/risk_indicators do backend dựng bằng
mẫu sau kiểm chứng, không lấy prose tự do từ model. Client cũ có thể bỏ qua trường
mới; client hiện hành hiển thị quote và lời giải thích đã kiểm tra. Không hiển thị
answers/source_matches/retrieval/prompt. Nguồn chuẩn: schemas.py và RISK_STATES.md.
Theo yêu cầu ngày 10/11/2026, đã loại trạng thái đối chiếu xác minh và màu đỏ đậm
khỏi schema/giao diện; high là mức cảnh báo cao nhất. Lỗi phân tích vẫn trả lỗi
riêng, không chuyển thành một mức cảnh báo. Các mô tả phiên bản cũ chỉ là lịch sử.

## Hiển thị kết quả — 10/11/2026

Bản two-pass-5 giảm regex thành gợi ý. Nội bộ FinalReviewV5 thêm
rule_hint_reviews[{hint_id,interpretation,evidence,finding_refs,missing_information}],
phải rà đủ mỗi rule_hints.id (tối đa 12). Bác/phân loại lại phải có trích dẫn gốc
liên quan; uncertain phải nêu phần thiếu, needs_context và chủ đề hỏi. Không rà đủ
thì yêu cầu sửa tối đa một lần, còn sai trả lỗi. Regex không được ghép vào preliminary
để tự tạo rule_conflicts hoặc ép need_context. Quan sát Gemini lượt đầu chưa được
giải quyết vẫn được giữ kiểm tra riêng. Analysis thêm ba bộ đếm rule_hints_reviewed,
rule_hints_reclassified, rule_hints_uncertain; rule_conflicts trong two-pass-5 còn
phản ánh bất đồng quan sát Gemini đầu/cuối, không phải quyền phủ quyết của regex.
Thêm chủ đề câu hỏi requested_action/requested_object/action_relation, vẫn tối đa hai.
Tiêu chí chi tiết: [RISK_STATES.md](ScamShield_AI/RISK_STATES.md).

Website và extension giữ nguyên request/response và quyết định risk_status của backend.
Giao diện dùng mức cảnh báo, trích dẫn đã khớp message/speaker/offset và các câu hỏi
bổ sung để dựng tóm tắt, bước xác minh và giải thích ngắn. Không hiển thị answers,
source_matches, retrieval, prompt, inference hoặc mô tả mô hình tự do. Những trường
này vẫn được giữ trong API để phân tích/kiểm thử. Thông tin URL kỹ thuật không phải
danh sách nguồn RAG. Bổ sung bối cảnh tiếp tục dùng context, giữ nguyên bản text/messages,
links và ocr_sources của đúng lần phân tích, xác nhận lại trước khi gửi; giới hạn cũ giữ nguyên.

Lỗi xác thực đầu vào HTTP 422 (`INVALID_INPUT`) có thể kèm `diagnostic` với
`stage=request_validation` và tối đa 5 `issues` gồm `path`/`type`. Không trả lại
nội dung đầu vào, URL, thông điệp ValueError hoặc tên trường tùy ý; tên trường
không thuộc schema được thay bằng `field`. Đầu vào lỗi vẫn bị chặn trước provider.

## Luồng hiện hành two_pass — response 1.3

Bổ sung chất lượng v2: FinalReviewV2 có uncertainty_reasons[{finding_id,kind}], kind là identity/purpose/action/relation. Thiếu danh tính/mục đích không tự phủ nhận yêu cầu đã quan sát; thiếu thông tin có thể đi kèm suspicious hoặc high. Bất định hành động/quan hệ, refs sai hoặc bối cảnh mâu thuẫn vẫn chặn nâng mức. Nguồn hỗ trợ có relation chưa rõ cũng không được nâng high. analysis có decision_version/information_needed. Claim/cảnh báo/phủ định không cần exemption benign dựa vào context; các request thực sự vẫn phải có context hợp lệ để miễn.

Gemini dùng json_schema dạng cấu trúc tương thích; schema Pydantic đủ giới hạn tiếp tục kiểm tra tại backend. Chỉ danh sách question_topics hợp lệ được bỏ trùng/giới hạn hai, không sửa finding/quote/quan hệ. Lỗi provider có diagnostic an toàn: stage/kind/attempts/output_format/issue path+type, không input/msg/ctx/key. Auto chọn schema cho host Gemini, json_object giữ cho adapter cũ; không tự hạ định dạng khi HTTP 400. Một retry cho 503/mất mạng nếu cấu hình, trong ngân sách 20 giây có sẵn; không retry 429, auth, schema sai hay đợi timeout thêm 20 giây.

Giữ request POST /api/analyze. Mode mới two_pass luôn gọi hai lượt model khi các bước trước thành công; không tự bỏ lượt hai. InitialReview gồm answers/findings/hypotheses/uncertainties; FinalReview gồm answers/findings/review/source_uses/scenario_refs. Provider không đặt risk_status hoặc verified_match. Quote duy nhất dùng null offset và backend tự tính; context hint là nguyên văn có vị trí backend tính sẵn.

Response thêm retrieval.scenarios và retrieval.official_sources, mỗi nhánh có status (disabled/no_approved_sources/no_match/matched/timeout/error), retrieved_count, elapsed_ms. analysis thêm pipeline=two_pass, routing=two_live_calls, initial_findings, initial_hypotheses, discarded_source_uses, scenario_matches và stage_timings_ms. source_matches chỉ chứa nguồn đã duyệt, thật sự được cung cấp và dùng, liên kết tới finding cuối hợp lệ; URL/quote lấy từ kho. Không trả nguồn ví dụ tổng hợp như nguồn nhà nước. Không suy verified_match từ nguồn tương tự.

Giới hạn mỗi lượt provider mặc định 20 giây, pipeline 45 (trần 50), client 55, tối đa 3 đoạn/nhánh, 1.600 ký tự/đoạn, nhánh mặc định 0,8 giây. Nhánh truy xuất lỗi vẫn đánh giá văn bản đủ căn cứ; lỗi provider ở lượt nào cũng trả lỗi, không fallback clear. Hai answers về tự nhận danh tính và mạo danh được trình bày từ quote có căn cứ, không phát nguyên văn suy luận tự do. Các mode/schema cũ dưới đây là hợp đồng đối chứng còn hỗ trợ. [Hợp đồng chi tiết](ScamShield_AI/TWO_PASS.md).

## Luồng kết hợp hybrid — 08/11/2026

Giữ POST /api/analyze và request 1.0; response 1.1 cho mode=hybrid. Thêm mode hybrid và analysis tùy chọn: pipeline, routing, rules_version, preliminary_risk, preliminary_findings, rule_conflicts, discarded_live_findings, live_status. Mock/live cũ vẫn trả schema_version=1.0; client cần hiện đúng hybrid, không gọi đó là mock. Luồng hybrid luôn gọi live đúng một lần sau phân tích sơ bộ, kể cả không có từ khóa. Không có cơ chế bỏ qua live khi chưa có số liệu điều phối. Lỗi live trả 502/503/504, không âm thầm trả mock hoặc clear.

Schema provider nội bộ HybridReview thêm review: risk_links(request_id/support_id), benign_finding_ids, uncertain_finding_ids, needs_context, question_topics, context_evidence. Tất cả references phải được backend đối chiếu với finding còn hợp lệ; context_evidence đối chiếu nguyên văn context. Model không đặt risk_status/nguồn/verified_match. Nhãn từ quy tắc là giả thuyết, không phải đáp án cần xác nhận. Backend chỉ công nhận ngữ cảnh giảm cảnh báo khi có trích context hợp lệ; đó vẫn là thông tin người dùng khai, không phải xác minh danh tính. Hybrid cũ không chạy nhánh RAG; luồng two_pass mới đã có nhánh thử nghiệm có cổng phê duyệt, chưa có nguồn thật đủ điều kiện trong kho hiện tại.

## Quyết định mock hành vi — 08/11/2026

Giữ schema 1.0 và endpoint chung, không thêm trường bắt buộc cho web/extension. ID finding là chuỗi opaque; mock mới có thể chứa tiền tố ID quy tắc để truy vết, client không phân tích định dạng ID. Phiên bản và registry quy tắc được lưu trong báo cáo riêng. Bằng chứng mock là câu/đoạn ngắn giữ nguyên Unicode gốc. inference/evidence_refs của kết quả chỉ được backend dựng lại sau kiểm chứng; không tin các liên kết hay giải thích do provider tự khai. Live giữ đường quyết định hiện có, việc mở rộng mock không được coi là cải thiện chất lượng live.

## Quyết định triển khai tuần 1 (08/11/2026)

Giới hạn question là 1.000 Unicode code point; context 2.000; tổng text/messages 10.000; tối đa 100 tin. Body UTF-8 tối đa 65.536 byte kể cả gửi chunked. Chuỗi nội dung không bị strip hoặc chuẩn hóa Unicode trước tính offset; chuỗi chỉ có khoảng trắng bị từ chối. ID tối đa 100 ký tự, speaker tối đa 100 ký tự; hai trường không rỗng. Trường dư bị từ chối. Request có đúng một khóa text/messages, kể cả null cũng không hợp lệ. Timeout provider mặc định 20 giây. Phiên bản tuần 1 chưa triển khai rate limit nên chưa phát 429 tại ứng dụng; lỗi 429 từ provider được chuyển 503. Chỉ cho origin được cấu hình qua môi trường.

Finding có thêm speaker được đối chiếu với message gốc. inference gồm status inferred/unknown, text và evidence_refs; explanation chỉ sinh lại từ findings đã kiểm chứng. Mô hình trả tám answers nội bộ, nhưng câu trả lời công khai được dựng lại bằng mẫu từ bằng chứng hợp lệ để không giữ văn bản suy luận bịa. source_matches có schema nhưng luôn rỗng trong tuần 1. Schema OpenAPI từ backend là nguồn chuẩn cho client. Mock là bộ quy tắc xác định phục vụ tích hợp, không đại diện chất lượng live.

POST /api/analyze nhận application/json. Dùng một trong hai đầu vào là text hoặc messages. text được bọc thành một tin m1 có speaker=unknown. messages gồm id duy nhất, speaker và text theo thứ tự gửi. context và question là trường tùy chọn. Đề xuất tối đa 10.000 ký tự phần nội dung và 2.000 ký tự cho bối cảnh. Backend chuẩn hóa giới hạn sau khi nhận và giữ nội dung đã gửi làm căn cứ offset.

Mỗi bằng chứng dùng message_id, start, end và quote. start và end là vị trí Unicode code point tính từ 0, end loại trừ. Chỉ highlight khi dùng cùng bản văn đã đối chiếu. Backend có thể tự tính offset từ câu nguyên văn nếu chỉ có một vị trí khớp. Nếu lặp nhiều lần và thiếu vị trí hợp lệ, loại trích dẫn hoặc yêu cầu đầu ra mới theo ngân sách timeout.

| Trường response | Kiểu và ý nghĩa |
| --- | --- |
| schema_version | 1.9 cho two-pass-6 (gồm OCR/URL); các mode đối chứng giữ phiên bản cũ |
| mode | mock, live, hybrid hoặc two_pass |
| risk_status | Một trong bốn mã: clear, need_context, suspicious, high |
| summary | Một đoạn ngắn tiếng Việt |
| answers | Object có tám khóa tại 03, mỗi giá trị gồm status, text và evidence_refs |
| findings | Mảng gồm id, action, description, speech_role, evidence và inference |
| suspected_scam_types | Mảng tên gợi ý, có thể rỗng |
| missing_information | Mảng chi tiết còn thiếu |
| follow_up_questions | Tối đa hai câu |
| recommended_actions | Mảng thao tác xác minh an toàn |
| answer_to_user | Chuỗi hoặc null, trả lời question dựa trên bằng chứng đã duyệt |
| source_matches | Mảng kết quả đối chiếu thật, có nguồn và mức đối chiếu, mặc định rỗng |

speech_role nhận request, quoted_warning, denial, claim hoặc unknown. action dùng mã hành vi như transfer_funds, share_auth_code, grant_access hoặc other kèm description. evidence_refs tham chiếu finding có bằng chứng còn hiệu lực. summary, answer_to_user và hành động đề xuất không được suy ra từ finding đã bị loại. Dùng mẫu giải thích xác định ở backend khi không kiểm tra được đầu ra tự do của mô hình.

Backend giữ quyền đặt risk_status. Provider nhận đầu vào và schema trích xuất. Provider không được gán trạng thái verified_match, thực hiện yêu cầu mạng theo nội dung, hoặc tự tạo nguồn. Không đưa tập validation hoặc holdout vào prompt.

Lỗi trả cấu trúc code, message và request_id. Dùng 422 cho dữ liệu sai, 413 khi vượt giới hạn kích thước body đã cấu hình, 429 khi vượt giới hạn tần suất và 502/503/504 cho lỗi provider theo nguyên nhân. Client hiển thị “Chưa kiểm tra được” và có nút thử lại. Thao tác bổ sung bối cảnh gửi lại nội dung cùng phần mới sau khi người dùng xác nhận.

### Kiểm tra nhất quán của two_pass — 09/11/2026

Luồng vẫn quan sát → kiểm chứng → hai nhánh song song → rà lại → kiểm chứng.
Trong bước rà lại, backend kiểm tra quan hệ giữa các trường của `FinalReviewV2`:
không cùng cặp vừa `risk_links` vừa `uncertain_relations`; không một finding vừa
benign vừa tham gia liên kết rủi ro; không liên kết đã khẳng định lại dựa trên finding
có bất định action/relation. Danh tính chưa xác minh không tự phủ nhận hành vi.

`uncertain_relations: [{request_id, support_id}]` biểu diễn từng quan hệ chưa rõ,
khác với `uncertainty_reasons` cho từng finding. Nếu có quan hệ chưa rõ phải hỏi thêm;
một quan hệ khác đủ căn cứ vẫn có thể làm mức cảnh báo high. Không có quan hệ rõ và
chỉ yêu cầu chuyển tiền chưa biết mục đích thì tiếp tục need_context.

Nếu phát hiện mâu thuẫn, gửi tối đa một yêu cầu sửa trong bước rà lại, kèm nguyên văn
đầu vào, hai nhánh tham khảo và danh sách mã lỗi. Không bỏ phiếu, không chọn mức cao
nhất, không dùng đầu ra trước làm bằng chứng. Nếu vẫn mâu thuẫn trả HTTP 502,
`code=PROVIDER_INCONSISTENT_OUTPUT`; không trả risk_status và không chuyển lỗi model
thành need_context. Lỗi mạng hoặc provider trong lần sửa cũng không được coi an toàn.
Một phân tích thường gọi model hai lần; có sửa gọi tối đa ba lần, chưa tính retry HTTP
hữu hạn. Khóa thời gian toàn lượt nếu được bật vẫn áp dụng cho cả lần sửa.

`analysis` bổ sung `consistency_repairs` (0/1) và `consistency_issues` (mã cố định,
không có văn bản/khóa bí mật), `decision_version=two-pass-3`. `schema_version=1.4`.
Nguồn chuẩn về kiểu và giới hạn là `ScamShield_AI/backend/schemas.py`.

### Bằng chứng quan hệ — bản 1.5, ngày 10/11/2026

Phần 1.4 bên trên mô tả phiên bản trước. Luồng hiện hành dùng `FinalReviewV3`
với trường bắt buộc `relation_assessments`, tối đa 50 cặp. Mỗi risk_link hoặc
uncertain_relation cần đúng một bản đánh giá tương ứng:

| Trường nội bộ | Quy định |
| --- | --- |
| request_id, support_id | ID finding hợp lệ, đúng vai/người nói và được kiểm chứng trích dẫn |
| status | supported, uncertain, not_supporting_risk |
| relation_type | payment_required_before_benefit, access_required_before_benefit, installation_required_before_benefit, other_prerequisite, ordinary_transaction, unrelated, unknown |
| relation_evidence | Tối đa 5 evidence từ text/messages, ít nhất 1 đoạn hợp lệ và chồng lên bằng chứng của một trong hai đầu; đối chiếu code point như evidence hành vi |
| assessment_note | Kết luận ngắn tối đa 400 ký tự; không xuất suy nghĩ nội bộ; không công bố như nội dung đã kiểm chứng |
| unresolved_reference | Cụm tham chiếu chưa rõ tối đa 300 ký tự, hoặc null |
| missing_information | Khoảng trống thông tin cụ thể tối đa 400 ký tự, hoặc null |

supported phải có risk_link, loại quan hệ rủi ro, không còn khoảng trống làm căn cứ
cho chính liên kết đó. uncertain phải có uncertain_relation, needs_context=true và
missing_information cụ thể. not_supporting_risk không được giữ cặp trong hai danh
sách trên. Không lấy nguồn kho, context hoặc question thay quote trong tin nhắn.

`relation_grounding.py` còn tìm tín hiệu có thể bỏ sót: đã có request và inducement
hợp lệ, cùng người nói, có cấu trúc điều kiện trong khoảng văn bản gốc liên quan
nhưng chưa nối risk_link. Tín hiệu chỉ yêu cầu rà lại, không tự nâng high. Không
ghép hai người nói, warning/denial hoặc request đã có context benign hợp lệ. Giới
hạn 12 gợi ý và vẫn tối đa một lần sửa trong bước rà cuối, không thêm vòng lặp.

Phản hồi sửa yêu cầu xét cả giữ và bác liên kết, đối chiếu tên gọi thay thế/đại từ,
giữ quote và nêu thông tin thiếu cụ thể. Không mặc định xóa link để hết mâu thuẫn.
Lần sửa vẫn không hợp lệ thì lỗi 502 như trước. Nếu output hợp lệ nhưng thực sự chưa
chốt quan hệ, có thể need_context; không coi việc quote khớp là chứng minh suy luận
ngữ nghĩa đúng. Không có cam kết rằng mọi ca bỏ sót sẽ được phát hiện.

API công khai giữ cấu trúc kết quả chính, `schema_version=1.5`,
`analysis.decision_version=two-pass-4`. Bổ sung số đếm `grounded_relation_count`
(risk_link có bằng chứng đã đối chiếu, không phải quan hệ được chứng minh đúng hoàn
toàn), `relation_review_candidates` và `unresolved_relation_candidates`. Bằng chứng
và đánh giá quan hệ chi tiết là dữ liệu nội bộ, không xuất prose chưa kiểm chứng
trực tiếp cho client. Nhãn và giới hạn thực tế lấy từ schema backend.

Bổ sung kiểm chứng phản ví dụ: assessment `not_supporting_risk` được phép nêu hai
người nói khác nhau để bác việc ghép sai; từng quote vẫn kiểm tra theo speaker thật
của tin chứa nó. Các liên kết supported/uncertain vẫn phải cùng speaker như trước.
missing_information nói về khoảng trống xác định quan hệ trong lời người gửi;
thiếu căn cứ pháp lý hoặc danh tính không tự xóa điều kiện đã nêu rõ trong tin.

Phản hồi sửa còn có `invalid_findings`: ID finding không qua kiểm chứng và mã lỗi
quote/speaker/offset cụ thể, gửi nội bộ cho model để sửa theo input gốc. Không tự
viết lại quote và không đưa các chi tiết input này vào diagnostic công khai.

### OCR ảnh — schema 1.6, 10/11/2026

POST `/api/ocr` nhận bytes PNG/JPEG/WebP (Content-Type tương ứng), tối đa 4 MB,
8 triệu pixel. Không nhận URL hoặc multipart. Body limit 65.536 byte vẫn giữ cho
`/api/analyze`; chỉ endpoint OCR có body limit riêng. Engine local Tesseract.js
vie+eng, tối đa 2 process đồng thời và 60 giây/ảnh. Không gửi ảnh tới Gemini.

Response chuẩn `OcrResponse` gồm source_id (null nếu no_text), text, status
ready/low_confidence/no_text, image_sha256, engine, confidence, width/height,
blocks với tọa độ dòng chữ, ocr_ms và notice. Confidence là điểm OCR, không phải
xác suất rủi ro. Ảnh không đọc được chữ không tự thành clear hoặc tự gọi phân tích.

`AnalyzeRequest` thêm `ocr_sources`, tối đa 4 `{message_id, source_id}`, chỉ trỏ
message có thật, không trùng. Backend đối chiếu nguồn OCR trong RAM và nội dung
message nguyên vẹn trước khi gọi provider: sửa text trả 422 OCR_TEXT_CHANGED,
nguồn giả/hết hạn trả 422 OCR_SOURCE_EXPIRED. Nguồn hiệu lực 15 phút hoặc tới restart.

Khi có OCR, `AnalyzeResponse` schema_version 1.6, thêm input_sources (kiểu lồng
OcrInputSource/OcrBlock/OcrBox) và input_warnings. Các trường này rỗng với đầu vào
cũ. Quote khớp message OCR chưa chứng minh đọc đúng ảnh; luôn có lời nhắc đối chiếu.
Nguồn ảnh tách khỏi source_matches của RAG, không tạo verified_match. Chuẩn chi tiết
là `backend/schemas.py`; hướng dẫn và kết quả tại `ScamShield_AI/README_OCR.md`.

### URL đi cùng nội dung — schema 1.8, 10/11/2026

Giữ POST `/api/analyze`. Thêm links tối đa 20 phần tử: id/message_id/url/
display_text/start/end/origin. URL tối đa 2.048 ký tự, nhãn 1.000; ID duy nhất,
message tồn tại, nhãn/offset nếu có khớp nguyên văn. origin chỉ dom_href hoặc
user_supplied, metadata do client báo, không phải xác minh pháp y DOM. URL sai
cấu trúc là dữ liệu để trả quan sát invalid; nhãn/ref sai là 422 trước provider.
Body limit phân tích vẫn 65.536 byte. Các client cũ không gửi links vẫn hoạt động.

Backend cũng trích HTTP(S)/www trong text/messages, origin text hoặc ocr. Không
tự tạo URL thứ hai từ nhãn đã gắn href; nhãn lặp không rõ vị trí không làm căn cứ
display_target_mismatch. Tối đa 20 URL được quan sát cấu trúc mỗi request. Tối đa 3
URL được kiểm tra DNS và redirect HTTP HEAD trong live; mock không gửi ra mạng.
Không đọc body/JS hoặc danh sách độc hại. PSL gồm private suffix để tách phần miền
đăng ký, không xác minh đăng ký WHOIS. Href ẩn được rút về origin trước khi truyền
model, bỏ userinfo/path/query/fragment; văn bản hiển thị/OCR vẫn nguyên để trích dẫn.

`FinalReviewV4` dùng url_uses: link_id/signal_codes/finding_refs/relation. ID/tín
hiệu phải có trong quan sát backend. Background có thể không có tín hiệu/finding;
không tăng mức từ background. supports_request_risk cần ít nhất một tín hiệu mạnh
đã có và request hợp lệ cùng message; không dùng warning/denial, benign hoặc request
bất định hành động/quan hệ để nâng mức. Tín hiệu đơn lẻ không tự tạo high hoặc
verified_match. Lượt Gemini 2 nhận URL song song kết quả hai nhánh cũ; không thêm
model thứ ba hoặc vượt tối đa một lần sửa hiện có.

Các mode đối chứng có URL dùng schema 1.8; two-pass-6 giữ 1.9: url_analysis với hostname ASCII/Unicode,
registered_domain, reference_domain, label_status, signals, status parsed/invalid,
origin và reputation_status=not_checked; url_uses chỉ chứa phần sử dụng hợp lệ.
Thêm network: status, hops (display_url origin/http_status), final_url origin,
final_hostname/final_registered_domain/final_http_status, reachable nullable,
elapsed_ms, reason mã cố định. Chỉ status=checked mới quan sát được phản hồi cuối;
reachable không có nghĩa an toàn/tài nguyên tồn tại. Timeout/blocked/error/unsupported/
deferred/redirect_limit/redirect_loop không tự đổi risk_status. Giới hạn 3 redirect,
4 HEAD, 6 giây mỗi URL; kiểm tra DNS/IP mỗi bước, không truy cập địa chỉ nội bộ.
analysis thêm discarded_url_uses/used_url_evidence; đếm cả background, không phải
số chứng cứ lừa đảo. Nguồn URL tách quote của finding và source_matches của RAG.
Không đưa URL nguồn model tự nghĩ ra vào bằng chứng. Registry chỉ hai miền tham
chiếu có tài liệu, không phải allowlist an toàn hoặc kho gov đã duyệt. Xem
`ScamShield_AI/README_URL.md` và kiểu chuẩn trong `backend/schemas.py`.

## Cập nhật 12/11/2026 — local-rules-2.1-support

Mục này thay thế mô tả Gemini/hai lượt ở các phần lịch sử phía trên. Backend hiện không gọi mô hình ngoài. API chung giữ schema 2.0 và bốn mức clear/need_context/suspicious/high.

Sau khi kiểm chứng sự kiện và áp quy tắc văn bản, cả `/api/analyze` và `/api/analyze-local` chạy song song truy xuất nguồn đã duyệt và đối chiếu URL/redirect; nhánh khẩn bỏ qua hai bước để không trì hoãn an toàn. `/api/observe` vẫn chỉ trích cấu trúc, không mở URL/truy xuất.

- URL có dấu hiệu mạnh chỉ nâng tối đa suspicious khi gắn với yêu cầu hợp lệ trong cùng đoạn và đúng message; không dùng lời phủ định/cảnh báo/giả định. Giữ high đã có căn cứ. Lỗi mạng, HTTP 404, đổi miền hoặc có URL đơn thuần không tự chứng minh lừa đảo.
- RAG truy vấn từ bằng chứng hành vi hợp lệ. Chỉ nguồn approved còn hiệu lực, được duyệt tái sử dụng và có liên hệ hành vi mới bổ trợ giải thích; background/candidate/hit lệch không đổi mức. RAG không tự tạo high hoặc verified_match. Hiện chưa có nguồn thực được duyệt.
- source_matches chỉ trả nguồn thực sự đã dùng; retrieval.official_sources ghi số hit truy xuất (có thể nhiều hơn số được dùng). evidence người dùng và quote tài liệu giữ riêng biệt.
- analysis.decision_version=`local-rules-2.1-support`; preliminary_risk là mức trước hỗ trợ. stage_timings_ms bổ sung retrieval/url/support_total, local_total chỉ là lõi văn bản. Hai nhánh chạy song song nên không cộng retrieval+url thành tổng.
- LocalResult bổ sung url_analysis, url_uses, support_indicators, official_retrieval, support_timings_ms, support_warnings. SourceSupport có relation behavior_support và event_refs; entity_verified luôn false.
- Truy xuất tối đa 3 đoạn, timeout mặc định 0,8 giây/trần 2 giây; URL HEAD tối đa 3 liên kết, 3 redirect, khoảng 6 giây/liên kết. Có cấu hình tắt RAG/mạng URL; lỗi từng nhánh giữ kết quả văn bản còn căn cứ và ghi trạng thái chưa kiểm tra.

Chi tiết: [LOCAL_SUPPORT.md](ScamShield_AI/LOCAL_SUPPORT.md). Schema backend là nguồn chuẩn. Giao diện tiếp tục ẩn answers, danh sách nguồn RAG và dữ liệu suy luận thô; chỉ hiển thị cảnh báo, trích dẫn hợp lệ và lời giải thích hướng tới người dùng.

## Bổ sung 12/11/2026 — facts-1.0-support

Trong mode local_rules, bộ quyết định mặc định chuyển sang `SCAMSHIELD_REASONER=facts`; legacy_engine chỉ chạy khi chọn `legacy` để đối chiếu. Bộ bóc tách Python và RAG/URL giữ vai trò hiện hành.

- Trước khi áp điều kiện, BE chuyển event/relation đã kiểm chứng sang FactRecord với value TRUE/FALSE/UNKNOWN, nguồn, phạm vi, phiên bản và bằng chứng. Thiếu payment_confirmed là UNKNOWN, không suy ra FALSE.
- Quy tắc đánh giá MATCHED/NOT_MATCHED/UNDETERMINED, kiểm tra người/giao dịch/quan hệ, cập nhật và ngoại lệ. Không gọi mô hình hoặc thực thi biểu thức tùy ý trong JSON.
- API chung vẫn schema 2.0 và bốn risk_status; analysis.decision_version=facts-1.0-support. stage_timings_ms bổ sung extraction/fact_build/rule_evaluation. Safety urgency vẫn độc lập.
- analysis_status hỗ trợ complete/partial/error. Partial có thể giữ high độc lập nhưng không biến thiếu bằng chứng thành clear; thất bại không có kết luận hợp lệ trả lỗi 503.
- API thô `/api/analyze-local` có fact_trace: facts, rule_evaluations, conflicts, discarded_event_ids, external_evidence và thời gian. Bằng chứng ngoài của URL/nguồn giữ riêng với span người dùng. Giao diện chính vẫn ẩn trace và answers/nguồn RAG.
- FactStore hiện là snapshot mỗi input, không phải kho lịch sử xuyên request. Cập nhật bối cảnh yêu cầu gửi lại hội thoại/bối cảnh để tính lại; fact_id phải đi cùng input_sha256/lần phân tích. Cơ chế bỏ phản hồi cũ theo phiên và phiên bản mục vẫn giữ ở client.

Hợp đồng/mapping/luật và chính sách ngoại lệ UNKNOWN: [FACT_REASONER.md](ScamShield_AI/FACT_REASONER.md). Schema máy đọc: [output.schema.json](data/v2/output.schema.json), [fact_record.schema.json](data/v2/fact_record.schema.json), [fact_rulebook.schema.json](data/v2/fact_rulebook.schema.json).

## Khôi phục theo yêu cầu tiếp theo — 12/11/2026

Phần mô tả mặc định facts phía trên đã được thay thế: cấu hình hiện hành là `SCAMSHIELD_MODE=local_rules`, `SCAMSHIELD_REASONER=legacy`. Luồng hoạt động: bóc tách Python → kiểm chứng event/relation/evidence → áp rulebook gốc → song song RAG và URL/redirect → ghép bằng chứng → phản hồi bốn mức.

`analysis.decision_version=local-rules-2.1-support`, rulebook local-rulebook-1.0. API thô không tạo fact_trace khi dùng legacy; các trường fact và partial vẫn là phần mở rộng tùy chọn để giữ tương thích bản thử nghiệm, không dùng trong quyết định mặc định. Không khôi phục Gemini hoặc prompt mô hình. Kiểm chứng khôi phục: [báo cáo](ScamShield_AI/reports/restore_event_flow_20261112/README.md).
