"""Human review notes + reproducible tables for the four-state probe run."""
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports/four_states_20261110'
FIXTURES=ROOT/'fixtures/four_states_20261110'
NOTES={
 'H01':'Yêu cầu giao OTP cho người khác để họ đăng nhập là hành vi trực tiếp đe dọa tài khoản; không phải người dùng tự nhập mã trong ứng dụng của mình.',
 'H02':'Có số tiền phí cụ thể và điều kiện trả phí trước khi nhận thưởng. Mức high cần dựa trên liên hệ giữa khoản chuyển và phần thưởng, không chỉ từ “chuyển”.',
 'H03':'Đổi tên phí thành “tiền đồng bộ” và mở đầu bằng “không thu phí” không xóa yêu cầu đưa 900 nghìn sang ví người gửi trước khi nhận 18 triệu.',
 'H04':'Cùng một người tự nhận cán bộ trợ cấp yêu cầu cài ứng dụng và giao quyền điều khiển làm điều kiện nhận 8 triệu. Phải nối đúng các tin của nguoi_la, không gán câu hỏi của nguoi_dung thành lời dụ.',
 'N01':'Chỉ thông báo lịch và đề nghị mang sổ; không có yêu cầu tiền, mã, quyền truy cập hoặc lợi ích đáng ngờ. Nếu lỗi provider, chưa thể coi đó là clear.',
 'N02':'Câu phương ngữ là nhắc trả khoản vay. Bối cảnh khai báo xác nhận mục đích và khoản 50 nghìn đã có, không phải nộp phí để được nhận lợi ích mới. Biết người gửi không miễn trừ mọi rủi ro, nhưng mục đích khoản trả phải được xét.',
 'N03':'Câu yêu cầu mật khẩu/OTP nằm trong bài cảnh báo và có phủ định rõ. Gán nó thành yêu cầu trực tiếp sẽ là cảnh báo nhầm.',
 'N04':'Người dùng mô tả tự nhập OTP trong ứng dụng đã biết, không giao mã cho người khác. Phải phân biệt thao tác tự xác nhận với yêu cầu tiết lộ mã.',
 'C01':'Chưa biết “một bước” là gì. Không được tự đoán đó là chuyển phí hoặc cung cấp mã; cần hỏi thao tác và kênh thực hiện.',
 'C02':'Chỉ có yêu cầu chuyển khoản, thiếu người nhận, mục đích và giao dịch liên quan. Chưa đủ để khẳng định lừa đảo hoặc coi là giao dịch bình thường.',
 'C03':'Chưa xác định “cái đó” là tài liệu, tiền, OTP hay thứ khác; việc “hoàn tất” cũng không có đối tượng. Cần hỏi rõ, không mặc định đó là mã bí mật.',
 'C04':'Có cấu trúc điều kiện nhưng hành động “bước kia” chưa được định danh. Cấu trúc điều kiện đơn thuần không đủ để nâng high.',
 'S01':'Yêu cầu giao quyền điều khiển đã rõ và đáng lo, nhưng câu “chưa giải thích dùng quyền này để làm gì” không nêu lợi ích hay điều kiện nhận lợi ích. Mục tiêu chốt trước là suspicious; high do ghép câu thiếu mục đích thành inducement là nâng mức thiếu căn cứ theo chính sách hiện hành.',
 'S02':'Yêu cầu cài APK qua tin riêng đã rõ, nguồn và mục đích chưa rõ. Mục tiêu là suspicious và hỏi thêm nguồn cài; không tự kết luận ứng dụng độc hại, không tự tạo quan hệ “cài để nhận thưởng”.',
 'S03':'Nhãn youtube.com dẫn tới một hostname khác. Đây là dấu hiệu kỹ thuật đi cùng yêu cầu đăng nhập, đủ cần xác minh; đích .invalid bị chặn mạng, chưa chứng minh một trang phishing đang hoạt động.',
 'S04':'Có yêu cầu chuyển kênh và giữ kín, chưa có tiền/mã/quyền. Mục tiêu suspicious là thận trọng với hành vi cô lập; need_context có thể phản ánh chưa nhận ra mục đích, nhưng khác nhãn mục tiêu đã khóa và phải báo riêng, không sửa nhãn sau chạy.'
}
LABELS={'high':'🔴 Rủi ro cao','suspicious':'🟠 Đáng ngờ','need_context':'🔵 Cần thêm thông tin','clear':'🟢 Chưa ghi nhận dấu hiệu','error':'Chưa kiểm tra được','not_run':'Chưa chạy'}
OBSERVED={
 'S01':'Rà đầu ra thật: Gemini gán câu “Tôi chưa giải thích dùng quyền này để làm gì” thành inducement và tạo risk_link từ quyền điều khiển tới câu này. Backend chấp nhận quote/quan hệ đã khai nên nâng high. Quote đúng chữ nhưng phân loại ý nghĩa và quan hệ không có căn cứ lợi ích rõ.',
 'S02':'Rà đầu ra thật: Gemini đã nhận ra yêu cầu cài APK; câu chưa cung cấp nhà phát hành/lý do được Gemini coi là claim. Quy tắc lại trích chính câu đó thành install_app request. rule_conflicts=1 khiến backend giữ need_context, dù bất định của Gemini chỉ là mục đích/danh tính.',
 'N04':'Rà đầu ra thật: Gemini cuối trả needs_context=false, không có risk_link hay finding bất định; nội dung là claim và denial. Tuy nhiên regex trích câu chứa “đã cài từ trước” thành install_app request. rule_conflicts=1 làm backend trả need_context. Đây là xung đột trích xuất quy tắc, không phải Gemini khẳng định người dùng đang giao OTP.',
 'S04':'Rà đầu ra thật: hành động chuyển kênh/giữ kín được nhận ra là other/request, nhưng mục đích chưa rõ. Với action=other, backend vẫn giữ needs_context; ngoại lệ bất định danh tính/mục đích không chặn suspicious hiện chỉ áp dụng rõ cho cài ứng dụng/cấp quyền. Đây là khác biệt ngưỡng chính sách cần thống nhất, không đủ kết luận trường hợp này chắc chắn lừa đảo.'
}

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def flat(text):return str(text).replace('|','／').replace('\n',' ')

if __name__=='__main__':
    samples=load(FIXTURES/'inputs.json');refs={r['id']:r for r in load(FIXTURES/'expected.json')['cases']}
    primary=load(OUT/'live/predictions.json');initial={r['id']:r for r in primary}
    final=dict(initial)
    retry_dir=OUT/'retry_errors'
    if (retry_dir/'predictions.json').exists():final.update({r['id']:r for r in load(retry_dir/'predictions.json') if r.get('executed')})
    lines=['# Kiểm thử bốn trạng thái — 10/11/2026','',
      '16 ca tổng hợp mới, 4 mục tiêu cho mỗi trạng thái. Nhãn tham chiếu được viết riêng trước chạy; không chỉnh prompt/model/quy tắc trong phiên đánh giá. Không đọc holdout hoặc đưa nhãn vào mô hình.',
      '', 'Chạy API qua ASGI TestClient và HTTP Gemini thật, cấu hình/phiên bản/hash ở từng lock.json. Đây là kiểm thử chức năng có chủ đích, không phải độ chính xác độc lập trên dữ liệu người dùng thật.',
      '', '| Ca | Tình huống | Mục tiêu trước chạy | Kết quả cuối | Giây |', '| --- | --- | --- | --- | --- |']
    reviews=[]
    for sample in samples:
        cid=sample['id'];record=final[cid];body=record.get('response',{})
        status=body.get('risk_status') if record.get('http_status')==200 else 'error' if record.get('executed') else 'not_run'
        ref=refs[cid];match=status in ref['acceptable']
        lines.append(f"| {cid} | {sample['name']} | {ref['target_status']} | {LABELS[status]}{' — khác mục tiêu' if not match else ''} | {record.get('api_ms',0)/1000:.2f} |")
        reviews.append({'id':cid,'target':ref['target_status'],'final_status':status,'target_match':match,'interpretation':NOTES[cid],
                        'first_http_status':initial[cid].get('http_status'),'final_http_status':record.get('http_status'),
                        'retried':record is not initial[cid]})
    lines+=['','## Giải thích từng ca','']
    for sample,review in zip(samples,reviews):
        cid=sample['id'];record=final[cid];body=record.get('response',{});p=sample['input']
        lines+=['### '+cid+' — '+sample['name'],'', '**Đầu vào:**']
        if 'text' in p:lines+=['', '> '+p['text'].replace('\n','\n> ')]
        else:lines+=['']+['> '+m['speaker']+': '+m['text'] for m in p['messages']]
        if p.get('context'):lines+=['','**Bối cảnh:** '+p['context']]
        if p.get('links'):lines+=['','**Đích liên kết đính kèm:** '+p['links'][0]['url']]
        lines+=['','**Kết quả thực tế:** '+LABELS[review['final_status']]+f"; HTTP {record.get('http_status')}; {record.get('api_ms',0)/1000:.2f} giây.", '',NOTES[cid]]
        if cid in OBSERVED:lines+=['',OBSERVED[cid]]
        if review['retried']:lines+=['',f"Lần đầu HTTP {review['first_http_status']}; kết quả trên thuộc lần kiểm tra lại riêng. Không xóa lỗi của lượt đầu."]
        if review['final_status']=='error':lines+=['','**Lỗi:** '+body.get('code','unknown')+'. Đây là lỗi thực thi, không phải kết quả need_context hoặc clear.']
        else:
            quotes=[e['quote'] for f in body.get('findings',[]) for e in f.get('evidence',[])]
            if quotes:lines+=['','**Trích dẫn hệ thống giữ:**']+['- “'+q+'”' for q in list(dict.fromkeys(quotes))[:4]]
            if body.get('follow_up_questions'):lines+=['','**Câu hỏi hệ thống trả:**']+['- '+q for q in body['follow_up_questions']]
        lines+=['']
    (OUT/'CASES.md').write_text('\n'.join(lines),encoding='utf-8')
    (OUT/'MANUAL_REVIEW.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
    successful=[r for r in final.values() if r.get('http_status')==200]
    final_summary={'final_distribution':dict(Counter(r['response']['risk_status'] for r in successful)),
                      'final_successful':len(successful),'matches':sum(r['target_match'] for r in reviews),
                      'mismatches':[r['id'] for r in reviews if not r['target_match']],
                      'first_attempt_successful':sum(r.get('http_status')==200 for r in primary),
                      'retried_cases':[r['id'] for r in reviews if r['retried']],
                      'all_first_and_retry_executions':len(primary)+(len(load(retry_dir/'predictions.json')) if (retry_dir/'predictions.json').exists() else 0)}
    (OUT/'final_summary.json').write_text(json.dumps(final_summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(final_summary))
