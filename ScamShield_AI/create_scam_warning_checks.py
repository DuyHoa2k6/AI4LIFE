"""Public synthetic regression inputs; never a runtime scenario index or holdout."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / 'fixtures/scam_warning_20261110'


def create():
    # Author references before predictions. Interleave scams with benign controls.
    cases = [
        ('Tiền công bị giữ', 'transfer_funds', 'scam',
         {'text': 'Tiền công của chị đang nằm ở ngăn chờ. Chị chuyển 840 nghìn vào ví của em làm khoản đối ứng, đủ đối ứng thì em mới giải phóng tiền công.'}),
        ('Đổi phí thành dấu xác nhận', 'transfer_funds', 'scam',
         {'text': 'Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.'}),
        ('Đòi thêm vốn qua hội thoại', 'transfer_funds', 'scam',
         {'messages': [{'id':'a','speaker':'khach','text':'Tôi đã hoàn tất việc rồi, sao chưa rút được?'},
                       {'id':'b','speaker':'quan_ly','text':'Chị cần chuyển thêm 2 triệu để bù điểm tín nhiệm.'},
                       {'id':'c','speaker':'quan_ly','text':'Có khoản bù đó thì bên em mới mở rút toàn bộ vốn và lãi cho chị.'}]}),
        ('Trả tiền ăn có bối cảnh', 'transfer_funds', 'normal',
         {'text': 'Chuyển lại mình 75 nghìn phần bún trưa nay nhé.',
          'context': 'Tôi và bạn vừa ăn cùng, bạn thanh toán hộ. Tôi đã đối chiếu đúng phần ăn và tài khoản của bạn.'}),

        ('Mã sáu số tránh chữ OTP', 'share_auth_code', 'scam',
         {'text': 'Ngân hàng vừa gửi sáu chữ số đăng nhập về điện thoại chị. Đọc nguyên dãy đó cho tôi qua cuộc gọi để tôi hủy giao dịch đang treo; đừng tự nhập.'}),
        ('Mật khẩu để chống khóa', 'share_auth_code', 'scam',
         {'text': 'Tài khoản mua sắm của anh sắp bị khóa. Nhắn cho tôi mật khẩu đăng nhập hiện tại, tôi mới giữ tài khoản hoạt động cho anh được.'}),
        ('Chuỗi khôi phục ví', 'share_auth_code', 'scam',
         {'text': 'Muốn nhận lại số dư ví, chép toàn bộ 12 từ khôi phục bí mật rồi gửi riêng cho tôi. Tôi phải có đủ 12 từ mới mở lại số dư cho bạn.'}),
        ('Tự nhập mã trong ứng dụng', 'share_auth_code', 'normal',
         {'text': 'Tôi tự mở ứng dụng ngân hàng đã cài, tự nhập mã xác thực để trả hóa đơn. Tôi không đọc hoặc gửi mã cho người khác.'}),

        ('Điều khiển máy để mở trợ cấp', 'grant_access', 'scam',
         {'text': 'Bật điều khiển từ xa và cho tôi thao tác trên điện thoại của cô. Chỉ khi tôi điều khiển được máy thì hồ sơ trợ cấp mới được duyệt giải ngân.'}),
        ('Thêm quản trị viên trang', 'grant_access', 'scam',
         {'text': 'Muốn nhận gói tài trợ cho trang, thêm tài khoản của tôi làm quản trị viên toàn quyền trước. Khi có toàn quyền tôi mới chuyển tiền tài trợ.'}),
        ('Chia sẻ ngân hàng để hoàn phí', 'grant_access', 'scam',
         {'messages': [{'id':'s1','speaker':'hotro','text':'Bật chia sẻ màn hình và mở phần số dư trong ứng dụng ngân hàng.'},
                       {'id':'s2','speaker':'hotro','text':'Đây là bước bắt buộc để tôi xử lý khoản hoàn phí cho anh.'}]}),
        ('Quyền thông báo lịch có bối cảnh', 'grant_access', 'normal',
         {'text': 'Cho phép ứng dụng lịch gửi thông báo để nhắc buổi học nhé.',
          'context': 'Tôi tự cài ứng dụng lịch của trường từ cửa hàng chính thức. Quyền đang hỏi chỉ là thông báo nhắc lịch, không xem màn hình hoặc điều khiển.'}),

        ('Tệp ngoài cửa hàng để nhận hỗ trợ', 'install_app', 'scam',
         {'text': 'Cài tệp ho-tro.apk tôi gửi ngoài cửa hàng ứng dụng, bật quyền trợ năng cho nó. Cài xong và cấp quyền thì tôi mới mở khoản hỗ trợ cho cô.'}),
        ('Phần mềm máy tính để lấy tiền', 'install_app', 'scam',
         {'text': 'Tải bộ cài exe qua đường dẫn riêng của tôi rồi tắt phần mềm bảo vệ để cài. Đây là điều kiện bắt buộc để nhận lại tiền đơn hàng bị hủy.'}),
        ('Đổi tên app thành công cụ đối soát', 'install_app', 'scam',
         {'text': 'Đây chỉ là công cụ đối soát, không phải ứng dụng ngân hàng. Cài gói tôi gửi và bật quyền điều khiển thiết bị; đủ hai bước này bên tôi mới giải ngân tiền hoàn.'}),
        ('Bài cảnh báo tệp APK', 'install_app', 'normal',
         {'text': 'Bản tin an toàn: kẻ gian thường nói “cài tệp APK này để nhận trợ cấp”. Đó là lời dụ được trích để cảnh báo. Đừng cài tệp người lạ gửi hoặc cấp quyền điều khiển.'}),

        ('Nhiệm vụ nhỏ dẫn sang ứng vốn', 'inducement', 'scam',
         {'messages': [{'id':'j1','speaker':'tuyendung','text':'Lượt đầu bấm thích bài đăng được trả 20 nghìn, không cần vốn.'},
                       {'id':'j2','speaker':'ungvien','text':'Tôi đã nhận 20 nghìn rồi.'},
                       {'id':'j3','speaker':'tuyendung','text':'Muốn nhận thưởng 900 nghìn ở lượt kế, em phải chuyển trước 500 nghìn tiền giữ suất cho chị.'}]}),
        ('Gây áp lực giả cơ quan', 'inducement', 'scam',
         {'text': 'Tôi là cán bộ xử lý hồ sơ. Trong mười phút anh phải chuyển 8 triệu vào tài khoản tôi cung cấp để kiểm tra nguồn tiền; chuyển xong mới được gỡ phong tỏa.'}),
        ('Nạp tiền giải phóng lợi nhuận', 'inducement', 'scam',
         {'text': 'Anh đã thắng 30 triệu nhưng hệ thống giữ khoản lãi. Nạp thêm 3 triệu bảo lãnh vào ví riêng của tôi ngay hôm nay, tôi mới cho rút cả gốc lẫn lãi.'}),
        ('Phần thưởng không yêu cầu tài sản', 'inducement', 'normal',
         {'text': 'Thư viện tặng một cuốn sách cho người tham dự buổi đọc. Đến quầy nhận miễn phí, không đóng phí, không cung cấp mã hay thông tin ngân hàng.'}),

        ('Xác nhận nhận hàng để được hoàn', 'other', 'scam',
         {'text': 'Bưu kiện chưa giao cũng cứ bấm đã nhận hàng trên sàn trước. Sau khi anh xác nhận hoàn tất đơn thì tôi mới hoàn lại tiền cho anh qua kênh riêng.'}),
        ('Ký quyền ví để nhận thưởng', 'other', 'scam',
         {'text': 'Ký chấp thuận cho địa chỉ tôi gửi được chi tiêu toàn bộ token trong ví trước. Chữ ký cấp quyền đó là điều kiện để tôi chuyển phần thưởng vào ví của bạn.'}),
        ('Gửi ảnh giấy tờ và video', 'other', 'scam',
         {'text': 'Gửi riêng cho tôi ảnh hai mặt căn cước và video quay mặt cầm căn cước. Có đủ bộ đó tôi mới duyệt suất vay ưu đãi, không gửi thì không nhận được khoản vay.'}),
        ('Nhận hàng sau khi kiểm tra', 'other', 'normal',
         {'text': 'Tôi chỉ bấm đã nhận hàng sau khi nhận đúng gói và kiểm tra đủ sản phẩm. Không ai yêu cầu tôi xác nhận trước hoặc hoàn tiền ngoài sàn.'}),
    ]
    DIRECTORY.mkdir(parents=True, exist_ok=False)
    inputs, refs = [], []
    for i, (name, family, group, payload) in enumerate(cases, 1):
        cid = f'NW-{i:02d}'
        inputs.append({'id': cid, 'name': name, 'behavior_group': family, 'input': payload})
        refs.append({'id': cid, 'name': name, 'group': group, 'behavior_group': family,
                     'acceptable': ['high' if group == 'scam' else 'clear'],
                     'questions_required': False,
                     'manual_focus': 'Rà người nói, vai lời trích và quan hệ yêu cầu/lợi ích; không xác minh tội phạm thực tế.'})
    scope = ('24 fresh public synthetic functional cases authored before predictions: '
             '18 explicit risky requests/conditions, 6 benign controls. Not independent '
             'human-labelled accuracy or real-user prevalence; no runtime data or prompt tuning.')
    for name, data in [('inputs.json', inputs), ('expected.json', {'scope': scope, 'cases': refs})]:
        (DIRECTORY / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Created 24 synthetic cases: 18 high-risk scenarios and 6 benign controls; labels separate.')


if __name__ == '__main__':
    create()
