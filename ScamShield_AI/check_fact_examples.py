"""Supplementary before/after development examples, not independent evaluation."""
import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.schema import CaseInput


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    texts=[('handover_missing','Anh giao máy cho tài xế nhé.'),
           ('handover_unpaid','Chưa thấy tiền về, nhưng cứ giao máy trước.'),
           ('handover_paid','Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy nhé.'),
           ('handover_denied','Nếu chưa nhận tiền thì đừng giao máy.'),
           ('screen_only','Chia sẻ màn hình để duyệt hoàn cọc nhé.'),
           ('code_ambiguous','Đọc sáu số vừa hiện để nhận tiền.'),
           ('credential','Gửi mã OTP cho tôi.')]
    cases=[(cid,CaseInput(messages=[{'id':'m1','speaker_id':'user','scope_id':'case','text':text}])) for cid,text in texts]
    cases.append(('screen_banking',CaseInput(messages=[
        {'id':'a','speaker_id':'sender','scope_id':'case','text':'Bấm chia sẻ màn hình để hoàn cọc nhé.'},
        {'id':'b','speaker_id':'recipient','scope_id':'case','text':'Sau khi chia sẻ thì mình cần làm gì?'},
        {'id':'c','speaker_id':'sender','scope_id':'case','text':'Mở ứng dụng ngân hàng và vào phần số dư để bên mình xem.'}])))
    cases.append(('payment_context_update',CaseInput(messages=[{'id':'m1','speaker_id':'user','scope_id':'case','text':texts[1][1]}],
        context_facts=[{'id':'checked','text':'Tôi đã tự kiểm tra tài khoản và nhận đủ tiền.','applies_to_message_ids':['m1']}])) )
    records=[]
    for cid,input in cases:
        row={'id':cid,'input':input.model_dump(mode='json')}
        for mode in ('legacy','facts'):
            with patch.dict(os.environ,{'SCAMSHIELD_REASONER':mode}):row[mode]=analyze_local(input).model_dump(mode='json')
        records.append(row)
    (output/'predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Supplementary known development cases','',
           '| Case | Old | New | Old question | New question |','|---|---|---|---|---|']
    for row in records:
        old=row['legacy']['assessment'];new=row['facts']['assessment']
        lines.append(f"| {row['id']} | {old['risk_status']} | {new['risk_status']} | {'; '.join(old['follow_up_questions'])} | {'; '.join(new['follow_up_questions'])} |")
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(records),'output':str(output)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
