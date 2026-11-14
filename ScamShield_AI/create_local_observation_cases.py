"""Manually specified development references, never used by runtime rules."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'fixtures/local_observation'


def event(kind,verb,polarity='positive',role='request',state='requested',occurrence=0,mid='m1'):
    return {'action_type':kind,'verb':verb,'polarity':polarity,'speech_role':role,
            'temporal_state':state,'occurrence':occurrence,'message_id':mid}


def spec(cid,text,events,relation_rules=(),questions=False):
    payload=text if isinstance(text,dict) else {'text':text}
    return {'id':cid,'input':payload}, {'id':cid,'events':events,'relation_rules':list(relation_rules),'questions_required':questions}


SPECS=[
 spec('A','Chưa thấy tiền về, nhưng cứ giao máy trước.',[
     event('receive_funds','thấy','negative','claim','pending'),event('handover_asset','giao')],['REL-HANDOVER-BEFORE-CONFIRMATION']),
 spec('B','Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy cho tài xế nhé.',[
     event('receive_funds','nhận',role='claim',state='completed'),event('handover_asset','giao')],['REL-REPORTED-PAYMENT-FIRST']),
 spec('C','Nếu chưa nhận tiền thì đừng giao máy.',[
     event('receive_funds','nhận','negative','claim','hypothetical'),event('handover_asset','giao','negative','request','hypothetical')],['REL-NEGATIVE-CONDITION']),
 spec('D','Tôi cảnh báo mọi người đừng nghe câu ‘cứ giao máy trước’.',[
     event('handover_asset','giao',role='quoted_warning',state='unknown')],['REL-QUOTED-WARNING']),
 spec('E','Hôm qua chưa nhận tiền. Hôm nay tôi đã kiểm tra và nhận đủ.',[
     event('receive_funds','nhận','negative','claim','pending'),event('receive_funds','nhận',role='claim',state='completed',occurrence=1)],['REL-TIMED-UPDATE']),
 spec('F','Đơn A chưa thanh toán. Đơn B đã nhận đủ, giao đơn B nhé.',[
     event('transfer_funds','thanh toán','negative','claim','pending'),event('receive_funds','nhận',role='claim',state='completed'),event('handover_asset','giao')],['REL-REPORTED-PAYMENT-FIRST']),
 spec('G','Đọc sáu số vừa hiện để nhận tiền.',[
     event('provide_code','Đọc'),event('receive_funds','nhận',role='claim',state='unknown')],['REL-EXPLICIT-PURPOSE','REL-STATED-REASON'],True),
 spec('H',{'messages':[{'id':'m1','speaker':'Người gửi','text':'Đọc sáu số vừa hiện để nhận tiền.'},
                       {'id':'m2','speaker':'Người nhận','text':'Đó là mã đăng nhập.'}]},[
     event('provide_code','Đọc'),event('receive_funds','nhận',role='claim',state='unknown'),
     event('code_identity','Đó là mã đăng nhập',role='claim',state='unknown',mid='m2')],['REL-EXPLICIT-PURPOSE','REL-STATED-REASON','REL-EXPLICIT-CODE-REPLY']),
 spec('I','Anh là người quen của em.',[event('relationship_claim','là người quen',role='claim',state='unknown')]),
 spec('J','😀 Chuyển 500.000 đồng. Mở https://example.invalid/a?x=1. Cảnh báo “họ nhắn ‘gửi OTP’”. Chuyển 500.000 đồng.',[
     event('transfer_funds','Chuyển'),event('open_link','Mở'),
     event('provide_code','gửi',role='quoted_warning',state='unknown'),event('transfer_funds','Chuyển',occurrence=1)],['REL-QUOTED-WARNING'],True),
 spec('K','Tài xế đang chờ.',[],questions=True),
 spec('L','Mưa rơi trên mái hiên.',[],questions=True),
 spec('NEGATION','Đừng chuyển tiền.',[event('transfer_funds','chuyển','negative')],questions=True),
 spec('COMPLETED','Tôi đã chuyển tiền.',[event('transfer_funds','chuyển',role='claim',state='completed')]),
 spec('NOT_YET','Tôi chưa chuyển tiền.',[event('transfer_funds','chuyển','negative','claim','pending')]),
 spec('NO_NEED','Không cần chuyển tiền.',[event('transfer_funds','chuyển','negative')]),
 spec('PENDING','Chưa được rút tiền.',[event('withdraw_funds','rút','negative','claim','pending')],questions=True),
 spec('MONEY','Ứng 500 nghìn để rút số dư.',[
     event('transfer_funds','Ứng'),event('withdraw_funds','rút',role='claim',state='unknown')],['REL-EXPLICIT-PURPOSE','REL-STATED-REASON']),
 spec('PASSWORD','Gửi mật khẩu cho tôi.',[event('provide_credentials','Gửi')]),
 spec('DOCUMENTS','Gửi ảnh hai mặt căn cước qua chat.',[event('provide_documents','Gửi')]),
 spec('INSTALL','Cài ứng dụng tôi gửi.',[event('install_app','Cài')]),
 spec('SCREEN','Bật chia sẻ màn hình.',[event('share_screen','Bật chia sẻ màn hình')]),
 spec('CONTROL','Cấp quyền điều khiển.',[event('grant_control','Cấp quyền')]),
 spec('CHANNEL','Chuyển sang Telegram nhé.',[event('change_channel','Chuyển sang')]),
 spec('SECRET','Giữ bí mật chuyện này.',[event('keep_secret','Giữ bí mật')]),
 spec('VERIFY','Đừng gọi số trong hợp đồng.',[event('avoid_verification','Đừng gọi')]),
 spec('IDENTITY','Tôi là công an.',[event('identity_claim','Tôi là',role='claim',state='unknown')]),
 spec('LOGIN','Tôi tự nhập mã trên ứng dụng chính thức.',[event('login','tự nhập',role='claim',state='unknown')]),
 spec('REPORTED','Bạn nói chưa thấy tiền về.',[event('receive_funds','thấy','negative','reported','pending')],['REL-REPORTED-SPEECH']),
 spec('DOUBLE_NEGATION','Không phải là không cần chuyển tiền.',[event('transfer_funds','chuyển','uncertain')]),
]


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=False)
    for name,data in [('inputs.json',[s[0] for s in SPECS]),('expected.json',{
        'scope':'Manual draft development annotations for local rules; needs independent human review. No validation/holdout used. Not a final risk-label evaluation.',
        'review_status':'draft_reference','provenance':'synthetic_and_user_supplied',
        'cases':[s[1] for s in SPECS]})]:
        (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Wrote 30 first-stage development cases and separate references.')
