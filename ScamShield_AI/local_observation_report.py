"""Render existing first-stage predictions; no analysis/provider calls."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent/'reports/local_observation_20261112'
FINAL=ROOT/'final'


if __name__=='__main__':
    records=json.loads((FINAL/'predictions.json').read_text(encoding='utf-8'))
    summary=json.loads((FINAL/'summary.json').read_text(encoding='utf-8'))
    lines=['# Đầu ra 30 ca phân tích đầu tiên', '',
           'Chỉ Python rules, không Gemini/RAG/URL và không mức rủi ro cuối. Nhãn nháp phát triển, không đánh giá độc lập.', '']
    for row in records:
        result=row['response'];spans={s['id']:s for s in result['evidence']}
        lines += [f"## Ca {row['id']}", '', '```json',json.dumps(row['input'],ensure_ascii=False,indent=2),'```','',
                  '| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |',
                  '|---|---|---|---|---|---|---|']
        for e in result['events']:
            s=spans[e['verb_span']]
            lines += [f"| {e['action_id']} | {e['action_type']} | {s['quote']} ({s['message_id']}:{s['start']}–{s['end']}) | {e['polarity']} | {e['speech_role']} | {e['temporal_state']} | {e['transaction_id'] or 'chưa có mã'} |"]
        if not result['events']:lines+=['', 'Không trích được hành vi thuộc mẫu; không tự coi là an toàn.']
        lines+=['','Quan hệ:']
        lines += [f"- {r['type']}: {r['from_id']} → {r['to_id']}; {r['status']}; luật {r['rule_id']}. "+' '.join(r['limitations']) for r in result['relations']] or ['- Không có quan hệ được trích.']
        lines += ['', 'Câu hỏi bổ sung:']
        lines += ['- '+q for q in result['follow_up_questions']] or ['- Không có câu hỏi theo bộ luật hiện tại.']
        unknown=[name for name,f in result['answers_18'].items() if f['status']=='unknown']
        lines += ['', 'Trường unknown: '+', '.join(unknown)+'.', '']
    (ROOT/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    first=next(r for r in records if r['id']=='A')
    (ROOT/'example_A.json').write_text(json.dumps(first,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    table=['| Loại đầu vào | Ký tự | Số lượt | p50 (ms) | p95 (ms) | Giới hạn 50 event |','|---|---:|---:|---:|---:|---|']
    for row in summary['timings']:
        table.append(f"| {row['kind']} | {row['characters']} | {row['n']} | {row['p50_ms']:.2f} | {row['p95_ms']:.2f} | {row['limited']} |")
    (ROOT/'TIMING.md').write_text('# Độ trễ bộ phân tích cục bộ\n\nKhông provider, không browser/extension, không tải đồng thời; warm cùng process.\n\n'+'\n'.join(table)+'\n',encoding='utf-8')
    print('Rendered CASES.md, TIMING.md and example_A.json from saved final results.')
