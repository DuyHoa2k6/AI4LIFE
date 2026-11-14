"""Three-valued reference, provenance, scope, update and API regression tests.

Synthetic fact matrices test the decision layer, not extraction accuracy.
"""
import copy
from itertools import product
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_reasoning.schema import CaseInput,Span,Event,Attribution,Relation
from backend.local_reasoning.extract import base,extract
from backend.local_reasoning.engine import analyze_local,load_assets
from backend.local_reasoning.facts import FactStore,build_facts
from backend.local_reasoning.fact_schema import Truth,conjunction,FactRecord
from backend.local_reasoning.fact_decision import evaluate_rule,assess


def query(text):return CaseInput(messages=[{'id':'m1','speaker_id':'user','scope_id':'case','text':text}])


def matrix_store(rule):
    s=FactStore()
    for slot,c in rule.required_conditions.items():
        f=s.add(fact_id=slot,event_id=slot,fact_type=c.fact_types[0],value=c.value,scope_id='case',source='observed_content',
            evidence_refs=['span:'+slot],participant_ids=['recipient'],attributes={'speech_role':c.speech_roles[0],
            'status':'observed','temporal_state':c.temporal_states[0] if c.temporal_states else 'requested',
            'attribution_kind':c.attribution_kinds[0] if c.attribution_kinds else 'sender_claim','affected_party':'recipient'})
        s.by_event[slot]=f
        if c.authentication_meaning is not None:
            s.add(fact_id=f.fact_id+':auth',fact_type='authentication_meaning',value=c.authentication_meaning,
                  scope_id='case',source='observed_content',evidence_refs=f.evidence_refs)
    for i,r in enumerate(rule.required_relations):
        f=s.add(fact_id='r'+str(i),fact_type='relation:'+r.type,value=Truth.TRUE,scope_id='case',source='derived',
                evidence_refs=['span:'+r.from_fact,'span:'+r.to_fact],dependency_refs=[r.from_fact,r.to_fact],rule_id='TEST-REL')
        s.relations[(r.type,r.from_fact,r.to_fact)]=f
    return s


def payment_graph(update=False,buyer=False,different_transaction=False):
    inputs=CaseInput(messages=[{'id':'m1','speaker_id':'seller','scope_id':'trade','text':'Chưa nhận tiền. Giao máy trước.'},
                              {'id':'m2','speaker_id':'buyer' if buyer else 'seller','scope_id':'other' if different_transaction else 'trade','text':'Đã nhận đủ tiền.'}])
    a=base(inputs)
    for sid,mid,start,end in [('s1','m1',0,14),('s2','m1',16,30),('s3','m2',0,16)]:
        m=next(m for m in inputs.messages if m.id==mid)
        a.spans.append(Span(span_id=sid,message_id=mid,start=start,end=min(end,len(m.text)),quote=m.text[start:end],label='action'))
    def event(eid,kind,polarity,speaker,ref,time,state='pending',scope='trade',role='claim'):
        return Event(event_id=eid,event_type=kind,description=kind,actor_id=None,affected_party_id='recipient:unknown',
            polarity=polarity,modality='request' if role=='request' else 'assertion',temporal_state=state,speech_role=role,
            attribution=Attribution(speaker_id=speaker,kind='sender_claim'),status='claimed',scope_id=scope,event_time=time,
            evidence_refs=[ref],extractor_rule_id='TEST-ANNOTATION')
    a.events=[event('negative','receive_funds','negative','seller','s1','before'),
              event('handover','handover_asset','positive','seller','s2',None,'requested',role='request'),
              event('positive','receive_funds','positive','buyer' if buyer else 'seller','s3','after','completed','other' if different_transaction else 'trade')]
    for rid,kind,left,right in [('r1','before','handover','negative'),('r2','same_transaction','handover','negative')]:
        a.relations.append(Relation(relation_id=rid,type=kind,from_id=left,to_id=right,evidence_refs=['s1','s2'],status='observed',
            scope_id='trade',rationale='TEST',rule_id='TEST-REL'))
    if update and not different_transaction:
        a.relations.append(Relation(relation_id='update',type='state_update',from_id='negative',to_id='positive',
            evidence_refs=['s1','s3'],status='observed',scope_id='trade',rationale='TEST explicit state update',rule_id='TEST-UPDATE'))
    return inputs,a


class FactReasonerTests(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ,{'SCAMSHIELD_REASONER':'facts','SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_URL_NETWORK_ENABLED':'0'})
        env.start();self.addCleanup(env.stop)

    def test_all_three_value_combinations_for_small_conjunctions(self):
        for length in (1,2,3):
            for values in product(Truth,repeat=length):
                expected=Truth.FALSE if Truth.FALSE in values else Truth.UNKNOWN if Truth.UNKNOWN in values else Truth.TRUE
                self.assertIs(conjunction(values),expected)

    def test_every_rule_positive_negative_missing_and_quoted(self):
        book,_=load_assets()
        for rule in book.rules:
            with self.subTest(rule=rule.rule_id):
                s=matrix_store(rule);self.assertEqual(evaluate_rule(rule,s)[0].status,'MATCHED')
                first=next(iter(rule.required_conditions));f=s.by_event[first]
                f.value=Truth.FALSE if f.value is Truth.TRUE else Truth.TRUE
                self.assertEqual(evaluate_rule(rule,s)[0].status,'NOT_MATCHED')
                s=matrix_store(rule);f=s.by_event[first];f.value=Truth.UNKNOWN
                self.assertEqual(evaluate_rule(rule,s)[0].status,'UNDETERMINED')
                s=matrix_store(rule);s.by_event[first].attributes['speech_role']='quoted_warning'
                self.assertEqual(evaluate_rule(rule,s)[0].status,'NOT_MATCHED')

    def test_missing_payment_is_unknown_and_specific_question(self):
        r=analyze_local(query('Anh giao máy cho tài xế nhé.'))
        payments=[f for f in r.fact_trace.facts if f.fact_type=='payment_confirmed']
        self.assertTrue(payments);self.assertTrue(all(f.value is Truth.UNKNOWN for f in payments))
        self.assertEqual(r.assessment.risk_status,'need_context')
        self.assertIn('Bạn đã kiểm tra và xác nhận khoản tiền vào tài khoản chưa?',r.assessment.follow_up_questions)

    def test_actual_handover_negative_paid_warning(self):
        examples=[('Chưa thấy tiền về, nhưng cứ giao máy trước.','suspicious'),
                  ('Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy nhé.','clear'),
                  ('Nếu chưa nhận tiền thì đừng giao máy.','clear')]
        for text,risk in examples:self.assertEqual(analyze_local(query(text)).assessment.risk_status,risk,text)

    def test_explicit_same_claimant_update_versions_and_recomputes(self):
        q,a=payment_graph(update=True);s=build_facts(q,a)
        self.assertEqual(s.by_event['negative'].superseded_by,'fact:positive')
        self.assertEqual(s.by_event['positive'].version,2)
        self.assertIn('fact:negative',s.by_event['positive'].dependency_refs)
        book,templates=load_assets();result,rows=assess(s,book,templates)
        self.assertNotIn('R-HANDOVER',result.applicable_rule_ids)
        self.assertEqual(next(r for r in rows if r.rule_id=='R-HANDOVER').status,'NOT_MATCHED')

    def test_buyer_claim_cannot_supersede_seller_even_with_update_edge(self):
        q,a=payment_graph(update=True,buyer=True);s=build_facts(q,a)
        self.assertIsNone(s.by_event['negative'].superseded_by);self.assertTrue(s.conflicts)
        result,_=assess(s,*load_assets());self.assertEqual(result.risk_status,'suspicious')
        self.assertTrue(any('Hai bên' in q for q in result.follow_up_questions))

    def test_same_arrival_order_without_update_does_not_overwrite(self):
        q,a=payment_graph();s=build_facts(q,a)
        self.assertIsNone(s.by_event['negative'].superseded_by);self.assertTrue(s.conflicts)
        self.assertEqual(s.by_event['positive'].version,1)

    def test_two_transactions_stay_separate(self):
        q,a=payment_graph(different_transaction=True);s=build_facts(q,a)
        self.assertFalse(s.conflicts);self.assertIsNone(s.by_event['negative'].superseded_by)
        result,_=assess(s,*load_assets());self.assertIn('R-HANDOVER',result.applicable_rule_ids)

    def test_screen_then_bank_high_and_missing_or_warning_not_high(self):
        q=CaseInput(messages=[{'id':'a','speaker_id':'sender','scope_id':'trade','text':'Bấm chia sẻ màn hình để hoàn cọc nhé.'},
                             {'id':'b','speaker_id':'recipient','scope_id':'trade','text':'Sau khi chia sẻ thì mình cần làm gì?'},
                             {'id':'c','speaker_id':'sender','scope_id':'trade','text':'Mở ứng dụng ngân hàng và vào phần số dư để bên mình xem.'}])
        r=analyze_local(q);self.assertEqual(r.assessment.risk_status,'high');self.assertIn('R-SCREEN-BANK',r.assessment.applicable_rule_ids)
        q.messages=q.messages[:1];self.assertEqual(analyze_local(q).assessment.risk_status,'suspicious')
        r=analyze_local(query('Cảnh báo: đừng chia sẻ màn hình rồi mở ứng dụng ngân hàng.'))
        self.assertEqual(r.assessment.risk_status,'clear')

    def test_screen_bank_different_speaker_or_transaction_not_joined(self):
        for speaker,scope in [('different','trade'),('sender','other')]:
            q=CaseInput(messages=[{'id':'a','speaker_id':'sender','scope_id':'trade','text':'Chia sẻ màn hình nhé.'},
                                 {'id':'b','speaker_id':speaker,'scope_id':scope,'text':'Sau đó mở ứng dụng ngân hàng.'}])
            self.assertNotIn('R-SCREEN-BANK',analyze_local(q).assessment.applicable_rule_ids)

    def test_wrong_quote_prunes_dependent_fact_but_keeps_independent_high(self):
        q=query('Gửi mã OTP cho tôi. Gửi ảnh CCCD qua chat.')
        original=extract(q);bad_event=next(e for e in original.events if e.event_type=='provide_documents')
        bad_span=next(s for s in original.spans if s.span_id==bad_event.evidence_refs[0]);bad_span.quote='FAKE QUOTE'
        with patch('backend.local_reasoning.engine.extract',return_value=original):r=analyze_local(q)
        self.assertEqual(r.analysis_status,'partial');self.assertEqual(r.assessment.risk_status,'high')
        self.assertIn(bad_event.event_id,r.fact_trace.discarded_event_ids)
        self.assertFalse(any(f.event_id==bad_event.event_id for f in r.fact_trace.facts))

    def test_high_does_not_depend_on_unknown_personal_relationship(self):
        r=analyze_local(query('Gửi mã OTP cho tôi.'))
        self.assertEqual(r.assessment.risk_status,'high')
        self.assertFalse(r.annotations.personal_relationships)

    def test_no_external_model_and_raw_api_trace_public_adapter(self):
        with patch('httpx.AsyncClient.post',side_effect=AssertionError('No model')),TestClient(app) as client:
            d=client.post('/api/analyze-local',json=query('Gửi mã OTP cho tôi.').model_dump(mode='json')).json()
            self.assertTrue(d['fact_trace']['facts'])
            r=client.post('/api/analyze',json={'text':'Gửi mã OTP cho tôi.'})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['analysis']['decision_version'],'facts-1.0-support')
        self.assertNotIn('fact_trace',r.json());self.assertEqual(r.json()['analysis']['live_status'],'not_used')

    def test_invalid_mode_or_extraction_error_never_clear(self):
        with patch.dict(os.environ,{'SCAMSHIELD_REASONER':'bad'}),TestClient(app) as client:
            self.assertEqual(client.post('/api/analyze',json={'text':'X'}).status_code,503)
        with patch('backend.local_reasoning.engine.extract',side_effect=RuntimeError('broken')):
            self.assertIsNone(analyze_local(query('Giao máy nhé.')).assessment.risk_status)

    def test_fact_dependencies_are_acyclic_and_new_rules_reject_code(self):
        from backend.local_reasoning.fact_schema import FactRule
        q,a=payment_graph(update=True);s=build_facts(q,a)
        def walk(fid,ancestors):
            self.assertNotIn(fid,ancestors)
            for dep in s.by_id[fid].dependency_refs:walk(dep,ancestors|{fid})
        for f in s.facts:walk(f.fact_id,set())
        data=load_assets()[0].rules[0].model_dump();data['python_expression']='__import__("os")'
        with self.assertRaises(ValueError):FactRule.model_validate(data)

    def test_user_payment_context_updates_only_one_explicit_scope(self):
        q=CaseInput(messages=query('Chưa thấy tiền về, nhưng cứ giao máy trước.').messages,
            context_facts=[{'id':'verified','text':'Tôi đã tự kiểm tra tài khoản và nhận đủ tiền.','applies_to_message_ids':['m1']}])
        r=analyze_local(q);self.assertEqual(r.assessment.risk_status,'clear')
        updated=next(f for f in r.fact_trace.facts if f.fact_id=='user:payment:verified')
        self.assertEqual(updated.source,'user_report');self.assertEqual(updated.attributes['status'],'claimed')
        q.context_facts[0].text='Người mua nói đã chuyển tiền rồi.'
        self.assertEqual(analyze_local(q).assessment.risk_status,'suspicious')
        for text in ['Tôi đã tự kiểm tra nhưng chưa nhận đủ tiền.',
                     'Người mua nói: tôi đã tự kiểm tra tài khoản và nhận đủ tiền.']:
            q.context_facts[0].text=text
            self.assertEqual(analyze_local(q).assessment.risk_status,'suspicious')

    def test_invalid_relation_is_partial_and_rule_truth_tables(self):
        q=query('Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy nhé.')
        a=extract(q);self.assertTrue(a.relations);a.relations[0].scope_id='wrong'
        with patch('backend.local_reasoning.engine.extract',return_value=a):r=analyze_local(q)
        self.assertEqual(r.analysis_status,'partial');self.assertNotEqual(r.assessment.risk_status,'clear')
        for rule in load_assets()[0].rules:
            keys=list(rule.required_conditions)
            if len(keys)>2:continue
            for states in product(Truth,repeat=len(keys)):
                s=matrix_store(rule)
                for key,state in zip(keys,states):
                    expected=rule.required_conditions[key].value
                    s.by_event[key].value=Truth.UNKNOWN if state is Truth.UNKNOWN else expected if state is Truth.TRUE else Truth.FALSE if expected is Truth.TRUE else Truth.TRUE
                expected=conjunction(states)
                self.assertEqual(evaluate_rule(rule,s)[0].status,
                    'MATCHED' if expected is Truth.TRUE else 'NOT_MATCHED' if expected is Truth.FALSE else 'UNDETERMINED')

    def test_invalid_relation_without_events_still_reports_partial(self):
        q=query('Nội dung chưa rõ.');a=base(q)
        a.spans=[Span(span_id='bad',message_id='m1',start=0,end=3,quote='WRONG',label='statement')]
        a.relations=[Relation(relation_id='bad-r',type='warning_about',from_id='speaker:user',to_id='recipient:unknown',
            evidence_refs=['bad'],status='observed',scope_id='case',rationale='TEST',rule_id='TEST')]
        with patch('backend.local_reasoning.engine.extract',return_value=a):r=analyze_local(q)
        self.assertEqual(r.analysis_status,'partial');self.assertEqual(r.assessment.risk_status,'need_context')


if __name__=='__main__':unittest.main()
