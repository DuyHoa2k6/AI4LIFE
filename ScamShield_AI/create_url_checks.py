"""Small public functional URL+text checks, labels outside model inputs."""
import json
from pathlib import Path

def main():
    path=Path(__file__).resolve().parent/'fixtures/url_checks';path.mkdir(parents=True,exist_ok=False)
    cases=[
      ('Yêu cầu OTP và miền gần giống','scam','high',{'text':'Tôi là hỗ trợ YouTube. Gửi mã OTP đăng nhập của bạn tại đây để tôi ngăn khóa tài khoản.',
        'links':[{'id':'u1','message_id':'m1','url':'https://youtubee.com/auth?token=SYNTHETIC','display_text':'tại đây','origin':'user_supplied'}]}),
      ('Bài cảnh báo nhắc tên gần giống','normal','clear',{'text':'Cảnh báo: link https://youtubee.com là ví dụ tên gần giống. Đừng đăng nhập hoặc gửi mã qua đó. Đây là bài phòng tránh, không yêu cầu làm theo.'}),
      ('Tự đọc nội dung tại miền tham chiếu','normal','clear',{'text':'Tôi tự mở https://www.youtube.com để xem video học. Không ai yêu cầu tôi đăng nhập hay cung cấp mã.'}),
      ('Đích ẩn khác nhãn và yêu cầu đăng nhập','suspicious','suspicious',{'text':'Đăng nhập tài khoản để xác minh tại https://youtube.com.',
        'links':[{'id':'u4','message_id':'m1','url':'https://youtube.com.account-check.net/login','display_text':'https://youtube.com','origin':'user_supplied'}]}),
      ('Tên miền tiếng Việt không tự thành độc hại','normal','clear',{'text':'Tôi đang đọc bài hướng dẫn ngôn ngữ tại https://vídụ.vn, không làm thao tác đăng nhập hay thanh toán.'}),
      ('Bài cảnh báo có nhãn và đích không khớp','normal','clear',{'text':'Bài cảnh báo đưa ví dụ: https://youtube.com. Đích thật của liên kết mẫu là một miền khác; đừng bấm đăng nhập.',
        'links':[{'id':'u6','message_id':'m1','url':'https://help.example.net/check','display_text':'https://youtube.com','origin':'user_supplied'}]})]
    inputs=[];refs=[]
    for i,(name,group,status,payload) in enumerate(cases,1):
        cid=f'URL-{i:02d}';inputs.append({'id':cid,'name':name,'input':payload})
        refs.append({'id':cid,'name':name,'group':group,'acceptable':[status],'questions_required':False})
    for name,data in [('inputs.json',inputs),('expected.json',{'scope':'6 public synthetic functional checks, authored labels; not independent URL reputation or overall accuracy. No destinations opened.','cases':refs})]:
        (path/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Created six URL+text checks with separate references.')

if __name__=='__main__':main()
