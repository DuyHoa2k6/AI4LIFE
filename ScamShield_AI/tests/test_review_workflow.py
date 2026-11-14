"""Review identities below are unit-test fixtures, never real reviewer attestations."""
import copy
import json
from pathlib import Path
import pytest
from evaluation.io import load, dump, jsonl, digest
from evaluation.review import export_pack, submit, reconcile, approve, canonical, identifier
from evaluation.training import prepare

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def workspace(tmp_path):
    row=load(ROOT/'evaluation/data/novel_cases.jsonl')[0]
    row.provenance['source_ref']='unit-test-fixture-only'
    source=tmp_path/'source.jsonl';jsonl(source,[row.model_dump()])
    pack=tmp_path/'pack';export_pack(source,pack)
    return tmp_path,source,pack,row

def annotation(row):
    from evaluation.review import input_digest
    return {'case_id':row.case_id,'input_sha256':input_digest(row.input.model_dump()),
      'expected':row.expected.model_dump(),'annotation_completeness':row.annotation_completeness,'issues':[]}

def send(ws,reviewer='unit-fixture-reviewer-a',change=None,attestation_change=None):
    tmp,source,pack,row=ws;value=annotation(row)
    if change:change(value)
    ann=tmp/(identifier(reviewer)+'.jsonl');jsonl(ann,[value])
    att=tmp/(identifier(reviewer)+'.json');data={'reviewer_reference':reviewer,'human_review_performed':True,
      'independent_of_other_reviewer':True,'used_model_generated_annotations':False}
    data.update(attestation_change or {});dump(att,data)
    return submit(pack,source,ann,att)

def resolution(ws,change=None):
    tmp,source,pack,row=ws;value=annotation(row)
    value.update(adjudicator_reference='unit-fixture-adjudicator',human_resolution_performed=True,
      approved_for_training=True,reason='Unit test simulation only, no actual human review.')
    if change:change(value)
    path=tmp/'resolution.jsonl';jsonl(path,[value]);return path

def test_export_has_no_draft_labels_or_prediction(workspace):
    tmp,source,pack,row=workspace
    record=json.loads((pack/'inputs.jsonl').read_text(encoding='utf-8'))
    assert set(record)=={'case_id','domain','input','input_sha256'}
    assert record['input']==row.input.model_dump()
    blank=json.loads((pack/'annotations_blank.jsonl').read_text(encoding='utf-8'))
    assert blank['expected'] is None and blank['partial_annotations']=={}
    assert all(v=='unannotated' for v in blank['annotation_completeness'].values())
    assert load(source)[0].review_status=='draft'

def test_export_cannot_overwrite(workspace):
    _,source,pack,_=workspace
    with pytest.raises(ValueError,match='already exists'):export_pack(source,pack)

def test_locked_export_rejected(workspace):
    tmp,source,_,row=workspace;row.split='locked';jsonl(source,[row.model_dump()])
    with pytest.raises(ValueError,match='custodian'):export_pack(source,tmp/'locked')

def test_tampered_pack_rejected(workspace):
    _,_,pack,_=workspace;(pack/'inputs.jsonl').write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='hash changed'):send(workspace)

def test_source_version_change_rejected(workspace):
    _,source,_,row=workspace;row.phenomena.append('unit-test');jsonl(source,[row.model_dump()])
    with pytest.raises(ValueError,match='Source dataset changed'):send(workspace)

@pytest.mark.parametrize('override',[{'human_review_performed':False},{'independent_of_other_reviewer':False},{'used_model_generated_annotations':True},{'reviewer_reference':'<reviewer>'}])
def test_attestation_must_be_explicit(workspace,override):
    with pytest.raises(ValueError):send(workspace,attestation_change=override)

def test_blank_not_review(workspace):
    with pytest.raises(ValueError,match='Blank worksheet'):send(workspace,change=lambda r:r.update(expected=None))

def test_partial_does_not_force_guessed_risk_or_approval(workspace):
    def partial(r):
        spans=r['expected']['spans'];r.update(expected=None,partial_annotations={'spans':spans,'risk_status':None})
        r['annotation_completeness']={k:'partial' for k in r['annotation_completeness']}
    send(workspace,change=partial);send(workspace,'unit-fixture-reviewer-b')
    tmp,source,pack,_=workspace
    rows=reconcile(pack,source,tmp/'status.jsonl')
    assert rows[0]['state']=='partial_annotation_needs_completion' and not rows[0]['approved']
    with pytest.raises(ValueError,match='Partial reviews'):approve(pack,source,resolution(workspace),tmp/'approved.jsonl')

@pytest.mark.parametrize('kind',['input_hash','quote','partial_quote'])
def test_input_binding_and_offsets(workspace,kind):
    def change(r):
        if kind=='input_hash':r['input_sha256']='0'*64
        else:
            r['expected']['spans'][0]['quote']='fabricated'
            if kind=='partial_quote':r.update(partial_annotations={'spans':r['expected']['spans']},expected=None)
    with pytest.raises(ValueError):send(workspace,change=change)

def test_reviewer_cannot_count_twice(workspace):
    send(workspace)
    with pytest.raises(ValueError,match='already submitted'):send(workspace)

def test_one_review_cannot_approve(workspace):
    send(workspace);tmp,source,pack,_=workspace
    assert reconcile(pack,source,tmp/'status.jsonl')[0]['state']=='needs_two_independent_reviews'
    with pytest.raises(ValueError,match='Two independent'):approve(pack,source,resolution(workspace),tmp/'approved.jsonl')

def test_agreement_still_needs_human_resolution(workspace):
    send(workspace);send(workspace,'unit-fixture-reviewer-b',change=lambda r:r['expected'].update(rationale='Equivalent prose in a fixture.'))
    tmp,source,pack,_=workspace;row=reconcile(pack,source,tmp/'status.jsonl')[0]
    assert row['state']=='structural_agreement_pending_human_resolution' and not row['approved']
    assert not (tmp/'approved.jsonl').exists()

def test_disagreement_is_not_autocorrected(workspace):
    send(workspace);send(workspace,'unit-fixture-reviewer-b',change=lambda r:r['expected'].update(risk_status='high'))
    tmp,source,pack,row=workspace;before=digest(source)
    status=reconcile(pack,source,tmp/'status.jsonl')[0]
    assert status['state']=='structural_disagreement' and 'risk' in status['different_fields']
    assert before==digest(source) and load(source)[0].review_status=='draft'

@pytest.mark.parametrize('change',[{'human_resolution_performed':False},{'approved_for_training':False},{'issues':['unresolved']},{'adjudicator_reference':'EXAMPLE-person'}])
def test_incomplete_resolution_blocked(workspace,change):
    send(workspace);send(workspace,'unit-fixture-reviewer-b');tmp,source,pack,_=workspace
    with pytest.raises(ValueError):approve(pack,source,resolution(workspace,lambda r:r.update(change)),tmp/'approved.jsonl')

def test_explicit_export_preserves_source_and_split_no_training(workspace):
    send(workspace);send(workspace,'unit-fixture-reviewer-b');tmp,source,pack,row=workspace;before=digest(source)
    out=tmp/'approved.jsonl';result=approve(pack,source,resolution(workspace),out)
    approved=load(out)[0]
    assert result['exported']==1 and result['training_started'] is False
    assert approved.review_status=='human_verified' and len(approved.reviewer_reference)==2
    assert approved.input==row.input and approved.split==row.split and approved.family_id==row.family_id
    assert digest(source)==before and load(source)[0].review_status=='draft'
    with pytest.raises(ValueError,match='already exists'):approve(pack,source,resolution(workspace),out)

def test_review_record_tamper_detected(workspace):
    send(workspace);tmp,source,pack,_=workspace
    path=next((pack/'submissions').glob('*/*.json'));record=json.loads(path.read_text(encoding='utf-8'))
    record['annotation']['expected']['risk_status']='high';dump(path,record)
    with pytest.raises(ValueError,match='record/hash'):reconcile(pack,source,tmp/'status.jsonl')

def test_canonical_graph_ids_and_prose_are_not_semantic_differences(workspace):
    row=workspace[3];other=copy.deepcopy(row);old=other.expected.spans[0].id;new='renamed-span'
    other.expected.spans[0].id=new
    for e in other.expected.events:
        if e.anchor_id==old:e.anchor_id=new
        e.argument_refs=[new if x==old else x for x in e.argument_refs]
    for p in other.expected.participants:
        if p.span_id==old:p.span_id=new
    for r in other.expected.relations:r.evidence_refs=[new if x==old else x for x in r.evidence_refs]
    other.expected.rationale='Different human prose.'
    assert canonical(row)==canonical(other)

def test_reviewed_validation_family_not_silently_trained(workspace):
    tmp,_,_,row=workspace;row.split='validation';row.review_status='human_verified'
    row.reviewer_reference=['unit-fixture-reviewer-a','unit-fixture-reviewer-b'];row.annotation_ambiguity=[]
    result=prepare([row],None,None,ROOT/'artifacts/phobert/smoke_heads',tmp/'training')
    assert result['status']=='blocked' and result['family_promotion_required']==[row.family_id]
    assert result['weights_changed'] is False
