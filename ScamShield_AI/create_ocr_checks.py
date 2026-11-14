"""Render deterministic OCR fixtures with actual Vietnamese glyphs, not real-user data."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
def main():
    directory=ROOT/'fixtures/ocr_checks';directory.mkdir(parents=True,exist_ok=False)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',38)
    cases=[
        ('O1','Yêu cầu chuyển phí', ['Chuyển trước 500 nghìn cho tôi.', 'Đó là điều kiện nhận lại 5 triệu tiền cọc.'], '', 'high'),
        ('O2','Ảnh lời dụ được bài viết cảnh báo', ['Nạp tiền để nhận hoa hồng.'], 'Bài viết cảnh báo: ảnh dưới đây trích lời dụ của kẻ gian để phòng tránh. Đừng làm theo, tôi không yêu cầu người đọc chuyển tiền.', 'clear'),
        ('O3','Nội dung bình thường', ['Tôi tự nhập mã trong ứng dụng ngân hàng.', 'Tôi không gửi mã cho người khác.'], '', 'clear'),
        ('O4','Ảnh không có chữ', [], '', 'no_text')]
    refs=[]
    for cid,name,lines,dom,expected in cases:
        image=Image.new('RGB',(1300,300),'white');draw=ImageDraw.Draw(image)
        for i,line in enumerate(lines):draw.text((35,45+i*75),line,font=font,fill='black')
        image.save(directory/f'{cid}.png')
        refs.append({'id':cid,'name':name,'dom':dom,'expected_text':'\n'.join(lines),'expected_status':expected})
    (directory/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Rendered four Vietnamese PNG OCR fixtures.')

if __name__=='__main__':main()
