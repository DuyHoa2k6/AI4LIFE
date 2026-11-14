"""Optional learned extractor -> existing local/API contract, with no rule fallback."""
import hashlib
import threading
from functools import lru_cache
from pathlib import Path
from ..settings import get_setting
from .extract import base
from .schema import LocalResult,Assessment,Span,Event,Relation,Attribution,SemanticEvent

ROOT=Path(__file__).resolve().parents[2]
_initialization=threading.Lock()

@lru_cache(maxsize=2)
def _load(path,allow):
    from ml.phobert.inference import Runtime
    return Runtime(path,allow_experimental=allow)

def get_runtime():
    location=Path(get_setting('SCAMSHIELD_PHOBERT_CHECKPOINT',str(ROOT/'artifacts/phobert/smoke_heads')))
    if not location.is_absolute():location=ROOT/location
    with _initialization:return _load(str(location.resolve()),get_setting('SCAMSHIELD_PHOBERT_ALLOW_EXPERIMENTAL','0')=='1')

def analyze(input):
    import time
    started=time.perf_counter();annotations=base(input);a=None;failure=None
    prohibited=['Không xác nhận người gửi phạm tội.','Không xác nhận danh tính hoặc nội dung đe dọa là thật.']
    try:
        if input.context_facts:raise ValueError('context_training_not_available')
        result=get_runtime().predict({'messages':[{'id':m.id,'speaker_id':m.speaker_id,'text':m.text} for m in input.messages]})
        graph=result['graph'];a=result['assessment'];by_id={m.id:m for m in input.messages}
        annotations.spans=[Span(span_id=s['id'],message_id=s['message_id'],start=s['start'],end=s['end'],quote=s['quote'],label='participant' if s['label']=='entity' else s['label'],review_status='weak_label') for s in graph['spans']]
        span_map={s.span_id:s for s in annotations.spans};person_ids={p.participant_id for p in annotations.participants}
        type_map={'transfer':'transfer_funds','receive':'receive_funds','disclose_credentials':'provide_credentials','grant_control':'grant_control','share_screen':'share_screen','install':'install_app','retain_documents':'retain_identity_documents','restrict_exit':'restrict_movement','threaten_disclosure':'threaten_disclosure','withdraw':'withdraw_funds','handover':'handover_asset','avoid_verification':'avoid_verification','login':'login'}
        for e in graph['events']:
            v=e['attributes'];s=span_map[e['anchor_id']];roles=e['roles'];kind=type_map.get(v['action_type'],'other')
            if v['action_type']=='receive' and v['object_type']!='money':kind='other'
            speaker=by_id[s.message_id].speaker_id
            annotations.events.append(Event(event_id=e['id'],event_type=kind,description=s.quote,
              actor_id=roles.get('performer') if roles.get('performer') in person_ids else None,
              affected_party_id=roles.get('affected_party') if roles.get('affected_party') in person_ids else None,
              recipient_id=roles.get('recipient') if roles.get('recipient') in person_ids else None,
              object=v['object_type'],polarity=v['polarity'],modality='possibility' if v['modality']=='promise' else v['modality'],
              temporal_state={'not_completed':'pending','future':'planned'}.get(v['temporal_state'],v['temporal_state']),
              speech_role='denial' if v['speech_act']=='prohibition' else v['speech_act'],
              attribution=Attribution(speaker_id=speaker,kind='quoted_warning' if v['speech_act']=='quoted_warning' else 'sender_claim'),
              status='inferred',scope_id=e.get('transaction_id') or 'analysis',evidence_refs=[e['anchor_id']],extractor_rule_id='phobert-learned-heads',
              semantic=SemanticEvent(message_id=s.message_id,situation_id=e.get('transaction_id') or 'analysis',speaker_id=speaker,
                requester_id=roles.get('requester'),performer_id=roles.get('performer'),affected_party_id=roles.get('affected_party'),
                normalized_action=v['action_type'],object_type=v['object_type'],speech_act=v['speech_act'],extraction_method='phobert-structured-1.0')))
        annotations.relations=[Relation(relation_id=r['id'],type=r['label'],from_id=r['source'],to_id=r['target'],evidence_refs=r['evidence_refs'],status='inferred',scope_id='analysis',rationale='Quan hệ do head PhoBERT dự đoán, đã kiểm tra tham chiếu và phạm vi.',rule_id='phobert-relation-head') for r in graph['relations']]
        annotations.graph_trace={'phobert':graph,'decision_rules':a['rules'],'classifier_baseline':result['classifier_baseline'],'classifier_disagrees':result['classifier_disagrees']}
        annotations.limitations=graph['limitations']+['Checkpoint nghiên cứu chưa được kiểm chứng chất lượng trên dữ liệu độc lập.']
        mapping={'situation':annotations.events,'requested_actions':[e for e in annotations.events if e.speech_role=='request'],
          'claims':[e for e in annotations.events if e.speech_role in ('claim','reported')],
          'action_targets':annotations.events,'assets_and_access':annotations.events,
          'contradictions_and_alternatives':[e for e in annotations.events if e.polarity=='negative' or e.speech_role in ('denial','quoted_warning')]}
        for key,events in mapping.items():
            if not events:continue
            field=getattr(annotations.answers_18,key);field.status='inferred';field.value.event_ids=[e.event_id for e in events];field.evidence_refs=[s for e in events for s in e.evidence_refs];field.value.statements=[span_map[e.evidence_refs[0]].quote for e in events]
        if annotations.relations:
            f=annotations.answers_18.conditions_and_sequence;f.status='inferred';f.value.relation_ids=[r.relation_id for r in annotations.relations];f.evidence_refs=list({s for r in annotations.relations for s in r.evidence_refs})
        f=annotations.answers_18.participants;f.status='observed';f.value.participant_ids=[p.participant_id for p in annotations.participants if p.interaction_role=='speaker']
        timings=result['timings_ms'];elapsed=timings['total']
    except (ImportError,RuntimeError,OSError,ValueError,TimeoutError) as exc:
        failure='busy' if type(exc).__name__=='ModelBusy' else 'checkpoint_or_runtime' if not isinstance(exc,ValueError) else 'unsupported_context_or_input'
        annotations.limitations=['PhoBERT chưa xử lý được đầu vào; không tự chuyển sang luật, mock hay API ngoài.']
        a={'analysis_status':'unsupported' if isinstance(exc,ValueError) else 'error','risk_status':None,'summary':'Chưa kiểm tra được bằng PhoBERT cục bộ.','action':'Kiểm tra checkpoint, dependency và phạm vi hỗ trợ.','evidence_refs':[],'rules':[],'missing':[],'questions':[]};timings={};elapsed=(time.perf_counter()-started)*1000
    assessment=Assessment(risk_status=a['risk_status'],safety_urgency='undetermined',supported_conclusions=[a['summary']] if a['risk_status'] else [],
      evidence_refs=a['evidence_refs'],applicable_rule_ids=[r['rule_id'] for r in a['rules']],missing_information=a['missing'],follow_up_questions=a['questions'],
      recommended_actions=[a['action']],explanation_template_id='PB-STRUCTURED',prohibited_conclusions=prohibited,summary=a['summary'])
    annotations.answers_18.assessment.status='inferred' if a['risk_status'] else 'unknown';annotations.answers_18.assessment.value.statements=[a['summary']];annotations.answers_18.assessment.evidence_refs=a['evidence_refs']
    annotations.answers_18.missing_information.missing_information=a['missing']
    return LocalResult(analysis_status=a['analysis_status'],input_sha256=hashlib.sha256(input.model_dump_json().encode()).hexdigest(),annotations=annotations,
      assessment=assessment,knowledge_status='not_checked',versions={'reasoner':'phobert','extractor':'phobert-structured-1.0','rulebook':'phobert-graph-rules-1.0',**({'failure_kind':failure} if failure else {})},elapsed_ms=elapsed,core_timings_ms=timings,
      support_warnings=['PhoBERT đang ở chế độ nghiên cứu; điểm mô hình chưa được hiệu chuẩn.'])
