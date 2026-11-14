"""Final public checks: known regression plus seven fresh synthetic variants/controls."""
import json
from pathlib import Path


def main():
    path=Path(__file__).resolve().parent/'fixtures/relation_v4_checked'
    path.mkdir(parents=True,exist_ok=False)
    cases=[
        ('NW-02 hồi quy', 'scam','high',
         {'text':'Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.'}),
        ('Neo đối soát thay tên phí', 'scam','high',
         {'text':'Khoản công 11 triệu chỉ được thả sau khi chị chuyển 720 nghìn sang ví em làm neo đối soát. Neo đó chưa đủ thì bên em không cho lấy lại tiền công.'}),
        ('Tham chiếu qua hai tin cùng người nói', 'scam','high',
         {'messages':[{'id':'q1','speaker':'quanly','text':'Anh gửi 380 nghìn vào tài khoản cá nhân của tôi làm khoản bảo chứng.'},
                      {'id':'q2','speaker':'khach','text':'Tại sao phải có bảo chứng?'},
                      {'id':'q3','speaker':'quanly','text':'Chỉ khi có khoản vừa nói thì tôi mới mở rút 5 triệu tiền hoa hồng cho anh.'}]}),
        ('Mua sách trả trước có đối chiếu', 'normal','clear',
         {'text':'Chuyển 185 nghìn giá đơn sách đã đặt, nhận đủ thanh toán thì cửa hàng giao sách.',
          'context':'Tôi chủ động đặt sách trên cửa hàng chính thức. Đã kiểm tra đơn hàng, hóa đơn và đúng tài khoản cửa hàng. Đây là giá sách đã thỏa thuận, không phải tiền để mở khoản hoàn hay rút.'}),
        ('Lời dụ trong bài cảnh báo', 'normal','clear',
         {'text':'Cảnh giác với lời dụ “chuyển tiền bảo chứng trước thì mới rút được hoa hồng”. Đây là ví dụ phòng tránh trong bản tin. Người đọc không được yêu cầu gửi khoản tiền nào; đừng chuyển theo lời dụ.'}),
        ('Tiền thuê và quà miễn phí khác người nói', 'normal','clear',
         {'messages':[{'id':'u1','speaker':'chunha','text':'Gửi tiền thuê phòng tháng này như hợp đồng nhé.'},
                      {'id':'u2','speaker':'thuvien','text':'Chỉ khi tới dự buổi giới thiệu thì mới nhận sách tặng miễn phí, không nộp phí.'}],
          'context':'Tôi đã kiểm tra hợp đồng thuê và tài khoản chủ nhà qua kênh đã biết. Thông báo thư viện do người khác gửi, không liên quan việc trả tiền thuê.'}),
        ('Bước nọ và khoản kia chưa xác định', 'uncertain','need_context',
         {'text':'Chuyển lại khoản kia trước nhé. Sau bước nọ tôi mới xử lý phần còn lại. Chưa có tin nào giải thích khoản kia hay bước nọ.'}),
        ('Quyền nào chưa biết', 'uncertain','need_context',
         {'text':'Một người nhắn bảo tôi bấm đồng ý cấp quyền, nhưng tôi chưa biết đó là quyền thông báo hay quyền điều khiển máy.'})]
    inputs=[]; refs=[]
    for i,(name,group,status,payload) in enumerate(cases,1):
        cid=f'RF-{i:02d}'
        inputs.append({'id':cid,'name':name,'input':payload})
        refs.append({'id':cid,'name':name,'group':group,'acceptable':[status],
                     'questions_required':group=='uncertain'})
    scope='8 final public synthetic checks after validation-driven revision: 1 known NW-02 regression and 7 fresh inputs; implementer labels, not independent accuracy. No tuning during this run.'
    for name,data in [('inputs.json',inputs),('expected.json',{'scope':scope,'cases':refs})]:
        (path/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Created 8 final inputs and separate references.')


if __name__=='__main__':
    main()
