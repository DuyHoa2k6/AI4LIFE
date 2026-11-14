import hashlib
import json
import re
import threading
import time
from pathlib import Path
from types import SimpleNamespace
import torch
from .schema import VERSION,SPAN_LABELS,ATTRS,ROLES,RELATIONS,RISKS,Message
from .model import StructuredPhoBERT,span_features
from .preprocess import RDRSegmenter
from .tasks import span_candidates,participant_candidates,pair_features,common_window
from .decision import verify_graph,assess

ROOT=Path(__file__).resolve().parents[2]

class ModelUnavailable(RuntimeError):pass
class ModelBusy(RuntimeError):pass

class Runtime:
    def __init__(self,path,allow_experimental=False):
        started=time.perf_counter();self.path=Path(path).resolve()
        try:
            self.manifest=json.loads((self.path/'manifest.json').read_text(encoding='utf-8'))
            if self.manifest['schema_version']!=VERSION:raise ValueError('schema mismatch')
            if not {'spans','attributes','roles','relations','baseline'}<=set(self.manifest['config']['stages']):raise ValueError('not all required heads have been trained')
            if self.manifest.get('preprocessing_version')!='rdr-cpmap-1.0' or self.manifest.get('preprocessing_sha256')!=hashlib.sha256(Path(__file__).with_name('preprocess.py').read_bytes()).hexdigest():raise ValueError('preprocessing version mismatch')
            if self.manifest['status']!='production_reviewed' and not allow_experimental:raise ValueError('checkpoint is experimental and not quality-approved')
            if hashlib.sha256((self.path/'heads.pt').read_bytes()).hexdigest()!=self.manifest['heads_sha256']:raise ValueError('checkpoint hash mismatch')
            labels=json.loads((self.path/'labels.json').read_text(encoding='utf-8'))
            if labels!={'schema_version':VERSION,'spans':SPAN_LABELS,'attributes':ATTRS,'roles':ROLES,'relations':RELATIONS,'risks':RISKS}:raise ValueError('label mapping mismatch')
            self.config=self.manifest['config'];torch.set_num_threads(self.config['threads'])
            for item in self.manifest['preparation']['files']:
                asset=(ROOT/'artifacts/phobert'/item['path']).resolve()
                if not asset.is_relative_to((ROOT/'artifacts/phobert').resolve()) or hashlib.file_digest(asset.open('rb'),'sha256').hexdigest()!=item['sha256']:raise ValueError('prepared asset hash mismatch')
            base=self.path/self.manifest['encoder_directory'] if self.manifest.get('encoder_directory') else ROOT/self.manifest['base_checkpoint']
            self.model=StructuredPhoBERT(base,True).to(self.config['device'])
            incompatible=self.model.load_state_dict(torch.load(self.path/'heads.pt',map_location=self.config['device'],weights_only=True),strict=False)
            if incompatible.unexpected_keys or any(not k.startswith('encoder.') for k in incompatible.missing_keys):raise ValueError('incomplete learned heads')
            self.model.eval()
            self.segmenter=RDRSegmenter(ROOT/self.config['segmenter']);self.lock=threading.Lock()
        except (OSError,ValueError,KeyError,RuntimeError,ImportError) as exc:raise ModelUnavailable('Local PhoBERT checkpoint missing, incompatible or not approved') from exc
        self.cold_load_ms=(time.perf_counter()-started)*1000

    def predict(self,inputs,oracle=None,ablation=None,include_debug=False):
        if not self.lock.acquire(blocking=False):raise ModelBusy('PhoBERT inference slot is busy; retry later')
        try:
            with torch.inference_mode():return self._predict(inputs,oracle,ablation,include_debug)
        finally:self.lock.release()

    def _predict(self,inputs,oracle,ablation,include_debug=False):
        start=time.perf_counter();messages=[Message.model_validate(m) for m in inputs['messages']]
        if len(messages)>100 or sum(len(m.text) for m in messages)>10000 or len({m.id for m in messages})!=len(messages):raise ValueError('input budget or duplicate IDs')
        words=[]
        for m in messages:
            part=self.segmenter(m.text)
            for w in part:w.message_id=m.id
            words+=part
        prep_ms=(time.perf_counter()-start)*1000;t=time.perf_counter()
        features,members,chunks=self.model.encode(words,self.config['max_length'],self.config['overlap'])
        dummy=SimpleNamespace(messages=messages)
        item={'words':words,'features':features,'members':members,'sample':dummy};pairs=span_candidates(item,self.config)
        vectors=torch.stack([span_features(features,*p) for p in pairs]);scores=self.model.span_head(vectors).sigmoid()
        selected=[]
        if oracle is None:
            for label in SPAN_LABELS:
                # Smoke data fully annotates actions only. Other heads remain experimental.
                if label!='action':continue
                ranked=sorted([(float(scores[i,SPAN_LABELS.index(label)]),i) for i in range(len(pairs))],reverse=True)
                occupied=[]
                for score,i in ranked:
                    if score<self.config['span_threshold']:break
                    a,b=pairs[i]
                    if any(a<end and b>begin for begin,end in occupied):continue
                    selected.append((a,b,label,score));occupied.append((a,b))
        else:
            # Evaluation with oracle spans is explicitly separate; never used by the API.
            for s in oracle:
                ix=[i for i,w in enumerate(words) if w.message_id==s.message_id and w.start>=s.start and w.end<=s.end]
                if s.label=='action' and ix and words[ix[0]].start==s.start and words[ix[-1]].end==s.end:selected.append((ix[0],ix[-1]+1,s.label,1.))
        by_message={m.id:m for m in messages};spans=[];events=[];event_vectors=[];event_word=[]
        people=participant_candidates(item,self.model,entity_spans=[])
        for i,(a,b,label,score) in enumerate(sorted(selected)):
            w,z=words[a],words[b-1];m=by_message[w.message_id];sid='p'+str(i);eid='e'+str(i)
            spans.append({'id':sid,'message_id':m.id,'start':w.start,'end':z.end,'quote':m.text[w.start:z.end],'label':label,'score_uncalibrated':score})
            vec=span_features(features,a,b);attributes={k:ATTRS[k][int(head(vec).argmax())] for k,head in self.model.attribute_heads.items()}
            roles={}
            for role,head in self.model.role_heads.items():
                pid=people[int(torch.stack([head(torch.cat([vec,p])).squeeze() for _,p in people]).argmax())][0]
                if pid!='null':roles[role]=pid
            if m.speaker_id:roles['speaker']='speaker:'+m.speaker_id
            sentence=m.text[max(m.text.rfind('.',0,w.start),m.text.rfind('\n',0,w.start))+1:]
            sentence=sentence.split('.')[0].split('\n')[0]
            codes=set(re.findall(r'\b(?:đơn|giao dịch|hóa đơn)\s+([A-Z][A-Z0-9-]*)\b',sentence))
            events.append({'id':eid,'anchor_id':sid,'attributes':attributes,'speaker_id':m.speaker_id,'roles':roles,'transaction_id':next(iter(codes)) if len(codes)==1 else None})
            event_vectors.append(vec);event_word.append((a,b))
        relations=[];limits=[]
        if not events:limits.append('Mô hình không tìm được đoạn hành động; chưa phân biệt được không có hành động với chưa hiểu.')
        if len(events)>50:limits.append('Quá nhiều sự kiện; chỉ kiểm tra 50 sự kiện đầu.');events=events[:50]
        for i,a in enumerate(events):
            for j,b in enumerate(events):
                if i==j:continue
                if not common_window(members,event_word[i],event_word[j]):
                    limits.append('Quan hệ xa ngoài cửa sổ chưa được hỗ trợ.');continue
                probabilities=self.model.relation_head(pair_features(event_vectors[i],event_vectors[j])).sigmoid()
                for k,value in enumerate(probabilities):
                    label=RELATIONS[k]
                    if value<self.config['relation_threshold'] or label=='same_transaction' and j<i or ablation=='no_relations':continue
                    relations.append({'id':'r'+str(len(relations)),'source':a['id'],'target':b['id'],'label':label,'evidence_refs':[a['anchor_id'],b['anchor_id']],'score_uncalibrated':float(value)})
        if ablation=='no_roles':
            for e in events:e['roles']={}
        inference_ms=(time.perf_counter()-t)*1000;t=time.perf_counter()
        raw={'spans':spans,'events':events,'relations':relations,'limitations':list(dict.fromkeys(limits))}
        if include_debug:
            import copy
            debug_raw=copy.deepcopy(raw)
        graph=verify_graph([m.model_dump() for m in messages],raw);assessment=assess(graph)
        classifier=RISKS[int(self.model.risk_head(features.mean(0)).argmax())]
        return {'schema_version':VERSION,'analysis_status':assessment['analysis_status'],'graph':graph,'assessment':assessment,
          **({'debug':{'pre_verification_graph':debug_raw}} if include_debug else {}),
          'classifier_baseline':classifier,'classifier_disagrees':classifier!=assessment['risk_status'],
          'scope':'oracle_spans' if oracle is not None else 'predicted_spans',
          'scores_notice':'Scores are uncalibrated, not real-world probabilities.',
          'timings_ms':{'preprocessing':prep_ms,'inference':inference_ms,'verification_reasoning':(time.perf_counter()-t)*1000,'total':(time.perf_counter()-start)*1000},'windows':chunks}
