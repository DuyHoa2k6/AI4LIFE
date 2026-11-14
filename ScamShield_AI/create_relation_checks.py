"""Public targeted checks; author labels before live predictions, no holdout access."""
import json
from pathlib import Path


def main():
    path=Path(__file__).resolve().parent/'fixtures/relation_v4'
    path.mkdir(parents=True,exist_ok=False)
    cases=[
        ('NW-02 hồi quy dấu xác nhận', 'scam','high',
         {'text':'Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.'}),
        ('Tên gọi thay thế cho tiền ứng trước', 'scam','high',
         {'text':'Để mở lại số dư 18 triệu, cô mua vé xác thực giá 900 nghìn bằng cách chuyển vào tài khoản của cháu. Vé đó là điều kiện bắt buộc, chưa mua thì cô chưa lấy lại được số dư.'}),
        ('Đặt mua hàng hợp pháp có hóa đơn', 'normal','clear',
         {'text':'Thanh toán 240 nghìn cho đơn sách trước, cửa hàng xác nhận đủ tiền rồi mới giao đúng đơn đã đặt.',
          'context':'Tôi chủ động đặt đơn sách này trong ứng dụng chính thức. Đã kiểm tra hóa đơn, giá và tài khoản cửa hàng; đây là giá mua sách, không phải phí để mở khoản tiền bị giữ.'}),
        ('Bản tin trích lời dụ', 'normal','clear',
         {'text':'Bản tin cảnh báo trích lời kẻ gian: “Mua vé xác thực bằng cách chuyển 900 nghìn cho tôi mới nhận lại số dư”. Đừng chuyển tiền theo lời dụ này. Bài viết không yêu cầu người đọc mua vé hay gửi tiền.'}),
        ('Hai người nói về hai sự việc', 'normal','clear',
         {'messages':[{'id':'m1','speaker':'ban_cung_phong','text':'Trả lại tớ 150 nghìn tiền ăn đã ứng hôm qua nhé.'},
                      {'id':'m2','speaker':'quangcao','text':'Chỉ khi đăng ký tham gia buổi đọc sách thì mới nhận quà sách miễn phí.'}],
          'context':'Tôi xác nhận khoản tiền ăn là khoản bạn cùng phòng đã ứng hộ, đúng số tiền và người nhận. Quảng cáo buổi đọc sách là người khác, không yêu cầu nộp tiền.'}),
        ('Chưa rõ đại từ chỉ thao tác nào', 'uncertain','need_context',
         {'text':'Anh chuyển lại khoản đó giúp tôi. Hoàn tất bước kia thì mới nhận phần còn lại. Tôi chưa giải thích khoản nào hay bước gì.'}),
        ('Đại từ nối điều kiện qua hội thoại', 'scam','high',
         {'messages':[{'id':'r1','speaker':'dieu_phoi','text':'Chị chuyển 650 nghìn sang ví của em làm phần đối ứng.'},
                      {'id':'r2','speaker':'khach','text':'Phần đối ứng đó để làm gì?'},
                      {'id':'r3','speaker':'dieu_phoi','text':'Không có khoản đó thì bên em chưa giải phóng tiền công 7 triệu cho chị được.'}]}),
        ('Một câu nhờ chuyển tiền thiếu bối cảnh', 'uncertain','need_context',
         {'text':'Bạn chuyển giúp mình 450 nghìn được không?'})]
    inputs=[];refs=[]
    for i,(name,group,status,payload) in enumerate(cases,1):
        cid=f'RG-{i:02d}'
        inputs.append({'id':cid,'name':name,'input':payload})
        refs.append({'id':cid,'name':name,'group':group,'acceptable':[status],
                     'questions_required':group=='uncertain'})
    scope='8 public targeted synthetic checks: 1 known regression, 7 newly authored variants/controls; not independently labelled accuracy. No tuning during run.'
    for name,data in [('inputs.json',inputs),('expected.json',{'scope':scope,'cases':refs})]:
        (path/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Created 8 targeted cases; predictions and references separate.')


if __name__=='__main__':
    main()
