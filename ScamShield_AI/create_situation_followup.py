"""Seal new synthetic cases after the regression fixes; labels stay out of model input."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'fixtures/situation_followup_20261110'


def dialogue(*rows):
    return {'messages': [{'id': f'm{i}', 'speaker': who, 'text': text}
                         for i, (who, text) in enumerate(rows, 1)]}


CASES = [
 ('F01', 'Tự nhập mã trên ứng dụng', {'text': 'Tôi tự mở ứng dụng chính thức và nhập mã xác thực trên điện thoại của mình. Tôi không gửi mã cho ai.'}, 'clear', 'Tự thao tác, phủ định việc giao mã cho người khác.'),
 ('F02', 'Giao loa sau khi tự kiểm tra tiền', dialogue(
     ('Khách mua', 'Người vận chuyển đã đến, bạn bàn giao bộ loa giúp tôi.'),
     ('Chủ hàng', 'Tôi vừa tự xem ứng dụng ngân hàng: tiền mua bộ loa đã vào đúng tài khoản, đủ số tiền.')), 'clear', 'Người nhận tiền tự báo đã kiểm tra; không phải lời khẳng định của người mua.'),
 ('F03', 'Bài cảnh báo thu giấy tờ', {'text': 'Lưu ý: có người giả danh ban học bổng nhắn “gửi căn cước hai mặt và ảnh chân dung qua chat để giữ suất”. Đừng gửi theo lời nhắn đó; tự hỏi nhà trường qua kênh chính thức.'}, 'clear', 'Lời dụ nằm trong bài cảnh báo, không phải yêu cầu trực tiếp.'),
 ('F04', 'Khoản vay có đối chiếu trong hội thoại', dialogue(
     ('Chủ nợ', 'Bạn chuyển trả khoản vay tuần trước giúp tôi nhé.'),
     ('Người vay', 'Đúng khoản tôi đã vay. Tôi vừa gọi số quen của bạn để đối chiếu số tiền và tài khoản, đều đúng thỏa thuận.')), 'clear', 'Bối cảnh trong messages giải thích riêng khoản thanh toán này.'),
 ('F05', 'Đối tượng chưa rõ', {'text': 'Bạn gửi lại cái đó qua đây để bên mình xử lý tiếp nhé.'}, 'need_context', 'Hỏi “cái đó” là loại thông tin hoặc đối tượng gì, không tự đoán là OTP.'),
 ('F06', 'Chờ xét lệnh rút', {'text': 'Yêu cầu rút số dư đang được bộ phận kiểm tra xem xét. Khi có hướng dẫn tiếp theo, chúng tôi sẽ thông báo.'}, 'need_context', 'Chưa có yêu cầu chuyển tiền hay giao thông tin; hỏi bước tiếp theo.'),
 ('F07', 'Thủ tục hoàn cọc chưa mô tả', {'text': 'Để nhận lại tiền đặt chỗ, bạn cần hoàn tất thủ tục Z. Mình chưa gửi mô tả thủ tục đó, mai mình báo.'}, 'need_context', 'Hỏi thao tác cụ thể trong thủ tục, không tự thêm phí hay mã.'),
 ('F08', 'Chuyển phần còn lại chưa rõ mục đích', {'text': 'Bạn chuyển nốt phần còn lại cho mình nhé.'}, 'need_context', 'Chưa rõ là khoản nợ, mua bán hay tiền để nhận lợi ích.'),
 ('F09', 'Giao loa khi tiền chưa vào', dialogue(
     ('Khách mua', 'Người vận chuyển đã đến, bạn bàn giao bộ loa giúp tôi.'),
     ('Chủ hàng', 'Tôi vừa tự xem ứng dụng ngân hàng: tiền mua bộ loa chưa vào tài khoản.'),
     ('Khách mua', 'Tôi có ảnh chuyển tiền rồi, bạn giao bộ loa trước đi, kiểm tra tiền sau.')), 'suspicious', 'Đối chứng F02: ảnh chuyển tiền không thay việc người nhận tự kiểm tra.'),
 ('F10', 'Thay tài khoản và hoãn đối chiếu', {'text': 'Hóa đơn bảo trì giữ nguyên, nhưng tháng này bên mình dùng tài khoản cá nhân mới. Cứ thanh toán theo số tài khoản trong chat ngay hôm nay, tuần tới hãy gọi số trên hợp đồng để đối chiếu.'}, 'suspicious', 'Thay người nhận tiền và yêu cầu thanh toán trước, xác minh sau.'),
 ('F11', 'Giữ suất học bổng bằng giấy tờ qua chat', {'text': 'Mình là cộng tác viên chương trình học bổng. Muốn giữ suất, bạn gửi ảnh căn cước cả hai mặt cùng ảnh chân dung vào chat riêng này nhé.'}, 'suspicious', 'Thu giấy tờ nhạy cảm qua chat; không mặc định high chỉ vì có lợi ích.'),
 ('F12', 'Mã đăng nhập bị gọi là chuỗi tám ký tự', dialogue(
     ('Hỗ trợ', 'Đọc giúp tôi chuỗi tám ký tự vừa hiện để mở khoản tiền đang chờ.'),
     ('Người nhận', 'Thông báo trên máy ghi đó là mã đăng nhập của tài khoản tôi.'),
     ('Hỗ trợ', 'Chính chuỗi đó, đọc cho tôi để làm tiếp.')), 'high', 'Nối ý nghĩa mã từ câu người nhận; không cần chữ OTP trong lời yêu cầu.'),
 ('F13', 'Chia sẻ màn hình rồi mở lịch sử ngân hàng', dialogue(
     ('Hỗ trợ', 'Bật chia sẻ màn hình để mình kiểm tra hồ sơ hoàn phí.'),
     ('Người nhận', 'Tiếp theo tôi mở mục nào?'),
     ('Hỗ trợ', 'Giữ chia sẻ và mở ứng dụng ngân hàng vào lịch sử giao dịch cho mình xem.')), 'high', 'Hai yêu cầu của cùng người gửi tạo chuỗi lộ dữ liệu tài chính.'),
 ('F14', 'Tiền đồng bộ để giải phóng số dư', {'text': 'Số dư của bạn đã hiện nhưng chưa rút được. Muốn giải phóng toàn bộ khoản đó, bạn phải chuyển thêm 700 nghìn tiền đồng bộ trước; không chuyển thì hệ thống tiếp tục giữ tiền.'}, 'high', 'Đổi cách gọi phí nhưng vẫn phải nộp thêm tiền để rút số dư.'),
]


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=False)
    inputs = [{'id': cid, 'name': name, 'input': payload} for cid, name, payload, _, _ in CASES]
    refs = {'scope': '14 new synthetic follow-up cases sealed after regression changes. Internal functional evaluation, not independently collected real-world accuracy. Labels excluded from provider payloads.',
            'cases': [{'id': cid, 'group': status, 'acceptable': [status],
                       'questions_required': status == 'need_context', 'manual_focus': focus}
                      for cid, _, _, status, focus in CASES]}
    for name, content in [('inputs.json', inputs), ('expected.json', refs)]:
        (OUT / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json')}
    (OUT / 'hashes.json').write_text(json.dumps(hashes, indent=2) + '\n', encoding='utf-8')
    print('Sealed 14 follow-up cases; labels remain separate.')
