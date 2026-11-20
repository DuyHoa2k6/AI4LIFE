"""Accent-aware semantic gate and typed rights/obligation graph, version 1.0.

Local bounded linguistic rules, not a trained language model. Case IDs and draft
answers never enter this module. New policy consumes the same verified graph.
"""
import re
from .schema import Span,Event,Relation,Participant,Attribution,SemanticEvent
from ..local_observation.text import normalize,quote_ranges

VERSION='semantic-contract-1.0'
def norm(s):return normalize(s).text
def has(pattern,text):return bool(re.search(pattern,text))

def clauses(input):
    result=[]
    for m in input.messages:
        for match in re.finditer(r'[^.!?;\n]+(?:[.!?;]|$)',m.text):
            raw=match.group();start=match.start()
            if not raw.strip():continue
            t=norm(raw);quoted=any(a<=start+len(raw)-len(raw.lstrip())<b for a,b in quote_ranges(m.text))
            warning=has(r'canh bao|canh giac|nhac moi nguoi|neu co ai|dung lam theo',norm(m.text)) and not has(r'\btoi (?:dang|hien) bi\b',t)
            epistemic=has(r'(?:chua|khong) (?:biet|ro)|chua mo duoc',t)
            alternatives=epistemic and has(r'\bhay\b|\bla .+ hay\b',t)
            code=re.search(r'(?i:hoa don|hóa đơn|giao dich|giao dịch|đơn hàng|don hang|đơn|don)\s+([A-Z][A-Z0-9_-]*|[0-9][A-Za-z0-9_-]*)\b',raw)
            scope=m.scope_id or 'analysis'
            if code:scope+='/transaction:'+code.group(1)
            result.append({'id':m.id+':c'+str(len(result)+1),'message':m.id,'speaker':m.speaker_id,'scope':scope,'start':start,'end':match.end(),'text':raw,'normalized':t,'warning':warning,'quoted':quoted,'epistemic':epistemic,'alternatives':alternatives})
    return result

def rejected_reason(e,c,spans):
    t=c['normalized'];refs=[spans[s] for s in e.evidence_refs if s in spans]
    verb=next((s.quote for s in refs if s.label=='verb'),None)
    if e.event_type=='transfer_funds':
        if norm(e.object or '') in ('cong viec','khi co chung tu duoc khong','nhe','giup'):return 'non_financial_or_particle_object'
        if has(r'\b(?:toi|minh)\b.{0,25}kiem tra.{0,60}truoc khi thanh toan',t):return 'verification_context_not_payment_event'
        if verb and norm(verb)=='dong' and verb.casefold() not in ('đóng','dong'):return 'noun_or_currency_not_payment'
        if has(r'\bhop dong\b|\bdong y\b|\bchuyen nhuong\b|\bchuyen quyen\b',t) and not has(r'\b(?:nop|tra|ung|thanh toan)\s+(?:tien|phi)|\bchuyen\s+(?:tien|khoan)|\bdong tien\b',t):return 'long_noun_or_rights_phrase_not_payment'
    if e.event_type=='handover_asset' and (has(r'\bgiao dich\b|\bgiao thong tin\b|\bdua vao danh sach\b',t) or norm(e.object or '') in ('nhe','di','a','nha','giup','dich vao')):return 'wrong_handover_object'
    if e.event_type=='receive_funds' and has(r'\bde .{0,30}\bnhan tien\b',t) and not has(r'da nhan|vua nhan|da vao',t):return 'purpose_not_receipt_occurrence'
    if e.event_type=='avoid_verification' and not has(r'\b(?:dung|khoi|cho|khong can|chua can|khong duoc)\s+(?:goi|hoi|kiem tra|xac minh)|(?:ngay mai|toi nay|sau do).{0,35}(?:goi|xac minh)',t):return 'verification_report_or_question_not_obstruction'
    if e.event_type in ('transfer_funds','provide_code','receive_funds','offer_employment','handover_asset','login'):
        if c['alternatives'] or (c['epistemic'] and e.event_type=='receive_funds'):return 'epistemic_unknown_not_occurrence'
        if has(r'(?:chua|khong) co (?:bat ky )?yeu cau',t):return 'negated_request_covers_coordination'
        if e.speech_role in ('request','unknown') and has(r'chua phai|chua dong y thi chua|khong (?:muon|can) .{0,25}(?:vay|cam ket)',t):return 'no_current_request'
        if e.event_type=='offer_employment' and has(r'khong (?:muon|can) (?:cam ket )?viec lam',t):return 'negated_employment_commitment'
    return None

# General action/object recognizers. These create candidates, not risk decisions.
PATTERNS=[
 ('sign_obligation','financial_obligation',r'\b(?:ky(?!\s+(?:nang|thuat|vong|niem))|chap nhan)\b.{0,40}\b(?:vay|nhan no|khoan no|nghia vu tai chinh)\b'),
 ('sign_obligation','financial_obligation',r'\b(?:ho so|giay|hop dong)\b.{0,35}\b(?:ghi toi vay|ghi .{0,15}vay tu)\b'),
 ('guarantee_debt','guarantee',r'\b(?:ky )?bao lanh\b'),
 ('misstate_information','information',r'\b(?:thu nhap|thong tin)\b.{0,25}\b(?:ghi|khai)\b.{0,20}(?:cao hon thuc te|sai|khong dung)|\b(?:ghi|khai)\b.{0,25}(?:thu nhap).{0,20}(?:cao hon|sai)'),
 ('misstate_information','account_usage',r'\b(?:neu|khi) ngan hang hoi\b.{0,70}\b(?:cu noi|khai|dung noi)\b'),
 ('purchase_asset','property',r'\b(?:mua|tra tien mua)\s+(?:xe|nha|dat|tai san|co phan)\b'),
 ('transfer_ownership','ownership',r'\b(?:quyen so huu|giay so huu|tai san)\b.{0,40}\b(?:chuyen|sang ten)|\b(?:sang|dung) ten\b.{0,35}(?:nguoi ban|nguoi khac|ben khac|nguoi thu ba)'),
 ('grant_authority','asset_disposal',r'\b(?:cho phep|uy quyen)\b.{0,90}\b(?:ky hop dong chuyen nhuong|dinh doat|nhan toan bo tien ban)'),
 ('confirm_completion','service_confirmation',r'\b(?:bam|hay|can|phai)\s+(?:xac nhan|bam xac nhan)\b.{0,25}(?:da nhan hang|hoan thanh|hoan tat)'),
 ('release_funds','money',r'\b(?:tien|thanh toan)\b.{0,20}(?:duoc giai phong|duoc mo|duoc tra)|\bgiai phong tien\b'),
 ('withhold_wages','wages',r'\b(?:chua|khong)\b.{0,25}\b(?:thanh toan|nhan|tra) luong\b|\bgiu luong\b'),
 ('restrict_movement','exit_right',r'\b(?:muon|khi) (?:roi|ve|nghi)\b.{0,50}\b(?:phai|can)\b.{0,35}(?:dong y|cho phep|tra)|\b(?:khong duoc|khong the)\s+(?:tu )?(?:roi|ve)\b'),
 ('provide_credentials','credentials',r'\b(?:giao|gui|dua|cung cap|chuyen)\b.{0,30}\b(?:thong tin dang nhap|mat khau)\b'),
 ('recover_access','account_recovery',r'\b(?:so dien thoai|dia chi|email) khoi phuc\b.{0,35}\b(?:so cua|cua quan ly|cua nguoi khac|ben khac)'),
 ('grant_asset_access','digital_assets',r'\bcap quyen\b.{0,90}\b(?:su dung|rut|chuyen)\b.{0,50}\b(?:token|tai san|so du)|\bcap quyen khong gioi han\b'),
 ('return_funds','money',r'\b(?:tra|hoan)\s+(?:lai )?(?:phan du|khoan du|tien du)|\b(?:tien san co)\b.{0,20}\btra truoc\b'),
 ('receive_funds','money',r'\b(?:chua|khong) nhan (?:duoc )?(?:khoan nao|tien|khoan tien)\b'),
 ('describe_terms','repayment',r'\bco viec\b.{0,18}\bmoi tra\b|\blich tra\b.{0,30}\bdu chua\b'),
 ('describe_terms','purpose',r'\bchi (?:dinh|muon)\b.{0,12}\b(?:cho thue|thue)\b'),
 ('describe_terms','liability',r'\b(?:khi|neu)\b.{0,20}\bkhong tra\b.{0,60}\b(?:toi|ban) thanh toan\b'),
 ('verification_status','authority',r'\bchua\b.{0,70}\b(?:uy quyen|quyen cho thue|quyen so huu|don vi nao)\b|\bchua\b.{0,35}\bgiay to\b.{0,35}\bdoi nguoi nhan\b'),
 ('verification_request','verification',r'\b(?:co the|duoc)\s+(?:xem|kiem tra)\s+(?:xac nhan|giay|uy quyen)\b'),
 ('verification_status','independent_confirmation',r'\b(?:toi|minh) da (?:tu )?goi\b.{0,90}\bxac nhan\b'),
 ('describe_terms','review_before_consent',r'\b(?:doc|xem) truoc\b.{0,90}\bchua dong y\b.{0,25}\bchua (?:dong|tra|thanh toan) tien\b'),
 ('handover_asset','goods',r'\b(?:toi|minh|anh|chi) chi giao sau khi tien\b'),
 ('describe_terms','benefit',r'\bcap quyen\b.{0,65}\bthi\b.{0,30}\b(?:qua|thuong|uu dai)\b'),
 ('verification_status','grantee',r'\bchua kiem tra\b.{0,30}\bdia chi\b'),
 ('other','document_unknown',r'\bky (?:giay|van ban|ho so|giup)\b'),
 ('describe_terms','interpersonal_pressure',r'\btin nhau thi khong can giay\b|\bneu\b.{0,20}\bthat long\b|\b(?:luat su|gia dinh)\b.{0,30}\bngan can\b'),
]

def refine(input,a):
    cs=clauses(input);spans={s.span_id:s for s in a.spans};old_events=[e.model_dump(mode='json') for e in a.events];old_relations=[r.model_dump(mode='json') for r in a.relations];rejected=[];kept=[]
    for e in a.events:
        anchor=next((spans[s] for s in e.evidence_refs if s in spans and spans[s].message_id),None)
        c=next((c for c in cs if anchor and c['message']==anchor.message_id and c['start']<=anchor.start<c['end']),None)
        reason=rejected_reason(e,c,spans) if c else None
        if reason:rejected.append({'event_id':e.event_id,'reason':reason,'clause_id':c['id']});continue
        if c and c['warning']:e.speech_role='quoted_warning';e.attribution.kind='quoted_warning'
        # Strong first-person occurrence is not the interlocutor's request.
        if c and has(r'^\s*(?:toi|minh) (?:lo |da |vua |tu )',c['normalized']) and not has(r'yeu cau|hay|nho',c['normalized']):
            e.speech_role='claim';e.modality='report';e.actor_id='speaker:'+c['speaker'] if c['speaker'] else None
            e.affected_party_id=e.actor_id;e.attribution.kind='self_report'
            if e.semantic:e.semantic.speech_act='claim';e.semantic.performer_id=e.actor_id;e.semantic.requester_id=None;e.semantic.affected_party_id=e.actor_id
        kept.append(e)
    a.events=kept
    # New candidates refer to actual speakers. Unknown addressees stay per-message.
    speakers=list(dict.fromkeys(m.speaker_id for m in input.messages if m.speaker_id))
    def person(pid,label,refs=()):
        if pid not in {p.participant_id for p in a.participants}:a.participants.append(Participant(participant_id=pid,label=label,interaction_role='unknown' if pid.startswith('unknown:') else 'mentioned',evidence_refs=list(refs)))
        return pid
    def target(c):
        others=[s for s in speakers if s!=c['speaker']]
        return 'speaker:'+others[0] if len(others)==1 else person('unknown:'+c['message']+':addressee','Người được nói tới, chưa rõ liên kết')
    typed=[];limited=[False]
    def add(c,kind,obj,match=None,traits=(),role=None):
        if len(typed)>=100:limited[0]=True;return None
        sid='sc:s'+str(len(a.spans)+1);raw=c['text'];t=c['normalized'];source='speaker:'+c['speaker'] if c['speaker'] else person('unknown:'+c['message']+':source','Người nói chưa rõ')
        a.spans.append(Span(span_id=sid,message_id=c['message'],start=c['start'],end=c['end'],quote=raw,label='statement'))
        reported=has(r'\btoi (?:doc|thay|chua nhan|da tu|thay hop dong)|ho so dang ghi|vi hien thi|ung dung ghi',t)
        self_claim=has(r'^\s*(?:toi|minh)\b',t)
        prefix=t[:match.start()] if match else ''
        neg=re.search(r'\b(?:dung|cho|khong(?: nen| can| duoc)?|chua)\s+(?:\w+\s+){0,2}$',prefix)
        if neg and neg.group().split()[0] in ('dung','cho'):
            original=normalize(raw);x,y=original.original_range(neg.start(),neg.start()+len(neg.group().split()[0]));word=raw[x:y].casefold()
            if word not in ('đừng','dung','chớ','cho'):neg=None
        denial=has(r'(?:chua|khong) (?:co )?yeu cau|chua phai|chua dong y thi chua',t) or neg is not None
        inferred_role=role or ('claim' if kind in ('describe_terms','verification_status','withhold_wages','release_funds') or self_claim or reported else 'request')
        claimed_delivery=kind=='handover_asset' and has(r'chi giao sau khi tien',t)
        if claimed_delivery:inferred_role='claim'
        if not role and has(r'\b(?:toi|minh) (?:can|nho|muon) (?:ban|anh|chi|em)\b',t):inferred_role='request'
        if c['warning']:inferred_role='quoted_warning'
        elif c['alternatives']:inferred_role='unknown'
        elif denial:inferred_role='denial'
        elif has(r'(?:ben ho tro|ho|nguoi do) (?:bao|yeu cau|noi).{0,30}\btoi\b',t):inferred_role='reported';reported=True
        elif has(r'(?:mot nguoi|ho|nguoi do).{0,15}(?:nho|yeu cau|bao) toi\b|chi co cau',t):inferred_role='reported';reported=True
        performer=source if (self_claim or (reported and has(r'\btoi\b',t))) and inferred_role=='claim' else target(c)
        if inferred_role=='reported' and reported and has(r'\btoi\b',t):performer=source
        if claimed_delivery:performer=source
        affected=target(c) if claimed_delivery else performer
        info='user_reported' if reported else 'unknown' if inferred_role=='unknown' else 'claimed'
        attributes=list(traits)
        if has(r'khong gioi han',t):attributes.append('unlimited_scope')
        elif has(r'toan bo',t):attributes.append('all_assets_scope')
        if has(r'tien cua em|tien cua (?:toi|ban|minh)',t):attributes.append('self_funded')
        if has(r'nguoi ban cua|nguoi khac|ben khac|ban toi|dia chi khac',t):attributes.append('third_party')
        if has(r'chua (?:xac minh|kiem tra|co thoa thuan)|khong can giay|khong co bao dam',t):attributes.append('unverified')
        if has(r'khai|ghi|noi',t) and has(r'cao hon thuc te|cu noi chi co em dung',t):attributes.append('false_information')
        sem=SemanticEvent(message_id=c['message'],situation_id=c['scope'],speaker_id=source,requester_id=source if inferred_role=='request' else None,performer_id=performer,affected_party_id=affected,
          normalized_action=kind,object_type=obj,information_status=info,extraction_method=VERSION,speech_act=inferred_role,clause_id=c['id'],traits=list(dict.fromkeys(attributes)),
          epistemic_state='alternatives' if c['alternatives'] else 'unknown' if c['epistemic'] else 'known',right_scope='unlimited' if 'unlimited_scope' in attributes else 'all_assets' if 'all_assets_scope' in attributes else None,
          arguments={'source':source,'performer':performer,'recipient':None,'object':obj},alternatives=['document','money'] if c['alternatives'] else [])
        if inferred_role=='reported':
            sem.requester_id=person('mentioned:'+c['id']+':requester','Nguồn yêu cầu được thuật lại, chưa rõ danh tính',(sid,));sem.arguments['reporter']=source;sem.is_reported_request=True
        if kind in ('purchase_asset','transfer_ownership','grant_authority','grant_asset_access'):
            sem.transfer_source=performer
            if 'self_funded' in attributes:sem.arguments['funds_source']=performer
            asset=re.search(r'\b(xe|nha|dat|co phan|token)\b',t)
            if asset:
                normalized=normalize(raw);x,y=normalized.original_range(*asset.span());sem.arguments['object_mention']=raw[x:y]
            mention=re.search(r'nguoi ban cua (?:anh|chi|em|toi)|nguoi khac|dia chi khac|ban toi',t)
            if mention:
                normalized=normalize(raw);x,y=normalized.original_range(*mention.span());mid=sid+':recipient'
                a.spans.append(Span(span_id=mid,message_id=c['message'],start=c['start']+x,end=c['start']+y,quote=raw[x:y],label='participant'))
                sem.transfer_destination=person('mentioned:'+c['id']+':recipient',raw[x:y],(mid,));sem.arguments['recipient']=sem.transfer_destination
        e=Event(event_id='sc:e'+str(len(a.events)+1),event_type=kind,description=kind,actor_id=performer,affected_party_id=affected,object=obj,polarity='negative' if kind=='receive_funds' and has(r'\b(?:chua|khong) nhan\b',t) else 'uncertain' if c['alternatives'] else 'positive',
          modality='request' if inferred_role=='request' else 'report',temporal_state='requested' if inferred_role=='request' else 'unknown',speech_role=inferred_role,
          attribution=Attribution(speaker_id=c['speaker'],kind='quoted_warning' if c['warning'] else 'user_report' if reported else 'sender_claim'),status='unknown' if inferred_role=='unknown' else 'inferred',scope_id=c['scope'],evidence_refs=[sid],extractor_rule_id=VERSION,semantic=sem)
        a.events.append(e);typed.append(e);return e
    for c in cs:
        if len(typed)>=100:limited[0]=True;break
        t=c['normalized']
        if c['alternatives']:
            add(c,'other','unresolved',role='unknown')
            # Sources mentioned inside a report are separate, not additional chat turns.
            for match in re.finditer(r'nguoi (?:thu nhat|thu hai|dau tien|con lai)\s+noi',t):
                person('mentioned:'+c['message']+':'+str(match.start()),'Nguồn lời nói được thuật lại')
            continue
        # Reported speakers inside quotations remain separate unresolved sources.
        for source_match in re.finditer(r'nguoi (?:thu nhat|thu hai|dau tien|con lai)\s+noi',t):
            pid=person('mentioned:'+c['message']+':'+str(c['start']+source_match.start()),'Nguồn lời nói được thuật lại')
            quoted=add(c,'other','reported_unresolved',role='reported')
            if quoted is None:break
            quoted.actor_id=quoted.affected_party_id=None;quoted.semantic.speaker_id=pid;quoted.semantic.performer_id=None;quoted.semantic.affected_party_id=None;quoted.semantic.information_status='user_reported';quoted.semantic.arguments['reporter']='speaker:'+c['speaker'];quoted.semantic.arguments['source']=pid
        for kind,obj,pattern in PATTERNS:
            match=re.search(pattern,t)
            if match:
                if kind=='transfer_ownership' and 'tai khoan' in t:continue
                add(c,kind,obj,match)
        if has(r'\b(?:anh|chi|ban|em)\s+(?:cu |hay |can |phai )?ky\b',t):
            antecedents=[e for e in typed if e.event_type=='sign_obligation' and e.speech_role not in ('denial','unknown','quoted_warning') and e.scope_id==c['scope'] and e.semantic.clause_id!=c['id']]
            if len(antecedents)==1 and not any(e.event_type=='sign_obligation' and e.semantic.clause_id==c['id'] for e in typed) and has(r'\b(?:do|ay|ho so|thu tuc)\b',t):add(c,'sign_obligation','financial_obligation')
        if has(r'\b(?:co viec|khoan vay|giay|van ban)\b',t) and c['epistemic']:add(c,'other','document_unknown',role='unknown')
        if has(r'\bchuyen (?:tien )?truoc\b',t) and has(r'tien coc|dat coc|tai khoan nhan',norm(' '.join(m.text for m in input.messages))) and not c['alternatives']:
            add(c,'transfer_funds','money',traits=['advance_payment'])
    # Assign explicit transaction codes. A group verification only covers the
    # enumerated transactions when the text explicitly says each/both.
    code_pattern=r'(?i:hoa don|hóa đơn|giao dich|giao dịch|đơn hàng|don hang|đơn|don)\s+([A-Z][A-Z0-9_-]*|[0-9][A-Za-z0-9_-]*)\b'
    codes=list(dict.fromkeys(match.group(1) for m in input.messages for match in re.finditer(code_pattern,m.text)))
    scoped_clause=set()
    if codes:
        confirmations=[c for c in cs if has(r'\b(?:toi|minh) da (?:tu )?goi\b.{0,100}xac nhan',c['normalized']) and has(r'tung|moi|ca hai',c['normalized'])]
        for c in cs:
            for code in codes:
                if re.search(r'\b(?:tiền|tien)\s+'+re.escape(code)+r'\b',c['text']) and has(r'\bchuyen\b',c['normalized']):
                    e=add(c,'transfer_funds','money',role='request')
                    if e is None:continue
                    e.scope_id='analysis/transaction:'+code;e.semantic.situation_id=e.scope_id;e.semantic.transaction_reference=code;e.semantic.transaction_binding='explicit_code';e.semantic.arguments['transaction']=code;scoped_clause.add(c['id'])
                    for confirmation in confirmations:
                        v=add(confirmation,'verification_status','independent_confirmation',traits=['reported_verified'],role='claim')
                        if v is None:continue
                        v.scope_id=e.scope_id;v.semantic.situation_id=e.scope_id;v.semantic.transaction_reference=code;v.semantic.transaction_binding='explicit_code';v.semantic.information_status='user_reported';v.actor_id='speaker:'+confirmation['speaker'];v.affected_party_id=v.actor_id;v.semantic.affected_party_id=v.actor_id
    # Keep the graph coherent when a typed object replaces a coarse guess.
    typed_by_clause={e.semantic.clause_id for e in typed}
    for e in list(a.events):
        if e in typed:continue
        s=next((spans[s] for s in e.evidence_refs if s in spans and spans[s].message_id),None)
        c=next((c for c in cs if s and c['message']==s.message_id and c['start']<=s.start<c['end']),None)
        if c and ((c['id'] in typed_by_clause and e.event_type in ('transfer_funds','handover_asset','grant_control','offer_employment') and not has(r'\bchuyen\s+(?:tien|khoan)|\bnop\b',c['normalized'])) or (c['id'] in scoped_clause and e.event_type=='transfer_funds')):
            a.events.remove(e);rejected.append({'event_id':e.event_id,'reason':'superseded_by_typed_action_object','clause_id':c['id']})
    ids={e.event_id for e in a.events};a.relations=[r for r in a.relations if r.from_id in ids and r.to_id in ids]
    # Remove stale answer dependencies before structural validation.
    for f in a.answers_18.__dict__.values():
        if not set(f.value.event_ids)<=ids:f.value.statements=[];f.status='unknown'
        f.value.event_ids=[x for x in f.value.event_ids if x in ids];f.value.relation_ids=[x for x in f.value.relation_ids if x in {r.relation_id for r in a.relations}]
    trace={'version':VERSION,'clauses':cs,'event_candidates':old_events+[e.model_dump(mode='json') for e in typed],'rejected_events':rejected,'relation_candidates':old_relations,'coverage_gaps':[],'questions':[],'processing_limit_reached':limited[0]}
    a.grounding_trace['semantic_contract']=trace
    link(input,a,typed,cs)
    return a

def link(input,a,typed,cs):
    """Narrow semantic bindings with explicit object/condition evidence, not distance."""
    by_clause={c['id']:c for c in cs}
    def t(e):return by_clause[e.semantic.clause_id]['normalized']
    def events(kind):return [e for e in typed if e.event_type==kind and e.speech_role not in ('quoted_warning','denial','unknown')]
    def relation(kind,x,y,why):
        if x.event_id==y.event_id:return
        if x.scope_id!=y.scope_id:return
        # Do not merge uncertain third-person roles to make a relation pass.
        if x.affected_party_id!=y.affected_party_id:return
        if any(r.type==kind and r.from_id==x.event_id and r.to_id==y.event_id for r in a.relations):return
        r=Relation(relation_id='sc:r'+str(len(a.relations)+1),type=kind,from_id=x.event_id,to_id=y.event_id,scope_id=x.scope_id,evidence_refs=list(dict.fromkeys(x.evidence_refs+y.evidence_refs)),status='inferred',rationale=why,rule_id=VERSION)
        a.relations.append(r);a.grounding_trace['semantic_contract']['relation_candidates'].append(r.model_dump(mode='json'))
    # Obligations and the concrete coercive or deceptive conditions attached to them.
    for debt in events('sign_obligation'):
        for statement in events('misstate_information'):
            if statement.semantic.object_type=='information' and has(r'ho so|thu nhap|duyet',t(statement)):relation('prerequisite_for',statement,debt,'Khai thông tin được yêu cầu để duyệt cùng hồ sơ nghĩa vụ.')
        for wages in events('withhold_wages'):
            if has(r'chua ky|khong ky',t(wages)):relation('coerced_by',debt,wages,'Chưa ký được nêu là điều kiện chưa được nhận lương.')
    for x in events('purchase_asset'):
        for y in events('transfer_ownership'):
            if 'self_funded' in x.semantic.traits and 'third_party' in y.semantic.traits:relation('funding_ownership_mismatch',x,y,'Nguồn tiền của người mua nhưng yêu cầu quyền sở hữu thuộc người thứ ba.')
    for x in events('describe_terms'):
        if x.semantic.object_type=='interpersonal_pressure':
            for y in events('transfer_ownership'):relation('reason_given_for',x,y,'Áp lực quan hệ được đưa ra để thúc thực hiện yêu cầu chuyển quyền sở hữu.')
    for x in events('grant_authority'):
        for y in events('describe_terms'):
            if y.semantic.object_type=='purpose' and has(r'cho thue|thue',t(y)):relation('exceeds_scope',x,y,'Quyền chuyển nhượng/nhận tiền bán khác mục đích cho thuê được thuật lại.')
    for x in events('provide_credentials'):
        for y in events('recover_access'):relation('transfers_control',x,y,'Giao thông tin truy cập cùng thay chủ quyền khôi phục của tài khoản.')
    for x in events('confirm_completion'):
        for y in events('release_funds'):
            if has(r'chi .{0,12}sau khi|sau khi tien|neu .{0,25}khong bam|hoan tat giao dich',t(y)):relation('prerequisite_for',x,y,'Xác nhận hoàn thành được dùng để giải phóng tiền trước giao hàng.')
    for x in events('release_funds'):
        for y in events('handover_asset'):
            if has(r'giao sau khi tien',t(y)):relation('before',x,y,'Lời người giao hàng đặt việc giải phóng tiền trước giao hàng.')
    for x in events('grant_asset_access'):
        for y in events('describe_terms'):
            if y.semantic.object_type=='benefit' and x.semantic.clause_id==y.semantic.clause_id:relation('prerequisite_for',x,y,'Lợi ích được hứa phụ thuộc việc cấp quyền tài sản trong cùng yêu cầu.')
    for x in events('return_funds'):
        for y in events('receive_funds'):
            if y.polarity=='negative' and has(r'tra truoc|dung doi|tien san co|tra phan du',t(x)):relation('before',x,y,'Yêu cầu hoàn từ tiền sẵn có trong khi người nhận báo chưa nhận khoản ban đầu.')
    for x in events('guarantee_debt'):
        for y in events('describe_terms'):
            if y.semantic.object_type=='liability':relation('liability_if_default',x,y,'Nghĩa vụ thanh toán được nêu khi bên vay không trả.')
    for x in events('transfer_funds'):
        for y in events('verification_status'):
            if y.semantic.object_type=='independent_confirmation' and 'reported_verified' in y.semantic.traits:relation('same_transaction',y,x,'Từng hóa đơn được người dùng báo xác nhận riêng trước thanh toán theo mã.')
    for y in events('verification_status'):
        if y.semantic.object_type!='authority':continue
        candidates=[e for e in a.events if e.event_type=='transfer_funds' and e.speech_role=='request' and e.polarity=='positive']
        scopes={e.scope_id for e in candidates}
        if len(scopes)==1:
            for x in candidates:
                # Link only if the receiving authority is explicitly in question,
                # not any missing identity in an unrelated topic.
                if has(r'uy quyen|quyen cho thue|doi nguoi nhan',t(y)) and has(r'tai khoan|chuyen truoc',norm(' '.join(s.quote for s in a.spans if s.span_id in x.evidence_refs))):relation('unverified_authority',x,y,'Yêu cầu thanh toán trong khi quyền thu tiền/nhận ủy quyền được nêu chưa có căn cứ.')
    # Explicit contradictory repayment statements, with original evidence on both ends.
    repayment=[e for e in events('describe_terms') if e.semantic.object_type=='repayment']
    for x in repayment:
        for y in repayment:
            if x!=y and has(r'co viec.{0,18}moi tra',t(x)) and has(r'du chua',t(y)):relation('contradiction',x,y,'Lời hứa trả khi có việc trái lịch trả dù chưa có việc được người học thuật lại.')

def assess(input,a,previous,status):
    """Decisions use retained typed events and directed relations, never test IDs."""
    trace=a.grounding_trace.get('semantic_contract',{});events={e.event_id:e for e in a.events};typed=[e for e in a.events if e.extractor_rule_id==VERSION]
    active=lambda e:e.speech_role not in ('denial','quoted_warning','unknown','hypothetical') and e.polarity!='uncertain'
    requests=[e for e in typed if e.speech_role=='request' and e.polarity=='positive']
    rules=[]
    descriptions={
      'prerequisite_for':('high','Yêu cầu thực hiện một bước có thể tạo nghĩa vụ hoặc giải phóng tiền trước khi quyền lợi được bảo đảm.','Chưa ký, khai sai hoặc xác nhận sự việc chưa xảy ra; kiểm tra hồ sơ và quy trình qua đầu mối độc lập.'),
      'coerced_by':('high','Việc nhận lương bị dùng làm điều kiện buộc chấp nhận nghĩa vụ nợ.','Lưu trao đổi và tìm hỗ trợ độc lập; ưu tiên an toàn nếu bị cản rời đi, tránh đối đầu.'),
      'funding_ownership_mismatch':('high','Bạn được yêu cầu bỏ tiền mua tài sản nhưng quyền sở hữu chuyển sang người thứ ba.','Chưa trả tiền hoặc chuyển quyền khi chưa có thỏa thuận bảo vệ quyền lợi và tư vấn độc lập.'),
      'exceeds_scope':('high','Quyền ký/chuyển nhượng hoặc nhận tiền bán rộng hơn mục đích giao dịch bạn nêu.','Chưa ký; đọc toàn bộ văn bản và nhờ tư vấn độc lập kiểm tra phạm vi quyền.'),
      'transfers_control':('high','Người gửi yêu cầu giao thông tin truy cập và để bên khác kiểm soát quyền khôi phục tài khoản.','Không giao mật khẩu hoặc quyền khôi phục; tự xác minh yêu cầu qua kênh độc lập.'),
      'before':('high','Bạn được yêu cầu hoàn tiền trước trong khi khoản thanh toán ban đầu chưa được báo nhận.','Không dùng tiền sẵn có để trả khoản chưa nhận; đối soát giao dịch thực tế trước.'),
      'liability_if_default':('suspicious','Ký bảo lãnh có thể khiến bạn phải thanh toán khi người vay không trả.','Đọc phạm vi nghĩa vụ và xác minh khả năng trả nợ; lời hứa lợi nhuận không thay thế chứng cứ.')}
    descriptions['unverified_authority']=('suspicious','Có yêu cầu chuyển tiền nhưng chưa có căn cứ xác nhận quyền nhận tiền của bên được chỉ định.','Chưa chuyển tiền; xác minh quyền nhận tiền hoặc ủy quyền qua đầu mối độc lập.')
    for r in a.relations:
        if r.rule_id!=VERSION or r.type not in descriptions:continue
        ends=[events.get(r.from_id),events.get(r.to_id)]
        if not all(ends) or not all(active(e) for e in ends):continue
        pairs={'coerced_by':('sign_obligation','withhold_wages'),'funding_ownership_mismatch':('purchase_asset','transfer_ownership'),
          'exceeds_scope':('grant_authority','describe_terms'),'transfers_control':('provide_credentials','recover_access'),
          'liability_if_default':('guarantee_debt','describe_terms'),'unverified_authority':('transfer_funds','verification_status')}
        if r.type in pairs and tuple(e.event_type for e in ends)!=pairs[r.type]:continue
        if r.type=='liability_if_default' and ends[1].semantic.object_type!='liability':continue
        if r.type=='exceeds_scope' and ends[1].semantic.object_type!='purpose':continue
        if r.type=='before' and not (ends[0].event_type=='return_funds' and ends[1].event_type=='receive_funds'):continue
        if r.type=='prerequisite_for' and not ((ends[0].event_type=='misstate_information' and ends[1].event_type=='sign_obligation') or (ends[0].event_type=='confirm_completion' and ends[1].event_type=='release_funds')):continue
        if r.type=='funding_ownership_mismatch' and not any(e.event_type=='verification_status' and e.semantic and e.semantic.object_type=='authority' and e.scope_id==r.scope_id and 'unverified' in e.semantic.traits for e in typed):continue
        rules.append((r.type,*descriptions[r.type],r.evidence_refs))
    for e in requests:
        if e.event_type=='grant_asset_access' and e.semantic.right_scope=='unlimited':
            benefit=[r for r in a.relations if r.type=='prerequisite_for' and r.from_id==e.event_id and events.get(r.to_id) and events[r.to_id].semantic.object_type=='benefit']
            unverified=[v for v in typed if v.event_type=='verification_status' and v.semantic.object_type=='grantee' and v.scope_id==e.scope_id]
            if benefit and unverified:rules.append(('unlimited_asset_authority','high','Lợi ích được hứa phụ thuộc cấp quyền tài sản số không giới hạn cho địa chỉ chưa kiểm tra.','Chưa cấp quyền; tự kiểm tra địa chỉ nhận quyền và phạm vi quyền trong ví.',e.evidence_refs+[s for v in unverified for s in v.evidence_refs]+[s for r in benefit for s in r.evidence_refs]))
            elif previous.risk_status not in ('high','suspicious'):rules.append(('asset_authority_review','suspicious','Có yêu cầu cấp quyền sử dụng tài sản số cần xác minh phạm vi và người nhận quyền.','Đọc và hiểu phạm vi quyền trước khi xác nhận.',e.evidence_refs))
    if rules:
        rules.sort(key=lambda r:r[1]!='high');rule,risk,summary,action,_=rules[0]
        previous.risk_status=risk;previous.summary=summary;previous.recommended_actions=[action];previous.evidence_refs=list(dict.fromkeys(s for r in rules for s in r[-1]));previous.applicable_rule_ids=['SC-'+r[0] for r in rules];previous.follow_up_questions=[];previous.missing_information=[];previous.supported_conclusions=[summary];previous.explanation_template_id='SC-TYPED';previous.safety_urgency='preventive'
    scoped_payments=[e for e in typed if e.event_type=='transfer_funds' and e.semantic.transaction_reference]
    confirmations={e.scope_id:e for e in typed if e.event_type=='verification_status' and 'reported_verified' in e.semantic.traits}
    controls=[e for e in typed if e.event_type=='describe_terms' and e.semantic.object_type=='review_before_consent' and e.speech_role not in ('quoted_warning','denial','unknown')]
    if previous.risk_status not in ('high','suspicious') and ((scoped_payments and all(e.scope_id in confirmations for e in scoped_payments)) or (controls and not requests)):
        basis=scoped_payments+list(confirmations.values()) if scoped_payments else controls
        previous.risk_status='clear';previous.summary='Chưa ghi nhận yêu cầu nguy hiểm trong phạm vi đã phân tích; thông tin xác minh hoặc quyền đọc trước và chưa đồng ý chưa thanh toán do người dùng cung cấp.'
        previous.follow_up_questions=[];previous.missing_information=[];previous.applicable_rule_ids=['SC-REPORTED-VERIFICATION' if scoped_payments else 'SC-CONSENT-CONTROLS'];previous.evidence_refs=[s for e in basis for s in e.evidence_refs];previous.recommended_actions=['Tiếp tục tự kiểm tra điều khoản và đúng thông tin từng giao dịch trước khi quyết định.']
    # Coverage measures unresolved structural cues, never claims 100% understanding.
    cs=trace.get('clauses',[]);typed_clause={e.semantic.clause_id for e in typed}
    span_map={s.span_id:s for s in a.spans}
    covered=set(typed_clause)
    for e in a.events:
        if e.event_type=='other' or e.speech_role=='unknown':continue
        for ref in e.evidence_refs:
            s=span_map.get(ref)
            if s:covered.update(c['id'] for c in cs if c['message']==s.message_id and c['start']<=s.start<c['end'])
    gaps=[c['id'] for c in cs if has(r'\b(?:ky(?! nang| thuat)|uy quyen|bao lanh|phai|bat buoc)\b',c['normalized']) and c['id'] not in covered and not c['warning'] and not has(r'khong (?:can|muon)|chua (?:ky|dong y)|neu can',c['normalized'])]
    trace['coverage_gaps']=gaps
    epistemic=[c for c in cs if c['epistemic'] or c['alternatives']]
    questions=[]
    if previous.risk_status not in ('high','suspicious'):
        if any(c['alternatives'] for c in cs):questions=[{'field':'action_object_and_scope','question':'Bạn có thể bổ sung tin trước đó để xác định thứ được yêu cầu gửi và các tin có cùng một việc không?'}]
        elif any(has(r'ky|giay|van ban',c['normalized']) and c['epistemic'] for c in cs):questions=[{'field':'document_rights_and_purpose','question':'Khoản tiền liên quan việc gì, và giấy đó yêu cầu bạn xác nhận hoặc ủy quyền điều gì?'}]
        elif gaps:previous.summary='Hệ thống chưa biểu diễn đầy đủ một phần yêu cầu đã có trong nội dung; chưa có kết luận an toàn.'
        if questions:previous.risk_status='need_context';previous.summary='Còn thông tin về hành động hoặc quyền nghĩa vụ cần làm rõ trước khi đánh giá.'
        if gaps and not questions:previous.follow_up_questions=[];previous.missing_information=['Giới hạn bộ phân tích; không yêu cầu người dùng nhắc lại dữ kiện đã có.']
        elif questions:previous.follow_up_questions=[q['question'] for q in questions][:2];previous.missing_information=[q['field'] for q in questions]
        # No active event alone is never sufficient for clear.
        elif previous.risk_status=='clear' and (gaps or any(e.speech_role=='unknown' for e in a.events)):
            previous.risk_status='need_context';previous.summary='Hệ thống chưa kiểm tra đầy đủ phần nội dung còn bất định; chưa có kết luận an toàn.'
    return previous,status
