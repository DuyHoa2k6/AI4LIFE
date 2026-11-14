"""Staged task training; CPU frozen-encoder smoke and explicit full fine-tuning."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path
import torch
import psutil
from .data import load,audit
from .model import StructuredPhoBERT
from .preprocess import RDRSegmenter
from .schema import VERSION,SPAN_LABELS,ATTRS,ROLES,RELATIONS,RISKS
from .tasks import prepare,loss_for

ROOT=Path(__file__).resolve().parents[2]

def read_config(path):
    config=json.loads(Path(path).read_text(encoding='utf-8'))
    if config['batch_size']!=1:raise ValueError('Only batch_size=1 is implemented; use gradient_accumulation')
    if config['device'] not in ('cpu','cuda'):raise ValueError('device must be explicit')
    if config['device']=='cpu' and config.get('precision','float32')!='float32':raise ValueError('CPU smoke uses float32')
    if config.get('gradient_accumulation',1)<1:raise ValueError('invalid accumulation')
    return config

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',default=str(Path(__file__).with_name('cpu_smoke.json')));parser.add_argument('--overfit-smoke',action='store_true');args=parser.parse_args()
    config=read_config(args.config);torch.manual_seed(config['seed']);random.seed(config['seed']);torch.set_num_threads(config['threads'])
    if config['device']=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA requested but unavailable; no silent device switch')
    train=load(ROOT/config['train'],supervised=True,allow_draft=config['allow_draft_smoke'])
    val=load(ROOT/config['validation'],supervised=True,allow_draft=config['allow_draft_smoke'])
    if config.get('train_sample_limit'):train=train[:config['train_sample_limit']]
    if args.overfit_smoke:
        if not config['allow_draft_smoke']:raise ValueError('Overfit mode must be explicitly experimental')
        chosen={}
        for row in train:
            if row.risk_reference not in chosen or len(row.relations)>len(chosen[row.risk_reference].relations):chosen[row.risk_reference]=row
        train=list(chosen.values());val=train
        config.update({'validation':config['train'],'output':'artifacts/phobert/overfit_heads','epochs':120,'early_stopping':120,'overfit_smoke':True})
    for key in ['family_id','conversation_group','template_group','source_group']:
        if not args.overfit_smoke and {getattr(x,key) for x in train}&{getattr(x,key) for x in val}:raise ValueError('train/validation leakage: '+key)
    started=time.perf_counter();model=StructuredPhoBERT(ROOT/config['checkpoint'],config['freeze_encoder']).to(config['device'])
    warm_start=None
    if config.get('warm_start'):
        from .warm_start import load_heads
        warm_start=load_heads(model,ROOT/config['warm_start'])
    def encoder_probe():
        return hashlib.sha256(model.encoder.encoder.layer[-1].output.LayerNorm.weight.detach().cpu().numpy().tobytes()).hexdigest()
    encoder_before=encoder_probe()
    segmenter=RDRSegmenter(ROOT/config['segmenter']);prepared=[]
    for name,rows in [('train',train),('validation',val)]:
        items=[]
        for row in rows:
            with torch.no_grad():item=prepare(row,segmenter,model,config)
            item['features']=item['features'].detach()
            items.append(item)
        prepared.append(items)
        print(json.dumps({'prepared':name,'count':len(items)}),flush=True)
    train_items,val_items=prepared
    preparation_s=time.perf_counter()-started;history={};output=ROOT/config['output'];output.mkdir(parents=True,exist_ok=True)
    def refresh(item):
        if not config['freeze_encoder']:
            features,members,chunks=model.encode(item['words'],config['max_length'],config['overlap']);item={**item,'features':features,'members':members,'chunks':chunks}
        return item
    for stage in config['stages']:
        stage_start=time.perf_counter()
        prefix={'spans':'span_head','attributes':'attribute_heads','roles':'role_heads','relations':'relation_head','baseline':'risk_head'}[stage]
        parameters=[p for n,p in model.named_parameters() if n.startswith(prefix) or stage=='roles' and n in ('null_participant','unknown_participant')]
        groups=[{'params':parameters,'lr':config['learning_rate']}]
        if not config['freeze_encoder']:groups.append({'params':model.encoder.parameters(),'lr':config['encoder_learning_rate']})
        optimizer=torch.optim.AdamW(groups);best=float('inf');best_weights=None;stale=0;entries=[]
        for epoch in range(config['epochs']):
            model.train();optimizer.zero_grad();losses=[];order=list(train_items);random.shuffle(order);pending=0
            for i,item in enumerate(order):
                loss=loss_for(stage,refresh(item),model,config)
                if loss is None:continue
                loss=loss*config['loss_weights'].get(stage,1.);losses.append(float(loss.detach()))
                (loss/config['gradient_accumulation']).backward()
                pending+=1
                if pending==config['gradient_accumulation']:
                    torch.nn.utils.clip_grad_norm_([p for group in groups for p in group['params']],1.0);optimizer.step();optimizer.zero_grad();pending=0
            if pending:
                for group in groups:
                    for p in group['params']:
                        if p.grad is not None:p.grad.mul_(config['gradient_accumulation']/pending)
                torch.nn.utils.clip_grad_norm_([p for group in groups for p in group['params']],1.0);optimizer.step();optimizer.zero_grad()
            model.eval();validation=[]
            with torch.no_grad():
                for item in val_items:
                    loss=loss_for(stage,refresh(item),model,config)
                    if loss is not None:validation.append(float(loss))
            if not losses or not validation:raise ValueError('No supervised train/validation examples for '+stage)
            vl=sum(validation)/len(validation);entries.append({'epoch':epoch+1,'train_loss':sum(losses)/len(losses),'validation_loss':vl})
            if vl<best:
                best=vl;stale=0;best_weights={n:p.detach().cpu().clone() for n,p in model.state_dict().items() if n.startswith(prefix) or stage=='roles' and n in ('null_participant','unknown_participant') or not config['freeze_encoder'] and n.startswith('encoder.')}
            else:stale+=1
            if stale>=config['early_stopping']:break
        model.load_state_dict(best_weights,strict=False)
        history[stage]={'epochs':entries,'seconds':time.perf_counter()-stage_start,'selected_by':'training_resubstitution_only' if args.overfit_smoke else 'validation_loss','best_validation_loss':best,'diagnostic_only':args.overfit_smoke}
        print(json.dumps({'stage':stage,'epochs':len(entries),'train_first':entries[0]['train_loss'],'train_last':entries[-1]['train_loss'],'seconds':history[stage]['seconds']}),flush=True)
    if not config['freeze_encoder']:
        model.encoder.save_pretrained(output/'encoder');model.tokenizer.save_pretrained(output/'encoder')
    weights={n:p.cpu() for n,p in model.state_dict().items() if not n.startswith('encoder.')}
    torch.save(weights,output/'heads.pt')
    mapping={'schema_version':VERSION,'spans':SPAN_LABELS,'attributes':ATTRS,'roles':ROLES,'relations':RELATIONS,'risks':RISKS}
    (output/'labels.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
    manifest={'schema_version':VERSION,'status':'research_smoke' if config['allow_draft_smoke'] else 'needs_quality_review',
      'warm_start':warm_start,
      'preprocessing_version':'rdr-cpmap-1.0','preprocessing_sha256':hashlib.sha256(Path(__file__).with_name('preprocess.py').read_bytes()).hexdigest(),
      'base_checkpoint':config['checkpoint'],'encoder_directory':'encoder' if not config['freeze_encoder'] else None,
      'training_scope':'frozen_PhoBERT_learned_heads' if config['freeze_encoder'] else 'fine_tuned_PhoBERT_and_heads',
      'encoder_probe_before':encoder_before,'encoder_probe_after':encoder_probe(),'encoder_probe_changed':encoder_before!=encoder_probe(),
      'config':config,'data':{name:{'sha256':hashlib.sha256((ROOT/config[name]).read_bytes()).hexdigest(),'selected_ids':[r.id for r in rows],'stats':audit(rows)} for name,rows in [('train',train),('validation',val)]},
      'tokenizer_class':type(model.tokenizer).__name__,'max_tokens':256,'uncalibrated_scores':True,
      'preparation':json.loads((ROOT/'artifacts/phobert/preparation.json').read_text()),
      'heads_sha256':hashlib.sha256((output/'heads.pt').read_bytes()).hexdigest(),
      'history':history,'preparation_seconds':preparation_s,'total_seconds':time.perf_counter()-started,
      'rss_bytes':psutil.Process().memory_info().rss,'peak_working_set_bytes':getattr(psutil.Process().memory_info(),'peak_wset',None),
      'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'saved':str(output),'total_seconds':manifest['total_seconds']}),flush=True)

if __name__=='__main__':main()
