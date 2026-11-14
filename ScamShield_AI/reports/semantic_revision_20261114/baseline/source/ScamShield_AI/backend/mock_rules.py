"""Versioned deterministic mock. No dataset, provider, URL or knowledge-store access."""
from dataclasses import dataclass
import re
import unicodedata
from .schemas import Answer, Answers, Evidence, Extraction, Finding, KEYS

VERSION = 'mock-behavior-2.0.0'


class MockLimitExceeded(Exception):
    pass


@dataclass(frozen=True)
class Rule:
    id: str
    action: str
    description: str
    pattern: str
    version: str = VERSION


RULES = (
    Rule('MR-MONEY', 'transfer_funds', 'Yêu cầu chuyển hoặc ứng tiền',
         r'\b(?:ứng\s+(?:tiền|\d[\d.,]*)|chuyển\s+(?:thêm|phí|tiền|khoản|ngay|gấp)|nộp\s+(?:thêm|trước|phí|tiền)|đóng\s+(?:phí|tiền)|đặt\s+cọc|thanh toán|nạp\s+(?:thêm|tiền))\b'),
    Rule('MR-CODE', 'share_auth_code', 'Yêu cầu giao mã xác thực',
         r'\b(?:đọc|gửi|cung cấp|chia sẻ)\b[^.!?;\n]{0,65}\b(?:otp|mã đăng nhập|mã xác thực|mã xác nhận)\b'),
    Rule('MR-CODE-LINK', 'share_auth_code', 'Yêu cầu nhập mã qua kênh được chỉ định',
         r'\bnhập\b[^.!?;\n]{0,35}\b(?:otp|mã đăng nhập|mã xác thực)\b[^.!?;\n]{0,55}\b(?:link|liên kết|trang này)\b'),
    Rule('MR-PASSWORD', 'other', 'Yêu cầu cung cấp mật khẩu',
         r'\b(?:gửi|đọc|cung cấp|cho\s+(?:tôi|mình|anh|chị))\b[^.!?;\n]{0,45}\bmật khẩu\b'),
    Rule('MR-ACCESS', 'grant_access', 'Yêu cầu chia sẻ màn hình hoặc quyền điều khiển',
         r'\b(?:bật\s+)?(?:chia sẻ màn hình|điều khiển từ xa|cấp quyền truy cập|cấp quyền trợ năng)\b'),
    Rule('MR-INSTALL', 'install_app', 'Yêu cầu cài phần mềm',
         r'\bcài(?: đặt)?\b[^.!?;\n]{0,55}\b(?:tệp|ứng dụng|phần mềm|apk)\b'),
    Rule('MR-REWARD', 'inducement', 'Lời hứa hoàn tiền hoặc trả thưởng',
         r'\b(?:hoàn\s+(?:gốc|tiền)|hoa hồng|nhận\s+(?:quà|ưu đãi)|hứa\s+hoàn)\b'),
    Rule('MR-UNLOCK', 'inducement', 'Điều kiện nộp thêm để rút hoặc mở khóa',
         r'\b(?:mở khóa|mới\s+(?:rút|lấy|nhận)(?:\s+được)?|để\s+rút|muốn\s+rút)\b'),
    Rule('MR-RECOVER', 'inducement', 'Lời hứa nhận lại tiền hoặc nhận quà',
         r'\b(?:nhận lại|lấy lại)\b[^.!?;\n]{0,45}\b(?:tiền|khoản|cọc)|\b(?:nhận|lấy)(?:\s+được)?\s+quà\b'),
    Rule('MR-SECRECY', 'inducement', 'Yêu cầu hạn chế xác minh độc lập',
         r'\b(?:đừng|không được|không nên)\s+(?:gọi|hỏi|kể|báo|nói)\b'),
    Rule('MR-URGENCY', 'inducement', 'Áp lực thời gian',
         r'\b(?:trong|chỉ còn|giữ lệnh)\s+\d+\s*(?:phút|giờ)|\b(?:ngay lập tức|nếu không[^.!?;\n]{0,35}mất)\b'),
)
COMPILED = {r.id: re.compile(r.pattern, re.I) for r in RULES}
WARNING = re.compile(r'cảnh (?:giác|báo)|bài tập|minh họa|ví dụ giả định|(?:nếu|khi) (?:gặp|nhận)|là lời dụ', re.I)
DENIAL = re.compile(r'\b(?:đừng|không(?: nên| được| cần)?|chớ|tránh|tuyệt đối không)\b', re.I)
REPORTED = re.compile(r'\b(?:họ|người đó|người lạ)\s+(?:nhắn|bảo|nói|yêu cầu)|\b(?:tôi|mình|em)\s+đã\b', re.I)
SELF_SERVICE = re.compile(r'tự nhập|ứng dụng chính thức|không (?:chia sẻ|cung cấp|gửi|đọc)', re.I)
BENEFIT = re.compile(r'hoa hồng|hoàn (?:gốc|tiền)|nhận (?:quà|ưu đãi)|(?:nhận|lấy) lại[^.!?;\n]{0,45}(?:tiền|cọc)|(?:nhận|lấy)(?: được)? quà|rút|mở khóa', re.I)
FINANCE = re.compile(r'tiền|phí|cọc|gốc|hoa hồng|rút|ví cá nhân|tài khoản cá nhân', re.I)
CONNECTOR = re.compile(r'\b(?:để|thì|xong|rồi|muốn|sẽ|mới|hứa)\b', re.I)


def norm(text):
    # Matching only: never use this string for public evidence offsets.
    return unicodedata.normalize('NFC', text).lower()


def unknown():
    return Answer(status='unknown', text='Chưa đủ căn cứ.', evidence_refs=[])


def segments(text):
    """Keep quotes and decimal money intact; split sentences and explicit contrast clauses."""
    start, closing = 0, []
    pairs = {'“': '”', '‘': '’', '"': '"'}
    spans = []
    for i, char in enumerate(text):
        if closing and char == closing[-1]:
            closing.pop()
        elif char in pairs:
            closing.append(pairs[char])
        decimal = char == '.' and i > 0 and i + 1 < len(text) and text[i-1].isdigit() and text[i+1].isdigit()
        if (char in '.!?;\n' and not closing and not decimal):
            spans.append((start, i + 1))
            start = i + 1
    if start < len(text):
        spans.append((start, len(text)))
    for a, b in spans:
        # Contrast marks a new instruction even inside an otherwise cautionary sentence.
        cursor = a
        for match in re.finditer(r',\s*(?:nhưng|tuy nhiên|còn)\s+', text[a:b], re.I):
            yield from _trim(text, cursor, a + match.start())
            cursor = a + match.end()
        yield from _trim(text, cursor, b)


def _trim(text, a, b):
    while a < b and text[a].isspace():
        a += 1
    while b > a and text[b-1].isspace():
        b -= 1
    if a < b:
        yield a, b


def role_for(text, action, match_start):
    if WARNING.search(text):
        return 'quoted_warning'
    # Negation scopes locally, rather than suppressing unrelated subsequent clauses.
    prefix = text[:match_start].rsplit(',', 1)[-1][-35:]
    coercion = re.search(r'nếu không[^.!?;]{0,70}(?:sẽ|thì|mất)', text)
    if DENIAL.search(prefix) and not coercion and 'không phải' not in prefix:
        return 'denial'
    if REPORTED.search(text) or '“' in text or '"' in text or text.rstrip().endswith('?'):
        return 'unknown'
    if action == 'inducement':
        return 'claim'
    return 'request'


def extract(request):
    findings = []
    for msg in request.as_messages():
        for start, end in segments(msg.text):
            quote = msg.text[start:end]
            text = norm(quote)
            for rule in RULES:
                match = COMPILED[rule.id].search(text)
                if not match:
                    continue
                role = role_for(text, rule.action, match.start())
                # A password mention or self-service code entry alone is not a disclosure request.
                if rule.id == 'MR-PASSWORD' and SELF_SERVICE.search(text):
                    role = 'denial'
                findings.append(Finding(id=f'{rule.id}:{len(findings)+1}', action=rule.action,
                    description=rule.description, speaker=msg.speaker, speech_role=role,
                    evidence=[Evidence(message_id=msg.id, quote=quote, start=start, end=end)],
                    inference=unknown()))
                if len(findings) > 50:
                    raise MockLimitExceeded()
    return Extraction(answers=Answers(**{k: unknown() for k in KEYS}), findings=findings)


def _linked(action, support, messages):
    """Conservative relation heuristic, not a semantic claim of causality."""
    if action.speaker != support.speaker:
        return False
    a, b = action.evidence[0], support.evidence[0]
    index = {m.id: i for i, m in enumerate(messages)}
    ai, bi = index[a.message_id], index[b.message_id]
    topics = {'rent': r'thuê nhà|tiền nhà', 'invoice': r'hóa đơn',
              'recovery': r'tiền.{0,20}(?:mất|lừa)|lấy lại|hồ sơ',
              'task': r'hoa hồng|nhiệm vụ|đánh giá sản phẩm',
              'investment': r'đầu tư|lợi nhuận|bảo chứng', 'gift': r'quà|hải quan'}
    def tags(quote):
        return {k for k, pattern in topics.items() if re.search(pattern, norm(quote))}
    action_topics, support_topics = tags(a.quote), tags(b.quote)
    if action_topics and support_topics and not action_topics & support_topics:
        return False
    intervening = '\n'.join(m.text for m in messages[min(ai, bi):max(ai, bi)+1])
    if re.search(r'không liên quan|chuyện khác|chủ đề khác', norm(intervening)):
        return False
    if a.message_id == b.message_id:
        if a.start == b.start and a.end == b.end:
            return bool(CONNECTOR.search(norm(a.quote)) and BENEFIT.search(norm(b.quote)))
        between = messages[ai].text[min(a.start, b.start):max(a.end, b.end)]
        return (len(between) <= 500 and len(list(segments(between))) <= 2 and
                bool(CONNECTOR.search(norm(b.quote))) and bool(BENEFIT.search(norm(b.quote))))
    if abs(ai - bi) > 2:
        return False
    # Other speakers between turns may add context, but cannot supply the inducement.
    if action.speaker == 'unknown':
        return False
    if not (FINANCE.search(norm(a.quote)) and BENEFIT.search(norm(b.quote)) and CONNECTOR.search(norm(b.quote))):
        return False
    return True


def assess(findings, messages):
    requests = [f for f in findings if f.speech_role == 'request' and f.action != 'inducement']
    supports = [f for f in findings if f.action == 'inducement' and f.speech_role == 'claim']
    # Urgency/secrecy alone do not establish the financial relation required for high.
    supports = [f for f in supports if BENEFIT.search(norm(f.evidence[0].quote))]
    links = []
    for action in requests:
        for support in supports:
            if _linked(action, support, messages):
                links.append((action, support))
    credential = [f for f in requests if f.action == 'share_auth_code' or (
        f.action == 'other' and 'mật khẩu' in norm(f.evidence[0].quote))]
    if credential or links:
        return 'high', links, []
    if requests:
        return 'suspicious', links, []
    questions = missing_questions(findings, messages)
    return ('need_context' if questions else 'clear'), links, questions


def missing_questions(findings, messages):
    # Only active clauses: an educational warning containing these words should stay clear.
    text = '\n'.join(m.text for m in messages)
    clauses = [norm(text[a:b]) for a, b in segments(text)]
    clauses = [s for s in clauses if not WARNING.search(s) and not DENIAL.search(s)]
    joined = '\n'.join(clauses)
    if any(f.speech_role == 'unknown' and f.action != 'inducement' for f in findings):
        return ['Đây là yêu cầu người gửi muốn bạn thực hiện, hay nội dung được trích lại để trao đổi?']
    if re.search(r'bị treo|chưa rút được|phí (?:xử lý|mở) hồ sơ', joined):
        return ['Họ có yêu cầu trả thêm phí hoặc chuyển tiền để nhận lại hay rút khoản tiền không?']
    if 'xác minh tài khoản' in joined:
        return ['Họ yêu cầu xác minh qua kênh nào và thực hiện thao tác gì?']
    if re.search(r'đổi tài khoản|tài khoản mới', joined):
        return ['Thông báo đổi tài khoản đã được xác nhận qua đầu mối nhà cung cấp mà bạn biết từ trước chưa?']
    if re.search(r'(?:gửi|có|nhận)(?: một)? tệp|mở tệp', joined):
        return ['Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì?']
    if re.search(r'(?:lấy|nhận|tìm) lại.{0,35}(?:tiền|khoản)', joined):
        return ['Dịch vụ có yêu cầu trả phí trước hoặc cung cấp dữ liệu nhạy cảm không?']
    return []


def catalog():
    return [{'id': r.id, 'version': r.version, 'action': r.action,
             'description': r.description, 'pattern': r.pattern} for r in RULES]
