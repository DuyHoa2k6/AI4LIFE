"""Detailed weak-label pilot; separate authored acceptance targets, no holdout access."""
import argparse
import json
from pathlib import Path
from backend.local_reasoning.schema import CaseInput,DatasetCase,Metadata
from backend.local_reasoning.engine import analyze_local

ROOT=Path(__file__).resolve().parent.parent/'data/v2'


def one(text,verified=False,scope='case'):
    return {'messages':[{'id':'m1','speaker_id':'user','text':text,'scope_id':scope}],
            'context_facts':[{'id':'c1','text':'Tôi đã gọi đầu mối độc lập để đối chiếu điều kiện và địa điểm; tôi có quyền từ chối và tự do rời đi.',
                'verification_status':'user_reports_verification','applies_to_message_ids':['m1']}] if verified else []}


# Short synthetic fragments for annotation, not reusable recruitment narratives.
GROUPS=[
 ('trust','Cứ tin tôi, anh sẽ lo.','Anh là người quen của em.','Cứ tin tôi, hãy đi cùng và giấu gia đình.'),
 ('travel','Mời bạn đi gặp mặt, địa điểm và điều kiện đã gửi rõ.','Sang bên này anh lo hết.','Hãy đi cùng và giấu gia đình.'),
 ('employment','Tuyển nhân viên, có hợp đồng và địa điểm để kiểm tra.','Có việc làm nhưng chưa mô tả công việc.','Mời làm việc nhưng công việc khác thỏa thuận.'),
 ('debt','Chi phí đi lại được hỗ trợ, không ghi nợ và có thể rời đi bất cứ lúc nào.','Có ghi nợ chi phí, chưa nêu điều kiện trả.','Tôi đang nợ chi phí và không được rời đi.'),
 ('secrecy','Cảnh báo: đừng nghe yêu cầu “giấu gia đình để đi cùng”.','Họ nhắc giữ bí mật, chưa rõ nội dung nào.','Hãy đi cùng và đừng báo người nhà.'),
 ('communication','Cảnh báo “cắt liên lạc với gia đình” là dấu hiệu cần xác minh.','Họ nói sẽ giữ điện thoại, chưa rõ thời hạn.','Tôi đang bị giữ điện thoại và không được rời đi.'),
 ('documents','Họ giữ hộ chiếu để đăng ký và trả lại hộ chiếu ngay; có thể rời đi bất cứ lúc nào.','Họ nói sẽ giữ hộ chiếu, chưa rõ lúc nhận lại.','Họ đang giữ hộ chiếu của tôi và tôi không được rời đi.'),
 ('movement','Tôi không bị cấm rời đi và được tự do rời đi.','Họ nói về việc không được rời đi, chưa rõ ai và thời điểm.','Hiện tại tôi bị giữ lại và không được rời đi.'),
 ('harm','Bài tuyên truyền cảnh báo lời “sẽ gây hại” để ép người khác.','Một lời đe dọa gây hại được kể lại, chưa rõ thời điểm.','Họ đe dọa gây hại tôi ngay bây giờ.'),
 ('disclosure','Cảnh báo tin nhắn “sẽ phát tán ảnh” là lời đe dọa.','Họ nhắc dữ liệu riêng tư, chưa rõ yêu cầu.','Người gửi nói sẽ phát tán ảnh riêng tư.'),
 ('release','Bài cảnh báo trích “trả tiền để được thả”.','Có nhắc khoản tiền nhưng chưa rõ điều kiện rời đi.','Bên đòi tiền yêu cầu chuyển tiền để thả người nhà.'),
 ('forced_work','Tôi không bị ép làm việc; có thể dừng theo thỏa thuận.','Họ nhắc giờ làm việc, chưa rõ quyền từ chối.','Hiện tại tôi bị ép làm việc và không được rời đi.'),
 ('illegal','Cảnh báo: có người bị ép tham gia lừa đảo.','Chưa mô tả công việc yêu cầu thực hiện.','Tôi đang bị ép tham gia lừa đảo.'),
 ('bodily','Tôi tự nguyện can thiệp cơ thể và có quyền dừng, có thể từ chối.','Có nhắc can thiệp cơ thể, chưa rõ thủ tục hoặc sự tự nguyện.','Hiện tại tôi bị ép can thiệp cơ thể.'),
 ('change','Cảnh báo về việc “đổi điểm đến” khác thỏa thuận.','Họ nói đổi địa điểm, chưa rõ đã đồng ý hay chưa.','Mời làm việc và công việc khác thỏa thuận.')]


def seeds():
    rows=[]
    target_positive={'trust':('suspicious','preventive'),'travel':('suspicious','preventive'),
        'employment':('suspicious','preventive'),'debt':('high','urgent'),'secrecy':('suspicious','preventive'),
        'communication':('high','urgent'),'documents':('high','urgent'),'movement':('high','urgent'),
        'harm':('high','urgent'),'disclosure':('high','preventive'),'release':('high','preventive'),
        'forced_work':('high','urgent'),'illegal':('high','urgent'),'bodily':('high','urgent'),'change':('suspicious','preventive')}
    uncertain_targets={'trust':('clear','undetermined'),'documents':('suspicious','preventive'),
                       'communication':('suspicious','preventive'),'harm':('high','preventive')}
    for group,normal,unknown,positive in GROUPS:
        for suffix,text,target in [('N',normal,('clear','undetermined')),('U',unknown,uncertain_targets.get(group,('need_context','undetermined'))),('P',positive,target_positive[group])]:
            # Some normal samples explicitly include the user's verification report.
            rows.append({'id':group+'-'+suffix,'family':group,'input':one(text,verified=suffix=='N' and group in ('travel','employment')),
                         'target_risk':target[0],'target_urgency':target[1]})
    financial=[
        ('finance-handover','Chưa thấy tiền về, nhưng cứ giao máy trước.','suspicious'),
        ('finance-paid','Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy cho tài xế nhé.','clear'),
        ('finance-code','Đọc sáu số vừa hiện để nhận tiền.','need_context'),
        ('finance-otp','Gửi mã OTP cho tôi.','high'),
        ('finance-warning','Cảnh báo “gửi OTP cho tôi”.','clear'),
        ('finance-withdraw','Chuyển thêm tiền để rút số dư.','high'),
        ('finance-docs','Gửi ảnh CCCD qua chat.','suspicious'),
        ('finance-app','Cài app này.','suspicious'),
        ('finance-outside','Mây bay trên đỉnh núi.','need_context')]
    for cid,text,risk in financial:
        rows.append({'id':cid,'family':cid,'input':one(text),'target_risk':risk,'target_urgency':'preventive' if risk in ('high','suspicious') else 'undetermined'})
    rows.append({'id':'finance-login-linked','family':'finance-login-linked','input':{'messages':[
        {'id':'m1','speaker_id':'sender','scope_id':'sale','text':'Đọc sáu số vừa hiện để nhận tiền.'},
        {'id':'m2','speaker_id':'receiver','scope_id':'sale','text':'Đó là mã đăng nhập.'}]},'target_risk':'high','target_urgency':'preventive'})
    rows.append({'id':'safety-past','family':'safety-past','input':one('Năm ngoái tôi từng bị giữ lại, hiện sự việc đã kết thúc.'),'target_risk':'clear','target_urgency':'undetermined'})
    extras=[
        ('threat-compels','Họ đang đe dọa gây hại tôi và tôi bị ép làm việc.','high','urgent'),
        ('bodily-sexual','Hiện tại tôi bị ép quan hệ tình dục.','high','urgent'),
        ('bodily-explicit','Hiện tại tôi bị dọa lấy nội tạng.','high','urgent'),
        ('no-organ-inference','Một người đi nước ngoài rồi mất liên lạc.','need_context','undetermined'),
        ('payment-update','Hôm qua chưa nhận tiền. Hôm nay tôi đã kiểm tra và nhận đủ. Anh giao máy nhé.','clear','undetermined'),
        ('payment-conflict','Tôi đã nhận đủ tiền nhưng tôi chưa nhận tiền.','need_context','undetermined'),
        ('two-transactions','Đơn A chưa nhận tiền. Đơn B giao máy nhé.','need_context','undetermined'),
        ('url-unverified','Mở liên kết https://example.invalid để kiểm tra.','need_context','undetermined')]
    for cid,text,risk,urgency in extras:rows.append({'id':cid,'family':cid,'input':one(text),'target_risk':risk,'target_urgency':urgency})
    relation_input=one('Tôi là người quen của bạn.')
    relation_input['context_facts']=[{'id':'family-user','text':'Người gửi là anh trai tôi, đây là thông tin tôi cung cấp.','applies_to_message_ids':['m1']}]
    rows.append({'id':'family-user-report','family':'family-user-report','input':relation_input,'target_risk':'clear','target_urgency':'undetermined'})
    for kind,risk in [('ocr','clear'),('comment','high')]:
        rows.append({'id':'warning-child-'+kind,'family':'warning-child',
            'input':{'messages':[{'id':'post','speaker_id':'author','text':'Cảnh báo lời dụ bên dưới.','content_type':'post'},
                {'id':'child','speaker_id':'other','text':'Gửi mã OTP cho tôi.','content_type':kind,'parent_message_id':'post'}]},
            'target_risk':risk,'target_urgency':'undetermined' if risk=='clear' else 'preventive'})
    return rows


def build(output):
    output.mkdir(parents=True,exist_ok=False)
    rows=seeds()
    dev=[json.loads(s) for s in (ROOT.parent/'dev.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()][:3]
    for row in dev:
        rows.append({'id':'legacy-'+row['id'],'family':'legacy-'+row['family_id'],
            'source_id':row['id'],'input':{'messages':[{'id':m['id'],'speaker_id':m['speaker'],'text':m['text'],'scope_id':row['id']} for m in row['input']['messages']]}})
    inputs=[{'case_id':r['id'],'input':r['input']} for r in rows]
    (output/'inputs.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cases=[];mismatches=[];targets=[]
    for row in rows:
        request=CaseInput.model_validate(row['input']);result=analyze_local(request)
        case=DatasetCase(metadata=Metadata(case_id=row['id'],family_id=row['family'],scenario_id=row['family'],
            variant_group_id=row['family'],source_id=row.get('source_id'),source_group_id=row['family'],origin_type='synthetic',
            review_status='weak_label',annotation_version='auto-local-2.0',split='pilot',channel='chat',license_or_permission='Project synthetic development examples; review before external use.'),
            input=request,annotations=result.annotations,expected_assessment=result.assessment)
        cases.append(case)
        if 'target_risk' in row:
            target={'case_id':row['id'],'risk_status':row['target_risk'],'safety_urgency':row['target_urgency']}
            targets.append(target)
            if (result.assessment.risk_status,result.assessment.safety_urgency)!=(row['target_risk'],row['target_urgency']) or result.analysis_status!='complete':
                mismatches.append({'case_id':row['id'],'expected':target,'actual':[result.assessment.risk_status,result.assessment.safety_urgency],'analysis_status':result.analysis_status})
    (output/'pilot.jsonl').write_text('\n'.join(c.model_dump_json() for c in cases)+'\n',encoding='utf-8')
    (output/'acceptance_targets.json').write_text(json.dumps({'scope':'Authored draft development targets, separate from automatic detailed weak labels. Not independent accuracy.','cases':targets},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'build_audit.json').write_text(json.dumps({'cases':len(cases),'authored_targets':len(targets),'mismatches':mismatches},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(cases),'mismatches':mismatches},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'pilot_draft1');build(p.parse_args().output)
