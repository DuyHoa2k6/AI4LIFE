"""Author additional synthetic development data; never rewrite existing holdout."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent/'data/v2/semantic_variants'
# Text and annotations are separate at runtime. Labels are project hypotheses,
# not expert reviewed truth; changing a case requires a new dataset version.
CASES=[
 ('P01','payment_condition','Số dư đã được niêm phong. Bạn mua thêm một gói xác thực thì bên mình mới nhả lại vốn.','high','mua thêm một gói xác thực','nhả lại vốn','prerequisite_for','request'),
 ('P02','payment_condition','Bạn mua gói mở quyền rút trước để nhận lại số dư.','high','mua gói mở quyền rút','nhận lại số dư','prerequisite_for','request'),
 ('P03','payment_condition','Bạn nộp thêm khoản đảm bảo trước thì mới được trả lại vốn.','high','nộp thêm khoản đảm bảo','trả lại vốn','prerequisite_for','request'),
 ('P04','optional','Bạn có thể mua thêm một gói xác thực, không ảnh hưởng việc nhận lại vốn.','clear','mua thêm một gói xác thực','không ảnh hưởng','no_required_condition','request'),
 ('P05','warning','Cảnh báo: đừng mua gói xác thực để được nhả lại vốn.','clear','mua gói xác thực','nhả lại vốn','inactive','warning'),
 ('P06','denial','Bạn đừng mua thêm gói xác thực để nhận lại tiền.','clear','mua thêm gói xác thực','nhận lại tiền','inactive','denial'),
 ('P07','insufficient','Bạn mua gói xác thực nhé.','need_context','mua gói xác thực',None,'unknown','request'),
 ('P08','ordinary_purchase','Bạn thanh toán tiền chiếc ghế trước để nhận hàng nhé.','clear','thanh toán tiền chiếc ghế','nhận hàng','purchase_exchange','request'),
 ('H01','unpaid_handover','Ngân hàng vẫn chưa báo có tiền. Anh cho người tới mang chiếc đàn đi luôn trước nhé.','suspicious','cho người tới mang chiếc đàn đi','chưa báo có tiền','before_payment_confirmation','request'),
 ('H02','unpaid_handover','Chưa ghi nhận thanh toán. Bạn cho tài xế mang chiếc tủ đi trước nhé.','suspicious','cho tài xế mang chiếc tủ đi','Chưa ghi nhận thanh toán','before_payment_confirmation','request'),
 ('H03','unpaid_handover','Tôi chưa thấy tiền vào. Bạn để tài xế lấy chiếc tủ trước nhé.','suspicious','để tài xế lấy chiếc tủ','chưa thấy tiền vào','before_payment_confirmation','request'),
 ('H04','paid_handover','Tôi đã tự kiểm tra và nhận đủ tiền. Bạn cho người tới mang chiếc đàn đi nhé.','clear','cho người tới mang chiếc đàn đi','nhận đủ tiền','after_reported_payment','request'),
 ('H05','warning','Cảnh báo: chưa báo có tiền thì đừng cho người tới mang chiếc đàn đi trước.','clear','cho người tới mang chiếc đàn đi','chưa báo có tiền','inactive','warning'),
 ('H06','denial','Bạn đừng cho người tới mang chiếc đàn đi trước khi nhận tiền.','clear','cho người tới mang chiếc đàn đi','nhận tiền','inactive','denial'),
 ('H07','insufficient','Bạn cho tài xế mang chiếc tủ đi nhé.','need_context','cho tài xế mang chiếc tủ đi',None,'unknown','request'),
 ('H08','separate_transactions','Đơn A chưa báo có tiền. Đơn B bạn cho người tới mang chiếc đàn đi trước nhé.','need_context','cho người tới mang chiếc đàn đi','Đơn A chưa báo có tiền','different_transaction','request'),
 ('C01','ordinary_purchase','Bạn thanh toán tiền chiếc bàn trước để nhận hàng.','clear','thanh toán tiền chiếc bàn','nhận hàng','purchase_exchange','request'),
 ('C02','self_report','Tôi mua gói xác thực trước để nhận lại vốn.','need_context','mua gói xác thực','nhận lại vốn','not_direct_request','claim'),
 ('C03','optional','Bạn mua gói xác thực tùy chọn, không phải điều kiện để nhận lại tiền.','clear','mua gói xác thực','không phải điều kiện','no_required_condition','request'),
 ('C04','quotation','Nếu có ai nói “mua gói xác thực thì mới nhả lại vốn”, đừng làm theo.','clear','mua gói xác thực','nhả lại vốn','inactive','warning'),
 ('C05','unicode','📩 Bạn mua thêm một gói xác thực thì mới nhận lại vốn.','high','mua thêm một gói xác thực','nhận lại vốn','prerequisite_for','request'),
 ('C06','conditional_denial','Bạn không cần mua gói xác thực để nhận lại tiền.','clear','mua gói xác thực','nhận lại tiền','inactive','denial'),
 ('C07','no_payment_purpose','Bạn bổ sung khoản đảm bảo nhé.','need_context','bổ sung khoản đảm bảo',None,'unknown','request'),
 ('C08','separate_beneficiary','Bạn nộp tiền trước để công ty nhận lại vốn.','need_context','nộp tiền','công ty nhận lại vốn','different_beneficiary','request'),
]


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    if (ROOT/'inputs.jsonl').exists():raise SystemExit('Dataset already exists; create a versioned directory rather than overwriting.')
    inputs=[];expected=[]
    for cid,family,text,risk,action,context,relation,role in CASES:
        inputs.append({'id':cid,'family':family,'variant_group':family,'input':{'text':text}})
        proofs=[]
        for label,quote in [('action',action),('context',context)]:
            if quote is None:continue
            start=text.index(quote)
            proofs.append({'label':label,'message_id':'m1','quote':quote,'start':start,'end':start+len(quote)})
        expected.append({'id':cid,'risk_status':risk,'speech_role':role,'semantic_relation':relation,
            'performer_role':'addressee' if role=='request' else 'not_active_addressee',
            'affected_role':'addressee' if role=='request' and relation not in ('different_beneficiary',) else 'unknown',
            'identity_verified':False,'evidence':proofs,'review_status':'authored_development_unreviewed'})
    for name,rows in [('inputs.jsonl',inputs),('expected.jsonl',expected)]:
        (ROOT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    manifest={'version':'semantic-variants-1.0','count':len(inputs),'origin':'synthetic','split':'development_only',
        'independent':False,'review_status':'authored_development_unreviewed','train':0,
        'validation':0,'independent_test':0,'note':'No model training; no existing dev/validation/holdout modified. Near-duplicate families must remain grouped in future independent splits.',
        'hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['inputs.jsonl','expected.jsonl']}}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False))


if __name__=='__main__':main()
