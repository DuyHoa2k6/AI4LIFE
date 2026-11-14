"""Fresh public synthetic probes, separated inputs/references; no evaluation dataset read."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
directory=ROOT/'fixtures/four_states_20261110'
directory.mkdir(parents=True,exist_ok=False)
rows=[
 ('H01','Giao mã rõ ràng','high','scam','Gửi mã OTP vừa nhận trên điện thoại cho tôi. Tôi cần mã đó để đăng nhập tài khoản của bạn.',None),
 ('N01','Lịch họp bình thường','clear','normal','Mai nhóm họp lúc 15 giờ tại phòng B203. Bạn mang theo sổ ghi chép nhé.',None),
 ('C01','Chưa nói bước xử lý','need_context','uncertain','Lệnh rút tiền của tôi đang bị treo. Người bên kia bảo phải làm thêm một bước nhưng chưa nói bước gì.',None),
 ('S01','Quyền điều khiển chưa rõ mục đích','suspicious','review','Tôi tự nhận là nhân viên hỗ trợ. Bạn hãy bật quyền điều khiển máy từ xa cho tôi. Tôi chưa giải thích dùng quyền này để làm gì.',None),
 ('H02','Nộp phí trước khi nhận thưởng','high','scam','Bạn trúng phần quà 20 triệu. Chuyển 500 nghìn vào tài khoản cá nhân của tôi trước, có tiền phí thì tôi mới giải ngân phần thưởng.',None),
 ('N02','Đòi khoản vay bằng phương ngữ','clear','normal','Chuyển tiền cho ta lại đi mi, hồi sáng mi ăn mượn của ta.','Người nhắn là bạn cùng lớp đã được tôi xác nhận qua số quen dùng. Sáng nay tôi mượn bạn 50 nghìn, nay bạn nhắc trả đúng khoản đó; không có phí mới hoặc đường dẫn.'),
 ('C02','Chuyển tiền chưa rõ mục đích','need_context','uncertain','Chuyển khoản cho tôi.',None),
 ('S02','APK không rõ nhà phát hành','suspicious','review','Hãy cài tệp APK tôi gửi trong tin nhắn riêng. Tôi chưa cung cấp tên nhà phát hành hoặc lý do cần cài tệp này.',None),
 ('H03','Biến thể tiền đồng bộ','high','scam','Không thu phí gì cả. Số dư 18 triệu đang chờ về ví của bạn. Bạn cần đưa 900 nghìn tiền đồng bộ sang ví cá nhân của tôi; hệ thống chỉ mở đường nhận 18 triệu sau khi có khoản đồng bộ này.',None),
 ('N03','Bài cảnh báo trích lời dụ','clear','normal','Cảnh báo sinh viên: kẻ giả mạo thường viết “nhập mật khẩu tài khoản trường và gửi mã OTP cho chúng tôi”. Đây là lời dụ được trích để cảnh báo. Nhà trường không yêu cầu bạn làm như vậy.',None),
 ('C03','Đối tượng thao tác chưa xác định','need_context','uncertain','Bạn gửi cái đó qua đây rồi tôi hoàn tất cho.','Tôi chỉ nhận được đúng câu này; không có tin nhắn trước để biết “cái đó” là gì hoặc hoàn tất việc nào.'),
 ('S03','Nhãn liên kết khác đích','suspicious','review','Hãy mở https://youtube.com để đăng nhập. Chưa có thông tin ai gửi yêu cầu hoặc lý do phải đăng nhập.',None),
 ('H04','Chuỗi hành vi qua nhiều tin','high','scam',None,None),
 ('N04','Tự dùng mã trong ứng dụng','clear','normal','Tôi tự mở ứng dụng ngân hàng chính thức đã cài từ trước và tự nhập mã OTP vào ứng dụng để xác nhận giao dịch của mình. Không ai yêu cầu tôi gửi mã hay chia sẻ màn hình.',None),
 ('C04','Tham chiếu bước kia bị thiếu','need_context','uncertain','Bạn làm bước kia trước thì bên tôi mới xử lý tiếp được.','Tôi không có hướng dẫn trước đó; chưa biết “bước kia” là thao tác gì và đang xử lý việc gì.'),
 ('S04','Chuyển sang kênh riêng và giữ kín','suspicious','review','Một người chưa xác minh yêu cầu tôi chuyển toàn bộ cuộc trao đổi sang tài khoản chat riêng của họ và giữ kín với nhóm chung. Họ chưa yêu cầu tiền, mật khẩu hoặc mã.',None),
]
inputs=[];refs=[]
for cid,name,target,group,text,context in rows:
    payload={'text':text}
    if context:payload['context']=context
    if cid=='S03':payload['links']=[{'id':'url-1','message_id':'m1','url':'https://youtube.com.xac-minh.invalid/login','display_text':'https://youtube.com','origin':'dom_href'}]
    if cid=='H04':payload={'messages':[
        {'id':'a','speaker':'nguoi_la','text':'Tôi bên tổ xét trợ cấp. Hồ sơ của bạn có khoản hỗ trợ 8 triệu.'},
        {'id':'b','speaker':'nguoi_dung','text':'Tôi phải làm gì để nhận?'},
        {'id':'c','speaker':'nguoi_la','text':'Bạn cài ứng dụng tôi gửi rồi bật quyền điều khiển máy cho tôi. Đây là điều kiện bắt buộc, không làm thì không nhận được 8 triệu.'}]}
    inputs.append({'id':cid,'name':name,'input':payload})
    refs.append({'id':cid,'group':group,'target_status':target,'acceptable':[target],
                 'questions_required':target=='need_context','manual_focus':name})
(directory/'inputs.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),encoding='utf-8')
(directory/'expected.json').write_text(json.dumps({'scope':'16 new public synthetic functional probes, 4 primary targets per active risk state. References written before execution, not an independent holdout or real-user accuracy estimate. No tuning permitted during this run.','cases':refs},ensure_ascii=False,indent=2),encoding='utf-8')
print('Created 16 public synthetic inputs and separate references.')
