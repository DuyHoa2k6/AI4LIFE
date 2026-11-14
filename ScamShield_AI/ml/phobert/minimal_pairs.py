"""Additional annotation queue. Unlabelled means unknown, never negative."""
from pathlib import Path
from .schema import Sample,SPAN_LABELS

PAIRS=[
 ('receive_object',['Tôi đã nhận tiền.','Tôi đã nhận tài liệu.']),
 ('send_information',['Bạn gửi hướng dẫn đăng nhập cho tôi.','Bạn gửi thông tin đăng nhập cho tôi.']),
 ('verification_order',['Bạn xác minh rồi chuyển tiền.','Bạn chuyển tiền rồi xác minh.']),
 ('payment_state',['Tôi đã nhận tiền đơn A.','Tôi chưa nhận tiền đơn A.']),
 ('conditional_negation',['Không nộp thêm tiền.','Nếu không nộp thêm tiền thì mất khoản cũ.']),
]

def main():
    output=Path(__file__).resolve().parents[3]/'data/phobert/minimal_pairs_unlabelled.jsonl';rows=[]
    for family,texts in PAIRS:
        for index,text in enumerate(texts):
            group='minimal-'+family
            rows.append(Sample(id=group+'-'+str(index),family_id=group,conversation_group=group,template_group=group,source_group=group,
                source='synthetic',review_status='draft',messages=[{'id':'m1','speaker_id':'sender','text':text}],
                task_status={k:'unannotated' for k in ['spans','attributes','roles','relations','risk']},span_label_status={k:'unannotated' for k in SPAN_LABELS}))
    output.write_text(''.join(r.model_dump_json()+'\n' for r in rows),encoding='utf-8')
    print('10 unlabelled examples queued; no risk or event targets supplied')

if __name__=='__main__':main()
