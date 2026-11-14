"""Evidence-backed event/relation -> facts, normalized once, indexed by scope/type."""
from collections import defaultdict
from datetime import datetime,timezone
import re
from ..local_observation.text import normalize,quote_ranges
from .fact_schema import FactRecord,Truth
from .validation import annotation_errors

NAMES={'handover_asset':'handover_requested','receive_funds':'payment_confirmed',
       'transfer_funds':'transfer_requested','provide_code':'code_requested',
       'provide_credentials':'credentials_requested','provide_documents':'documents_requested',
       'install_app':'install_requested','share_screen':'screen_share_requested','grant_control':'control_requested'}


def fact_type(event_type):return NAMES.get(event_type,event_type)


class FactStore:
    def __init__(self):
        self.facts=[];self.by_type=defaultdict(list);self.by_id={};self.by_event={}
        self.relations={};self.conflicts=[];self.discarded=[];self.verified_scopes=set()
        self.now=datetime.now(timezone.utc)

    def add(self,**kwargs):
        fact=FactRecord(observed_at=self.now,**kwargs)
        self.facts.append(fact);self.by_type[fact.fact_type].append(fact);self.by_id[fact.fact_id]=fact
        return fact

    def candidates(self,types):
        return [f for t in types for f in self.by_type[t] if f.superseded_by is None]


def build_facts(input,a):
    if annotation_errors(input,a):raise ValueError('Invalid evidence or reference before fact construction')
    store=FactStore();spans={s.span_id:s for s in a.spans};events={e.event_id:e for e in a.events}
    for event in a.events:
        value=Truth.TRUE if event.polarity=='positive' else Truth.FALSE if event.polarity=='negative' else Truth.UNKNOWN
        if event.event_type=='receive_funds' and value is Truth.TRUE and event.temporal_state!='completed':value=Truth.UNKNOWN
        source='user_report' if event.attribution.kind in ('user_report','self_report') else 'sender_claim' if event.attribution.kind in ('sender_claim','reported') else 'observed_content'
        attributes={'event_type':event.event_type,'speech_role':event.speech_role,'temporal_state':event.temporal_state,
                    'attribution_kind':event.attribution.kind,'speaker':event.attribution.speaker_id or '',
                    'affected_party':event.affected_party_id or '', 'status':event.status}
        refs=event.evidence_refs
        f=store.add(fact_id='fact:'+event.event_id,fact_type='bank_information_requested' if event.extractor_rule_id=='FACT-BANK-INFO-1' else fact_type(event.event_type),value=value,
            participant_ids=list(dict.fromkeys(x for x in (event.actor_id,event.recipient_id,event.affected_party_id) if x)),
            scope_id=event.scope_id,transaction_id=event.scope_id.split('/transaction:',1)[1] if event.scope_id and '/transaction:' in event.scope_id else None,
            source=source,evidence_refs=refs,event_time=event.event_time,event_id=event.event_id,attributes=attributes)
        store.by_event[event.event_id]=f
        role=Truth.UNKNOWN if event.speech_role=='unknown' else Truth.TRUE if event.speech_role=='request' else Truth.FALSE
        store.add(fact_id=f.fact_id+':direct',fact_type='direct_request',value=role,scope_id=f.scope_id,source='observed_content',
                  participant_ids=f.participant_ids,evidence_refs=refs,event_id=event.event_id)
        for label in ('quoted_warning','denial'):
            store.add(fact_id=f.fact_id+':'+label,fact_type=label,value=Truth.UNKNOWN if event.speech_role=='unknown' else Truth.TRUE if event.speech_role==label else Truth.FALSE,
                      scope_id=f.scope_id,source='observed_content',participant_ids=f.participant_ids,evidence_refs=refs,event_id=event.event_id)
        if event.event_type in ('provide_code','provide_credentials','code_identity'):
            text=normalize(' '.join(spans[s].quote for s in refs)).text
            auth=Truth.TRUE if event.event_type in ('provide_credentials','code_identity') or any(x in text for x in ('otp','ma dang nhap','ma xac thuc','ma xac nhan')) else Truth.FALSE if any(x in text for x in ('ma don hang','ma van don','ma san pham')) else Truth.UNKNOWN
            store.add(fact_id=f.fact_id+':auth',fact_type='authentication_meaning',value=auth,scope_id=f.scope_id,source='observed_content',
                      participant_ids=f.participant_ids,evidence_refs=refs,event_id=event.event_id)
    for relation in a.relations:
        dependencies=['fact:'+x for x in (relation.from_id,relation.to_id) if x in store.by_event]
        if not dependencies:continue
        value=Truth.UNKNOWN if relation.status=='unknown' else Truth.TRUE
        f=store.add(fact_id='fact:'+relation.relation_id,fact_type='relation:'+relation.type,value=value,
                  scope_id=relation.scope_id,source='derived',evidence_refs=relation.evidence_refs,
                  participant_ids=list(dict.fromkeys(p for d in dependencies for p in store.by_id[d].participant_ids)),
                  dependency_refs=list(dict.fromkeys(dependencies)),rule_id=relation.rule_id,
                  attributes={'from_id':relation.from_id,'to_id':relation.to_id,'status':relation.status})
        store.relations[(relation.type,relation.from_id,relation.to_id)]=f
    # A later observation timestamp is NOT an event timestamp. Only a grounded
    # state_update from the same claimant and transaction can supersede a claim.
    for relation in a.relations:
        if relation.type!='state_update' or relation.status=='unknown':continue
        old=store.by_event.get(relation.from_id);new=store.by_event.get(relation.to_id)
        if not old or not new or old.fact_type!=new.fact_type or old.scope_id!=new.scope_id:continue
        if old.attributes['affected_party']!=new.attributes['affected_party']:continue
        old_event=events[relation.from_id];new_event=events[relation.to_id]
        old_messages={spans[s].message_id for s in old.evidence_refs};new_messages={spans[s].message_id for s in new.evidence_refs}
        same_claimant=bool(old.attributes['speaker']) and old.attributes['speaker']==new.attributes['speaker']
        if not same_claimant and not (old_messages==new_messages and len(old_messages)==1):continue
        if new.attributes['speech_role'] in ('quoted_warning','hypothetical','unknown') or new.value is Truth.UNKNOWN:continue
        old.superseded_by=new.fact_id;new.version=old.version+1
        # Do not depend on the relation fact: it already depends on this new
        # observation, which would introduce a cycle in the dependency graph.
        new.dependency_refs=list(dict.fromkeys(new.dependency_refs+[old.fact_id]))
        new.attributes['update_relation_id']='fact:'+relation.relation_id
        new.rule_id='UPDATE-SAME-CLAIMANT-STATE'
    groups=defaultdict(list)
    for f in store.by_type['payment_confirmed']:
        if f.superseded_by is None and f.attributes['speech_role'] not in ('quoted_warning','hypothetical','denial','unknown') and f.attributes['temporal_state'] not in ('past','hypothetical'):
            groups[(f.scope_id,f.attributes['affected_party'])].append(f)
    for group in groups.values():
        if any(f.value is Truth.TRUE for f in group) and any(f.value is Truth.FALSE for f in group):
            store.conflicts.append([f.fact_id for f in group])
            store.add(fact_id='conflict:payment:'+str(len(store.conflicts)),fact_type='payment_resolution',value=Truth.UNKNOWN,
                      scope_id=group[0].scope_id,source='derived',participant_ids=list(dict.fromkeys(p for f in group for p in f.participant_ids)),
                      evidence_refs=list(dict.fromkeys(r for f in group for r in f.evidence_refs)),
                      dependency_refs=[f.fact_id for f in group],rule_id='UNRESOLVED-PAYMENT-CLAIMS')
    for event in a.events:
        if event.event_type!='handover_asset':continue
        if not any(f.scope_id==event.scope_id and f.attributes.get('affected_party')==(event.affected_party_id or '') for f in store.by_type['payment_confirmed']):
            store.add(fact_id='unknown:payment:'+event.event_id,fact_type='payment_confirmed',value=Truth.UNKNOWN,
                      scope_id=event.scope_id,participant_ids=[event.affected_party_id] if event.affected_party_id else [],
                      source='observed_content',attributes={'reason':'missing_payment_observation'})
    for context in input.context_facts:
        text=normalize(context.text).text
        targets=set(context.applies_to_message_ids) or ({input.messages[0].id} if len(input.messages)==1 else set())
        if any(x in text for x in ('da goi','tu kiem tra','da doi chieu')):
            for m in input.messages:
                if m.id in targets:store.verified_scopes.add(m.scope_id or 'message:'+m.id)
        ref='context:'+context.id
        if ref in spans:
            context_fact=store.add(fact_id='user:'+context.id,fact_type='user_context_provided',value=Truth.TRUE,scope_id=None,
                      source='user_report',evidence_refs=[ref],attributes={'context_id':context.id})
            checked=bool(re.search(r'\btoi (?:da )?(?:tu )?kiem tra\b',text))
            received=bool(re.search(r'\b(?:da nhan du tien|nhan du tien|tien da vao tai khoan)\b',text))
            negated=bool(re.search(r'\b(?:khong|chua)\s+(?:\w+\s+){0,3}(?:nhan|thay|xac nhan|tien)\b',text))
            reported=bool(re.search(r'nguoi mua noi|nguoi gui noi|ho noi|trich|canh bao|gia su|\bneu\b',text) or quote_ranges(context.text))
            eligible=[f for f in store.by_event.values() if f.fact_type in ('payment_confirmed','handover_requested')
                      and {spans[s].message_id for s in f.evidence_refs if s in spans and spans[s].message_id}<=targets]
            scopes={f.scope_id for f in eligible if f.scope_id is not None}
            # No attachment to all transactions in a long conversation: a user
            # update must resolve to one known scope and explicit verification.
            if checked and received and not negated and not reported and len(scopes)==1 and targets:
                scope=next(iter(scopes))
                transaction_mentions={m.group() for m in re.finditer(r'\b(?:don|giao dich|hop dong)\s+[a-z0-9]+\b',text)
                                      if m.group().rsplit(' ',1)[-1] not in ('nay','do','hang','cua','da','chua')}
                expected_transaction=scope.split('/transaction:',1)[1] if '/transaction:' in scope else None
                if transaction_mentions and transaction_mentions!={expected_transaction}:continue
                previous=[f for f in eligible if f.fact_type=='payment_confirmed' and f.superseded_by is None]
                previous += [f for f in store.by_type['payment_confirmed'] if f.scope_id==scope and f.event_id is None and f.superseded_by is None]
                updated=store.add(fact_id='user:payment:'+context.id,event_id='user:payment:'+context.id,
                    fact_type='payment_confirmed',value=Truth.TRUE,scope_id=scope,source='user_report',evidence_refs=[ref],
                    participant_ids=list(dict.fromkeys(p for f in eligible for p in f.participant_ids)),
                    version=1+max((f.version for f in previous),default=0),dependency_refs=[context_fact.fact_id]+[f.fact_id for f in previous],
                    rule_id='UPDATE-USER-REPORTED-VERIFICATION',attributes={'speech_role':'claim','temporal_state':'completed',
                        'attribution_kind':'user_report','speaker':'user_context','affected_party':eligible[0].attributes.get('affected_party',''),
                        'status':'claimed','event_type':'receive_funds','user_reports_verification':'true'})
                store.by_event[updated.event_id]=updated
                for old in previous:old.superseded_by=updated.fact_id
                for conflict in store.by_type['payment_resolution']:
                    if conflict.scope_id==scope:conflict.superseded_by=updated.fact_id
                store.conflicts=[group for group in store.conflicts if not any(fid in {f.fact_id for f in previous} for fid in group)]
    coverage=Truth.UNKNOWN if not a.events else Truth.FALSE if any('giới hạn' in x or 'chưa được phân tích' in x or 'phân tích một phần' in x for x in a.limitations) else Truth.TRUE
    # Quality predicates describe the analysis, not the truth of the sender's claims.
    first=next(iter(spans.values()),None)
    store.add(fact_id='quality:coverage',fact_type='analysis_coverage',value=coverage if first else Truth.UNKNOWN,
              scope_id=None,source='technical_check',evidence_refs=[first.span_id] if first else [])
    return store
