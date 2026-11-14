"""Evidence, scope, urgency, error paths and leakage checks for local v2."""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock,patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_reasoning.schema import CaseInput,DatasetCase
from backend.local_reasoning.engine import analyze_local,apply_rules,load_assets
from backend.local_reasoning.extract import extract
from backend.local_reasoning.validation import annotation_errors,dataset_errors
from backend.local_reasoning.splits import plan

ROOT=Path(__file__).resolve().parents[1]


def request(text,scope='case'):
    return CaseInput(messages=[{'id':'m1','speaker_id':'user','scope_id':scope,'text':text}])


class LocalReasoningTests(unittest.TestCase):
    def setUp(self):
        # These direct engine/evidence tests exercise the preserved fact branch.
        # The restored default is tested via test_local_provider and support APIs.
        mode=patch.dict(os.environ,{'SCAMSHIELD_REASONER':'facts'})
        mode.start();self.addCleanup(mode.stop)

    def test_urgent_does_not_wait_for_full_parser_or_sources(self):
        with patch('backend.local_reasoning.engine.extract',side_effect=RuntimeError('must not wait')) as parser, \
             patch('backend.retrieval.search',side_effect=RuntimeError('must not wait')) as search:
            result=analyze_local(request('Hiện tại tôi bị giữ lại và không được rời đi.'))
        self.assertEqual(result.assessment.risk_status,'high')
        self.assertEqual(result.assessment.safety_urgency,'urgent')
        self.assertTrue(result.assessment.urgency_evidence_refs)
        self.assertEqual(result.versions['path'],'urgent_precheck')
        parser.assert_not_called();search.assert_not_called()
        self.assertEqual(result.annotations.answers_18.technical_checks.status,'unknown')

    def test_unverified_release_demand_not_proven_kidnapping_or_urgent(self):
        result=analyze_local(request('Bên đòi tiền yêu cầu chuyển tiền để thả người nhà.'))
        self.assertEqual(result.assessment.risk_status,'high')
        self.assertNotEqual(result.assessment.safety_urgency,'urgent')
        self.assertIn('chưa chứng minh',result.assessment.summary)
        self.assertIn('kidnapping_proven',result.assessment.prohibited_conclusions)

    def test_no_organ_inference_from_travel_or_documents(self):
        for text in ('Một người đi nước ngoài rồi mất liên lạc.','Họ nói sẽ giữ hộ chiếu.'):
            r=analyze_local(request(text))
            self.assertFalse(any(e.event_type=='bodily_integrity_threat' for e in r.annotations.events))
            self.assertNotIn('nội tạng',r.assessment.summary)
            self.assertNotEqual(r.assessment.safety_urgency,'urgent')

    def test_nationality_gender_country_not_risk_features(self):
        base='Mời bạn đi gặp mặt.'
        results=[analyze_local(request(base+' '+extra)).assessment.risk_status for extra in
                 ('','Người mời là nam.','Người mời là nữ.','Địa điểm ở Việt Nam.','Địa điểm ở nước ngoài.')]
        self.assertEqual(len(set(results)),1)
        self.assertNotIn(results[0],('suspicious','high'))

    def test_denials_warning_and_past_are_not_current_emergencies(self):
        for text in ('Tôi không bị cấm rời đi và được tự do rời đi.',
                     'Cảnh báo: có người bị ép tham gia lừa đảo.',
                     'Năm ngoái tôi từng bị giữ lại, hiện sự việc đã kết thúc.',
                     'Bài tuyên truyền cảnh báo “đang bị giữ lại và không được rời đi”.'):
            r=analyze_local(request(text))
            self.assertEqual(r.assessment.risk_status,'clear',text)
            self.assertNotEqual(r.assessment.safety_urgency,'urgent')

    def test_planned_document_retention_differs_from_current_exit_restriction(self):
        planned=analyze_local(request('Họ nói sẽ giữ hộ chiếu.'))
        current=analyze_local(request('Họ đang giữ hộ chiếu của tôi và tôi không được rời đi.'))
        self.assertNotEqual(planned.assessment.safety_urgency,'urgent')
        self.assertEqual(current.assessment.safety_urgency,'urgent')

    def test_family_claim_is_not_independently_verified(self):
        q=request('Anh là người quen của em.')
        a=analyze_local(q).annotations
        self.assertTrue(a.personal_relationships)
        self.assertEqual(a.personal_relationships[0].status,'claimed')
        self.assertEqual(a.personal_relationships[0].relationship_type,'unknown')

    def test_context_relationship_is_user_report_only(self):
        q=CaseInput(messages=[{'id':'m1','speaker_id':'sender','text':'Anh là người quen của em.'}],
            context_facts=[{'id':'c1','text':'Người gửi là anh trai tôi.','applies_to_message_ids':['m1']}])
        relations=analyze_local(q).annotations.personal_relationships
        self.assertTrue(any(r.status=='user_reported' and r.relationship_type=='family' for r in relations))

    def test_different_scopes_cannot_create_travel_secrecy_chain(self):
        q=CaseInput(messages=[{'id':'m1','speaker_id':'s','scope_id':'one','text':'Hãy đi cùng.'},
                             {'id':'m2','speaker_id':'s','scope_id':'two','text':'Giấu gia đình.'}])
        r=analyze_local(q)
        self.assertNotIn('R-TRAVEL-SECRET',r.assessment.applicable_rule_ids)
        self.assertFalse(any(x.type=='travel_conditioned_on_secrecy' for x in r.annotations.relations))

    def test_invalid_quote_or_scope_cannot_support_conclusion(self):
        q=request('Chưa thấy tiền về, nhưng cứ giao máy trước.')
        a=extract(q);book,templates=load_assets()
        self.assertEqual(apply_rules(q,a,book,templates).risk_status,'suspicious')
        a.spans[0].quote='Bịa bằng chứng'
        with self.assertRaises(ValueError):apply_rules(q,a,book,templates)
        a=extract(q);a.relations[0].scope_id='unrelated'
        self.assertIn('cross_scope_relation',annotation_errors(q,a))

    def test_absence_is_not_negative_payment_fact(self):
        r=analyze_local(request('Tài xế đang chờ.'))
        self.assertEqual(r.assessment.risk_status,'need_context')
        self.assertFalse(any(e.event_type=='receive_funds' for e in r.annotations.events))
        self.assertNotIn('R-HANDOVER',r.assessment.applicable_rule_ids)

    def test_same_transaction_needs_existing_scoped_relationship(self):
        r=analyze_local(request('Chưa thấy tiền về, nhưng cứ giao máy trước.'))
        self.assertTrue(any(x.type=='same_transaction' for x in r.annotations.relations))
        q=CaseInput(messages=[{'id':'a','speaker_id':'s','scope_id':'one','text':'Chưa nhận tiền.'},
                             {'id':'b','speaker_id':'s','scope_id':'two','text':'Giao máy trước.'}])
        self.assertFalse(any(x.type=='same_transaction' for x in analyze_local(q).annotations.relations))

    def test_current_error_does_not_return_green(self):
        with patch('backend.local_reasoning.engine.extract',side_effect=ValueError('private raw data')):
            r=analyze_local(request('Mây bay trên núi.'))
        self.assertEqual(r.analysis_status,'error')
        self.assertIsNone(r.assessment.risk_status)
        self.assertTrue(r.assessment.recommended_actions)
        self.assertNotIn('private raw data',r.model_dump_json())

    def test_broken_rulebook_returns_safe_error(self):
        with patch('backend.local_reasoning.engine.load_assets',side_effect=ValueError('malformed private config')):
            r=analyze_local(request('Tôi đang bị giữ lại.'))
        self.assertEqual(r.analysis_status,'error')
        self.assertIsNone(r.assessment.risk_status)
        self.assertTrue(r.assessment.recommended_actions)

    def test_no_contacts_invented_and_no_candidate_sources(self):
        r=analyze_local(request('Gửi mã OTP cho tôi.'))
        self.assertEqual(r.support_contacts,[])
        self.assertEqual(r.source_matches,[])
        self.assertEqual(r.knowledge_status,'not_checked')  # Pure core; APIs enrich through support.py.

    def test_returning_documents_does_not_exempt_phone_control(self):
        r=analyze_local(request('Họ giữ điện thoại và trả lại hộ chiếu ngay.'))
        self.assertIn('R-CONTROL',r.assessment.applicable_rule_ids)
        self.assertEqual(r.assessment.risk_status,'suspicious')

    def test_pilot_is_structurally_valid_not_gold(self):
        rows=[DatasetCase.model_validate_json(s) for s in (ROOT.parent/'data/v2/release_final/pilot.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertFalse(dataset_errors(rows))
        self.assertTrue(all(r.metadata.review_status=='weak_label' for r in rows))
        self.assertTrue(all(r.metadata.split=='pilot' for r in rows))
        self.assertEqual(len(rows),70)

    def test_validator_detects_leak_duplicates_and_invalid_urgency(self):
        original=DatasetCase.model_validate_json((ROOT.parent/'data/v2/pilot_final/pilot.jsonl').read_text(encoding='utf-8').splitlines()[0])
        other=original.model_copy(deep=True);other.metadata.case_id='different';other.metadata.split='test'
        errors=dataset_errors([original,other])
        self.assertIn('cross_split_variant',errors);self.assertIn('normalized_exact_duplicate',errors)
        original.expected_assessment.safety_urgency='urgent';original.expected_assessment.urgency_evidence_refs=[]
        self.assertIn('urgent_without_evidence',dataset_errors([original]))

    def test_api_accepts_input_only_and_makes_zero_external_calls(self):
        with patch('httpx.AsyncClient.post',new_callable=AsyncMock,side_effect=AssertionError('External model HTTP forbidden')) as live, \
             patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('Network forbidden')) as network,TestClient(app) as client:
            response=client.post('/api/analyze-local',json=request('Tôi đang bị ép làm việc.').model_dump(mode='json'))
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['assessment']['safety_urgency'],'urgent')
            self.assertEqual(client.post('/api/analyze-local',json={'input':request('x').model_dump(),'expected_assessment':{'risk_status':'high'}}).status_code,422)
            self.assertEqual(client.get('/local').status_code,200)
            self.assertIn('safety_urgency',client.get('/assets/local.js').text)
            live.assert_not_called();network.assert_not_called()

    def test_no_training_export_from_weak_labels_and_grouped_draft_split(self):
        rows=[DatasetCase.model_validate_json(s) for s in (ROOT.parent/'data/v2/pilot_final/pilot.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertFalse(plan(rows)['assignments'])
        draft=plan(rows,allow_draft=True)
        for key in ('scenario_id','variant_group_id','source_group_id'):
            groups={}
            for case in rows:
                group=getattr(case.metadata,key)
                if group:groups.setdefault(group,set()).add(draft['assignments'][case.metadata.case_id])
            self.assertTrue(all(len(s)==1 for s in groups.values()))

    def test_unsupported_custom_rule_expression_is_rejected(self):
        from backend.local_reasoning.rule_schema import Rule
        rule=load_assets()[0].rules[0].model_dump();rule['python_expression']='__import__("os")'
        with self.assertRaises(ValueError):Rule.model_validate(rule)

    def test_ocr_and_parent_link_are_preserved_without_relabeling_as_verified(self):
        q=CaseInput(messages=[{'id':'post','speaker_id':'author','text':'Cảnh báo lời dụ bên dưới.','content_type':'post'},
            {'id':'image','speaker_id':None,'text':'Gửi mã OTP cho tôi.','content_type':'ocr','parent_message_id':'post'}])
        r=analyze_local(q)
        self.assertTrue(all(e.attribution.verification_status=='unverified' for e in r.annotations.events))
        self.assertEqual(r.assessment.risk_status,'clear')
        self.assertEqual(r.annotations.answers_18.requested_actions.status,'unknown')
        self.assertEqual(q.messages[1].parent_message_id,'post')

    def test_independent_comment_under_warning_is_not_hidden(self):
        q=CaseInput(messages=[{'id':'post','speaker_id':'author','text':'Cảnh báo lời dụ bên dưới.','content_type':'post'},
            {'id':'comment','speaker_id':'other','text':'Gửi mã OTP cho tôi.','content_type':'comment','parent_message_id':'post'}])
        self.assertEqual(analyze_local(q).assessment.risk_status,'high')

    def test_word_warning_does_not_hide_first_person_current_danger(self):
        result=analyze_local(request('Cảnh báo, tôi đang bị giữ lại và không được rời đi.'))
        self.assertEqual(result.assessment.safety_urgency,'urgent')

    def test_repeated_mapping_does_not_duplicate_statements(self):
        result=analyze_local(request('Họ nói sẽ giữ hộ chiếu.'))
        for field in result.annotations.answers_18.__dict__.values():
            self.assertEqual(len(field.value.statements),len(set(field.value.statements)))

    def test_user_verification_context_does_not_exempt_unrelated_invitation(self):
        q=CaseInput(messages=[{'id':'one','speaker_id':'a','scope_id':'job','text':'Mời làm việc.'},
                             {'id':'two','speaker_id':'b','scope_id':'trip','text':'Hãy đi cùng.'}],
            context_facts=[{'id':'c','text':'Tôi đã gọi đầu mối độc lập đối chiếu công việc.','applies_to_message_ids':['one']}])
        self.assertEqual(analyze_local(q).assessment.risk_status,'need_context')
