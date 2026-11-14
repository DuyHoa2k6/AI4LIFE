"""Graph, roles, directed relations and controls; public draft regression, not gold."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.diagnostics import capture_traces
from backend.local_reasoning.schema import CaseInput,Span,Event,SemanticEvent,Attribution,Relation,Assessment
from backend.local_reasoning.extract import base
from backend.local_reasoning.semantic_contract import assess,VERSION
from backend.local_reasoning.validation import annotation_errors

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def outputs():
    results={}
    with TestClient(app) as client:
        for row in map(json.loads,(ROOT/'fixtures/reasoning_document_20261114/inputs.jsonl').read_text(encoding='utf-8').splitlines()):
            with capture_traces() as traces:r=client.post('/api/analyze',json=row['request'])
            assert r.status_code==200 and len(traces)==1
            q=CaseInput(messages=[{'id':m['id'],'speaker_id':m['speaker'],'text':m['text'],'scope_id':'analysis'} for m in row['request']['messages']])
            results[row['case_id']]=(r.json(),traces[0],q)
    return results

@pytest.mark.parametrize('cid,required',[
 ('TH01',{'sign_obligation','misstate_information','describe_terms'}),('TH02',{'provide_documents'}),
 ('TH03',{'purchase_asset','transfer_ownership','describe_terms'}),('TH04',{'sign_obligation','withhold_wages','restrict_movement'}),
 ('TH05',{'confirm_completion','release_funds','handover_asset'}),('TH06',{'verification_request','verification_status','transfer_funds'}),
 ('TH07',{'grant_authority','describe_terms'}),('TH08',{'provide_credentials','recover_access','misstate_information'}),
 ('TH09',{'grant_asset_access','verification_status'}),('TH10',{'transfer_funds','verification_status'}),
 ('TH11',{'return_funds','receive_funds'}),('TH12',{'guarantee_debt','describe_terms'}),('TH13',{'describe_terms'}),
 ('TH14',{'other'}),('TH15',{'verification_status','transfer_funds'}),('TH16',{'other'})])
def test_required_events_and_real_request_binding(outputs,cid,required):
    response,trace,q=outputs[cid];a=trace['annotations']
    assert required<={e['event_type'] for e in a['events']}
    assert response['request_id']==trace['request_id']
    from backend.local_reasoning.schema import Annotations
    assert annotation_errors(q,Annotations.model_validate(a))==[]
    gate=a['grounding_trace']['semantic_contract']
    assert set(gate['policy_event_ids'])=={e['event_id'] for e in a['events']}
    assert set(gate['policy_relation_ids'])=={r['relation_id'] for r in a['relations']}

@pytest.mark.parametrize('cid,kind,left,right',[
 ('TH01','prerequisite_for','misstate_information','sign_obligation'),('TH01','contradiction','describe_terms','describe_terms'),
 ('TH03','funding_ownership_mismatch','purchase_asset','transfer_ownership'),('TH04','coerced_by','sign_obligation','withhold_wages'),
 ('TH05','prerequisite_for','confirm_completion','release_funds'),('TH05','before','release_funds','handover_asset'),
 ('TH06','unverified_authority','transfer_funds','verification_status'),('TH07','exceeds_scope','grant_authority','describe_terms'),
 ('TH08','transfers_control','provide_credentials','recover_access'),('TH09','prerequisite_for','grant_asset_access','describe_terms'),
 ('TH10','unverified_authority','transfer_funds','verification_status'),('TH11','before','return_funds','receive_funds'),
 ('TH12','liability_if_default','guarantee_debt','describe_terms')])
def test_directed_relation_endpoints_evidence(outputs,cid,kind,left,right):
    response,trace,_=outputs[cid];a=trace['annotations'];es={e['event_id']:e for e in a['events']}
    matches=[r for r in a['relations'] if r['type']==kind and es[r['from_id']]['event_type']==left and es[r['to_id']]['event_type']==right]
    assert matches
    for r in matches:
        x,y=es[r['from_id']],es[r['to_id']]
        assert set(x['evidence_refs']+y['evidence_refs'])<=set(r['evidence_refs'])
        assert x['scope_id']==y['scope_id']==r['scope_id']

def test_scholarship_no_fake_payment_or_obstruction(outputs):
    _,t,_=outputs['TH02']
    assert not [e for e in t['annotations']['events'] if e['event_type'] in ('transfer_funds','avoid_verification') and e['speech_role']=='request' and e['polarity']=='positive']
    assert not any(e['event_type']=='handover_asset' for e in t['annotations']['events'])

def test_user_reports_and_independent_transactions(outputs):
    _,t,_=outputs['TH15'];payments=[e for e in t['annotations']['events'] if e['event_type']=='transfer_funds']
    assert {e['scope_id'] for e in payments}=={'analysis/transaction:A','analysis/transaction:B'}
    confirmations=[e for e in t['annotations']['events'] if e['semantic'] and 'reported_verified' in e['semantic']['traits']]
    assert len(confirmations)==2 and all(e['semantic']['information_status']=='user_reported' for e in confirmations)
    assert not any(e['event_type']=='avoid_verification' for e in t['annotations']['events'])

def test_unknown_sources_and_alternatives_not_payments(outputs):
    _,t,_=outputs['TH16'];a=t['annotations']
    sources=[e['semantic']['speaker_id'] for e in a['events'] if e['semantic'] and e['semantic']['object_type']=='reported_unresolved']
    assert len(set(sources))==2
    assert not any(e['event_type']=='transfer_funds' for e in a['events'])
    assert 'thanh toán' not in ' '.join(t['assessment']['follow_up_questions'])
    assert len(t['assessment']['follow_up_questions'])<=2

def test_negated_coordination_and_unknown_purpose(outputs):
    _,t,_=outputs['TH14']
    assert not any(e['event_type'] in ('transfer_funds','provide_code') and e['speech_role']=='request' for e in t['annotations']['events'])
    assert 'ủy quyền' in t['assessment']['follow_up_questions'][0]

def oracle(reverse=False,denied=False):
    q=CaseInput(messages=[{'id':'m1','speaker_id':'worker','text':'Ký nhận nợ. Lương bị giữ tới khi ký.','scope_id':'S'}]);a=base(q)
    for i,(kind,text) in enumerate([('sign_obligation','Ký nhận nợ.'),('withhold_wages','Lương bị giữ tới khi ký.')]):
        start=q.messages[0].text.index(text);sid='s'+str(i);eid='e'+str(i)
        a.spans.append(Span(span_id=sid,message_id='m1',start=start,end=start+len(text),quote=text,label='statement'))
        a.events.append(Event(event_id=eid,event_type=kind,description=kind,actor_id='speaker:worker',affected_party_id='speaker:worker',object='financial_obligation' if i==0 else 'wages',polarity='positive',modality='request',temporal_state='requested',speech_role='denial' if denied else 'request',attribution=Attribution(speaker_id='worker',kind='sender_claim'),status='inferred',scope_id='S',evidence_refs=[sid],extractor_rule_id=VERSION,semantic=SemanticEvent(message_id='m1',situation_id='S',normalized_action=kind,extraction_method=VERSION)))
    a.relations.append(Relation(relation_id='r1',type='coerced_by',from_id='e1' if reverse else 'e0',to_id='e0' if reverse else 'e1',evidence_refs=['s0','s1'],status='inferred',scope_id='S',rationale='Explicit reviewed-for-test condition, synthetic draft.',rule_id=VERSION))
    a.grounding_trace['semantic_contract']={'clauses':[]};assert annotation_errors(q,a)==[]
    previous=Assessment(risk_status='need_context',safety_urgency='undetermined',supported_conclusions=[],evidence_refs=[],applicable_rule_ids=[],missing_information=[],follow_up_questions=[],recommended_actions=[],explanation_template_id='TEST',prohibited_conclusions=[],summary='Test draft')
    return assess(q,a,previous,'complete')[0]

def test_oracle_structured_data_uses_directed_relation():
    a=oracle();assert a.risk_status=='high' and a.evidence_refs==['s0','s1'] and a.applicable_rule_ids==['SC-coerced_by']

def test_oracle_reversed_or_denied_not_high():
    assert oracle(reverse=True).risk_status!='high'
    assert oracle(denied=True).ris