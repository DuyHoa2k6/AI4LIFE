"""Hand-authored draft annotations, never promoted to human-reviewed gold."""
import json
from pathlib import Path
from .schema import Sample, ATTRS,SPAN_LABELS
from .data import grouped_split,write_manifest,audit

DATA=Path(__file__).resolve().parents[3]/'data/phobert'

def main():
    rows=[]
    def add(family,text,risk,specs,links=(),missing=()):
        spans=[];events=[];arguments=[]
        for i,spec in enumerate(specs):
            quote,action,obj,speech,polarity,temporal,*rest=spec
            start=text.index(quote);sid='s'+str(i);eid='e'+str(i)
            spans.append({'id':sid,'message_id':'m1','start':start,'end':start+len(quote),'quote':quote,'label':'action'})
            attributes=dict(zip(ATTRS,[action,obj,speech,polarity,temporal,rest[0] if rest else 'request' if speech=='request' else 'assertion']))
            events.append({'id':eid,'anchor_id':sid,'attributes':attributes,'transaction_id':'t1'})
            arguments += [{'event_id':eid,'role':'speaker','participant_id':'sender'},
                          {'event_id':eid,'role':'performer','participant_id':'recipient:unknown' if speech=='request' else 'sender'}]
        relations=[]
        for source,target,label in links:
            relations.append({'source':'e'+str(source),'target':'e'+str(target),'label':label,'evidence_refs':['s'+str(source),'s'+str(target)]})
        # Extra overlapping spans remain separate candidates, not forced into BIO.
        for label,quote in [('negation','không'),('time','hôm nay'),('condition','Nếu không nộp thêm'),('object','thông tin đăng nhập'),('object','tài liệu'),('entity','Tôi')]:
            if quote in text:
                at=text.index(quote);spans.append({'id':'aux'+str(len(spans)),'message_id':'m1','start':at,'end':at+len(quote),'quote':quote,'label':label})
        raw={'id':'smoke-'+str(len(rows)+1).zfill(2),'family_id':family,'conversation_group':family,'template_group':family,'source_group':family,
          'source':'synthetic','review_status':'draft','reviewers':[],
          'messages':[{'id':'m1','speaker_id':'sender','text':text}],
          'participants':[{'id':'sender','kind':'metadata','speaker_id':'sender'},{'id':'recipient:unknown','kind':'unknown'}],
          'spans':spans,'span_label_status':{k:'complete' if k=='action' else 'partial' if any(s['label']==k for s in spans) else 'unannotated' for k in SPAN_LABELS},'events':events,'event_arguments':arguments,'relations':relations,
          'transactions':{'t1':[e['id'] for e in events]} if events else {},'risk_reference':risk,
          'risk_basis':[e['id'] for e in events] if risk!='clear' else [],'missing_information':list(missing),
          'task_status':{t:'partial' if t=='spans' else 'complete' for t in ['spans','attributes','roles','relations','risk']}}
        rows.append(Sample.model_validate(raw))
    add('receive_object','Tôi đã nhận tiền.','clear',[('nhận','receive','money','claim','positive','completed')])
    add('receive_object','Tôi chưa nhận tài liệu.','need_context',[('nhận','receive','document','claim','negative','not_completed')],missing=['Tài liệu được nhắc là gì?'])
    add('send_credentials','Bạn gửi hướng dẫn đăng nhập.','clear',[('gửi','handover','document','request','positive','requested')])
    add('send_credentials','Bạn gửi thông tin đăng nhập cho tôi.','high',[('gửi','disclose_credentials','credentials','request','positive','requested')])
    add('verification_order','Bạn gọi xác minh rồi chuyển tiền.','clear',[('gọi','verify','information','request','positive','requested'),('chuyển','transfer','money','request','positive','requested')],[(0,1,'before'),(0,1,'same_transaction')])
    add('verification_order','Bạn chuyển tiền trước, đừng gọi xác minh.','suspicious',[('chuyển','transfer','money','request','positive','requested'),('gọi','avoid_verification','information','prohibition','negative','requested')],[(1,0,'obstructs_verification'),(0,1,'same_transaction')])
    add('payment_status','Tôi đã nhận tiền đơn A. Bạn giao đơn A.','clear',[('nhận','receive','money','claim','positive','completed'),('giao','handover','goods','request','positive','requested')],[(0,1,'same_transaction')])
    add('payment_status','Tôi chưa nhận tiền đơn A. Bạn giao đơn A.','suspicious',[('nhận','receive','money','claim','negative','not_completed'),('giao','handover','goods','request','positive','requested')],[(0,1,'same_transaction')])
    add('conditional_payment','Bạn không nộp thêm tiền nhé.','clear',[('nộp','transfer','money','prohibition','negative','requested')])
    add('conditional_payment','Bạn nộp thêm để được rút tiền.','high',[('nộp','transfer','money','request','positive','requested'),('rút tiền','withdraw','money','claim','positive','pending')],[(0,1,'prerequisite_for'),(0,1,'same_transaction')])
    add('auth_warning','Đừng gửi mã đăng nhập cho ai.','clear',[('gửi','disclose_credentials','auth_code','prohibition','negative','requested')])
    add('auth_warning','Bạn gửi mã đăng nhập cho tôi.','high',[('gửi','disclose_credentials','auth_code','request','positive','requested')])
    add('remote_access','Bạn cấp quyền điều khiển và mở ngân hàng.','high',[('cấp quyền','grant_control','device','request','positive','requested'),('mở','login','financial_data','request','positive','requested')],[(0,1,'controls_during'),(0,1,'same_transaction')])
    add('remote_access','Bạn cài ứng dụng chưa rõ nhà phát hành.','suspicious',[('cài','install','device','request','positive','requested')])
    add('extortion','Bạn chuyển tiền thì tôi không phát tán ghi hình.','high',[('chuyển','transfer','money','request','positive','requested'),('phát tán','threaten_disclosure','information','claim','negative','future','threat')],[(1,0,'threatens_unless'),(0,1,'same_transaction')])
    add('extortion','Tôi sẽ gửi hướng dẫn cụ thể sau.','need_context',[('gửi','handover','document','claim','positive','future')],missing=['Hướng dẫn yêu cầu thực hiện việc gì?'])
    add('travel_custody','Bạn giao hộ chiếu và phải trả tiền mới được về.','high',[('giao','retain_documents','identity_document','request','positive','requested'),('về','restrict_exit','movement','claim','positive','pending','conditional')],[(0,1,'prerequisite_for'),(0,1,'same_transaction')])
    add('travel_custody','Tôi tự giữ hộ chiếu và được tự do về.','clear',[('giữ','retain_documents','identity_document','claim','positive','ongoing')])
    add('loan_coercion','Bạn đứng tên vay giúp tôi và đừng báo gia đình.','suspicious',[('vay','borrow','money','request','positive','requested')])
    add('loan_coercion','Bạn chuyển khoản giúp tôi nhé.','need_context',[('chuyển khoản','transfer','money','request','positive','requested')],missing=['Khoản chuyển dùng để làm gì?'])
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/'smoke_draft.jsonl').write_text(''.join(r.model_dump_json()+'\n' for r in rows),encoding='utf-8')
    manifest=write_manifest(DATA/'splits',grouped_split(rows))
    (DATA/'schema.json').write_text(json.dumps(Sample.model_json_schema(),ensure_ascii=False,indent=2),encoding='utf-8')
    (DATA/'audit.json').write_text(json.dumps(audit(rows),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({s:len(v['ids']) for s,v in manifest.items()}))

if __name__=='__main__':main()
