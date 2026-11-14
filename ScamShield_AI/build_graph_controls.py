"""Author behavioral contrast cases, not runtime rules or independent holdout."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent/'fixtures/semantic_graph'
CASES=[
('A-new','high','Bạn chuyển tiền vào tài khoản cá nhân mới, đừng gọi đầu mối cũ.','Hợp đồng tôi giữ ghi tài khoản công ty, không có phụ lục thay đổi.'),
('A-valid','not_high','Tài khoản nhận tiền vừa đổi. Bạn chuyển tiền vào tài khoản mới nhé.','Tôi đã tự gọi đầu mối trên hợp đồng và xác nhận tài khoản nhận tiền mới.'),
('A-missing','not_high','Tài khoản nhận tiền vừa đổi. Bạn chuyển tiền vào tài khoản mới nhé.'),
('A-warning','not_high','Cảnh báo: tài khoản nhận tiền vừa đổi. Bạn chuyển tiền vào tài khoản cá nhân, đừng gọi số cũ. Hợp đồng ghi tài khoản công ty.'),
('A-two','not_high','Đơn A: Bạn chuyển tiền vào tài khoản cá nhân mới.','Đơn B: đừng gọi số cũ. Hợp đồng ghi tài khoản công ty.'),
('A-update','not_high','Tài khoản nhận tiền vừa đổi. Bạn chuyển tiền vào tài khoản cá nhân, đừng gọi số cũ.','Hợp đồng tôi giữ ghi tài khoản công ty.','Tôi đã tự gọi đầu mối trên hợp đồng và xác nhận tài khoản nhận tiền mới.'),
('B-new','high','Anh nhờ nhận tiền hộ, một người gửi tiền vào tài khoản em. Em chuyển tiếp sang tài khoản khác. Nếu ngân hàng hỏi thì cứ nói tiền người nhà trả nợ, đừng nhắc chuyện nhận hộ.'),
('B-valid','not_high','Em nhận tiền hộ mẹ rồi chuyển hộ vào tài khoản của bố. Nếu ngân hàng hỏi thì nói đúng là tiền gia đình.'),
('B-missing','not_high','Em nhận tiền hộ rồi chuyển tiếp sang tài khoản khác nhé.'),
('B-warning','not_high','Cảnh báo: nhờ nhận tiền hộ rồi chuyển tiếp sang tài khoản khác, nếu ngân hàng hỏi thì cứ nói là tiền trả nợ.'),
('B-two','not_high','Đơn A: Anh nhờ một người gửi tiền vào tài khoản em.','Đơn B: Em chuyển tiếp sang tài khoản khác. Nếu ngân hàng hỏi thì cứ nói tiền người nhà trả nợ.'),
('B-update','high','Anh nhờ nhận tiền hộ rồi chuyển tiếp sang tài khoản khác. Chuyện này chỉ hai đứa mình biết.','Tôi không biết người sẽ gửi tiền là ai.'),
('C-new','high','Bạn giao giấy tờ cho trưởng nhóm giữ. Không được tự rời chỗ ở. Muốn về phải thanh toán chi phí đã ứng.'),
('C-valid','not_high','Bạn giao hộ chiếu cho nhân viên giữ hộ khi làm thủ tục, có thể lấy lại bất cứ lúc nào. Bạn được tự do rời đi.'),
('C-missing','not_high','Bạn giao hộ chiếu cho trưởng nhóm giữ để làm thủ tục nhé.'),
('C-warning','not_high','Cảnh báo: giao hộ chiếu cho trưởng nhóm giữ, không được tự rời chỗ ở, muốn về phải thanh toán chi phí.'),
('C-two','not_high','Đơn A: Bạn giao hộ chiếu cho trưởng nhóm giữ.','Đơn B: Không được tự rời chỗ ở, muốn về phải thanh toán chi phí.'),
('C-update','high','Bạn giao hộ chiếu cho trưởng nhóm giữ.','Không được tự rời chỗ ở. Muốn về phải thanh toán chi phí.'),
('D-new','high','Bạn nộp thêm khoản bảo chứng, hệ thống sẽ hoàn lại tiền vốn.'),
('D-valid','not_high','Bạn thanh toán tiền chiếc bàn trước để nhận hàng nhé.'),
('D-missing','not_high','Bạn cần hoàn tất nhiệm vụ 3 triệu mới được rút toàn bộ.'),
('D-warning','not_high','Cảnh báo: bạn nộp thêm tiền bảo chứng, hệ thống sẽ trả cả vốn lẫn tiền bảo chứng.'),
('D-two','not_high','Đơn A: Tôi đã nộp 1 triệu, nhưng không rút được.','Đơn B: Bạn hoàn tất nhiệm vụ 3 triệu mới được rút toàn bộ.'),
('D-update','high','Bạn hoàn tất nhiệm vụ 3 triệu mới được rút toàn bộ.','Tôi đã nộp 1 triệu nhưng không rút được.'),
('E-new','high','Bạn cho tôi kiểm tra từ xa. Trong khi tôi thao tác, bạn mở ngân hàng xem số dư.'),
('E-valid','not_high','Bạn cài ứng dụng hỗ trợ và đọc mã kết nối để tôi kiểm tra từ xa. Không mở ngân hàng trong lúc hỗ trợ.'),
('E-missing','not_high','Bạn mở ứng dụng ngân hàng xem số dư nhé.'),
('E-warning','not_high','Cảnh báo: kiểm tra từ xa rồi yêu cầu mở ngân hàng trong lúc tôi thao tác.'),
('E-two','not_high','Đơn A: Bạn cho tôi kiểm tra từ xa.','Đơn B: Trong lúc tôi thao tác, bạn mở ngân hàng.'),
('E-update','high','Bạn cho tôi kiểm tra từ xa.','Trong lúc tôi thao tác, bạn mở ứng dụng ngân hàng.'),
('F-new','high','Tôi có video của bạn. Nếu không chuyển tiền, tôi sẽ gửi cho bạn bè.'),
('F-valid','not_high','Đừng gửi thông tin đăng nhập. Hãy tự kiểm tra thông báo.'),
('F-missing','not_high','Tôi có ảnh của bạn.'),
('F-warning','not_high','Bài tuyên truyền: Tôi có ảnh của bạn. Chuyển tiền thì tôi xóa, còn không tôi gửi cho chỗ làm.'),
('F-two','not_high','Đơn A: Tôi có ảnh của bạn.','Đơn B: Chuyển tiền thì tôi xóa, còn không tôi gửi cho chỗ làm.'),
('F-update','high','Tôi có ảnh của bạn.','Chuyển tiền thì tôi xóa, còn không tôi gửi cho chỗ làm.'),
('G-new','high','Anh đây, máy anh hỏng. Em chuyển tiền vào tài khoản người khác nhé. Đừng gọi số cũ.'),
('G-valid','not_high','Anh đây, máy anh hỏng. Em chuyển tiền vào tài khoản người khác nhé. Đừng gọi số cũ.','Tôi đã tự gọi số cũ và xác nhận người quen cùng tài khoản nhận tiền.'),
('G-missing','not_high','Anh đây, em chuyển tiền giúp anh nhé.'),
('G-warning','not_high','Cảnh báo: Anh đây, máy anh hỏng. Em chuyển tiền vào tài khoản người khác nhé. Đừng gọi số cũ.'),
('G-two','not_high','Đơn A: Anh đây, máy anh hỏng, em chuyển tiền nhé.','Đơn B: Tài khoản người khác, đừng gọi số cũ.'),
('G-update','not_high','Anh đây, máy anh hỏng. Em chuyển tiền vào tài khoản người khác nhé. Đừng gọi số cũ.','Tôi đã tự gọi số cũ và xác nhận người quen cùng tài khoản nhận tiền.')
]


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    if (ROOT/'inputs.json').exists():raise SystemExit('Do not overwrite versioned fixtures')
    rows=[];expected=[]
    for row in CASES:
        cid,risk,*texts=row
        # Explicit user reports are separate speakers; recruiter's continued
        # instructions retain the same source. No expectation enters payload.
        messages=[{'id':'m'+str(i+1),'speaker':'user' if text.startswith(('Hợp đồng tôi','Tôi đã','Tôi không')) else 'sender','text':text} for i,text in enumerate(texts)]
        rows.append({'id':cid,'input':{'messages':messages}})
        expected.append({'id':cid,'risk':risk,'review_status':'authored_development_unreviewed'})
    for name,data in [('inputs.json',rows),('expected.json',expected)]:
        (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Created 42 development controls; no holdout modified.')


if __name__=='__main__':main()
