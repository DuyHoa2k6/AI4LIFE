"""Task examples and loss masks; incomplete labels are never blanket negatives."""
import torch
from torch.nn import functional as F
from .schema import SPAN_LABELS,ATTRS,ROLES,RELATIONS,RISKS,runtime_input
from .model import candidates,span_features

def prepare(sample,segmenter,model,config):
    words=[]
    for m in sample.messages:
        part=segmenter(m.text)
        for word in part:word.message_id=m.id
        words+=part
    features,members,chunks=model.encode(words,config['max_length'],config['overlap'])
    spans={}
    for s in sample.spans:
        indices=[i for i,w in enumerate(words) if w.message_id==s.message_id and w.start>=s.start and w.end<=s.end]
        if not indices or words[indices[0]].start!=s.start or words[indices[-1]].end!=s.end:
            raise ValueError('gold boundary is not aligned to an RDR word: '+sample.id+':'+s.id)
        spans[s.id]=(indices[0],indices[-1]+1)
    return {'sample':sample,'words':words,'features':features,'members':members,'chunks':chunks,'gold_spans':spans}

def span_candidates(item,config):
    return [(i,j) for i,j in candidates(item['words'],config['max_span_words'])
            if item['words'][i].message_id==item['words'][j-1].message_id
            and set.intersection(*(item['members'][k] for k in range(i,j)))]

def event_feature(item,event):return span_features(item['features'],*item['gold_spans'][event.anchor_id])

def participant_candidates(item,model,entity_spans=None):
    features=item['features'];words=item['words'];sample=item['sample']
    people=[('null',model.null_participant),('recipient:unknown',model.unknown_participant)]
    for speaker in dict.fromkeys(m.speaker_id for m in sample.messages if m.speaker_id):
        ids={m.id for m in sample.messages if m.speaker_id==speaker}
        ix=[i for i,w in enumerate(words) if w.message_id in ids]
        people.append(('speaker:'+speaker,features[ix].mean(0)))
    if entity_spans is None:entity_spans=[(s.id,item['gold_spans'][s.id]) for s in sample.spans if s.label=='entity']
    for sid,(start,end) in entity_spans:people.append(('mention:'+sid,features[start:end].mean(0)))
    return people

def canonical_participant(p):
    return 'speaker:'+p.speaker_id if p.kind=='metadata' else 'mention:'+p.span_id if p.kind=='mention' else 'recipient:unknown'

def pair_features(a,b):return torch.cat([a,b])

def common_window(members,a,b):
    indices=list(range(*a))+list(range(*b))
    return bool(indices) and bool(set.intersection(*(members[i] for i in indices)))

def loss_for(task,item,model,config):
    sample=item['sample'];device=item['features'].device;zero=item['features'].sum()*0
    if sample.task_status[task if task!='baseline' else 'risk']=='unannotated':return None
    if task=='spans':
        pairs=span_candidates(item,config)
        if any(pair not in pairs for pair in item['gold_spans'].values()):raise ValueError('gold span exceeds configured candidate scope')
        x=torch.stack([span_features(item['features'],*p) for p in pairs]);logits=model.span_head(x)
        target=torch.zeros_like(logits);mask=torch.zeros_like(logits)
        for label,status in sample.span_label_status.items():
            if status=='complete':mask[:,SPAN_LABELS.index(label)]=1
        for s in sample.spans:
            if sample.span_label_status[s.label]=='unannotated':continue
            i=pairs.index(item['gold_spans'][s.id]);j=SPAN_LABELS.index(s.label);target[i,j]=1;mask[i,j]=1
        if not mask.any():return None
        weights=torch.tensor([config.get('span_positive_weight',12.)]*len(SPAN_LABELS),device=device)
        return (F.binary_cross_entropy_with_logits(logits,target,reduction='none',pos_weight=weights)*mask).sum()/mask.sum().clamp_min(1)
    if task=='attributes':
        losses=[]
        for event in sample.events:
            x=event_feature(item,event)
            for k,value in event.attributes.items():
                if value is not None:losses.append(F.cross_entropy(model.attribute_heads[k](x).unsqueeze(0),torch.tensor([ATTRS[k].index(value)],device=device)))
        return torch.stack(losses).mean() if losses else None
    if task=='roles':
        people=participant_candidates(item,model);ps={p.id:p for p in sample.participants};losses=[]
        for event in sample.events:
            x=event_feature(item,event)
            for role,head in model.role_heads.items():
                gold=next((canonical_participant(ps[a.participant_id]) for a in sample.event_arguments if a.event_id==event.id and a.role==role),None)
                if gold is None and sample.task_status['roles']!='complete':continue
                target=next((i for i,(pid,_) in enumerate(people) if pid==gold),0)
                logits=torch.stack([head(torch.cat([x,p])).squeeze() for _,p in people])
                losses.append(F.cross_entropy(logits.unsqueeze(0),torch.tensor([target],device=device)))
        return torch.stack(losses).mean() if losses else None
    if task=='relations':
        losses=[]
        for a in sample.events:
            for b in sample.events:
                if a.id==b.id:continue
                if not common_window(item['members'],item['gold_spans'][a.anchor_id],item['gold_spans'][b.anchor_id]):continue
                positives=[r.label for r in sample.relations if (r.source,r.target)==(a.id,b.id) or r.label=='same_transaction' and (r.source,r.target)==(b.id,a.id)]
                if not positives and sample.task_status['relations']!='complete':continue
                logits=model.relation_head(pair_features(event_feature(item,a),event_feature(item,b)))
                target=torch.tensor([float(r in positives) for r in RELATIONS],device=device)
                if sample.task_status['relations']=='partial':
                    mask=target;loss=(F.binary_cross_entropy_with_logits(logits,target,reduction='none')*mask).sum()/mask.sum().clamp_min(1)
                else:loss=F.binary_cross_entropy_with_logits(logits,target)
                losses.append(loss)
        return torch.stack(losses).mean() if losses else None
    if task=='baseline' and sample.risk_reference is not None:
        return F.cross_entropy(model.risk_head(item['features'].mean(0)).unsqueeze(0),torch.tensor([RISKS.index(sample.risk_reference)],device=device))
    return None
