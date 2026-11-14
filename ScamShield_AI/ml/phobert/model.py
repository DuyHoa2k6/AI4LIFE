"""One PhoBERT encoder, independently trainable task heads (not 18 models)."""
from contextlib import nullcontext
import torch
from torch import nn
from transformers import AutoModel,AutoTokenizer
from .schema import SPAN_LABELS,ATTRS,ROLES,RELATIONS,RISKS
from .preprocess import windows

class StructuredPhoBERT(nn.Module):
    def __init__(self,checkpoint,freeze_encoder=True):
        super().__init__()
        self.tokenizer=AutoTokenizer.from_pretrained(checkpoint,local_files_only=True,use_fast=False)
        if self.tokenizer.is_fast:raise ValueError('unexpected tokenizer; alignment contract must be retested')
        self.encoder=AutoModel.from_pretrained(checkpoint,local_files_only=True)
        self.freeze_encoder=freeze_encoder;hidden=self.encoder.config.hidden_size
        for p in self.encoder.parameters():p.requires_grad=not freeze_encoder
        self.span_head=nn.Linear(hidden*2,len(SPAN_LABELS))
        self.attribute_heads=nn.ModuleDict({k:nn.Linear(hidden*2,len(v)) for k,v in ATTRS.items()})
        self.role_heads=nn.ModuleDict({k:nn.Sequential(nn.Linear(hidden*3,64),nn.Tanh(),nn.Linear(64,1)) for k in ROLES if k!='speaker'})
        self.relation_head=nn.Sequential(nn.Linear(hidden*4,128),nn.GELU(),nn.Linear(128,len(RELATIONS)))
        self.risk_head=nn.Linear(hidden,len(RISKS))
        self.null_participant=nn.Parameter(torch.zeros(hidden))
        self.unknown_participant=nn.Parameter(torch.randn(hidden)*.02)

    def encode(self,words,max_length=256,overlap=24):
        device=next(self.parameters()).device;chunks=windows(words,self.tokenizer,max_length,overlap)
        vectors=[[] for _ in words];members=[set() for _ in words]
        if self.freeze_encoder:self.encoder.eval()
        with torch.no_grad() if self.freeze_encoder else nullcontext():
            for wi,chunk in enumerate(chunks):
                ids=torch.tensor([chunk['input_ids']],device=device)
                encoded=self.encoder(input_ids=ids,attention_mask=torch.ones_like(ids)).last_hidden_state[0]
                for local,(start,end) in enumerate(chunk['word_tokens']):
                    index=chunk['start_word']+local;vectors[index].append(encoded[start:end].mean(0));members[index].add(wi)
        return torch.stack([torch.stack(v).mean(0) for v in vectors]),members,len(chunks)

def span_features(features,start,end):
    return torch.cat([features[start],features[end-1]])

def candidates(words,max_width=12):
    return [(i,j) for i in range(len(words)) for j in range(i+1,min(len(words),i+max_width)+1)]
