"""Build a factual handoff from saved experiments; no model calls or label tuning."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/phobert_20261114'

def read(path):return json.loads(path.read_text(encoding='utf-8'))

def main():
    val=read(OUT/'validation_report.json');api=read(OUT/'api_smoke.json');hardware=read(OUT/'hardware.json')
    smoke=read(ROOT/'artifacts/phobert/smoke_heads/manifest.json');overfit=read(ROOT/'artifacts/phobert/overfit_heads/manifest.json');step=read(ROOT/'artifacts/phobert/finetune_step/manifest.json')
    diagnostic=read(OUT/'overfit_report.json');vp=read(OUT/'validation_predictions.json');old=read(ROOT/'reports/eight_scenarios_20261113/predictions.json');new=read(OUT/'api_eight_predictions.json')
    lines=['# PhoBERT cục bộ — báo cáo thực nghiệm 14/11/2026','',
      '**Đã triển khai và chạy pipeline nghiên cứu; chưa đạt chất lượng để thay backend mặc định.** Không có suy luận Gemini/API mô hình ngoài. Chỉ bước chuẩn bị tải thư viện, checkpoint và RDRSegmenter dùng mạng.','',
      '## Máy và checkpoint','',
      f"- CPU: {hardware['windows_cim']['cpu'][0]['Name']}; {hardware['logical_cpus']} logical CPU; RAM {hardware['ram_total_bytes']/1024**3:.2f} GiB; cấu hình thí nghiệm 2 thread, batch 1, float32.",
      '- GPU Intel Iris Xe tích hợp; CUDA không có. AdapterRAM báo 1 GiB không phải VRAM CUDA dùng được. Không giả định có NVIDIA.',
      f"- Python {hardware['python']}, PyTorch {hardware['torch']}, Transformers {hardware['versions']['transformers']}. Đĩa trống lúc audit {hardware['disk']['free']/1024**3:.1f} GiB.",
      f"- Checkpoint `vinai/phobert-base`, revision `{smoke['preparation']['revision']}`; PhoBERT base 135M, MIT, giới hạn 256 token. [Model card](https://huggingface.co/vinai/phobert-base), [config](https://huggingface.co/vinai/phobert-base/raw/main/config.json), [giấy phép](https://github.com/VinAIResearch/PhoBERT/blob/master/LICENSE). Dùng bản gốc MIT, không tự chuyển sang base-v2 hoặc mô hình khác.",
      '- [preparation.json](../../artifacts/phobert/preparation.json) lưu URL, revision và SHA-256 mọi asset. Model card và LICENSE nằm cùng checkpoint. Tokenizer thực là PhobertTokenizer slow; không có offset_mapping/word_ids để dùng như fast tokenizer.','',
      '## Dữ liệu','',
      '- Canonical v2: 70/70 ca và 356 span là weak_label; manifest ghi 0 ca đủ điều kiện supervised. Không đổi chúng thành gold hoặc dùng kết quả rulebook tự chấm rulebook.',
      '- Bộ smoke: 20 ca nháp tổng hợp, 10 cặp đối chiếu (không phải tất cả chỉ đổi một biến); 7 clear, 3 need_context, 4 suspicious, 6 high. Bổ sung 10 đầu vào ở minimal_pairs_unlabelled.jsonl cho đúng năm nhóm cặp tối thiểu; tất cả task ở file này unannotated, không dùng làm negative hoặc đưa vào train. Chưa có người rà độc lập. Bộ smoke có 14 quan hệ: same_transaction 8, before 1, obstructs_verification 1, prerequisite_for 2, controls_during 1, threatens_unless 1.',
      '- Chia theo nhóm liên thông family/conversation/template/source và near-duplicate: 12 train, 4 validation, 4 test_locked. Không coi test nghiên cứu này là holdout độc lập: các mẫu do agent biên soạn và công khai trong repo. Chưa chạy đánh giá file test. Holdout cũ không được mở.',
      '- Mọi task đều có trạng thái gán nhãn; span còn có coverage từng nhãn. Chỉ action có coverage hoàn thiện; nhãn span khác partial hoặc unannotated. Null thuộc tính bị mask; role/quan hệ partial không sinh negative từ phần chưa gán nhãn.',
      '- [Hướng dẫn](../../../data/phobert/ANNOTATION_GUIDE.md), [schema](../../../data/phobert/schema.json), [phân bố](../../../data/phobert/audit.json), [hash/split](../../../data/phobert/splits/manifest.json). Log bất đồng rỗng vì chưa rà, không phải đồng thuận 100%.','',
      '## Những phép chạy đã hoàn tất','',
      '| Phép chạy | Phạm vi | Thời gian | Kết quả |',
      '| --- | --- | ---: | --- |',
      f"| Head smoke | 12 train, chọn epoch bằng 4 validation; encoder đóng băng | {smoke['total_seconds']:.2f} s | Head có học, encoder không đổi |",
      f"| Overfit chẩn đoán | 4 mẫu train; cùng mẫu để kiểm khả năng ghi nhớ | {overfit['total_seconds']:.2f} s | Action F1 resubstitution {diagnostic['metrics']['spans']['action']['f1']:.3f}; risk Macro-F1 {diagnostic['metrics']['risk']['macro_f1']:.3f} |",
      f"| Fine-tune encoder thật | 2 mẫu, 1 epoch, một bước optimizer, task span | {step['total_seconds']:.2f} s | Encoder probe thay đổi: {step['encoder_probe_changed']}; checkpoint chỉ cho stage span |",'',
      'Fine-tuning dùng checkpoint pretrained, không phải huấn luyện mô hình nền từ đầu. Bản fine-tune một bước có các head khác chưa học nên loader từ chối dùng nó làm pipeline API đầy đủ. Head smoke và overfit đều là nghiên cứu, không có checkpoint được duyệt production.',
      f"RAM working set cao nhất của bước fine-tune: {step['peak_working_set_bytes']/1024**3:.2f} GiB. Chưa chạy khóa encoder mở trong nhiều epoch trên dữ liệu đủ lớn; chưa thử class weights/AMP/multi-task chung. Các task được huấn luyện riêng tuần tự.",'',
      '## Validation: chất lượng thực tế','',
      f"Chỉ **4 ca nháp**, không phải bằng chứng khái quát. Action span: precision {val['predicted_spans']['spans']['action']['precision']:.3f}, recall {val['predicted_spans']['spans']['action']['recall']:.3f}, F1 {val['predicted_spans']['spans']['action']['f1']:.3f}. Thuộc tính action_type đúng 0/8 sự kiện gold khi tính cả lỗi trích đầu vào. Offset hợp lệ không chứng minh đúng ngữ nghĩa.",
      '', '| Phương án | Risk Macro-F1 |', '| --- | ---: |',
      f"| Rulebook hiện tại | {val['rules_baseline_metrics']['macro_f1']:.3f} |",
      f"| PhoBERT baseline phân loại bốn mức | {val['four_class_classifier']['macro_f1']:.3f} |",
      f"| PhoBERT span dự đoán + quan hệ + quy tắc | {val['predicted_spans']['risk']['macro_f1']:.3f} |",
      f"| Cấp span gold cho các head phía sau | {val['oracle_spans']['risk']['macro_f1']:.3f} |",
      f"| Bỏ quan hệ | {val['ablations']['no_relations']['risk']['macro_f1']:.3f} |",
      f"| Bỏ role | {val['ablations']['no_roles']['risk']['macro_f1']:.3f} |",'',
      'Cấp span gold còn kém hơn trong phép nhỏ này: head thuộc tính/quan hệ và quy tắc vẫn lỗi; chưa có bằng chứng cải thiện từ PhoBERT. Hai ablation bằng nhau không chứng minh các thành phần vô ích; tập quá nhỏ và quan hệ đầu ra sai/chưa tạo được khác biệt. Không sửa cấu hình theo tám ca công khai để gọi đó là kết quả độc lập.',
      '', 'Ma trận thực của pipeline (hàng gold, cột dự đoán; kết quả unsupported/error đếm riêng):', '',
      '| Gold \\ Pred | clear | need_context | suspicious | high | unsupported/error |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    matrix=val['predicted_spans']['risk']['confusion_matrix'];unscored=val['predicted_spans']['risk']['unscored_by_reference']
    for risk in ['clear','need_context','suspicious','high']:lines.append('| '+risk+' | '+' | '.join(str(matrix[risk][p]) for p in ['clear','need_context','suspicious','high'])+' | '+str(unscored.get(risk,0))+' |')
    support={risk:sum(matrix[risk].values())+unscored.get(risk,0) for risk in matrix}
    lines+=['',f'Hỗ trợ theo nhãn tham chiếu: {support}. Nhãn có hỗ trợ 0 chưa đo được recall; số 0 trong JSON dùng quy ước zero_division=0, không phải chứng minh không bỏ sót. Macro-F1 báo trên danh sách bốn nhãn cố định, không phải accuracy hoặc xác suất đúng ngoài thực tế.']
    lines += ['', 'Precision/recall/F1 từng nhãn span/quan hệ/rủi ro, đúng từng thuộc tính, role, hướng cạnh, no_relation và trạng thái xử lý nằm trong [validation_report.json](validation_report.json). Nhãn không có annotation hoàn thiện ghi not_measured; số hỗ trợ bằng 0 không phải bằng chứng chất lượng.',
      '', '## Độ trễ và tài nguyên','',
      f"- Inference trực tiếp, n=4: p50 {val['timings']['p50_ms']:.2f} ms, p95 nearest-rank {val['timings']['p95_nearest_rank_ms']:.2f} ms; nạp model trong process {val['timings']['cold_model_load_ms']:.2f} ms; RSS quan sát {val['timings']['rss_bytes']/1024**2:.1f} MiB.",
      f"- Toàn route ASGI /api/analyze, n=8: p50 {api['p50_api_ms']:.2f} ms, p95 nearest-rank {api['p95_nearest_rank_api_ms']:.2f} ms; startup process + lifespan {api['startup_cold_ms']:.2f} ms. Chưa đo từ lúc bấm ở browser/extension, tải dài, disk cold hoặc nhiều mức tải.",
      f"- Đồng thời 3 request vào Runtime một slot, không hàng đợi ẩn: {val['timings']['concurrency_3']}. Hai lượt bận bị từ chối, không biến thành clear/need_context. Public API ánh xạ trạng thái bận sang 503 PHOBERT_BUSY.",
      '- RDRSegmenter hiện khởi chạy Java theo request, góp phần lớn thời gian tiền xử lý; chưa triển khai segmenter persistent. Chi tiết preprocessing/inference/verification_reasoning/total từng ca ở predictions JSON. Không hứa thời gian trên nội dung khác.',
      '', '## Tám ca công khai trước đó — chỉ hồi quy','',
      '| Ca | Backend luật trước | PhoBERT thử nghiệm | Nhận xét rà |', '| --- | --- | --- | --- |']
    notes={'01':'Sai cơ chế: giải thích chung về quyền/giấy tờ/tài chính, chưa nhận đúng giả người quen.',
      '02':'Chưa nhận điều kiện nộp thêm để rút; cơ chế giải thích lệch.',
      '03':'False-clear nghiêm trọng: nội dung có yêu cầu mã đăng nhập.',
      '04':'Chưa giải thích đúng việc trung gian tiền và khai sai nguồn.',
      '05':'503: không đủ đầu ra có cấu trúc để quyết định; không đổi thành need_context.',
      '06':'Chỉ cảnh báo chung, chưa nối đúng điều khiển từ xa với ngân hàng.',
      '07':'High nhưng giải thích sai cơ chế sang giao mã đăng nhập; không tính là đúng chỉ vì trùng mức.',
      '08':'Có đầu ra high theo cơ chế giữ giấy tờ/khả năng trở về; cần người rà kiểm tra toàn bộ evidence.'}
    for before,after in zip(old['cases'],new):lines.append(f"| {after['id']} | {before['response']['risk_status']} | {after['response'].get('risk_status','HTTP '+str(after['http_status']))} | {notes[after['id']]} |")
    lines += ['', '[api_eight_predictions.json](api_eight_predictions.json) giữ response và ms từng ca; [api_smoke.json](api_smoke.json) ghi kiểm tra nạp một lần, 422 đầu vào sai, 503 thiếu checkpoint và chặn mô hình chưa duyệt. Các lỗi trên là lý do không bật PhoBERT làm mặc định.',
      '', '## Ví dụ chuỗi và bằng chứng','',
      'Xem [overfit_predictions.json](overfit_predictions.json): đầu vào, span có quote/offset, sáu thuộc tính từng sự kiện, vai, cạnh, rule_id, cơ chế, giới hạn và quyết định đều từ lần chạy thật trên bốn mẫu đã học. Đây là ví dụ resubstitution, không phải ca mới độc lập. Một quote chỉ xác nhận vị trí chữ; không xác nhận action_type/role mô hình suy ra là đúng.',
      '', '## Tích hợp và nghiệm thu','',
      '- `SCAMSHIELD_REASONER=phobert` chọn pipeline riêng; mặc định legacy giữ nguyên. Runtime nạp một lần qua lifespan và cache, chỉ local_files_only; xác minh hash asset, heads, preprocessing và label mapping. Không có fallback sang Gemini, mock hoặc quy tắc trích cũ.',
      '- Backend đọc sự kiện/quan hệ đã kiểm tra để quyết định; classifier bốn mức chỉ dùng đối chứng và ghi bất đồng. Không có bitmask hoặc cộng điểm trùng bằng chứng.',
      '- 18 trường dùng kiểu hiện có, tổng hợp những dữ kiện có căn cứ, còn lại unknown. Các trường quan hệ/phạm vi lỗi bị loại trước quyết định. Quote, ID, speaker và transaction kiểm riêng. Không suy từ high thành phạm tội.',
      '- RAG/URL tiếp tục nhánh enrich hiện có sau mô hình. Chế độ chạy offline mẫu tắt HTTP HEAD; không thêm nguồn chính thống chưa duyệt. Nội dung OCR vẫn phải qua cơ chế xác nhận cũ.',
      '- Chưa hỗ trợ context_facts/bổ sung bối cảnh trong pipeline ML nháp: trả unsupported/503, không âm thầm bỏ qua hoặc hỏi người dùng điều đã có. Không thay khả năng này của reasoner mặc định.',
      '- Đã chạy toàn bộ pytest backend và kiểm Node popup/worker/OCR; log chính xác tại final_tests.log và commands.json. Có thêm kiểm chặn checkpoint chỉ học stage span, speaker metadata nhiều người và RDR emoji/xuống dòng.',
      '', '## Phần chưa hoàn thành để dùng thực tế','',
      'Chưa có gold độc lập hoặc đo test độc lập; chưa được hai người rà bất kỳ ca mới nào; chưa huấn luyện đủ span entity/object/condition/benefit/consequence, vai đối tượng nhắc gián tiếp và đồng tham chiếu; chưa nghiệm thu nhiều giao dịch/hội thoại dài bằng mô hình học; chưa có resolver quan hệ xa cửa sổ; chưa hiệu chuẩn điểm; chưa huấn luyện encoder đầy đủ qua các stage trên dữ liệu đủ; chưa có kiểm chứng giải thích ngữ nghĩa quy mô lớn, cân bằng lớp hoặc multi-task. Full fine-tuning path đã chạy một bước thật, không được gọi đó là mô hình hoàn chỉnh.',
      '', 'Mã, cấu hình và lệnh tái lập: [README_PHOBERT.md](../../README_PHOBERT.md).']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'MANUAL_REVIEW.md').write_text('# Rà tám ca công khai\n\nĐây là rà bởi agent, chưa có người rà độc lập.\n\n'+'\n'.join(f"- {k}: {v}" for k,v in notes.items())+'\n',encoding='utf-8')

if __name__=='__main__':main()
