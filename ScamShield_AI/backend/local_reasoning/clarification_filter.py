"""Local relevance filtering, not truth detection or a general chat model."""
import re
from pydantic import Field
from ..schemas import Strict
from ..local_observation.text import normalize


class FilteredAnswer(Strict):
    status: str
    relevant_text: str
    ignored_count: int
    topics: list[str] = Field(default_factory=list)
    related_questions: list[str] = Field(default_factory=list)


TOPICS={
 'payment':r'tien|thanh toan|chuyen khoan|nhan du|tra no|so du|hoa hong|bao chung|rut|tien coc|phi|\bmua\b|ky quy|bao dam|goi xac thuc',
 'code':r'\botp\b|ma dang nhap|ma xac thuc|ma don hang|day so|sau so|mat khau',
 'identity':r'nguoi gui|nguoi mua|nguoi ban|anh trai|chi gai|me toi|bo toi|xac minh|da goi|nguoi quen|cong an|danh tinh',
 'documents':r'giay to|can cuoc|ho chieu|lay lai|giu giay',
 'access':r'ung dung|chia se man hinh|dieu khien|cap quyen|ngan hang',
 'safety':r'giu lai|roi di|tu do|de doa|ep lam|gia dinh|hop dong|viec lam|dia diem|nguoi moi|lien lac'}


def filter_answer(text):
    parts=[p.strip() for p in re.split(r'[\n.!?;]+|,(?=\s*(?:nhan tien|toi |minh |thoi tiet|hom nay))',text) if p.strip()]
    accepted=[];topics=set();ignored=0;questions=[]
    for part in parts:
        normalized=normalize(part).text
        if re.search(r'bo qua quy tac|doi ket qua thanh|system prompt|ignore.*instruction|in khoa api',normalized):ignored+=1;continue
        found={name for name,pattern in TOPICS.items() if re.search(pattern,normalized)}
        if re.search(r'lam gi|co nen|nen xu ly|cach xac minh',normalized) or (found and re.search(r'tai sao|vi sao|nhu the nao',normalized)):
            questions.append(part);topics.update(found);continue
        if found:accepted.append(part);topics.update(found)
        else:ignored+=1
    status='mixed' if accepted and (ignored or questions) else 'accepted' if accepted else 'question' if questions else 'off_topic'
    return FilteredAnswer(status=status,relevant_text='\n'.join(accepted),ignored_count=ignored,topics=sorted(topics),related_questions=questions)
