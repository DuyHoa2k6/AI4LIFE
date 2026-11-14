"""Bounded object, clause-scope and explicit transaction helpers, no risk rules."""
import re
from .text import normalize


def direct_object(tail):
    text=normalize(tail).text
    text=re.sub(r'^\s*(?:giup|ho)\s+(?:toi|minh|anh|chi|em|ban)\s+','',text)
    text=re.sub(r'^\s*(?:(?:duoc|du|du so|them|lai|giup|ho|mot|ca)\s+)*','',text)
    if re.match(r'(?:tien|so tien|von|so du|phi|thanh toan|khoan (?:tien|thanh toan)|\d[\d.,]*\s*(?:trieu|nghin|ngan|dong))\b',text):return 'money'
    if re.match(r'(?:phu luc|hop dong|tai lieu|huong dan|giay xac nhan|thong bao)\b',text):return 'document'
    if re.match(r'(?:hang|may|dien thoai|don hang)\b',text):return 'goods'
    if re.match(r'(?:ma|otp|day so)\b',text):return 'code'
    if re.match(r'(?:thong tin dang nhap|mat khau)\b',text):return 'credentials'
    return 'unknown'


def speech_scope(prefix,clause):
    p=normalize(prefix).text;t=normalize(clause).text
    if re.search(r'\b(?:toi|minh)\s+khong\s+yeu cau\b',p):return 'denied_request'
    condition=re.search(r'\b(?:neu|con)\s+khong\b',p)
    if condition and not re.search(r'\bthi\b',p[condition.end():]):return 'conditional_nonperformance'
    if re.search(r'\b(?:toi|minh)\s+chua\s*$',p):return 'not_yet_report'
    if re.search(r'\b(?:dung|cho|khong can|khong nen|khong duoc)\s*$',p):return 'prohibition'
    return None


def transaction_at(text,offset):
    """Nearest explicit code in this clause, including the direct object after verb."""
    n=normalize(text);point=len(normalize(text[:offset]).text)
    matches=[]
    for m in re.finditer(r'\b(?:don|giao dich|hop dong)\s+([a-z0-9_-]+)\b',n.text):
        x,y=n.original_range(*m.span(1));code=text[x:y]
        if re.fullmatch(r'[A-Z0-9_-]+',code) and (len(code)==1 or any(c.isdigit() for c in code)):
            matches.append(m)
    if not matches:return None
    stop=re.search(r'[.!?;\n]',n.text[point:]);end=point+stop.start() if stop else len(n.text)
    start=max([n.text.rfind(c,0,point) for c in '.!?;\n'])+1
    local=[m for m in matches if start<=m.start()<end]
    before=[m for m in local if m.start()<=point]
    if before:return before[-1].group()
    if local:return local[0].group()
    preceding=[m for m in matches if m.start()<point]
    return preceding[-1].group() if preceding else None
