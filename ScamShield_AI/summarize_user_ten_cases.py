"""Explain actual API outputs separately from manual observations; never change predictions."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent/'reports/user_ten_cases_20261110'
LABELS={'clear':'🟢 clear','need_context':'🔵 need_context','suspicious':'🟠 suspicious','high':'🔴 high'}
NOTES={
 'U01':'Nội dung nêu chưa thấy tiền nhưng yêu cầu giao tài sản trước, kèm sức ép tài xế chờ. Đây là dấu hiệu cần được rà kỹ về khả năng mất hàng. Chỉ có lời nhắn nhắc ảnh biên lai, không có ảnh thực để OCR hoặc xác minh giao dịch.',
 'U02':'Câu giao OTP nằm trong lời nhắc phòng tránh có “đừng làm theo”. Cần phân biệt lời trích cảnh báo với yêu cầu trực tiếp.',
 'U03':'Có nói hoàn cọc sau một bước nhưng chưa nêu thao tác cụ thể. Không được tự suy bước đó là chuyển tiền hoặc giao mã.',
 'U04':'Yêu cầu chia sẻ màn hình và mở phần số dư ngân hàng liên quan dữ liệu tài chính; đọc cùng lời duyệt hoàn cọc và đúng người nói. Chưa có căn cứ nói đã có chuyển tiền hoặc chiếm quyền thực tế.',
 'U05':'Có thay đổi tài khoản nhận tiền qua chat và yêu cầu chuyển trước khi gọi đầu mối hợp đồng. Cần xét việc trì hoãn xác minh, không chỉ riêng từ khóa chuyển khoản.',
 'U06':'Người bán nói đã tự kiểm tra đúng tài khoản và đủ tiền. Đây là bối cảnh khác ca U01; hệ thống chỉ nhận lời khai trong hội thoại, không kết nối ngân hàng để xác minh tiền thật.',
 'U07':'Người nhận xác định dãy số là mã đăng nhập tài khoản của mình; người gửi vẫn yêu cầu đọc mã để giải ngân. Cần nối ba tin và không nhầm với tự nhập mã trong ứng dụng.',
 'U08':'Chỉ có trạng thái chờ kiểm tra, chưa có yêu cầu hành động. Không có căn cứ tự tạo phí bổ sung hoặc yêu cầu OTP.',
 'U09':'Tự nhận phụ trách hỗ trợ phường không xác minh được danh tính. Xin hai mặt căn cước và chân dung qua chat để giữ suất có rủi ro lộ dữ liệu định danh.',
 'U10':'Nội dung chuyển từ hoa hồng ban đầu sang ứng tiền và nộp thêm để mở khóa. Cần nối quan hệ nộp tiền trước với khả năng rút tiền được hứa.'
}

if __name__=='__main__':
    inputs=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8'))
    records=json.loads((ROOT/'predictions.json').read_text(encoding='utf-8'))
    final={r['id']:r for r in records}
    summary=json.loads((ROOT/'summary.json').read_text(encoding='utf-8'))
    text=['# Kết quả chạy đúng 10 trường hợp người dùng cung cấp','',
          'Đây là phản hồi thực của POST /api/analyze qua ASGI TestClient và provider cấu hình thật. Không dùng nhãn mục tiêu, không sửa prompt/quy tắc trong lượt chạy, không thay kết quả bằng nhận định thủ công. Phần “Nhận xét rà soát” là đối chiếu riêng với đầu vào.',
          '', '| Ca | Tình huống | Kết quả cuối | Giây |', '| --- | --- | --- | --- |']
    for case in inputs:
        r=final.get(case['id']);b=r.get('response',{}) if r else {}
        label=LABELS.get(b.get('risk_status'),'Chưa kiểm tra được' if r else 'Chưa chạy')
        text.append(f"| {case['id']} | {case['name']} | {label} | {r['api_ms']/1000:.2f} |" if r else f"| {case['id']} | {case['name']} | {label} | — |")
    for case in inputs:
        cid=case['id'];r=final.get(cid);b=r.get('response',{}) if r else {};p=case['input']
        text+=['','## '+cid+' — '+case['name'],'','**Đầu vào:**','']
        if 'text' in p:text+=['> '+p['text']]
        else:text+=['> '+m['speaker']+': '+m['text'] for m in p['messages']]
        text+=['','**Kết quả API:** '+LABELS.get(b.get('risk_status'),b.get('code','Chưa chạy')),
               '', '**Nhận xét rà soát:** '+NOTES[cid]]
        if r and r['http_status']==200:
            text+=['','**Tóm tắt backend:** '+b['summary']]
            quotes=[e['quote'] for f in b.get('findings',[]) for e in f.get('evidence',[])]
            if quotes:text+=['','**Trích dẫn đã giữ trong kết quả:**']+['- “'+q+'”' for q in dict.fromkeys(quotes)]
            if b.get('follow_up_questions'):text+=['','**Câu hỏi thực tế hệ thống trả:**']+['- '+q for q in b['follow_up_questions']]
            a=b.get('analysis',{})
            text+=['',f"Kiểm tra: {r['evidence_check']['exact_quotes']}/{r['evidence_check']['quote_count']} quote khớp; quan hệ rủi ro được giữ: {a.get('grounded_relation_count',0)}; xung đột quan sát: {a.get('rule_conflicts',0)}; hint regex đã rà: {a.get('rule_hints_reviewed',0)}."]
        elif r:text+=['','API lỗi; không có risk_status để coi là clear hoặc need_context.']
        attempts=[x for x in records if x['id']==cid]
        text+=['', '**Các lần chạy:** '+', '.join(f"lần {x['attempt']}: HTTP {x['http_status']}, {x['response'].get('risk_status',x['response'].get('code','error'))}, {x['api_ms']/1000:.2f}s" for x in attempts)]
    text+=['','## Phạm vi và số liệu','',json.dumps(summary,ensure_ascii=False,indent=2),
           '', 'Không đo thời gian từ lúc bấm gửi ở trình duyệt/extension. Không có ảnh biên lai hoặc ảnh căn cước thực; không chạy OCR trên các câu nhắc đến ảnh. Quote khớp không tự chứng minh đúng ý nghĩa. Các thông tin người nói tự khai không được xác nhận ngoài đời. Không tính độ chính xác vì không có bộ nhãn độc lập.',
           '', 'Lệnh đã chạy: `python run_user_ten_cases.py`; xuất báo cáo: `python summarize_user_ten_cases.py`. Output không ghi đè; đổi OUT nếu cần một lượt chạy mới.']
    (ROOT/'CASES.md').write_text('\n'.join(text),encoding='utf-8')
    print('Wrote report for '+str(len(inputs))+' cases.')
