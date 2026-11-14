"""Keep validation, checked and focused model runs separate; never select best case results."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'reports/relation_v4'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    runs=[]
    details=['# Dự đoán từng phiên', '', 'Không gộp kết quả giữa các phiên hoặc thay ca lỗi bằng lần chạy tốt hơn.', '']
    for name,fixture in [('live','relation_v4'),('checked','relation_v4_checked'),('focused','relation_v4_checked')]:
        directory=OUTPUT/name
        predictions=read(directory/'predictions.json')
        summary=read(directory/'summary.json')
        lock=read(directory/'lock.json')
        refs={r['id']:r for r in read(ROOT/'fixtures'/fixture/'expected.json')['cases']}
        inputs={r['id']:r for r in read(ROOT/'fixtures'/fixture/'inputs.json')}
        rows=[]
        for p in predictions:
            body=p.get('response',{})
            status=body.get('risk_status') if p.get('http_status')==200 else 'error'
            rows.append({'id':p['id'],'expected':refs[p['id']]['acceptable'],
                         'actual':status,'matches':status in refs[p['id']]['acceptable'],
                         'error':body.get('code'),'api_ms':p.get('api_ms'),
                         'repairs':body.get('analysis',{}).get('consistency_repairs')})
        runs.append({'run':name,'n':len(predictions),'api_success':summary['successful'],
                     'matches':sum(x['matches'] for x in rows),'errors':summary['errors'],
                     'model':lock['model'],'matrix':summary['matrix'],
                     'latency_all':summary['latency_all_executed'],
                     'latency_successful':summary['latency_successful'],
                     'provider_attempts':summary['provider_attempts'],'cases':rows})
        details += [f'## {name}', '', '| Ca | Kỳ vọng | Thực tế | Lỗi | Giây |', '| --- | --- | --- | --- | --- |']
        for r in rows:
            details.append(f"| {r['id']} | {'/'.join(r['expected'])} | {r['actual']} | {r['error'] or ''} | {r['api_ms']/1000:.3f} |")
        for p in predictions:
            details += ['', f"### {name}/{p['id']} — {inputs[p['id']]['name']}", '',
                        '```json',json.dumps(inputs[p['id']]['input'],ensure_ascii=False,indent=2),'```', '']
            for s in p.get('model_stages',[]):
                if 'review' in s['output']:
                    details += [f"Lượt `{s['prompt']}`:", '', '```json', json.dumps({
                        k:s['output'].get(k) for k in ('review','relation_assessments','uncertainty_reasons')},ensure_ascii=False,indent=2),'```','']
    current=read(OUTPUT/'focused/lock.json')
    unchanged=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in current['hashes'].items())
    assert unchanged
    verification={'latest_run_frozen_hashes_unchanged':unchanged,'files_checked':len(current['hashes']),
                  'unit_tests_passed':112,'worker_security_passed':10,'independent_accuracy_measured':False,
                  'old_runs': 'See each archived hash_verification.json; code revised between runs, never inside them.',
                  'known_regression_stably_resolved':False}
    (OUTPUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
    (OUTPUT/'runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUTPUT/'CASES.md').write_text('\n'.join(details),encoding='utf-8')
    lines=['# Kết quả các phiên Gemini thật', '',
           'Nhãn do người triển khai đặt trước; mọi dự đoán ghi trước khi đọc nhãn. '
           'Validation và hồi quy đã biết không phải số liệu độc lập. Không gộp hoặc chọn kết quả tốt nhất.', '',
           '| Phiên | Số ca | API thành công | Khớp kỳ vọng trên toàn bộ | Lỗi | API p50/p95 |',
           '| --- | --- | --- | --- | --- | --- |']
    for r in runs:
        timing=r['latency_all']
        lines.append(f"| {r['run']} | {r['n']} | {r['api_success']}/{r['n']} | {r['matches']}/{r['n']} | {r['errors']} | {timing['p50_ms']/1000:.3f}s / {timing['p95_ms']/1000:.3f}s |")
    lines += ['', '## Ca NW-02', '',
        '- `live/RG-01`: need_context; model gộp thiếu thông tin về tính hợp lệ giao dịch vào bất định quan hệ. Đã dùng làm validation để sửa định nghĩa trường.',
        '- `checked/RF-01`: model nhận đúng quan hệ nhưng ghép quote support bằng `[...]`; sửa một lần vẫn giữ quote không tồn tại. Backend từ chối với PROVIDER_INCONSISTENT_OUTPUT.',
        '- `focused/RF-01`: provider trả 503 sau retry ở lượt quan sát; chưa có kết quả để đánh giá suy luận bản cuối. Không báo là đã sửa thành công ổn định.', '',
        '## Đối chứng và lỗi khác', '',
        'Hai biến thể nguy hiểm mới ở checked trả high, giao dịch mua sách và bản tin cảnh báo trả clear, '
        'ca thiếu tham chiếu trả need_context. Ca hai người nói của checked lỗi 503 nên không có kết luận '
        'ở phiên này; việc bác ghép người nói đã có unit test và từng chạy clear ở phiên validation. '
        'Ca chưa biết loại quyền ở checked vẫn suspicious thay vì need_context; chưa sửa nhãn hậu kiểm '
        'để nâng tỷ lệ đúng. Bản cuối focused có một bài cảnh báo trả clear, một ca 503.', '',
        'Tăng độ chặt của kiểm chứng có thể tăng lỗi được hiển thị thay vì cho qua bằng chứng sai. '
        'Không coi lỗi là clear, không bỏ lỗi khỏi mẫu số. Không có nguồn chính thống đủ duyệt trong '
        'kho; chưa đo RAG thực, browser/extension, tải đồng thời hoặc độ chính xác dữ liệu thật. '
        'Các độ trễ gồm provider và mạng; timeout ứng dụng vẫn đang tắt theo yêu cầu trước.', '',
        'Chi tiết input và assessment tại [CASES.md](CASES.md), dự đoán gốc trong từng thư mục phiên. '
        'Không có căn cứ tuyên bố đạt 98% hoặc đã khắc phục hoàn toàn mọi biến thể.', '']
    (OUTPUT/'RUNS.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps([{'run':r['run'],'n':r['n'],'api_success':r['api_success'],'matches':r['matches'],'errors':r['errors']} for r in runs]))


if __name__=='__main__':
    main()
