"""Additional public contrast cases, authored before their first inference run."""
import json,sys,time
from pathlib import Path
from run_reasoning_document import ROOT,jsonl,dump
from backend.diagnostics import capture_traces
from backend.main import app
from fastapi.testclient import TestClient

CASES=[
 ('V01','Hợp đồng đã được gửi.','not_high',['transfer_funds']),
 ('V02','Hop dong da duoc gui.','not_high',['transfer_funds']),
 ('V03','Hop đồng đã duoc gửi.','not_high',['transfer_funds']),
 ('V04','Tôi đã gọi đầu mối để đối chiếu.','not_high',['avoid_verification']),
 ('V05','Toi da goi dau moi de doi chieu.','not_high',['avoid_verification']),
 ('V06','Đừng đợi giao dịch vào.','not_high',['handover_asset']),
 ('V07','Tôi chưa xác minh được người đăng ký.','not_high',['avoid_verification']),
 ('V08','Toi chưa xac minh được người đăng ký.','not_high',['avoid_verification']),
 ('V09','Chưa có yêu cầu chuyển tiền hay gửi mã.','not_high',['transfer_funds','provide_code']),
 ('V10','Chua co yeu cau chuyen tien hay gui ma.','not_high',['transfer_funds','provide_code']),
 ('V11','Bạn đừng cung cấp mật khẩu cho tôi hoặc người khác.','not_high',['provide_credentials']),
 ('V12','Tôi chủ động mua xe bằng tiền của tôi và chuyển quyền sở hữu sang tên người bạn. Hai bên đã lập thỏa thuận bảo vệ quyền lợi, không có yêu cầu giữ bí mật.','not_high',[]),
 ('V13','Bạn cấp quyền không giới hạn cho ứng dụng đã kiểm tra. Không có lời hứa nhận thưởng nào.','not_high',[]),
 ('V14','Bạn phải ký giấy nhận nợ. Chưa ký thì chưa được nhận lương.','high',[]),
 ('V15','Cảnh báo: người khác có thể nói “Bạn phải ký giấy nhận nợ. Chưa ký thì chưa được nhận lương.” Đừng làm theo.','not_high',[]),
 ('V16','Giao dịch A yêu cầu bạn ký giấy nhận nợ. Giao dịch B chưa ký thì chưa được nhận lương.','not_high',[]),
 ('V17','Tôi chưa mở được văn bản cần ký. Tôi cũng chưa biết mình nhận tiền cho việc gì.','need_context',['provide_code','transfer_funds']),
 ('V18','Không biết thứ cần gửi là hồ sơ hay chuyển tiền. Người yêu cầu chưa nói rõ.','need_context',['transfer_funds']),
 ('V19','Bạn có thể đọc trước và hỏi tư vấn độc lập, chưa đồng ý thì chưa đóng tiền.','clear',[]),
 ('V20','Mình cần bạn ký bảo lãnh khoản vay. Tôi thấy hợp đồng ghi khi bạn không trả thì bên cho vay có thể yêu cầu tôi thanh toán.','suspicious',[]),
]

def run(out):
    out.mkdir(parents=True,exist_ok=True)
    if (out/'predictions.jsonl').exists():raise ValueError('Do not overwrite variant predictions')
    # References remain draft and never enter the API request.
    jsonl(out/'inputs.jsonl',[{'case_id':cid,'request':{'text':text}} for cid,text,_,_ in CASES])
    jsonl(out/'reference_draft.jsonl',[{'case_id':cid,'expected':risk,'forbidden_active_types':forbidden,'review_status':'agent_authored_public_draft'} for cid,_,risk,forbidden in CASES])
    result=[]
    with TestClient(app) as client:
        for cid,text,expected,forbidden in CASES:
            start=time.perf_counter()
            with capture_traces() as captured:r=client.post('/api/analyze',json={'text':text})
            response=r.json();trace=captured[0] if captured else {};events=trace.get('annotations',{}).get('events',[])
            false_active=[e['event_id'] for e in events if e['event_type'] in forbidden and e['speech_role']=='request' and e['polarity']=='positive']
            actual=response.get('risk_status');match=(actual!='high' if expected=='not_high' else actual==expected) and r.status_code==200
            result.append({'case_id':cid,'expected_draft':expected,'actual':actual,'http_status':r.status_code,'elapsed_ms':(time.perf_counter()-start)*1000,'level_constraint_passed':match,'false_active':false_active,'response':response,'trace':trace})
            jsonl(out/'predictions.jsonl',result);print(cid,expected,actual,'false_active',false_active,flush=True)
    dump(out/'metrics.json',{'cases':len(result),'label_constraints_passed':sum(r['level_constraint_passed'] for r in result),'false_active_cases':sum(bool(r['false_active']) for r in result),'public_development_only':True,'independent_holdout':False})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add