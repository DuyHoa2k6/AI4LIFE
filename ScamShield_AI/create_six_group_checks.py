"""Author 30 public synthetic checks, separate inputs and reference judgments."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FAMILIES=['transfer_funds','share_auth_code','grant_access','install_app','inducement','other']
NAMES=['Chuyển tiền','Giao mã/mật khẩu','Cấp quyền','Cài ứng dụng','Lời dụ/điều kiện','Hành vi khác']
groups={k:[] for k in FAMILIES}


def add(family,name,group,text,status,actions=(),context=None,focus=''):
    payload=text if isinstance(text,dict) else {'text':text}
    if context:payload['context']=context
    groups[family].append((name,group,payload,status,list(actions),focus))


add('transfer_funds','Phí xác nhận để lấy lại cọc','scam',
    'Muốn nhận lại 6 triệu tiền cọc, bạn chuyển trước 650 nghìn phí xác nhận vào ví cá nhân của tôi. Chỉ khi có phí này tôi mới trả khoản cọc cũ.',
    'high',['transfer_funds','inducement'],focus='Phải trả thêm là điều kiện hoàn cọc; chưa xác minh danh tính không phủ nhận quan hệ đã nêu.')
add('transfer_funds','Đệm số dư thay cách nói nạp tiền','scam',
    'Để giải phóng tiền công đang giữ, chị cần đệm 1 triệu số dư bảo chứng sang ví của em. Khi hệ thống ghi nhận khoản đệm, em mới mở quyền lấy cả tiền công lẫn vốn.',
    'high',['transfer_funds','inducement'],focus='Biến thể đổi cách diễn đạt nhưng giữ cơ chế trả trước mới nhận tiền.')
add('transfer_funds','Trả khoản vay đã đối chiếu','normal','Bạn trả lại mình 320 nghìn đã vay hôm qua nhé.','clear',['transfer_funds'],
    context='Tôi xác nhận đây là bạn đã cho tôi mượn 320 nghìn. Tôi vừa gặp trực tiếp và đối chiếu đúng khoản vay cùng tài khoản nhận.')
add('transfer_funds','Bài cảnh báo chứa chuyển phí','normal',
    'Cảnh báo: câu “chuyển phí xác nhận để lấy lại cọc” là dấu hiệu cần xác minh. Đừng chuyển thêm theo tin nhắn của người lạ.',
    'clear',focus='Lời trích cảnh báo/phủ định không phải yêu cầu chuyển tiền.')
add('transfer_funds','Nhắc chuyển tiền chưa rõ khoản gì','uncertain',
    'Chuyển lại cho tôi khoản hôm trước nhé.','need_context',focus='Hỏi quan hệ và mục đích khoản tiền, không tự kết luận lừa đảo.')

add('share_auth_code','Đòi OTP để chống khóa tài khoản','scam',
    'Tôi là hỗ trợ ngân hàng. Đọc mã OTP đăng nhập cho tôi để chống khóa tài khoản ngay.','high',['share_auth_code'],
    focus='Yêu cầu giao mã trực tiếp; tự xưng hỗ trợ không xác minh danh tính.')
add('share_auth_code','Chuỗi sáu số trong SMS','scam',
    'Hãy chép cho tôi chuỗi sáu số trong SMS đăng nhập vừa tới, tôi sẽ dùng nó mở lại quyền truy cập hộ bạn.',
    'high',['share_auth_code'],focus='Biến thể không dùng từ OTP nhưng đòi mã đăng nhập.')
add('share_auth_code','Tự nhập mã trên máy mình','normal',
    'Tôi tự mở ứng dụng ngân hàng chính thức và nhập OTP trên điện thoại của mình. Tôi không gửi mã cho ai.',
    'clear',focus='Tự nhập khác với giao mã cho người khác.')
add('share_auth_code','Tập huấn trích câu dụ lấy mã','normal',
    'Buổi tập huấn đưa ví dụ “đọc OTP cho tôi để nhận quà”. Đây là lời dụ cần tránh, không đọc mã hoặc mật khẩu cho ai.',
    'clear',focus='Đúng vai lời trích và phủ định.')
add('share_auth_code','Chưa biết mã được yêu cầu là mã gì','uncertain',
    'Họ nhắn gửi cho họ mã đó. Tôi chưa biết họ nói mã đơn hàng hay mã xác thực nào.',
    'need_context',focus='Không tự coi mọi mã là OTP; hỏi loại mã và nguồn yêu cầu.')

add('grant_access','Điều khiển để nhận hoàn phí','scam',
    'Bật quyền điều khiển từ xa cho tôi rồi mở ứng dụng ngân hàng. Đây là điều kiện để tôi giải ngân khoản hoàn phí cho bạn.',
    'high',['grant_access','inducement'])
add('grant_access','Quyền quản trị trang không rõ mục đích','suspicious',
    'Thêm tài khoản của tôi làm quản trị viên trang và cho quyền xóa thành viên khác.',
    'suspicious',['grant_access'],focus='Đã rõ yêu cầu quyền nhạy cảm; có thể cảnh báo và hỏi thêm, chưa khẳng định tội phạm.')
add('grant_access','Quyền thông báo hợp lệ','normal',
    'Ứng dụng lịch đang hỏi tôi có cho phép gửi thông báo nhắc lịch không.',
    'clear',context='Tôi tự mở ứng dụng lịch đã dùng lâu nay trong phần cài đặt, chỉ bật thông báo, không cấp điều khiển hay truy cập tài khoản.')
add('grant_access','Cảnh báo không chia sẻ màn hình','normal',
    'Không cấp quyền điều khiển hoặc chia sẻ màn hình ngân hàng cho người lạ. Bài viết này hướng dẫn bảo vệ tài khoản.',
    'clear')
add('grant_access','Chưa biết loại quyền','uncertain',
    'Người gửi bảo bật quyền đó thì họ mới hỗ trợ được. Tôi chưa thấy họ chỉ rõ quyền gì hoặc trên ứng dụng nào.',
    'need_context',focus='Hỏi quyền gì/mục đích; không bịa quyền điều khiển đã xuất hiện.')

add('install_app','APK trợ cấp kèm cấp quyền','scam',
    'Cài TroCapMoi.apk tôi gửi và bật quyền điều khiển để được nhận khoản trợ cấp. Không cài thì không được giải ngân.',
    'high',['install_app','grant_access','inducement'])
add('install_app','Cài APK ngoài kho chưa rõ lý do','suspicious',
    'Cài BanHoTro.apk tôi gửi trực tiếp trong tin nhắn, đừng dùng bản trên kho ứng dụng.',
    'suspicious',['install_app'],focus='Cảnh báo trước thao tác cài đặt; không bịa thêm điều kiện tiền hay mã.')
add('install_app','Cập nhật ứng dụng đã xác nhận','normal',
    'Bạn cập nhật ứng dụng họp đang dùng từ kho chính thức nhé.','clear',
    context='Tôi đã đối chiếu yêu cầu cập nhật với quản trị công ty qua số nội bộ quen thuộc. Đó là ứng dụng đang dùng, đúng nhà phát hành trên kho, không phải tệp/link người gửi cung cấp.')
add('install_app','Bài cảnh báo cài tệp','normal',
    'Cảnh giác với lời nhắn “cài APK rồi bật trợ năng để nhận tiền”. Không cài tệp được gửi từ người chưa xác minh.',
    'clear')
add('install_app','Tệp mới tải nhưng chưa biết loại','uncertain',
    'Họ gửi một tệp đính kèm và nhờ tôi mở. Tôi chưa biết đó là tài liệu hay chương trình.',
    'need_context')

add('inducement','Làm thử rồi phải ứng vốn','scam',{'messages':[
    {'id':'d1','speaker':'tuyển dụng','text':'Nhiệm vụ đầu không mất phí, bạn được thưởng 40 nghìn.'},
    {'id':'d2','speaker':'tôi','text':'Tôi đã làm xong việc đầu.'},
    {'id':'d3','speaker':'tuyển dụng','text':'Bây giờ ứng trước 800 nghìn vào ví nhóm để mở nhiệm vụ cuối, xong sẽ được rút vốn cùng hoa hồng.'}]},
    'high',['transfer_funds','inducement'],focus='Nối đúng chuỗi người tuyển dụng, không ghép lời người nhận.')
add('inducement','Phí giữ suất để nhận tài trợ','scam',
    'Suất tài trợ của bạn đã được giữ. Nộp 500 nghìn phí giữ suất vào tài khoản riêng của tôi trong 10 phút thì mới được nhận tiền tài trợ.',
    'high',['transfer_funds','inducement'])
add('inducement','Khuyến mại không đòi tài sản','normal',
    'Thư viện tặng dấu trang miễn phí cho người tới đọc sách vào chủ nhật, không cần đăng ký tài khoản hoặc đóng phí.',
    'clear')
add('inducement','Giảng giải lời hứa lợi nhuận','normal',
    'Bài học nhắc: đừng tin lời hứa lợi nhuận chắc chắn hoặc chuyển vốn cho người lạ. Ví dụ này là nội dung phòng tránh, lớp không nhận tiền đầu tư.',
    'clear')
add('inducement','Hứa tiền nhưng chưa rõ điều kiện','uncertain',
    {'text':'Có người bảo tôi sắp được nhận một khoản tiền, nhưng chưa nói vì sao hoặc phải làm gì.',
     'question':'Tôi nên hỏi gì để biết điều kiện có rủi ro không?'},
    'need_context',focus='Hỏi nguồn/điều kiện, không tự thêm yêu cầu ứng tiền.')

add('other','Xác nhận hàng chưa tới để được hoàn tiền','scam',
    'Dù hàng chưa tới, bạn bấm xác nhận đã nhận đủ hàng trên sàn trước đi. Chỉ sau khi bạn xác nhận, tôi mới hoàn lại tiền cho bạn.',
    'high',['other','inducement'],focus='Hành động làm mất bảo vệ giao dịch, không giới hạn vào chuyển tiền trực tiếp.')
add('other','Tắt cảnh báo ví và ký chấp thuận','suspicious',
    'Tắt mọi cảnh báo an toàn của ví rồi ký chấp thuận không giới hạn cho địa chỉ tôi vừa gửi.',
    'suspicious',focus='Hành vi mới có thể được mô tả other hoặc grant_access; chấm mức cảnh báo, không ép taxonomy.')
add('other','Xác nhận hàng đã kiểm tra đủ','normal',
    'Bạn xác nhận đã nhận hàng sau khi kiểm tra đủ số lượng nhé.','clear',
    context='Tôi đã nhận đủ kiện hàng đúng đơn, tự kiểm tra số lượng/chất lượng rồi mới xác nhận trên ứng dụng chính thức của sàn.')
add('other','Cảnh báo bảo vệ quyền khiếu nại','normal',
    'Đừng xác nhận đã nhận đủ hàng khi hàng chưa tới, cũng đừng rút khiếu nại chỉ vì người bán hứa hoàn tiền sau. Đây là bài hướng dẫn tự bảo vệ.',
    'clear')
add('other','Yêu cầu xác nhận chưa rõ tác động','uncertain',
    'Họ bảo tôi bấm xác nhận mục đó trong tài khoản. Tôi chưa biết xác nhận điều gì hoặc có mất quyền gì không.',
    'need_context')

if __name__=='__main__':
    directory=ROOT/'fixtures/six_groups_30'
    directory.mkdir(parents=True,exist_ok=False)
    inputs=[];refs=[]
    for round_index in range(5):
        for family,label in zip(FAMILIES,NAMES):
            name,group,payload,status,actions,focus=groups[family][round_index]
            key=f'SG-{FAMILIES.index(family)+1}{round_index+1}'
            inputs.append({'id':key,'name':name,'behavior_group':family,'behavior_label':label,'input':payload})
            refs.append({'id':key,'group':group,'behavior_group':family,'acceptable':[status],
                'questions_required':status=='need_context','expected_actions':actions,'manual_focus':focus})
    assert len(inputs)==30 and all(len(groups[f])==5 for f in FAMILIES)
    for name,data in [('inputs.json',inputs),('expected.json',{'scope':'30 public synthetic functional checks, 5 per user-selected behavior family; not independent or real-user accuracy. Reference judgments authored by implementer; no tuning in test run.','cases':refs})]:
        (directory/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Created 30 input-only cases and separate references; six families interleaved.')
