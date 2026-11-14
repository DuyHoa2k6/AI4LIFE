"""Agent review of actual saved outputs; references remain unreviewed drafts."""
import collections
import json
from pathlib import Path
from run_reasoning_document import ROOT,dump,jsonl,rows,sha

out=ROOT/'reports/reasoning_document_20261114';data=ROOT/'fixtures/reasoning_document_20261114'
metrics=json.loads((out/'metrics.json').read_text(encoding='utf-8'));run=json.loads((out/'run_manifest.json').read_text(encoding='utf-8'))
audit={r['case_id']:r for r in rows(out/'case_audit.jsonl')};pred={r['case_id']:r['response'] for r in rows(out/'predictions.jsonl')}
traces={r['case_id']:r['response'] for r in rows(out/'debug_traces.jsonl')};inputs={r['case_id']:r['request'] for r in rows(data/'inputs.jsonl')};refs={r['case_id']:r for r in rows(data/'reference_draft.jsonl')};meta={r['case_id']:r for r in json.loads((data/'case_metadata.json').read_text(encoding='utf-8'))}

# Findings below were written after reading the saved predictions and debug traces.
# They are agent diagnoses, not independent human annotation or training labels.
notes={
'TH01':('extraction_object_error','Chỉ giữ offer_employment và avoid_verification; thiếu ký vay, khai thu nhập sai và lịch trả dù chưa có việc. Không có relation.', 'Bộ trích chưa biểu diễn đầy đủ nghĩa vụ tài chính/khai sai; vì vậy policy không có chuỗi căn cứ để match high. Câu hỏi về người mời việc và giữ giấy tờ lệch trọng tâm vay học phí.', 'Trích ký nghĩa vụ và khai sai; nối lời hứa với điều khoản trả nợ, kiểm nguồn tự nhận và câu người học đọc hợp đồng. Đối chứng khoản vay được giải thích đầy đủ.'),
'TH02':('negation_scope_error','R-DATA nhận đúng yêu cầu gửi giấy tờ. Nhưng graph thêm transfer_funds/request/positive từ “Hiện chỉ cần ảnh, chưa phải đóng tiền.”; còn biến “Tôi chưa gửi ảnh và chưa xác minh...” thành avoid_verification/request.', 'Đúng mức nhưng graph có dữ kiện sai. Phủ định “chưa phải” không được giữ ở nhánh graph; báo cáo chưa xác minh bị hiểu thành ngăn xác minh. Nhãn người phụ trách ở m1/m3 khác nhau cũng là bất định đầu vào cần lưu.', 'Loại yêu cầu thanh toán từ câu phủ định; phân biệt chưa xác minh với cấm xác minh. Giữ R-DATA có căn cứ, không tự khẳng định đánh cắp danh tính.'),
'TH03':('unsupported_input','Không trích được event hoặc relation nào; analysis_status=unsupported, risk=need_context.', 'Tầng trích chưa nhận ra mua tài sản bằng tiền của người dùng nhưng chuyển quyền sang người thứ ba, áp lực tình cảm và cản tư vấn. Đây là thiếu khả năng của parser, không phải đoạn gốc thiếu mọi hành động.', 'Mở rộng action-object-role cho mua/chuyển quyền sở hữu; nối tác động và bất lợi. Đối chứng đồng sở hữu có thỏa thuận và quyền rút lui.'),
'TH04':('extraction_object_error','Chỉ còn transfer_funds với polarity negative từ “chưa được thanh toán lương đã làm”; không có ký nhận nợ, hạn chế rời nơi ở hoặc gây áp lực gia đình.', 'Lỗi đầu tiên ở trích cấu trúc. Policy tiếp tục coi chỉ có event phủ định, không còn active event là clear. Nhánh fallback clear trong legacy_engine.py không chứng minh đã đọc đủ nội dung. Đây là bỏ sót nghiêm trọng.', 'Trích điều kiện nợ chưa xác định, giữ lương và quyền rời đi; yêu cầu coverage đủ trước clear. Đối chứng chi phí đào tạo minh bạch, cho tự do nghỉ, không ép ký.'),
'TH05':('extraction_object_error','Không có event xác nhận hoàn thành/nhận hàng trước thực tế. Có handover_asset với object “nhé”; không có relation.', 'Parser bám “giao” thay vì hành động chủ chốt “bấm xác nhận”. Mất chuỗi xác nhận → giải phóng tiền → mới giao; câu hỏi mã đơn không sửa được thiếu sót này.', 'Trích xác nhận trạng thái và quyền khiếu nại do người dùng thuật lại; tách tác giả và người thực hiện. Đối chứng hàng đã nhận rồi mới xác nhận.'),
'TH06':('speech_act_error','Có chuyển tiền, nhưng câu hỏi “Tôi có thể xem xác nhận...” thành avoid_verification/request; chỉ có một relation same_object, không có quan hệ quyền nhận/ủy quyền.', 'clause_context.py có mẫu verification_delay dùng từ chuẩn hóa “toi”; có thể nhầm “tôi” với “tối”. Bất thường người nhận và thiếu ủy quyền chưa có cấu trúc policy phù hợp; không được nâng high khi người đăng cho phép chờ.', 'Phân biệt người hỏi xác minh với người cản xác minh; nối tài khoản được đề nghị với quyền nhận chưa chứng minh. Đối chứng ủy quyền và công khai chi được cung cấp.'),
'TH07':('extraction_object_error','“hợp đồng chuyển nhượng” có anchor “đồng” gán transfer_funds; “chuyển nhượng” cũng bị gán chuyển tiền. Không có event quyền ký/chuyển tài sản hoặc relation.', 'Chuẩn hóa bỏ dấu và pattern chuyển tiền quá rộng làm “đồng/đóng” lẫn nhau. Đúng quote về mặt offset nhưng sai nghĩa; policy không thấy quyền rộng hơn mục đích cho thuê.', 'Phân giải cụm danh từ hợp đồng và hành động ủy quyền theo đối tượng; so phạm vi ký với mục đích. Đối chứng ủy quyền hẹp đúng giao dịch, đủ bản sao.'),
'TH08':('extraction_object_error','“giao thông tin đăng nhập” thành handover_asset; báo cáo/đề nghị “Tôi tự giữ tài khoản...” bị thành yêu cầu chuyển tiền cho bên còn lại. Không có relation.', 'SG-CREDENTIAL trong semantic_graph_patterns.json nhận gui/cung cap/dua/chuyen, thiếu cách nói “giao”. Quyền khôi phục và nghĩa vụ khai đúng người sử dụng chưa được nối thành cơ chế mất quyền tài khoản.', 'Trích surrender_credentials, đổi recovery owner và khai sai; không đồng nhất giao thông tin đăng nhập với tự đăng nhập. Đối chứng tự giữ mật khẩu/số khôi phục.'),
'TH09':('condition_relation_missing','Trích hai grant_control/request, rule R-ACCESS đưa suspicious; không trích quyền sử dụng token vô hạn và quan hệ nhận quà phụ thuộc cấp quyền.', 'Mức thấp hơn tham khảo vì quyền ví bị đưa vào nhóm quyền truy cập chung. Mô tả cài ứng dụng/chia sẻ quyền là mẫu chung, chưa giải thích đúng nguy cơ quyền định đoạt token.', 'Gắn grant_authority với tài sản/quy mô quyền và điều kiện nhận quà; giữ nguồn user_reported của thông báo ví, không khẳng định đã kiểm hợp đồng blockchain.'),
'TH10':('negation_scope_error','Chỉ trích chuyển tiền phủ định “chưa chuyển” và avoid_verification từ “Tôi chưa gọi được chủ nhà...”; không thấy yêu cầu “chuyển trước hôm nay” hay quyền cho thuê.', 'Cấu trúc điều kiện và phạm vi phủ định bị mất; thiếu authority/ủy quyền khiến policy không biểu diễn bất thường đúng mức suspicious. Báo chưa gọi được khác cấm gọi.', 'Phân giải yêu cầu hiện tại với mệnh đề chưa chuyển; trích bất nhất người ký và quyền thu cọc. Đối chứng đã xem phòng và xác minh người được ủy quyền.'),
'TH11':('extraction_object_error','“giao dịch” bị cắt thành handover_asset anchor “giao”, object “dịch vào”. “Tôi lỡ chuyển thừa tiền” có nhánh thành request của người bán. Thiếu event chưa nhận tiền và hoàn từ tiền sẵn có; không có relation.', 'Đa nghĩa cụm từ và sai vai lời báo xảy ra trước suy luận. Không nối chưa có khoản vào → dùng tiền sẵn có trả bên thứ ba. Câu hỏi mục đích khoản thanh toán hỏi lại dữ kiện đã nêu.', 'Trích refund/return_funds, negative receipt và third-party destination; giữ biên lai là lời người mua đưa ra, không kết luận giả. Đối chứng đã đối soát nhận khoản dư thật.'),
'TH12':('extraction_object_error','Chỉ có transfer_funds/claim từ nghĩa vụ trả thay trong hợp đồng; không có event ký bảo lãnh hay nghĩa vụ có điều kiện.', 'Schema/event inventory đang dùng chưa mô hình đầy đủ bảo lãnh và khả năng trả nợ. Câu hỏi thao tác cụ thể là thừa vì hành động ký đã có. Chưa có căn cứ ép ký nên không tự sửa bằng cách nâng high.', 'Trích ký bảo lãnh và điều kiện trả thay, quyền kiểm tra đã được cho phép; giải thích nghĩa vụ tiềm tàng. Đối chứng nghĩa vụ được hiểu rõ và hồ sơ tài chính đầy đủ.'),
'TH13':('negation_scope_error','“không cần cam kết việc làm” thành offer_employment/positive; “đồng” trong “hợp đồng” và “chưa đồng ý thì chưa đóng tiền” tạo transfer_funds/request.', 'Phủ định và từ đa nghĩa tạo yêu cầu không có thật, làm đối chứng hợp lệ bị need_context. Đây không phải thiếu dữ kiện về chuyển tiền nhận thưởng.', 'Giữ scope của không muốn/không cần/chưa đồng ý; nhận diện lời cho phép đọc trước, chưa đóng tiền. Test đối chứng có cùng khóa học/học phí/việc làm.'),
'TH14':('negation_scope_error','Mức need_context khớp, nhưng “chưa có yêu cầu chuyển tiền hay gửi mã” sinh provide_code/request/positive và một payment/request. “chưa biết mình nhận tiền...” bị hiểu là trạng thái nhận tiền phủ định.', 'Đúng mức nhưng sai căn cứ. Phạm vi phủ định không phủ hết vế phối hợp “hay”, và chưa biết X bị lẫn với X chưa xảy ra. Câu hỏi thiếu mục tiêu đọc nội dung/quyền trên giấy.', 'Giữ sự chưa biết độc lập với phủ định sự kiện, không dựng gửi mã/chuyển tiền. Hỏi mục đích nhận tiền và nội dung xác nhận/ủy quyền của giấy.'),
'TH15':('transaction_scope_error','“đồng” trong “hợp đồng” sinh transfer_funds; “Tôi đã gọi...” sinh avoid_verification/request. Không có relation tách giao dịch A/B.', 'Hai giao dịch đã được người dùng báo xác minh bị đưa vào pattern tiền chung; không có trạng thái xác minh theo từng hóa đơn để giảm bất định. “Tôi/tối” sau bỏ dấu là một nguồn nhầm cần kiểm.', 'Giữ hai transaction và xác nhận user_reported riêng; không coi có hai người nhận là đổi tài khoản. Đối chứng chỉ A được xác minh, B chưa rõ.'),
'TH16':('speech_act_error','Mức need_context khớp, nhưng sự lựa chọn “gửi giấy hay chuyển tiền” trong câu không biết bị trích transfer_funds/request/positive. Không trích hai người được thuật lại thành hai nguồn riêng.', 'Đúng mức nhưng sai căn cứ; parser không giữ alternatives/unknown cho đối tượng và nguồn lời trích. Câu hỏi “Khoản này dùng để thanh toán việc gì?” đã giả định là thanh toán.', 'Giữ đối tượng unresolved và hai nguồn được kể lại riêng; không biến lời người dùng mô tả bất định thành yêu cầu. Hỏi tin trước để xác định gửi gì và cùng hay khác việc.')}

reviews=[];lines=['# Rà từng ca — dữ liệu công khai, nhãn tham khảo draft','', 'Đây là rà soát do agent dựa trên đầu ra đã lưu và mã nguồn, chưa phải hai người rà độc lập. Không thay nhãn để khớp dự đoán. Trace `/api/analyze-local` là lượt chạy chẩn đoán riêng sau toàn bộ dự đoán API chính; 16/16 mức khớp nhau, không mặc nhận trace nội bộ từng byte giống lượt trước.','']
table=['| Ca | Tình huống | Kỳ vọng draft | API thực tế | ms |','| --- | --- | --- | --- | ---: |']
for cid,row in audit.items():
    kind,observed,cause,fix=notes[cid];r=pred[cid];trace=traces[cid];title=meta[cid]['title']
    reviews.append({'case_id':cid,'reviewer_type':'agent_not_independent_human','expected_draft':row['expected_draft'],'actual':row['predicted'],'first_error_category':kind,'first_error_stage':'extraction_or_semantic_grounding','observed_trace':observed,'cause_hypothesis':cause,'recommended_regression':fix,'fully_semantically_correct':False,'policy_contribution':'No matched rule falls back to need_context; TH04 falls back clear because all remaining events are negative.' if cid!='TH02' and cid!='TH09' else 'Matched rule produces a supported coarse risk, but the whole graph still needs review.','runtime_changed':False})
    table.append(f"| {cid} | {title} | {row['expected_draft']} | **{row['predicted']}** | {row['ms']:.2f} |")
    lines += [f'## {cid} — {title}', '',f"Kỳ vọng draft **{row['expected_draft']}**; thực tế **{row['predicted']}**, HTTP 200, {row['ms']:.2f} ms. {row['events']} event, {row['relations']} relation trong lượt debug.",'','**Đầu vào nguyên văn, đúng nhãn người nói:**','']
    lines += [f"> [{m['id']}] {m['speaker']}: {m['text']}\n" for m in inputs[cid]['messages']]
    lines += ['**API trả cho người dùng:**', '',r.get('display_summary',r.get('summary','')), '', 'Hành động đề xuất: '+r.get('display_action',''),'', 'Câu hỏi: '+json.dumps(r.get('follow_up_questions',[]),ensure_ascii=False),'', '**Quan sát trong trace:** '+observed,'','**Nguyên nhân/giới hạn:** '+cause,'','**Cách sửa tổng quát và đối chứng cần bổ sung:** '+fix,'','**Phân tích tham khảo của tài liệu, không đưa vào inference:**','',refs[cid]['reference_text'],'']
jsonl(out/'agent_review.jsonl',reviews);(out/'CASES.md').write_text('\n'.join(lines),encoding='utf-8')
relations=sum(r['relations'] for r in audit.values());lat=metrics['latency_ms'];statuses=collections.Counter(t['analysis_status'] for t in traces.values())
body=f'''# 16 tình huống suy luận — kết quả backend ngày 14/11/2026

**Chạy backend đang cấu hình: local_rules + legacy-event-rules. Không phải phép đo PhoBERT hoặc Gemini.** Không thay backend, luật, cấu hình riêng hoặc trọng số trong đợt này. Tập do người dùng cung cấp đã công khai, tổng hợp, 0 ca được hai người rà độc lập; không huấn luyện trên đáp án.

## Kết quả chính

- 16 request `/api/analyze` độc lập, **16 HTTP 200**, không lỗi giao thức. Có thêm 16 lượt `/api/analyze-local` chẩn đoán riêng; mức trùng API chính cả 16. Không trộn hai loại thời gian.
- **{metrics['level_matches']}/16 = {metrics['level_agreement']:.2%} khớp mức draft**, Macro-F1 **{metrics['macro_f1']:.4f}**. Không gọi đây là độ chính xác ngoài thực tế.
- Cả **8/8 ca kỳ vọng high bị bỏ sót**: 6 need_context, 1 suspicious, **TH04 bị clear**. Không có dự đoán high; precision high không xác định vì mẫu số 0, recall high so draft là 0/8.
- Ba ca khớp mức: TH02, TH14, TH16. Cả ba còn có dữ kiện trích sai trong trace; không được tính là ba ca đúng toàn bộ. Theo rà agent hiện tại chưa có ca nào được chấp nhận đúng đầy đủ mọi tầng; semantic_accuracy đo bằng người vẫn **chưa đo**.
- Tự động đối chiếu {metrics['evidence_checked']} lượt quote ở findings và risk_indicators: **0 lỗi quote/offset hoặc nhãn speaker của finding**. Điều này không chứng minh actor/affected, loại hành động hoặc phạm vi phủ định đúng. Nhiều quote đúng nguyên văn nhưng dùng sai nghĩa.
- Trace có {relations} relation tổng cộng, chỉ TH06 có một same_object; 15/16 không có relation. Tất cả cơ chế semantic-graph được ghi nhận đều rỗng. Trạng thái báo từ backend: {dict(statuses)}; chữ complete không chứng minh hiểu đúng toàn bộ.

## Từng ca

{chr(10).join(table)}

Toàn bộ đầu vào, nội dung API trả, câu hỏi, căn cứ quan sát, lỗi đầu tiên và đối chứng đề xuất: [CASES.md](CASES.md). Dữ liệu máy đọc: [predictions.jsonl](predictions.jsonl), [debug_traces.jsonl](debug_traces.jsonl), [diagnostic_summary.json](diagnostic_summary.json), [agent_review.jsonl](agent_review.jsonl), [metrics.json](metrics.json).

## Ma trận nhầm lẫn

Hàng = tham khảo draft, cột = thực tế:

| Tham khảo / dự đoán | high | suspicious | need_context | clear |
| --- | ---: | ---: | ---: | ---: |
'''
for label in ['high','suspicious','need_context','clear']:body+='| '+label+' | '+' | '.join(str(metrics['confusion_matrix'][label][p]) for p in ['high','suspicious','need_context','clear'])+' |\n'
body+=f'''
## Tầng gây lỗi

1. **Trích sai cụm hành động/đối tượng**: đồng trong hợp đồng → chuyển tiền; giao trong giao dịch → giao tài sản; giao thông tin đăng nhập → handover_asset; bỏ sót ký nghĩa vụ/ủy quyền/bảo lãnh. Đây là quan sát trực tiếp trong trace; pattern sau chuẩn hóa thiếu phân giải nghĩa là nguyên nhân được mã nguồn hỗ trợ.
2. **Scope phủ định và speech act**: “chưa có yêu cầu chuyển tiền hay gửi mã” thành yêu cầu gửi mã; báo “tôi chưa gọi được” hoặc hỏi xem xác nhận thành avoid_verification. Mẫu verification_delay trong clause_context.py có token chuẩn hóa “toi”, có thể nhầm “tôi” với “tối”. Không phải xung đột regex–Gemini vì Gemini không được dùng.
3. **Vai và nguồn**: có câu tự thuật được gán actor là người bên kia; metadata speaker trên finding vẫn đúng vì adapter ghép lại theo message ID. Kiểm quote và speaker vì vậy không bắt hết lỗi người thực hiện/người chịu tác động.
4. **Thiếu graph/transaction**: yêu cầu chính và quan hệ điều kiện bị bỏ, nên không có chuỗi đủ điều kiện cho high. Tách A/B và cập nhật xác minh chưa đáp ứng TH15.
5. **Policy fallback**: khi không match luật, phần lớn trả need_context vì thiếu dữ kiện trong cấu trúc của BE, dù đầu vào đã có căn cứ. TH04 nghiêm trọng hơn: parser chỉ giữ thanh toán lương phủ định, nhánh clear do không còn active event làm bỏ qua ký nợ/giữ lương/hạn chế nghỉ.

Đề xuất ưu tiên: sửa tiêu chuẩn coverage trước clear và phân biệt unsupported với thiếu dữ kiện thật; phân giải cụm danh từ, phủ định phối hợp và speech act; bổ sung kiểu ký nghĩa vụ/ủy quyền/quyền tài sản với nhãn được duyệt; sau đó mới nối graph và hiệu chỉnh policy. Không sửa bằng cách ép mọi yêu cầu tiền/quyền lên high. Chưa triển khai các sửa này trong phép đo hiện tại, nên không có con số cải thiện trước/sau.

## Hiệu năng và phạm vi

- 16 lượt tuần tự, mỗi ca một lần qua ASGI TestClient: p50 **{lat['p50']:.2f} ms**, p95 nearest-rank **{lat['p95']:.2f} ms**. Lượt đầu **{lat['first_request']:.2f} ms**; 15 lượt còn lại p50 **{lat['remaining_15_p50']:.2f} ms**. Không đo bấm gửi ở browser/extension, tải đồng thời hay cold start được kiểm soát.
- Cấu hình hiện hành có RAG và URL bật; không có URL trong 16 input, mọi url_analysis rỗng. Tất cả source_matches rỗng; knowledge_status no_approved_sources ở 13 ca, no_match ở TH03/TH04/TH12. Không đo chất lượng RAG với tài liệu thật và không có kiểm tra redirect trong tập này.
- Công tắc timeout đang là `{run['configuration']['SCAMSHIELD_DISABLE_RESPONSE_TIMEOUTS']}` theo cấu hình hiện tại, không bị đổi trong lần chạy. Không lấy việc 16 request không lỗi làm bằng chứng đã kiểm timeout hoặc provider.
- TH02 giữ nguyên hai nhãn người phụ trách như tài liệu, không khẳng định họ là hai tài khoản hay tự xác minh họ cùng người. TH16 giữ một message người dùng thuật lại hai người khác; không tách lời được kể thành tin nhắn trực tiếp giả.
- Chỉ đo backend legacy đang dùng. Checkpoint PhoBERT không được nạp, chưa chạy huấn luyện/so sánh PhoBERT ở đây. Số đo trên báo cáo ML trước không thể đem so trực tiếp với bộ mới và pipeline này.

## Lệnh chạy và dữ liệu

Chạy từ thư mục ứng dụng có backend và .venv-phobert. Đầu vào đã chuẩn bị tại [fixtures/reasoning_document_20261114](../../fixtures/reasoning_document_20261114/inputs.jsonl); expected draft lưu tách. `run` chỉ đọc inputs, lưu tất cả prediction trước debug và trước `score`. Agent đã nhìn tài liệu công khai; không gọi đây là blind đánh giá.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\\.venv-phobert\\Scripts\\python.exe tests/run_reasoning_document.py run --out reports/reasoning_document_new_run
.\\.venv-phobert\\Scripts\\python.exe tests/run_reasoning_document.py score --out reports/reasoning_document_new_run
```

Chọn thư mục mới cho mỗi lần chạy. Script từ chối ghi đè prediction đã có. `tests/inspect_reasoning_document.py` và `tests/report_reasoning_document.py` dựng lại phần chẩn đoán của đợt này từ dữ liệu đã lưu, không gọi model. Manifest lưu cấu hình cho phép công khai, hash input/mã/asset; không xuất private settings hoặc khóa.

Input SHA256: `{run['input_sha256']}`. [run_manifest.json](run_manifest.json) và [data_manifest.json](../../fixtures/reasoning_document_20261114/data_manifest.json). Không tự chuyển 16 ca thành train/gold hoặc đổi nhãn cho khớp kết quả.
'''
(out/'README.md').write_text(body,encoding='utf-8')
dump(out/'review_source_hashes.json',{p:sha(ROOT/p) for p in ['backend/local_observation/analyzer.py','backend/local_observation/segmentation.py','backend/local_reasoning/clause_context.py','backend/local_reasoning/semantic_graph.py','backend/local_reasoning/grounding.py','backend/local_reasoning/legacy_engine.py']})
print('Wrote README.md, CASES.md and agent_review.jsonl from saved actual outputs.')
