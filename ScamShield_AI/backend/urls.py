"""Offline URL observations. Never resolve DNS, open a URL or claim malware reputation."""
from functools import lru_cache
import ipaddress
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit
import idna
import tldextract
from rapidfuzz.distance import DamerauLevenshtein
from .schemas import UrlAnalysis, UrlSignal

ROOT=Path(__file__).resolve().parent.parent/'knowledge/url'
EXTRACT=tldextract.TLDExtract(cache_dir=None,suffix_list_urls=(),include_psl_private_domains=True)
URL_PATTERN=re.compile(r'https?://[^\s<>"“”]+|www\.[^\s<>"“”]+',re.I)
STRONG={'display_target_mismatch','brand_in_subdomain','lookalike_reference_domain','unicode_confusable_reference'}


@lru_cache(maxsize=1)
def reference_data():
    data=json.loads((ROOT/'domain_references.json').read_text(encoding='utf-8'))
    return [r for r in data['references'][:200] if r.get('status')=='documented_reference']


@lru_cache(maxsize=1)
def confusables():
    mapping={}
    path=ROOT/'confusables.txt'
    if not path.exists():return mapping
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        row=line.split('#',1)[0].strip()
        if not row:continue
        source,target,*_=row.split(';')
        codes=source.split()
        if len(codes)==1:mapping[chr(int(codes[0],16))]=''.join(chr(int(c,16)) for c in target.split())
    return mapping


def skeleton(value):
    return unicodedata.normalize('NFD',''.join(confusables().get(c,c) for c in unicodedata.normalize('NFD',value.lower())))


def parse(value):
    if (not value or any(c.isspace() or unicodedata.category(c).startswith('C') for c in value)
            or '\\' in value):raise ValueError('invalid URL')
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',value) and '://' not in value:raise ValueError('unsupported scheme')
    # Only bare hostname input may infer https; explicit foreign schemes are not opened.
    normalized=value if '://' in value else 'https://'+value
    p=urlsplit(normalized)
    if p.scheme.lower() not in ('http','https') or not p.hostname:raise ValueError('invalid URL')
    host=p.hostname.rstrip('.')
    try: host=ipaddress.ip_address(host).compressed
    except ValueError:host=idna.encode(host,uts46=True,std3_rules=True).decode('ascii').lower()
    if not host or len(host)>253:raise ValueError('invalid host')
    port=p.port
    unicode_host=idna.decode(host) if ':' not in host else host
    ext=EXTRACT(host)
    registered=ext.top_domain_under_public_suffix or None
    netloc=('['+host+']' if ':' in host else host)+((':'+str(port)) if port is not None else '')
    # Hidden href secrets (userinfo/query/fragment/path) do not go to the model/UI.
    safe_url=p.scheme.lower()+'://'+netloc+'/'
    return p,host,unicode_host,registered,ext,safe_url


def model_input(request):
    raw=request.model_dump(exclude_none=True)
    for link in raw.get('links',[]):
        try:link['url']=parse(link['url'])[-1]
        except (ValueError,idna.IDNAError):link['url']='[invalid_or_unsupported_url]'
    return raw


def collect(request):
    records=[];occupied={};ids=set()
    for link in request.links:
        record=link.model_dump();record['label_status']='none'
        if link.display_text:
            text=next(m.text for m in request.as_messages() if m.id==link.message_id)
            start=link.start
            if start is None and text.count(link.display_text)==1:start=text.index(link.display_text)
            record['label_status']='grounded' if start is not None else 'ambiguous'
            if start is not None:occupied.setdefault(link.message_id,[]).append((start,start+len(link.display_text)))
        records.append(record);ids.add(link.id)
    ocr_ids={r.message_id for r in request.ocr_sources}
    for i,msg in enumerate(request.as_messages()):
        for j,match in enumerate(URL_PATTERN.finditer(msg.text)):
            if len(records)>=20:return records
            if any(match.start()<end and match.end()>start for start,end in occupied.get(msg.id,[])):continue
            url=match.group().rstrip('.,;:!?)]}。')
            if len(url)>2048:continue
            if any(r['message_id']==msg.id and r['url']==url for r in records):continue
            lid=f'auto-url-{i}-{j}'
            while lid in ids:lid+='a'
            ids.add(lid)
            records.append({'id':lid,'message_id':msg.id,'url':url,'display_text':url,
                            'origin':'ocr' if msg.id in ocr_ids else 'text','label_status':'grounded'})
    return records


def analyze_urls(request):
    result=[]
    for link in collect(request):
        signals=[]
        def add(code,detail,level='review'):
            if code not in {s.code for s in signals}:signals.append(UrlSignal(code=code,level=level,detail=detail))
        base=dict(link_id=link['id'],message_id=link['message_id'],origin=link['origin'],label_status=link['label_status'])
        try:p,host,uhost,registered,ext,safe=parse(link['url'])
        except (ValueError,idna.IDNAError):
            add('invalid_url','Không phân tích được URL HTTP/HTTPS theo bộ kiểm tra cấu trúc.')
            result.append(UrlAnalysis(**base,status='invalid',display_url='[URL không hợp lệ hoặc không hỗ trợ]',signals=signals));continue
        if p.username is not None or p.password is not None:add('userinfo_present','URL có phần trước @; hostname đích là '+host)
        if p.scheme.lower()=='http':add('http_transport','URL dùng HTTP; chưa kiểm tra nội dung hoặc độ an toàn trang.','info')
        if p.port is not None and p.port not in (80,443):add('nonstandard_port','URL có cổng khác 80/443.','info')
        try:ipaddress.ip_address(host);add('ip_literal','Địa chỉ đích dùng IP trực tiếp.','info')
        except ValueError:pass
        if not registered:add('unknown_public_suffix','Chưa xác định miền đăng ký trong PSL đã đóng gói.','info')
        if any(label.startswith('xn--') for label in host.split('.')):add('punycode_hostname','Tên miền có dạng Punycode; không tự chứng minh độc hại.','info')
        scripts={unicodedata.name(c,'').split()[0] for c in uhost if c.isalpha()}
        if len(scripts & {'LATIN','CYRILLIC','GREEK'})>1:add('mixed_script_hostname','Hostname pha các hệ chữ Latin/Cyrillic/Greek; cần đối chiếu.','info')
        label=link['display_text'].strip()
        if link['label_status']=='grounded' and re.fullmatch(r'(?:https?://|www\.)?[^\s/]+\.[^\s]+',label):
            try:
                _,shown,_,shown_reg,_,_=parse(label)
                if shown.removeprefix('www.')!=host.removeprefix('www.') and (not registered or shown_reg!=registered):
                    add('display_target_mismatch','Tên miền hiển thị '+shown+' khác tên miền đích '+host)
            except (ValueError,idna.IDNAError):pass
        reference=None
        for ref in reference_data():
            canonical=ref['domain']
            if registered==canonical:reference=canonical;continue
            canonical_label=EXTRACT(canonical).domain
            if canonical_label in ext.subdomain.split('.'):
                add('brand_in_subdomain','Tên tham chiếu '+canonical+' chỉ xuất hiện ở phần miền phụ của '+host)
            if registered:
                if skeleton(idna.decode(registered))==skeleton(canonical):
                    add('unicode_confusable_reference','Tên miền có skeleton ký tự giống '+canonical+', không phải đối chiếu vụ lừa đảo.')
                distance=DamerauLevenshtein.distance(ext.domain,canonical_label)
                if min(len(ext.domain),len(canonical_label))>=5 and 0<distance<=1:
                    add('lookalike_reference_domain','Tên miền gần giống '+canonical+' theo khoảng cách ký tự, không phải xác suất lừa đảo.')
        result.append(UrlAnalysis(**base,status='parsed',display_url=safe,hostname=host,unicode_hostname=uhost,
                                  registered_domain=registered,reference_domain=reference,signals=signals))
    return result


def apply_url_evidence(response, reviewed, analyses, request):
    response.url_analysis=analyses
    if analyses and response.schema_version!='1.9':response.schema_version='1.8'
    if reviewed is None:return response
    observed={a.link_id:a for a in analyses};findings={f.id:f for f in response.findings if f.speech_role!='unknown'}
    benign=set(reviewed.review.benign_finding_ids)
    blocking={r.finding_id for r in reviewed.uncertainty_reasons if r.kind in ('action','relation')}
    accepted=[];discarded=0;supporting=[]
    for use in reviewed.url_uses:
        link=observed.get(use.link_id)
        refs=[findings.get(fid) for fid in use.finding_refs]
        if (link is None or not set(use.signal_codes)<={s.code for s in link.signals} or
                any(f is None for f in refs) or (not refs and use.relation!='background') or
                (refs and not any(e.message_id==link.message_id for f in refs for e in f.evidence))):
            discarded+=1;continue
        if use.relation=='supports_request_risk':
            requests=[f for f in refs if f.speech_role=='request' and f.action!='inducement'
                      and f.id not in benign|blocking and any(e.message_id==link.message_id for e in f.evidence)]
            if not requests or not set(use.signal_codes)&STRONG:discarded+=1;continue
            supporting.append((link,requests[0]))
        elif use.relation=='quoted_warning' and not any(f.speech_role in ('quoted_warning','denial') for f in refs):
            discarded+=1;continue
        accepted.append(use)
    response.url_uses=accepted
    response.analysis.discarded_url_uses=discarded
    response.analysis.used_url_evidence=len(accepted)
    if supporting:
        # Technical hints plus a grounded request justify review, never high alone.
        nonblocking={r.finding_id for r in reviewed.uncertainty_reasons if r.kind in ('identity','purpose')}
        can_review=(response.risk_status=='clear' or (response.risk_status=='need_context'
                    and not response.analysis.rule_conflicts and any(f.id in nonblocking and f.action!='transfer_funds'
                        for _,f in supporting)))
        if can_review:
            response.risk_status='suspicious'
            response.summary='Có yêu cầu trong văn bản đi kèm dấu hiệu tên miền cần xác minh trước khi thực hiện.'
            if response.display_summary is not None:response.display_summary=response.summary
            response.answers.evidence_sufficiency.text=response.summary
            if request.question:response.answer_to_user=response.summary
        response.recommended_actions.append('Không đăng nhập hoặc giao mã qua liên kết chưa xác minh; tự mở kênh chính thức đã biết.')
    return response
