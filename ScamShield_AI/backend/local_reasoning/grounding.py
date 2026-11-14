"""Reconcile object/speech/transaction/mention bindings before any decision.

No verdict rules live here. Invalid events and their dependent relations are
removed, duplicates alias to one fact, and legacy summaries are rebuilt.
"""
import re
import uuid
from collections import defaultdict
from ..local_observation.text import normalize
from ..local_observation.syntax import direct_object,speech_scope
from .clause_context import units
from .extract import scope_for
from .schema import Event,Span,Attribution,SemanticEvent,Participant,PersonMention,Relation


def reconcile(input,a,frames):
    token=uuid.uuid4().hex[:12]
    trace={'version':'grounding-2.0','removed_events':[],'aliases':{},'removed_relations':[],
        'coverage_gaps':[],'field_needs':[],'question_bindings':[]}
    messages={m.id:m for m in input.messages};spans={s.span_id:s for s in a.spans}
    clauses=list(units(input));new=[];drop=set()
    def text_for(e):
        ss=[spans[s] for s in e.evidence_refs if s in spans and spans[s].message_id in messages]
        if not ss:return None
        verb=next((s for s in ss if s.label=='verb'),None)
        point=verb.start if verb else min(s.start for s in ss)
        if verb and verb.quote.casefold().startswith('bạn giao'):point+=4
        m=messages[ss[0].message_id]
        unit=next((u for u in clauses if u[0].id==m.id and u[1]<=point<u[2]),None)
        if not unit:return None
        _,start,end,raw,source=unit
        if not verb:
            frame=next((f for f in frames if f.action_event_id==e.event_id),None)
            if frame and frame.requested_action:
                n=normalize(raw);found=n.text.find(normalize(frame.requested_action).text)
                if found>=0:
                    part=n.text[found:];head=re.search(r'\b(?:giao|dua|cho|de|chuyen|nop|dong|ung|mua|thanh toan)\b',part)
                    pos=found+(head.start() if head else 0);point=start+n.original_range(pos,pos+1)[0]
            elif e.object:
                n=normalize(raw);found=n.text.find(normalize(e.object).text)
                if found>=0:
                    head=re.search({'receive_funds':r'\b(?:nhan|thay)\b','transfer_funds':r'\b(?:chuyen|nop|ung|dong|thanh toan|mua)\b'}.get(e.event_type,r'(?!)'),normalize(e.object).text)
                    pos=found+(head.start() if head else 0);point=start+n.original_range(pos,pos+1)[0]
            else:
                patterns={'transfer_funds':r'\b(?:chuyen|nop|dong|ung|thanh toan|mua)\b',
                    'receive_funds':r'\b(?:nhan|thay)\b','handover_asset':r'\b(?:giao|cho|dua|de)\b',
                    'provide_code':r'\b(?:gui|doc|cung cap)\b','withdraw_funds':r'\brut\b'}
                found=re.search(patterns.get(e.event_type,r'(?!)'),normalize(raw).text)
                if found:point=start+normalize(raw).original_range(*found.span())[0]
        return m,start,end,raw,source,point
    def add(m,start,end,action,kind,role='claim',polarity='positive',state='unknown'):
        sid='ground:s'+str(len(a.spans)+1)
        s=Span(span_id=sid,message_id=m.id,start=start,end=end,quote=m.text[start:end],label='action')
        a.spans.append(s);spans[sid]=s
        src='speaker:'+(m.speaker_id or m.id);scope=scope_for(m,start)
        raw=m.text[start:end];t=normalize(raw).text
        main=re.search(r'\b(?:nhan|gui|giu|kiem tra|chuyen|giao)\b',t)
        prefix=t[:main.start()] if main else ''
        speech=speech_scope(prefix,t)
        if speech is None and re.search(r'\bchua\s*$',prefix) and action.startswith(('receive_','send_')):speech='not_yet_report'
        warning=bool(re.search(r'canh bao|canh giac|bai tuyen truyen',normalize(m.text[:start]).text) or re.search(r'canh bao|canh giac|bai tuyen truyen',t))
        if warning:role='quoted_warning'
        elif speech=='not_yet_report':role='claim';polarity='negative';state='pending'
        elif speech in ('prohibition','denied_request'):role='denial' if speech=='prohibition' else 'claim';polarity='negative'
        elif role=='claim' and re.search(r'\bse\s*$',prefix):state='planned'
        e=Event(event_id='ground:e'+str(len(a.events)+len(new)+1),event_type=kind,description=action,actor_id=src,
            affected_party_id=None,polarity=polarity,modality='request' if role=='request' else 'assertion',temporal_state=state,
            speech_role=role,attribution=Attribution(speaker_id=m.speaker_id,kind='quoted_warning' if role=='quoted_warning' else 'sender_claim'),status='claimed' if role=='claim' else 'observed',
            scope_id=scope,evidence_refs=[sid],extractor_rule_id='GROUND-OBJECT-SPEECH',
            semantic=SemanticEvent(message_id=m.id,situation_id=scope,speaker_id=src,normalized_action=action,object_type=None,
                speech_act=speech or ('assertion' if role=='claim' else role),information_status='claimed' if role in ('claim','reported') else 'observed'))
        new.append(e);return e
    for e in list(a.events):
        info=text_for(e)
        if not info:continue
        m,start,end,raw,source,point=info;n=normalize(raw);t=n.text
        relative=max(0,point-start);prefix=raw[:relative];tail=raw[relative:]
        verb=re.match(r'(?:nhan|thay|gui|chuyen|ung|nop|tra|dang nhap|doc|giao|mua)\b',normalize(tail).text)
        after=normalize(tail).text[verb.end():] if verb else ''
        if e.event_type=='receive_funds' and verb and direct_object(after) not in ('money',):
            obj=direct_object(after)
            if obj in ('document','goods','code'):
                e.event_type='other';e.description='receive_'+obj
                if e.semantic:e.semantic.normalized_action=e.description;e.semantic.object_type=obj
            elif not re.search(r'(?:nhan|nha|lay) lai|tra (?:ca|lai)|se hoan|moi.*rut',t):
                drop.add(e.event_id);trace['removed_events'].append({'id':e.event_id,'reason':'unresolved_receipt_object'})
        if e.event_type=='transfer_funds' and verb and verb.group()=='ung' and re.match(r'\s+dung\b',after):
            drop.add(e.event_id);trace['removed_events'].append({'id':e.event_id,'reason':'application_noun_not_advance_payment'})
        elif e.event_type=='transfer_funds' and verb and direct_object(after) in ('document','goods','code','credentials'):
            obj=direct_object(after);e.event_type='other';e.description='transfer_'+obj
            if e.semantic:e.semantic.normalized_action=e.description;e.semantic.object_type=obj
        if e.event_type in ('login','provide_credentials') and re.search(r'(?:gui|cung cap).{0,20}(?:huong dan|tai lieu).{0,15}dang nhap',t):
            e.event_type='other';e.description='send_document'
            if e.semantic:e.semantic.normalized_action='send_document';e.semantic.object_type='document'
            e.speech_role='claim' if re.search(r'\b(?:toi|minh)\s+(?:se|da)',t) else e.speech_role
        if e.extractor_rule_id=='FACT-BANK-INFO-1' and not re.search(r'\b(?:mo|xem)\b|vao (?:phan|muc)',t):
            drop.add(e.event_id);trace['removed_events'].append({'id':e.event_id,'reason':'not_financial_display_instruction'})
        scope_kind=speech_scope(prefix,raw)
        verify_gate=e.event_type=='transfer_funds' and bool(re.search(r'(?:xac nhan|xac minh)\b.{0,35}(?:roi|thi) moi\s*$',normalize(prefix).text))
        if verify_gate:
            e.speech_role='claim';e.modality='conditional';e.temporal_state='planned'
            if e.semantic:
                e.semantic.speech_act='deferred_until_verification'
                e.semantic.condition={'predicate':'verify_payee','polarity':'positive','evidence_refs':e.evidence_refs}
        if e.speech_role not in ('quoted_warning','hypothetical'):
            if scope_kind in ('not_yet_report','denied_request'):
                e.speech_role='claim';e.polarity='negative';e.modality='report' if scope_kind=='not_yet_report' else 'assertion'
                e.temporal_state='pending' if scope_kind=='not_yet_report' else 'unknown'
            elif scope_kind=='conditional_nonperformance' and e.event_type=='transfer_funds':
                e.speech_role='reported' if re.search(r'ho doa|ho noi',t[:max(0,relative)]) else 'claim'
                e.polarity='negative';e.modality='conditional';e.temporal_state='hypothetical'
            elif scope_kind=='prohibition':e.speech_role='denial';e.polarity='negative';e.modality='assertion'
            elif re.search(r'\b(?:khoan |tien )?da\s*$',normalize(prefix).text):
                e.speech_role='claim';e.polarity='positive';e.temporal_state='completed'
        e.scope_id=scope_for(m,point)
        if e.semantic:
            e.semantic.situation_id=e.scope_id
            e.semantic.speech_act=scope_kind or e.semantic.speech_act or e.speech_role
            if scope_kind=='conditional_nonperformance':
                if e.event_type!='transfer_funds':e.semantic.speech_act='stated_conditional_consequence'
                e.semantic.condition={'predicate':'payment' if e.event_type!='transfer_funds' else e.event_type,'polarity':'negative','evidence_refs':e.evidence_refs}
    # Receipt/document/hold/check are meaningful events too; don't force their
    # objects into the money ontology just to satisfy existing risk rules.
    for m,start,end,raw,source in clauses:
        t=normalize(raw).text
        for action,pattern,obj in [('receive_document',r'nhan (?:duoc )?(?:phu luc|tai lieu|hop dong)','document'),
            ('send_document',r'gui (?:lai )?(?:huong dan|tai lieu|giay xac nhan)','document'),
            ('verify_information',r'kiem tra (?:giup )?(?:thong tin|tai khoan)|xac nhan dung','verification'),
            ('hold_asset',r'\bgiu lai\b','asset')]:
            if re.search(pattern,t):
                e=add(m,start,end,action,'other','claim' if action=='receive_document' or re.search(r'\btoi se\b',t) else 'request')
                e.semantic.object_type=obj
        conditional=re.search(r'\bneu khong\b(?P<ante>[^.!?;]+?)\bthi\b(?P<out>[^.!?;]+)',t)
        if conditional and re.search(r'\b(?:mat|het hieu luc)\b',conditional.group('out')):
            e=add(m,start,end,'loss_consequence','other','reported' if re.search(r'ho doa|ho noi',t[:conditional.start()]) else 'claim')
            e.modality='threat';e.semantic.condition={'predicate':'payment','polarity':'negative','evidence_refs':e.evidence_refs}
            e.temporal_state='hypothetical'
            e.semantic.speech_act='stated_conditional_consequence';e.semantic.object_type='money'
            if e.speech_role=='reported':
                pid='mentioned:threat_source:'+token+':'+m.id
                a.participants.append(Participant(participant_id=pid,label='Bên đe dọa được thuật lại, chưa xác minh danh tính',interaction_role='mentioned',evidence_refs=e.evidence_refs))
                e.actor_id=pid;e.attribution.kind='reported';e.semantic.requester_id=pid;e.semantic.performer_id=pid
        if re.search(r'\bchua (?:tra|thanh toan)\b.*\bthi khong duoc (?:tu )?ve\b',t):
            e=add(m,start,end,'exit_payment','impose_debt');e.modality='conditional'
            e.semantic.condition={'predicate':'repay_cost','polarity':'negative','evidence_refs':e.evidence_refs}
            e.semantic.object_type='freedom'
        existing=[e for e in a.events+new if any(s in spans and spans[s].message_id==m.id and start<=spans[s].start<end for s in e.evidence_refs)]
        generic=re.search(r'^\s*(?:(?:ban|anh|chi|em|toi|minh)\s+)?(?:(?:da|se|chua)\s+)?(chuyen|gui|nhan|giao)\b',t)
        if not existing and generic:
            action={'chuyen':'transfer_unknown','gui':'send_unknown','nhan':'receive_unknown','giao':'handover_unknown'}[generic.group(1)]
            e=add(m,start,end,action,'other','claim' if re.match(r'\s*(?:toi|minh)',t) else 'request');e.semantic.object_type='unknown'
    a.events=[e for e in a.events if e.event_id not in drop]+new
    # Deduplicate one action occurrence, not different actions in one sentence.
    kept=[];index={};alias={}
    for e in a.events:
        info=text_for(e)
        if not info:kept.append(e);continue
        m,start,end,raw,source,point=info
        key=(m.id,point,e.event_type,e.description if e.event_type=='other' else '',e.speech_role,e.polarity,e.scope_id)
        if key not in index:index[key]=e;kept.append(e);continue
        old=index[key];alias[e.event_id]=old.event_id
        old.evidence_refs=list(dict.fromkeys(old.evidence_refs+e.evidence_refs))
        if e.extractor_rule_id.startswith('SG-') and e.semantic:old.semantic=e.semantic
        old.stated_purpose=old.stated_purpose or e.stated_purpose
    a.events=kept;trace['aliases']=alias
    ids={e.event_id for e in kept}
    def mapped(eid):return alias.get(eid,eid)
    for f in list(frames):
        f.action_event_id=mapped(f.action_event_id)
        if f.benefit_event_id:f.benefit_event_id=mapped(f.benefit_event_id)
        if f.action_event_id not in ids:frames.remove(f)
    for r in a.relations:r.from_id=mapped(r.from_id);r.to_id=mapped(r.to_id)
    # Mention IDs are per analysis; unresolved roles never prove coreference.
    sources={}
    for m,start,end,raw,source in clauses:sources[(m.id,start)]=source
    known_sources=set(sources.values())
    def person(pid,label,role='mentioned',refs=()):
        if pid not in {p.participant_id for p in a.participants}:
            a.participants.append(Participant(participant_id=pid,label=label,interaction_role=role,evidence_refs=list(refs)))
        return pid
    def addressee(source,scope):
        others=known_sources-{source}
        return next(iter(others)) if len(known_sources)==2 else person('role:'+token+':'+scope+':address:'+source,'Bên được xưng hô trực tiếp trong tình huống, chưa xác minh danh tính','recipient')
    for source in known_sources:person(source,'Nguồn lời nói, chưa xác minh danh tính','speaker')
    for m,start,end,raw,source in clauses:
        n=normalize(raw)
        pattern=r'tai xe(?: ten [a-z]+)?|nguoi quen(?: cua (?:chi|anh))?(?: ten [a-z]+)?|truong nhom|nguoi don|anh ay|chi ay|nguoi do'
        for match in re.finditer(pattern,n.text):
            x,y=n.original_range(*match.span());sid='mention:s'+str(len(a.spans)+1)
            span=Span(span_id=sid,message_id=m.id,start=start+x,end=start+y,quote=raw[x:y],label='participant')
            a.spans.append(span);spans[sid]=span;scope=scope_for(m,start+x)
            mid='mention:'+token+':'+str(len(a.mentions)+1);name=re.search(r'\bten ([a-z]+)',match.group())
            pronoun=match.group() in ('anh ay','chi ay','nguoi do')
            antecedents=[q for q in a.mentions if q.scope_id==scope and q.message_id==m.id and q.role!='pronoun'] if pronoun else []
            candidates=list(dict.fromkeys(q.participant_id or q.mention_id for q in antecedents))
            if pronoun and len(candidates)==1 and antecedents and not antecedents[0].participant_id:
                pid=person('entity:'+antecedents[0].mention_id,'Người được nhắc chưa rõ danh tính; đại từ có một tiền ngữ')
                antecedents[0].participant_id=pid;antecedents[0].resolution='unique_antecedent';candidates=[pid]
            pid=person('named:'+token+':'+scope+':'+name.group(1),'Người được gọi tên trong văn bản') if name else candidates[0] if len(candidates)==1 else None
            a.mentions.append(PersonMention(mention_id=mid,message_id=m.id,scope_id=scope,role='pronoun' if pronoun else 'mentioned',participant_id=pid,
                candidate_ids=candidates,resolution='explicit_name' if name else 'unique_antecedent' if pid else 'unresolved',evidence_refs=[sid]))
    owner_by_scope=defaultdict(set)
    for e in a.events:
        info=text_for(e)
        if info and e.event_type=='receive_funds':
            text=normalize(info[3]).text
            if re.search(r'nhan du|da nhan|chua (?:nhan|thay)',text):
                if re.search(r'\b(?:toi|minh)\b',text):owner=info[4]
                else:owner=addressee(info[4],e.scope_id)
                owner_by_scope[e.scope_id].add(owner)
                if e.polarity=='positive' and re.search(r'nhan du|da nhan',text):e.temporal_state='completed'
    for e in a.events:
        info=text_for(e)
        if not info:continue
        m,start,end,raw,source,point=info;t=normalize(raw).text
        target=addressee(source,e.scope_id)
        owner=next(iter(owner_by_scope[e.scope_id])) if len(owner_by_scope[e.scope_id])==1 else None
        if e.event_type in ('handover_asset','receive_funds') and owner:affected=owner
        elif (e.event_type=='code_identity' or e.semantic and e.semantic.normalized_action=='independent_confirmation') and len(known_sources)==2:affected=source
        elif e.speech_role in ('claim','reported') and (re.search(r'\b(?:toi|minh)\s+(?:da|vua|chua|khong|tu)',t[:max(0,point-start)]) or re.search(r'hop dong toi',t)):affected=source
        else:affected=target
        if e.event_type=='other' and e.description=='hold_asset' and owner:affected=owner
        e.affected_party_id=affected
        if e.actor_id in (None,'recipient:unknown') or (e.actor_id and e.actor_id.startswith('old:')):
            e.actor_id=target if e.speech_role in ('request','denial') else source
        if e.recipient_id and e.recipient_id.startswith('old:'):e.recipient_id=None
        if not e.semantic:
            e.semantic=SemanticEvent(message_id=m.id,situation_id=e.scope_id,normalized_action=e.description if e.event_type=='other' else e.event_type)
        e.semantic.speaker_id=source;e.semantic.performer_id=e.actor_id;e.semantic.affected_party_id=affected;e.semantic.situation_id=e.scope_id
        reference=re.search(r'\b(?:khoan|don) (?:kia|nay|do)\b',t)
        e.semantic.transaction_reference=e.scope_id.split('/transaction:',1)[1] if '/transaction:' in e.scope_id else reference.group() if reference else None
        e.semantic.transaction_binding='explicit_code' if '/transaction:' in e.scope_id else 'unresolved'
        if e.speech_role=='request' and not e.semantic.is_reported_request:e.semantic.requester_id=source
        mentions=[q for q in a.mentions if q.message_id==m.id and any(spans[s].start>=start and spans[s].end<=end for s in q.evidence_refs)]
        e.semantic.mention_refs=[q.mention_id for q in mentions]
        recipients=[q for q in mentions if q.participant_id]
        if len(recipients)==1:e.recipient_id=recipients[0].participant_id
        elif len(mentions)==1:e.semantic.transfer_destination=mentions[0].mention_id
        if e.actor_id=='recipient:unknown':e.actor_id=None
    # Context carries the existing bound case, not an arbitrary global recipient.
    for e in a.events:
        if text_for(e):continue
        candidates={x.affected_party_id for x in a.events if x.scope_id==e.scope_id and x.speech_role=='request' and text_for(x)}
        affected=next(iter(candidates)) if len(candidates)==1 else person('unresolved:'+token+':'+e.event_id,'Bên bị tác động chưa giải quyết')
        if e.affected_party_id=='recipient:unknown':e.affected_party_id=affected
        if e.actor_id=='recipient:unknown':e.actor_id=affected
        if e.semantic:e.semantic.affected_party_id=e.affected_party_id;e.semantic.performer_id=e.actor_id
    for f in frames:
        e=next(e for e in a.events if e.event_id==f.action_event_id)
        f.speech_role=e.speech_role;f.target_id=e.actor_id
        f.scope_id=e.scope_id
        if e.semantic:f.requester_id=e.semantic.requester_id or e.semantic.speaker_id
        if f.benefit_event_id and not any(b.event_id==f.benefit_event_id and b.event_type in ('receive_funds','withdraw_funds') for b in a.events):
            f.benefit_event_id=None;f.condition=None
    valid=[];seen=set();emap={e.event_id:e for e in a.events}
    for r in a.relations:
        endpoints=[emap[x] for x in (r.from_id,r.to_id) if x in emap]
        reason='removed_endpoint' if any(x not in ids and x.startswith(('old:a','ctx:e','graph:e','safe:e','ground:e','bank:e')) for x in (r.from_id,r.to_id)) else None
        if len(endpoints)==2:
            if any(e.scope_id!=r.scope_id for e in endpoints):reason='scope_rebound'
            if endpoints[0].affected_party_id!=endpoints[1].affected_party_id:reason='participant_binding_mismatch'
            if any(e.speech_role in ('denial','quoted_warning','hypothetical') for e in endpoints) and r.type not in ('warning_about','reported_by'):reason='inactive_endpoint'
            if r.type=='contradiction' and any(e.semantic and e.semantic.speech_act=='conditional_nonperformance' for e in endpoints):reason='condition_not_contradictory_state'
            if {e.event_type for e in endpoints}&{'handover_asset'} and {e.event_type for e in endpoints}&{'receive_funds','transfer_funds'}:
                refs=[e.semantic.transaction_reference if e.semantic else None for e in endpoints]
                if any(refs) and refs[0]!=refs[1] and not all(e.semantic.transaction_binding=='explicit_code' for e in endpoints):reason='unresolved_transaction_reference'
        if reason:trace['removed_relations'].append({'id':r.relation_id,'reason':reason});continue
        key=(r.type,r.from_id,r.to_id)
        if key in seen:trace['removed_relations'].append({'id':r.relation_id,'reason':'duplicate_relation'});continue
        seen.add(key);valid.append(r)
    a.relations=valid
    def relate(kind,left,right,method):
        if left.scope_id!=right.scope_id or left.affected_party_id!=right.affected_party_id:return
        if {left.event_type,right.event_type}=={'receive_funds','handover_asset'} and left.semantic and right.semantic:
            refs=(left.semantic.transaction_reference,right.semantic.transaction_reference)
            if any(refs) and refs[0]!=refs[1]:return
        if any(r.type==kind and r.from_id==left.event_id and r.to_id==right.event_id for r in a.relations):return
        a.relations.append(Relation(relation_id='ground:r'+str(len(a.relations)+1),type=kind,from_id=left.event_id,to_id=right.event_id,
            scope_id=left.scope_id,status='inferred',evidence_refs=list(dict.fromkeys(left.evidence_refs+right.evidence_refs)),
            rationale='Đúng đối tượng/giao dịch và vai bị tác động sau kiểm chứng ngữ nghĩa; lời báo chưa được xác minh ngoài đời.',rule_id=method))
    for paid in [e for e in a.events if e.event_type=='receive_funds' and e.polarity=='positive' and e.temporal_state=='completed' and e.speech_role=='claim']:
        paid_info=text_for(paid)
        if paid_info and (paid_info[0].speaker_id in ('buyer','Người mua','người mua') or 'nguoi mua' in normalize(paid_info[4]).text):continue
        for hand in [e for e in a.events if e.event_type=='handover_asset' and e.speech_role=='request']:
            left=text_for(paid);right=text_for(hand)
            if left and right and left[0].id==right[0].id and left[1]<right[1]:relate('before',paid,hand,'REL-REPORTED-PAYMENT-FIRST')
    for loss in [e for e in a.events if e.semantic and e.semantic.normalized_action=='loss_consequence']:
        for ante in [e for e in a.events if e.semantic and e.semantic.speech_act=='conditional_nonperformance']:
            if set(loss.evidence_refs)&set(ante.evidence_refs) or text_for(loss) and text_for(ante) and text_for(loss)[1:3]==text_for(ante)[1:3]:
                relate('threatens_unless',loss,ante,'GROUND-CONDITIONAL-LOSS');ante.semantic.consequence_refs=[loss.event_id]
    for debt in [e for e in a.events if e.semantic and e.semantic.normalized_action=='exit_payment']:
        for custody in [e for e in a.events if e.event_type=='retain_identity_documents']:
            relate('release_conditioned_on_payment',debt,custody,'SG-LINK-EXIT-COST')
    for f in frames:
        if f.condition and not any(f.action_event_id in (r.from_id,r.to_id) and r.type in ('prerequisite_for','before') for r in a.relations):f.condition=None
    for payment in [e for e in a.events if e.semantic and e.semantic.speech_act=='deferred_until_verification']:
        for check in [e for e in a.events if e.semantic and e.semantic.normalized_action=='verify_information']:
            if text_for(check) and text_for(payment) and text_for(check)[1:3]==text_for(payment)[1:3]:
                relate('prerequisite_for',check,payment,'GROUND-VERIFY-BEFORE-PAYMENT')
    # Replace every surviving global placeholder. Equality is now role-bound to
    # a conversation/scope, explicit name, or unique mention, never "unknown".
    for rel in a.personal_relationships:
        scope=rel.scope_id or 'analysis';src=next(iter(known_sources))
        rel.participant_ids=[addressee(src,scope) if p=='recipient:unknown' else p for p in rel.participant_ids]
    for e in a.events:
        if e.recipient_id=='recipient:unknown':e.recipient_id=None
    rids={r.relation_id for r in a.relations};ids={e.event_id for e in a.events}
    for field in a.answers_18.__dict__.values():
        field.value.event_ids=list(dict.fromkeys(mapped(x) for x in field.value.event_ids if mapped(x) in ids))
        field.value.relation_ids=[x for x in field.value.relation_ids if x in rids]
        field.value.participant_ids=[x for x in field.value.participant_ids if x!='recipient:unknown']
        field.value.statements=[];field.evidence_refs=[];field.status='unknown'
    a.participants=[p for p in a.participants if p.participant_id!='recipient:unknown']
    a.grounding_trace=trace
    return a,frames


def check_coverage(input,a):
    """Bounded coverage sentinels distinguish lost explicit facts from unknowns."""
    spans={s.span_id:s for s in a.spans}
    probes=[('payment_status',r'\b(?:da|vua)\b.{0,65}\bnhan du tien\b','receive_funds'),
        ('document_receipt',r'\bnhan (?:duoc )?phu luc\b','other')]
    for m,start,end,raw,source in units(input):
        text=normalize(raw).text
        for field,pattern,kind in probes:
            if not re.search(pattern,text):continue
            found=any(e.event_type==kind and any(s in spans and spans[s].message_id==m.id and start<=spans[s].start<end for s in e.evidence_refs) for e in a.events)
            if not found:a.grounding_trace['coverage_gaps'].append({'message_id':m.id,'start':start,'end':end,'field':field,'reason':'explicit_fact_not_extracted'})
    if a.grounding_trace['coverage_gaps']:
        a.limitations.append('Phân tích một phần: có dữ kiện tường minh chưa được bộ trích biểu diễn; không quy thiếu dữ kiện cho người dùng.')
    return a


def finalize(input,a,interpretation,assessment):
    """Question selection uses known/unknown fields of the active situation."""
    spans={s.span_id:s for s in a.spans}
    for scope in {e.scope_id for e in a.events}:
        events=[e for e in a.events if e.scope_id==scope]
        raw=' '.join(spans[s].quote for e in events for s in e.evidence_refs if s in spans);n=normalize(raw).text
        states=[e for e in events if e.event_type=='receive_funds' and e.temporal_state in ('pending','completed')]
        for field,known,answered,refs in [
            ('payment_purpose',bool(re.search(r'hoa don|tra no|bao chung|(?:de|cho) thanh toan|nhan lai|rut tien',n)),bool(re.search(r'hoa don|tra no|bao chung|(?:de|cho) thanh toan|nhan lai|rut tien|chua ro.*khoan',n)),[s for e in events if e.event_type=='transfer_funds' for s in e.evidence_refs]),
            ('payment_status',bool(states),bool(states),[s for e in states for s in e.evidence_refs]),
            ('independent_confirmation',bool(re.search(r'da (?:tu )?goi.*xac nhan',n)),bool(re.search(r'(?:da|chua).*xac nhan|chua.*xac minh',n)),[s for e in events if e.semantic and e.semantic.normalized_action=='independent_confirmation' for s in e.evidence_refs])]:
            a.grounding_trace['field_needs'].append({'situation_id':scope,'field':field,'known':known,'answered':answered,'evidence_refs':list(dict.fromkeys(refs))})
    if assessment.risk_status=='high':return assessment
    losses=[e for e in a.events if e.semantic and e.semantic.normalized_action=='loss_consequence' and e.speech_role in ('claim','reported')]
    if losses and assessment.risk_status in ('clear','need_context'):
        assessment.risk_status='suspicious'
        assessment.summary='Nội dung nêu hoặc thuật lại sức ép mất khoản tiền nếu không nộp. Cần làm rõ căn cứ yêu cầu; chưa xác minh hậu quả đã xảy ra hoặc người thuật lại là bên đe dọa.'
        assessment.evidence_refs=list(dict.fromkeys(s for e in losses for s in e.evidence_refs))
        assessment.applicable_rule_ids=['GROUND-CONDITIONAL-PRESSURE']
        assessment.recommended_actions=['Đối chiếu căn cứ khoản phải nộp qua đầu mối độc lập trước khi làm theo.']
        assessment.follow_up_questions=['Bên đó yêu cầu nộp khoản nào và nêu căn cứ gì cho việc mất khoản tiền trước đó?']
        return assessment
    active=[e for e in a.events if e.speech_role=='request' and e.polarity=='positive']
    passive=all(e.semantic and (e.semantic.normalized_action in ('receive_document','send_document') or e.event_type=='receive_funds' and e.polarity=='positive' and e.temporal_state=='completed') for e in a.events)
    if not active and a.events and passive and not assessment.applicable_rule_ids:
        what='việc nhận tiền' if any(e.event_type=='receive_funds' for e in a.events) else 'trạng thái nhận hoặc gửi tài liệu'
        assessment.risk_status='clear';assessment.summary='Nội dung trao đổi '+what+'; chưa ghi nhận yêu cầu nguy hiểm còn hiệu lực trong phần đã phân tích.'
        assessment.follow_up_questions=[];assessment.missing_information=[]
        assessment.evidence_refs=list(dict.fromkeys(s for e in a.events for s in e.evidence_refs));return assessment
    paid={r.to_id for r in a.relations if r.rule_id=='REL-REPORTED-PAYMENT-FIRST'}
    harmless=[e for e in active if e.event_id in paid or e.semantic and e.semantic.normalized_action in ('hold_asset','verify_information')]
    strong=bool(assessment.applicable_rule_ids and assessment.risk_status=='suspicious')
    if not strong and active and len(harmless)==len(active):
        assessment.risk_status='clear';assessment.summary='Trong phần đã phân tích, yêu cầu giao hàng gắn với đúng giao dịch được báo đã nhận đủ tiền; phần chưa thanh toán được giữ lại hoặc chỉ yêu cầu kiểm tra thông tin.'
        assessment.evidence_refs=list(dict.fromkeys(s for r in a.relations if r.rule_id=='REL-REPORTED-PAYMENT-FIRST' for s in r.evidence_refs))
        if not paid:
            assessment.risk_status='need_context';assessment.summary='Có yêu cầu kiểm tra thông tin, chưa ghi nhận yêu cầu chuyển tiền đang có hiệu lực; cần đối chiếu thay đổi trước khi thanh toán.'
        else:assessment.follow_up_questions=[];assessment.missing_information=[];return assessment
    payments=[e for e in active if e.event_type=='transfer_funds']
    if payments and assessment.risk_status=='need_context':
        spans={s.span_id:s for s in a.spans};text=' '.join(spans[s].quote for e in payments for s in e.evidence_refs if s in spans)
        n=normalize(text).text
        purpose_known=bool(re.search(r'\b(?:de|cho) thanh toan|hoa don|tien dien|tien nuoc|tra no|bao chung|rut tien|nhan lai',n))
        questions=[]
        if not purpose_known:questions.append('Khoản này dùng để thanh toán việc gì?')
        if not re.search(r'nguoi khac|tai khoan.{0,15}(?:toi|minh|anh|chi|em)|cho (?:toi|em|anh|chi)',n):
            questions.append('Ai là người thụ hưởng khoản thanh toán và thông tin đó có khớp thỏa thuận không?')
        if questions:
            assessment.follow_up_questions=questions[:2]
            a.grounding_trace['question_bindings']=[{'situation_id':payments[0].scope_id,'field':'payment_purpose' if not purpose_known else 'payee','answered':False}]
    elif assessment.risk_status=='need_context' and any(s.conflicting_refs for s in interpretation.situations):
        assessment.follow_up_questions=['Các nguồn đang mô tả khác nhau về cùng khoản thanh toán. Người nhận xác nhận trạng thái nào sau khi kiểm tra lại giao dịch đó?']
    elif assessment.risk_status=='need_context' and any(e.event_type=='handover_asset' and e.event_id not in paid for e in active):
        assessment.follow_up_questions=['Khoản thanh toán vào tài khoản và yêu cầu giao hàng có thuộc cùng một đơn không? Bạn có thể cho biết mã đơn tương ứng?']
    elif assessment.risk_status=='need_context' and any(e.semantic and e.semantic.object_type=='unknown' for e in active):
        assessment.follow_up_questions=['Nội dung đang yêu cầu chuyển hoặc gửi thứ gì? Chỉ mô tả loại thông tin, không gửi mã thật hay mật khẩu.']
    return assessment


def project(a):
    """Discard stale text and regenerate summary fields from surviving facts."""
    spans={s.span_id:s for s in a.spans}
    groups={'claims':[e for e in a.events if e.speech_role in ('claim','reported')],
        'requested_actions':[e for e in a.events if e.speech_role=='request' and e.polarity=='positive'],
        'assets_and_access':[e for e in a.events if e.event_type in ('transfer_funds','receive_funds','withdraw_funds','handover_asset','provide_code','provide_credentials','retain_identity_documents','grant_control','share_screen') and e.speech_role not in ('quoted_warning','denial','hypothetical')],
        'action_targets':[e for e in a.events if e.affected_party_id],
        'sender_identity':[e for e in a.events if e.event_type in ('identity_claim','relationship_claim')]}
    for key,events in groups.items():
        field=getattr(a.answers_18,key)
        field.value.event_ids=[e.event_id for e in events]
        field.evidence_refs=list(dict.fromkeys(s for e in events for s in e.evidence_refs))
        field.value.statements=list(dict.fromkeys(next((spans[s].quote for s in e.evidence_refs if s in spans and spans[s].label in ('action','statement')),spans[e.evidence_refs[0]].quote) for e in events))
        field.status='unknown' if not events else 'claimed' if key=='claims' else 'observed'
        field.extraction_method='grounding-2.0-projection'
    for key in ('conditions_and_sequence','contradictions_and_alternatives'):
        rels=a.relations if key=='conditions_and_sequence' else [r for r in a.relations if r.type in ('contradiction','state_update')]
        field=getattr(a.answers_18,key);field.value.relation_ids=[r.relation_id for r in rels]
        field.value.event_ids=list(dict.fromkeys(x for r in rels for x in (r.from_id,r.to_id) if any(e.event_id==x for e in a.events)))
        field.evidence_refs=list(dict.fromkeys(s for r in rels for s in r.evidence_refs));field.value.statements=list(dict.fromkeys(r.rationale for r in rels))
        field.status='inferred' if rels else 'unknown';field.extraction_method='grounding-2.0-projection'
