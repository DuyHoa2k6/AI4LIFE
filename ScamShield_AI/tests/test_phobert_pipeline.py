import copy
import json
from pathlib import Path
import pytest
from ml.phobert.schema import Sample,ATTRS,runtime_input
from ml.phobert.data import load,grouped_split
from ml.phobert.preprocess import align,AlignmentError,windows,Word,InputLimit
from ml.phobert.decision import verify_graph,assess

ROOT=Path(__file__).resolve().parents[1]

def graph(text,specs,links=()):
    spans=[];events=[]
    for i,(quote,action,obj,*state) in enumerate(specs):
        start=text.index(quote);sid='s'+str(i)
        spans.append({'id':sid,'message_id':'m1','start':start,'end':start+len(quote),'quote':quote,'label':'action'})
        attrs=dict(zip(ATTRS,[action,obj,'request','positive','requested','request']))
        if state:attrs.update(state[0])
        events.append({'id':'e'+str(i),'anchor_id':sid,'speaker_id':'sender','roles':{'performer':'recipient:unknown'},'transaction_id':'A','attributes':attrs})
    relations=[{'id':'r'+str(i),'source':'e'+str(a),'target':'e'+str(b),'label':label,'evidence_refs':['s'+str(a),'s'+str(b)]} for i,(a,b,label) in enumerate(links)]
    return {'spans':spans,'events':events,'relations':relations,'limitations':[]}

def checked(text,g):return verify_graph([{'id':'m1','speaker_id':'sender','text':text}],g)

@pytest.mark.parametrize('text,segmented',[
 ('😀 Tôi nhận tài liệu.',['😀','Tôi','nhận','tài_liệu','.']),
 ('Tôi\nnhận tiền.',['Tôi','nhận','tiền','.']),
 ('a\u0301',['á']),
 ('khoẻ',['khỏe']),
])
def test_alignment_original_codepoints(text,segmented):
    result=align(text,segmented)
    assert result[0].start==0 and result[-1].end==len(text)
    assert all(text[w.start:w.end] for w in result)

def test_alignment_failure_not_silenced():
    with pytest.raises(AlignmentError):align('nhận tài liệu',['nhận','tiền'])

@pytest.mark.parametrize('speech,polarity,expected',[('request','positive','high'),('prohibition','negative','clear'),('quoted_warning','positive','clear')])
def test_credentials_not_warning(speech,polarity,expected):
    text='Gửi mã đăng nhập.';g=graph(text,[('Gửi','disclose_credentials','auth_code',{'speech_act':speech,'polarity':polarity})])
    assert assess(checked(text,g))['risk_status']==expected

def test_conditional_payment_requires_relation():
    text='Nộp thêm để rút tiền.';g=graph(text,[('Nộp','transfer','money'),('rút tiền','withdraw','money',{'speech_act':'claim','temporal_state':'pending'})],[(0,1,'same_transaction'),(0,1,'prerequisite_for')])
    assert assess(checked(text,g))['risk_status']=='high'
    g['relations']=[]
    assert assess(checked(text,g))['risk_status']=='need_context'

def test_invalid_quote_cannot_support_high_or_clear():
    text='Gửi mã.';g=graph(text,[('Gửi','disclose_credentials','auth_code')]);g['spans'][0]['quote']='BỊA'
    result=assess(checked(text,g))
    assert result['risk_status'] is None and result['analysis_status']=='unsupported'

def test_wrong_speaker_rejected():
    text='Gửi mã.';g=graph(text,[('Gửi','disclose_credentials','auth_code')]);g['events'][0]['speaker_id']='someone_else'
    assert not checked(text,g)['events']

def test_transaction_mismatch_removes_relation_and_recomputes():
    text='Nộp rồi rút.';g=graph(text,[('Nộp','transfer','money'),('rút','withdraw','money')],[(0,1,'same_transaction'),(0,1,'prerequisite_for')]);g['events'][1]['transaction_id']='B'
    verified=checked(text,g)
    assert not verified['relations'] and assess(verified)['risk_status'] is None

def test_wrong_relation_endpoint_removed():
    text='Nộp rồi rút.';g=graph(text,[('Nộp','transfer','money'),('rút','withdraw','money')],[(0,1,'prerequisite_for')]);g['relations'][0]['target']='fake'
    assert not checked(text,g)['relations']

@pytest.mark.parametrize('obj,state,expected',[('money','not_completed','suspicious'),('money','completed','clear'),('document','not_completed','clear')])
def test_receive_object_and_state(obj,state,expected):
    text='Nhận xong mới giao.';g=graph(text,[('Nhận','receive',obj,{'speech_act':'claim','temporal_state':state}),('giao','handover','goods')],[(0,1,'same_transaction')])
    assert assess(checked(text,g))['risk_status']==expected

def test_two_transactions_no_cross_contamination():
    text='Nhận A đủ. Nhận B chưa đủ. Giao A.'
    g=graph(text,[('Nhận A','receive','money',{'speech_act':'claim','temporal_state':'completed'}),('Nhận B','receive','money',{'speech_act':'claim','temporal_state':'not_completed'}),('Giao A','handover','goods')],[(0,2,'same_transaction')]);g['events'][1]['transaction_id']='B'
    assert assess(checked(text,g))['risk_status']=='clear'

def test_updated_payment_supersedes_old_state():
    text='Chưa nhận. Đã nhận. Giao hàng.'
    g=graph(text,[('Chưa nhận','receive','money',{'speech_act':'claim','temporal_state':'not_completed'}),('Đã nhận','receive','money',{'speech_act':'claim','temporal_state':'completed'}),('Giao','handover','goods')],[(0,1,'same_transaction'),(0,1,'state_update'),(0,2,'same_transaction'),(1,2,'same_transaction')])
    assert assess(checked(text,g))['risk_status']=='clear'

def test_draft_not_auto_promoted():
    with pytest.raises(ValueError,match='Unreviewed'):load(ROOT.parent/'data/phobert/smoke_draft.jsonl',supervised=True)

def test_runtime_input_excludes_all_targets():
    row=load(ROOT.parent/'data/phobert/smoke_draft.jsonl')[0]
    payload=runtime_input(row)
    assert set(payload)=={'messages'} and 'risk_reference' not in json.dumps(payload) and 'family_id' not in json.dumps(payload)

def test_validator_rejects_bogus_offset():
    row=load(ROOT.parent/'data/phobert/smoke_draft.jsonl')[0].model_dump();row['spans'][0]['start']+=1
    with pytest.raises(ValueError):Sample.model_validate(row)

def test_group_split_keeps_minimal_pair_together():
    rows=load(ROOT.parent/'data/phobert/smoke_draft.jsonl');splits=grouped_split(rows)
    for field in ['family_id','conversation_group','template_group','source_group']:
        groups=[{getattr(x,field) for x in s} for s in splits.values()]
        assert all(not groups[i]&groups[j] for i in range(len(groups)) for j in range(i))

@pytest.fixture(scope='module')
def real_runtime():
    pytest.importorskip('torch')
    from ml.phobert.inference import Runtime
    if not (ROOT/'artifacts/phobert/smoke_heads/manifest.json').exists():pytest.skip('checkpoint not prepared')
    return Runtime(ROOT/'artifacts/phobert/smoke_heads',allow_experimental=True)

def test_real_tokenizer_is_slow_and_windows_cover_all(real_runtime):
    tokenizer=real_runtime.model.tokenizer
    assert not tokenizer.is_fast
    with pytest.raises(NotImplementedError):tokenizer('tài_liệu',return_offsets_mapping=True)
    words=[Word('tài_liệu',i*10,i*10+8) for i in range(100)]
    result=windows(words,tokenizer,max_length=32,overlap=3)
    assert all(len(w['input_ids'])<=32 for w in result)
    assert set(range(100))=={i for w in result for i in range(w['start_word'],w['stop_word'])}
    with pytest.raises(InputLimit):windows(words,tokenizer,max_length=8,max_windows=1)

def test_real_inference_cannot_use_network(real_runtime,monkeypatch):
    import socket
    def denied(*args,**kwargs):raise AssertionError('external inference network forbidden')
    monkeypatch.setattr(socket.socket,'connect',denied)
    text='Bạn gửi mã đăng nhập cho tôi.'
    result=real_runtime.predict({'messages':[{'id':'m1','speaker_id':'sender','text':text}]})
    assert result['assessment']['risk_status'] in ('clear','need_context','suspicious','high',None)
    assert all(text[s['start']:s['end']]==s['quote'] for s in result['graph']['spans'])

def test_unapproved_or_missing_checkpoint_fails_closed(tmp_path):
    from ml.phobert.inference import Runtime,ModelUnavailable
    with pytest.raises(ModelUnavailable):Runtime(tmp_path)
    with pytest.raises(ModelUnavailable):Runtime(ROOT/'artifacts/phobert/smoke_heads')

def test_partial_stage_checkpoint_cannot_run_full_pipeline():
    from ml.phobert.inference import Runtime,ModelUnavailable
    with pytest.raises(ModelUnavailable):Runtime(ROOT/'artifacts/phobert/finetune_step',allow_experimental=True)

def test_multispeaker_metadata_survives_real_inference(real_runtime):
    messages=[{'id':'m1','speaker_id':'nguoi_gui','text':'Bạn đọc mã cho tôi.'},
              {'id':'m2','speaker_id':'nguoi_nhan','text':'Đây là mã đăng nhập.'}]
    result=real_runtime.predict({'messages':messages})
    spans={s['id']:s for s in result['graph']['spans']};speaker={m['id']:m['speaker_id'] for m in messages}
    assert all(e['speaker_id']==speaker[spans[e['anchor_id']]['message_id']] for e in result['graph']['events'])
    assert result['windows']>=1

def test_real_segmenter_keeps_emoji_newline_offsets(real_runtime):
    text='😀 Tôi nhận tài liệu.\nBạn giữ giấy tờ.'
    words=real_runtime.segmenter(text)
    assert words[0].text=='😀' and text[words[0].start:words[0].end]=='😀'
    assert words[-1].end==len(text)

def test_relation_requires_whole_endpoints_in_one_window():
    from ml.phobert.tasks import common_window
    members=[{0},{0},{0,1},{1},{1}]
    assert common_window(members,(0,2),(2,3))
    assert not common_window(members,(0,2),(2,5))

def test_complete_labels_cannot_hide_missing_annotation():
    row=load(ROOT.parent/'data/phobert/splits/train.jsonl')[0].model_dump()
    row['events'][0]['attributes']['object_type']=None
    with pytest.raises(ValueError):Sample.model_validate(row)

def test_evaluation_masks_unannotated_tasks():
    from ml.phobert.evaluate import score
    row=load(ROOT.parent/'data/phobert/splits/train.jsonl')[0].model_copy(deep=True)
    row.task_status={task:'unannotated' for task in row.task_status};row.risk_reference=None
    result=score([row],[{'assessment':{'risk_status':'clear'},'analysis_status':'complete','graph':{'spans':[],'events':[],'relations':[]}}])
    assert sum(sum(x.values()) for x in result['risk']['confusion_matrix'].values())==0
    assert all(x['gold_events']==0 for x in result['attributes'].values())
