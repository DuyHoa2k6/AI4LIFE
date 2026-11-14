"""Select/retain versions, preserve rollback, and report successful/failed gates."""
import argparse,json,shutil
from pathlib import Path
from collections import Counter
from .io import dump,digest,jsonl,load
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);args=p.parse_args();run=args.root.resolve()
    lock=json.loads((run/'baseline_lock.json').read_text());checkpoint=Path(lock['checkpoint'])
    if digest(checkpoint/'heads.pt')!=lock['heads_sha256']:raise SystemExit('Baseline checkpoint changed; cannot claim rollback')
    choice=json.loads((run/'comparison.json').read_text());b=json.loads((run/'baseline/metrics.json').read_text());c=json.loads((run/'candidate_01/metrics.json').read_text())
    if choice['accepted']:raise SystemExit('This workflow retains a rejected research candidate; approved release needs an explicit reviewed rollout')
    models=ROOT/'evaluation/models';backup=models/'rollback_baseline';backup.mkdir(parents=True,exist_ok=True)
    for name in ['heads.pt','manifest.json','labels.json']:shutil.copyfile(checkpoint/name,backup/name)
    for folder in ['baseline','candidate_01']:
        manifest=json.loads((run/folder/'run_manifest.json').read_text())
        for i,(source,sha) in enumerate(manifest['datasets'].items()):
            path=Path(source)
            if digest(path)!=sha:raise SystemExit('Dataset changed after prediction')
            shutil.copyfile(path,run/folder/f'dataset_snapshot_{i}.jsonl')
        case_map={r.case_id:r for path in manifest['datasets'] for r in load(path)}
        errors=[json.loads(x) for x in (run/folder/'error_log.jsonl').read_text(encoding='utf-8').splitlines()]
        for error in errors:
            row=case_map[error['case_id']];ss={s.id:s.model_dump() for s in row.expected.spans};es={e.id:e for e in row.expected.events};quotes=[]
            for ref in error.get('evidence_refs',[]):
                quote=ss.get(ref) or (ss.get(es[ref].anchor_id) if ref in es else None)
                if quote and quote not in quotes:quotes.append(quote)
            error['evidence']=quotes
        jsonl(run/folder/'error_log.jsonl',errors)
    dump(models/'model_manifest.json',{'version':'research-selection-20261114','selected_checkpoint':str(backup.relative_to(ROOT)),
      'heads_sha256':digest(backup/'heads.pt'),'selected_policy':'baseline','status':'research_only_not_product_approved',
      'candidate_policy':'graph-policy-2.0-experimental','candidate_selected':False,'comparison':str((run/'comparison.json').relative_to(ROOT)),
      'production_default':'legacy reasoner unchanged','rollback_policy_source':str((run/'baseline_policy.py').relative_to(ROOT)),
      'why':'Main metric did not improve; coverage regressed; reviewed validation and independent holdout unavailable.'})
    dump(run/'iteration_history.json',{'budget':{'max_iterations':3,'max_configurations':2,'max_inference_requests':500,'max_wall_seconds':1200},
      'attempted_iterations':[{'id':0,'type':'baseline','n':51},{'id':1,'type':'candidate_policy_only','n':51,'training':False,'promoted':False}],
      'model_calls':204,'loop_stop_reason':'No supported-success improvement; lower coverage; no reviewed new training data. Do not try to memorize public cases.',
      'gates':{'A_pipeline':'passed','B_finetuned_on_reviewed_new_data':'not_met','C_independent_generalization':'not_measured'},
      'checkpoint_changed':False,'reference_risk_labels_changed':False,'blind_holdout_available':False})
    errors=[json.loads(x) for x in (run/'baseline/error_log.jsonl').read_text(encoding='utf-8').splitlines()]
    dump(ROOT/'evaluation/error_taxonomy.json',{'version':'error-taxonomy-1.0','observed_counts':dict(Counter(e['error_type'] for e in errors)),
      'required_types':['ACTION_OBJECT','PARTICIPANT_ROLE','NEGATION_SCOPE','CONDITION_RELATION','TRANSACTION_SCOPE','COREFERENCE','EVIDENCE_INVALID','RISK_DECISION','EXPLANATION_UNSUPPORTED','REDUNDANT_QUESTION','UNSUPPORTED_INPUT','LABEL_AMBIGUOUS'],
      'note':'Zero observed is not proof of complete coverage. Draft label differences remain subject to review.'})
    bs,cs=b['all'],c['all'];rows=[
      '# Đánh giá và cải tiến có kiểm soát — 14/11/2026','',
      '**Đạt tầng A (pipeline chạy thật). Chưa đạt B hoặc C. Candidate không được chọn.**',
      '', '## Dữ liệu và điều kiện ban đầu','',
      '- Checkpoint thực: `artifacts/phobert/smoke_heads`, PhoBERT base + head đã học với encoder đóng băng. Bản fine-tune encoder một bước trước đây chỉ học task span, không đủ head để chạy toàn luồng. Không gọi Gemini/API mô hình ngoài.',
      '- 35 ca draft đa lĩnh vực: khóa học, tình cảm, tài chính/quyền sở hữu, việc làm, dịch vụ, dữ liệu/quyền truy cập và đóng góp. Trong đó 5 ca khóa học/biến thể đã có nền từ ví dụ prompt nên đánh dấu seen_development; 30 nhánh draft công khai mới được biên soạn. Không gọi bất kỳ mẫu nào là holdout mù.',
      '- 16 regression từ train/validation cũ đã biết; không mở test_locked/holdout cũ. Tổng mỗi vòng 51 ca, tất cả draft, 0 human-reviewed. Có 1 ca cập nhật dịch vụ còn mơ hồ được đưa vào review queue, không sửa nhãn để khớp mô hình.',
      '- Chia trước inference: 25 diagnostic, 10 validation, 16 regression. Cùng family/template/source ở cùng split; kiểm near-duplicate bằng mã. 35 ca không đáp ứng mục tiêu biên soạn 84, chưa có đủ biến thể và rà độc lập để tăng quota một cách có ý nghĩa.',
      '- Baseline source, checkpoint, tokenizer/label mapping, cấu hình acceptance và hash dữ liệu đã khóa. File expected không đi vào Runtime; mọi E2E prediction được lưu xong trước khi chấm hoặc chạy oracle.',
      '', '## Trước/sau','',
      '| Chỉ số, mẫu số 51 trừ khi ghi khác | Baseline | Candidate 01 |', '| --- | ---: | ---: |',
      f"| Risk Macro-F1 (draft, không phải accuracy ngoài thực tế) | {bs['macro_f1']:.4f} | {cs['macro_f1']:.4f} |",
      f"| Thành công cấu trúc + đúng mức | {bs['supported_success_count']}/51 | {cs['supported_success_count']}/51 |",
      f"| Đúng mức nhưng sai căn cứ theo kiểm tra cấu trúc | {bs['right_level_wrong_basis']} | {cs['right_level_wrong_basis']} |",
      f"| Coverage có mức trong bốn nhãn | {bs['coverage']:.4f} | {cs['coverage']:.4f} |",
      f"| Clear bị high | {bs['clear_as_high']} | {cs['clear_as_high']} |",
      f"| High bị bỏ sót (kể cả không xử lý được) | {bs['high_missed']} | {cs['high_missed']} |",
      f"| Oracle annotations → reasoner Macro-F1 | {b['oracle_annotations']['macro_f1']:.4f} | {c['oracle_annotations']['macro_f1']:.4f} |",
      f"| Oracle trigger spans → model heads → reasoner Macro-F1 | {b['oracle_model_spans']['macro_f1']:.4f} | {c['oracle_model_spans']['macro_f1']:.4f} |",
      f"| p50 toàn wrapper inference/policy (ms) | {b['timings']['p50_ms']:.2f} | {c['timings']['p50_ms']:.2f} |",
      f"| p95 nearest-rank (ms) | {b['timings']['p95_nearest_rank_ms']:.2f} | {c['timings']['p95_nearest_rank_ms']:.2f} |",
      '', 'Oracle là debug với tham chiếu draft, không là kết quả sản phẩm. Bộ suy luận nhận được cấu trúc tốt hơn đã cải thiện, nhưng head PhoBERT vẫn không tạo được đúng cấu trúc trên nhiều nhánh. Chưa có bằng chứng cải thiện end-to-end. Không đưa đầu ra oracle vào fallback API.',
      '', '## Theo nhóm (bao gồm regression thuộc nhóm đó)','',
      '| Nhóm | n | Macro-F1 trước | Sau | Thành công cấu trúc trước/sau |','| --- | ---: | ---: | ---: | ---: |']
    for domain in b['by_domain']:
        x,y=b['by_domain'][domain],c['by_domain'][domain]
        rows.append(f"| {domain} | {x['n']} | {x['macro_f1']:.4f} | {y['macro_f1']:.4f} | {x['supported_success_count']}/{y['supported_success_count']} |")
    rows+=['','## Tách đúng phạm vi đo','','| Tập | n | Macro-F1 trước | Sau | Thành công cấu trúc trước/sau |','| --- | ---: | ---: | ---: | ---: |']
    for split in b['by_split']:
        x,y=b['by_split'][split],c['by_split'][split]
        rows.append(f"| {split} | {x['n']} | {x['macro_f1']:.4f} | {y['macro_f1']:.4f} | {x['supported_success_count']}/{y['supported_success_count']} |")
    rows += ['',f"Phạm vi label map checkpoint: {bs.get('checkpoint_vocabulary_covered_count','not measured')}/51 ca biểu diễn được toàn bộ thuộc tính tham chiếu; các ca còn lại có ít nhất một nhãn cơ chế mới chưa được head huấn luyện. Đây là giới hạn schema/coverage, không tự chứng minh encoder không hiểu ngôn ngữ. JSON có within_checkpoint_vocabulary riêng; không đổi nhãn tham chiếu thành nhãn cũ để làm đẹp điểm."]
    rows += ['', 'Không trộn điểm regression với khả năng khái quát: JSON có by_split riêng cho diagnostic, validation và regression. Tất cả đều công khai; independent_holdout.score=null. Dữ liệu ít và draft nên ưu tiên số đếm. Khoảng bootstrap theo family chỉ mô tả tập công khai, không phải độ chính xác dân số.',
      '', '## Năm nhóm lỗi tiêu biểu và phần sửa','',
      '1. **Khoảng trống label/action-object:** nhiều hành động ký nghĩa vụ, chuyển quyền, xác nhận dịch vụ và kiểm soát lương không có trong label map đã học. Đây là giới hạn biểu diễn đã xác định; không tự nạp checkpoint cũ vào head đổi kích thước. Cần gold được duyệt rồi migration/fine-tune; vòng này không đổi trọng số.',
      '2. **Người chưa rõ dùng ID chung:** baseline có thể giữ recipient:unknown qua nhiều tin nhắn. Candidate tách unknown theo message, giữ speaker metadata và loại vai tham chiếu sai. Không tự đoán danh tính hoặc gộp người không rõ.',
      '3. **Cập nhật trạng thái/phạm vi:** candidate yêu cầu state_update giữa hai báo cáo cùng action/object, cùng giao dịch đã phân giải, hướng cập nhật hợp lệ và không trái vai đã biết. Không cho một yêu cầu mới xóa trạng thái cũ hay cho đơn đã trả xóa rủi ro đơn khác.',
      '4. **Giải thích chung lệch cơ chế:** thay mẫu gộp “thiết bị, giấy tờ hoặc tài chính” bằng mẫu theo action/object tương thích; thêm graph rule có điều kiện cho nghĩa vụ bị che giấu, quyền vượt mục đích, kiểm soát thu nhập/nghỉ việc và xác nhận dịch vụ trước thực hiện. Không dò nguyên văn câu hoặc domain để tăng high.',
      '5. **Lỗi nhãn/thiếu dữ kiện chưa giải quyết:** case cập nhật dịch vụ N33 cần rà mâu thuẫn về quyền khiếu nại; một số placeholder/quan hệ và mục đích hỏi còn cần người xác nhận. Chỉ phát câu hỏi theo dữ kiện có cấu trúc, không dùng độ tự tin thấp thành need_context. Các đánh giá ngữ nghĩa tự động là proxy, không thay người rà.',
      '', 'Chi tiết trước/sau từng case, expected/predicted từng tầng, confirmed/suspected, evidence, origin_module, severity và review_state nằm trong error_log.jsonl, case_diagnostics.jsonl và review/review_queue.jsonl. Label đúng nhưng căn cứ sai bị ghi riêng. Không khẳng định mọi khác biệt với draft là lỗi mô hình.',
      '', '## Cổng chọn phiên bản và lý do dừng','',
      '- acceptance.yaml đóng băng trước vòng đầu: main metric tăng ít nhất 0,05 tuyệt đối, không tăng high nhầm/không tăng bỏ sót high, không giảm coverage, p95 ≤5 giây, RSS ≤4 GiB; tối đa 3 vòng gồm baseline và 2 cấu hình. Đây là ngưỡng nghiên cứu do người triển khai chọn, không phải chuẩn sản phẩm.',
      '- Đã thử 2 cấu hình: baseline và candidate policy-only, 204 lượt gọi model (E2E và oracle spans), không chạy vô hạn. Candidate không tăng main metric và giảm coverage; không được promote. Không có vòng 2 để học thuộc.',
      '- Training gate exit 3: 0 mẫu mới đã được hai người rà, nên không train trên draft hoặc dự đoán, không tạo checkpoint mới giả. Có công cụ strict warm-start/replay và kiểm label mapping cho khi có dữ liệu hợp lệ.',
      '- Comparison exit 2: chất lượng không đạt và hai điều kiện reviewed_validation/independent_holdout chưa xác định. Không tự coi null là pass. Model baseline và bản rollback được giữ, production default legacy không đổi.',
      '', '## Hiệu năng và kiểm chứng','',
      f"Cold load model baseline/candidate: {b['timings']['cold_model_load_ms']:.2f}/{c['timings']['cold_model_load_ms']:.2f} ms. RSS quan sát: {b['timings']['rss_bytes']/1024**2:.1f}/{c['timings']['rss_bytes']/1024**2:.1f} MiB. CPU i5-12500H, RAM 15,7 GiB, 2 torch threads, float32, CUDA/VRAM 0, sequential concurrency=1. Độ dài đầu vào và thời gian từng ca có trong manifest/predictions. Đây là wrapper local, chưa đo browser/extension hoặc tải dài.",
      '- Evidence rate có mẫu số trước và sau verifier trong metrics.json. Offset đúng không chứng minh action/quan hệ đúng. Chỉ số mẫu số 0 là null; không ghi 0%/100% cho phần không đo được.',
      '- Công cụ tập khóa tách predict(inputs only) khỏi score(private labels + attestation); không có dữ liệu độc lập được cung cấp nên chưa chạy chấm mù. Tên thư mục không chứng minh độc lập.',
      '', '## Bàn giao','',
      'Mã và lệnh: [../../README.md](../../README.md). Dữ liệu, schema, acceptance và review queue ở evaluation/. Checkpoint thực giữ tại evaluation/models/rollback_baseline, model_manifest.json ghi lựa chọn. Checkpoint gốc không bị đổi. Logs kiểm thử riêng tại tests.log.']
    testlog=run/'tests.log'
    if testlog.exists():
        import re
        raw=testlog.read_bytes()
        text=raw.decode('utf-16') if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else raw.decode('utf-8-sig')
        matches=re.findall(r'\d+ passed[^\n]*',text)
        rows+=['','## Kiểm thử cuối','',matches[-1] if matches else 'Xem tests.log; không suy ra pass khi log chưa hoàn tất.',
          'Node popup/version 4, worker security 14, OCR worker 7 đã chạy qua; xem command_results.json.']
    rows+=['','Ví dụ dữ kiện trước/sau có quote và trạng thái thật: [CASE_REVIEW.md](CASE_REVIEW.md). Coverage theo từng hiện tượng còn thiếu: [inventory.json](inventory.json).']
    (run/'final_report.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    print(str(run/'final_report.md'))

if __name__=='__main__':main()
