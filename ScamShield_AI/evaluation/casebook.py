"""Readable before/after facts from immutable predictions, not invented examples."""
import argparse,json
from pathlib import Path
from .io import load

def read_predictions(path):return {x['case_id']:x['prediction'] for x in [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--cases',type=Path,required=True);args=p.parse_args()
    rows={r.case_id:r for r in load(args.cases)};runs={}
    for folder in ['baseline','candidate_01']:
        runs[folder]={'e2e':read_predictions(args.root/folder/'predictions.jsonl'),'oracle':read_predictions(args.root/folder/'oracle_predictions.jsonl')}
    lines=['# Năm ca chẩn đoán: dữ kiện trước/sau','',
      'Tham chiếu là draft; nhận xét ở đây do agent chuẩn bị, chưa có người rà độc lập. Không sửa label hoặc huấn luyện theo các kết quả này. Oracle dùng annotation chuẩn bị sẵn, không là output sản phẩm.']
    for cid in ['N01','N04','N08','N20','N29']:
        row=rows[cid];e=row.expected;lines += ['',f'## {cid} — {row.domain}', '', ' | '.join(['Tham chiếu draft',e.risk_status]),'']
        for m in row.input.messages:lines.append(f'> {m.speaker_id or "chưa rõ người nói"}: {m.text}')
        lines+=['','| Chế độ | Trước | Sau |','| --- | --- | --- |']
        for mode in ['e2e','oracle']:
            a=runs['baseline'][mode][cid]['assessment'].get('risk_status');b=runs['candidate_01'][mode][cid]['assessment'].get('risk_status')
            lines.append(f'| {mode} | {a} | {b} |')
        lines += ['','Dữ kiện tham chiếu:']
        by_id={s.id:s for s in e.spans}
        for event in e.events:
            s=by_id[event.anchor_id];v=event.attributes
            lines.append(f'- “{s.quote}” → action={v["action_type"]}, object={v["object_type"]}, speech={v["speech_act"]}, polarity={v["polarity"]}, scope={event.transaction_id}.')
        for folder in ['baseline','candidate_01']:
            pred=runs[folder]['e2e'][cid];spans={s['id']:s for s in pred['graph']['spans']}
            lines+=['',folder+' — dữ kiện do model thực sự trả:']
            for event in pred['graph']['events'][:6]:
                s=spans[event['anchor_id']];v=event['attributes']
                lines.append(f'- “{s["quote"]}” → action={v["action_type"]}, object={v["object_type"]}, speech={v["speech_act"]}, polarity={v["polarity"]}; roles={event.get("roles",{})}.')
            if not pred['graph']['events']:lines.append('- Không còn sự kiện hợp lệ để kết luận.')
            lines.append('- Giải thích: '+pred['assessment'].get('summary','Chưa có giải thích.'))
        missing_labels=sorted({event.attributes['action_type'] for event in e.events if event.attributes['action_type'] not in __import__('ml.phobert.schema',fromlist=['ATTRS']).ATTRS['action_type']})
        lines += ['',f'Label chưa có trong head checkpoint: {missing_labels}. Nếu oracle tốt hơn E2E, đây là dấu hiệu lỗi trích/biểu diễn, không chứng minh đã sửa model. Quote khớp chỉ là kiểm chứng vị trí, không xác nhận mọi thuộc tính suy ra đúng nghĩa.']
    (args.root/'CASE_REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
