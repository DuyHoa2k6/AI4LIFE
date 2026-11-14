"""Layered diagnostics. Undefined rates stay null; draft differences need review."""
from collections import Counter,defaultdict
from statistics import mean
from ml.phobert.schema import ATTRS,RISKS,RELATIONS

def div(a,b):return a/b if b else None
def prf(tp,fp,fn):return {'tp':tp,'fp':fp,'fn':fn,'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn)}
RULE_TAGS={'PB-CREDENTIALS':['access_loss'],'PB-PAY-TO-WITHDRAW':['pay_to_withdraw'],'PB-REMOTE-BANKING':['access_loss'],'PB-EXTORTION':['threat_to_compel'],'PB-CONTROL-EXIT':['coerced_exit'],'PB-HANDOVER-UNPAID':['premature_delivery'],'PB-TRANSFER-NO-VERIFY':['verification_obstructed'],'PB-SENSITIVE-REQUEST':['sensitive_request']}

def span_key(s):return (s['message_id'],s['start'],s['end'],s['label'])
def overlap(a,b):
    if a['message_id']!=b['message_id']:return 0.
    return max(0,min(a['end'],b['end'])-max(a['start'],b['start']))/(max(a['end'],b['end'])-min(a['start'],b['start']))

def diagnose(case,prediction):
    expected=case.expected;graph=prediction.get('graph',{'spans':[],'events':[],'relations':[]});verdict=prediction.get('assessment',{})
    gs={s.id:s.model_dump() for s in expected.spans};ps={s['id']:s for s in graph['spans']};pe={e['id']:e for e in graph['events']};ge={e.id:e for e in expected.events}
    matches={};used=set()
    for g in expected.events:
        ranked=sorted([(overlap(gs[g.anchor_id],ps[p['anchor_id']]),p['id']) for p in pe.values() if p['anchor_id'] in ps and p['id'] not in used],reverse=True)
        if ranked and ranked[0][0]>=.30:matches[g.id]=ranked[0][1];used.add(ranked[0][1])
    inverse={v:k for k,v in matches.items()};issues=[];attrs={k:[0,0] for k in ATTRS};role_correct=role_total=0
    def error(kind,expected_value,predicted_value,evidence=(),cause='suspected',module='extractor',severity='medium'):
        quotes=[]
        for ref in evidence:
            span=gs.get(ref)
            if not span and ref in ge:span=gs.get(ge[ref].anchor_id)
            if span and span not in quotes:quotes.append(span)
        issues.append({'error_type':kind,'expected':expected_value,'predicted':predicted_value,'evidence_refs':list(evidence),'evidence':quotes,'origin_module':module,'impact':severity,'root_cause_status':cause,
          'review_status':'pending_independent_review','label_status':case.review_status,'fix':'Review labels and target the identified layer; never train on the prediction.',
          'regression_test':case.case_id})
    for g in expected.events:
        p=pe.get(matches.get(g.id));bad=[]
        for key,value in g.attributes.items():
            if value is None:continue
            attrs[key][1]+=1
            if p and p['attributes'].get(key)==value:attrs[key][0]+=1
            else:bad.append(key)
        if not p or any(k in bad for k in ['action_type','object_type']):
            unavailable=g.attributes['action_type'] not in ATTRS['action_type'] or g.attributes['object_type'] not in ATTRS['object_type']
            error('ACTION_OBJECT',{'event_id':g.id,**g.attributes},p,[g.anchor_id],cause='confirmed' if unavailable else 'suspected',severity='high',module='trained_label_vocabulary' if unavailable else 'span_or_attribute_heads')
        if any(k in bad for k in ['polarity','speech_act','temporal_state','modality']):error('NEGATION_SCOPE',{k:g.attributes[k] for k in bad},p and p['attributes'],[g.anchor_id])
        for a in (a for a in expected.event_arguments if a.event_id==g.id and a.role!='speaker'):
            participant=next(x for x in expected.participants if x.id==a.participant_id)
            gold='speaker:'+participant.speaker_id if participant.kind=='metadata' else participant.id
            actual=p.get('roles',{}).get(a.role) if p else None
            if actual=='recipient:unknown':actual='unknown:'+gs[g.anchor_id]['message_id']+':addressee'
            role_total+=1;role_correct+=actual==gold
            if actual!=gold:error('PARTICIPANT_ROLE',{'event':g.id,'role':a.role,'participant':gold},actual,[g.anchor_id])
    gold_rel=set();pred_rel=set();cross_scope=0;matched_pair_rel=0
    def rel_key(a,b,label):return (min(a,b),max(a,b),label) if label=='same_transaction' else (a,b,label)
    for r in expected.relations:gold_rel.add(rel_key(r.source_id,r.target_id,r.type))
    for r in graph['relations']:
        a,b=inverse.get(r['source']),inverse.get(r['target'])
        if a is None or b is None:pred_rel.add(('unmatched:'+r['source'],'unmatched:'+r['target'],r['label']));continue
        pred_rel.add(rel_key(a,b,r['label']));matched_pair_rel+=1
        if ge[a].transaction_id and ge[b].transaction_id and ge[a].transaction_id!=ge[b].transaction_id:cross_scope+=1;error('TRANSACTION_SCOPE',[ge[a].transaction_id,ge[b].transaction_id],r,r['evidence_refs'],severity='high',module='relation_head_or_verifier')
    missing=gold_rel-pred_rel;extra=pred_rel-gold_rel
    for rel in sorted(missing):error('CONDITION_RELATION',rel,None,[ge[rel[0]].anchor_id,ge[rel[1]].anchor_id],module='relation_head_or_missing_anchor',severity='high')
    for rel in sorted(extra):error('CONDITION_RELATION',None,rel,module='relation_head',severity='high')
    wrong_direction=sum((b,a,l) in gold_rel and l!='same_transaction' for a,b,l in extra)
    inputs={m.id:m.text for m in case.input.messages}
    def evidence_counts(spans):
        return sum(not (s.get('message_id') in inputs and isinstance(s.get('start'),int) and isinstance(s.get('end'),int) and 0<=s['start']<s['end']<=len(inputs[s['message_id']]) and inputs[s['message_id']][s['start']:s['end']]==s['quote']) for s in spans)
    raw=prediction.get('debug',{}).get('pre_verification_graph');pre_invalid=evidence_counts(raw['spans']) if raw is not None else None
    post_invalid=evidence_counts(graph['spans'])
    if post_invalid or pre_invalid:error('EVIDENCE_INVALID',0,{'before':pre_invalid,'after':post_invalid},cause='confirmed',module='offset_alignment',severity='critical')
    rule_tags=set(verdict.get('mechanism_tags',[]))
    for rule in verdict.get('rules',[]):rule_tags.update(RULE_TAGS.get(rule.get('rule_id'),[]))
    mechanism_ok=set(expected.mechanism_tags)<=rule_tags
    if not mechanism_ok:error('EXPLANATION_UNSUPPORTED',expected.mechanism_tags,sorted(rule_tags),expected.decisive_event_refs,module='decision_explanation',severity='high')
    actual_questions=verdict.get('question_targets')
    if actual_questions is None:actual_questions=['payment_purpose'] if verdict.get('questions') and any('Khoản chuyển' in q for q in verdict['questions']) else ['current_state'] if verdict.get('questions') else []
    question_ok=set(actual_questions)<=set(expected.acceptable_question_targets) and (not expected.missing_information or bool(actual_questions))
    if not question_ok:error('REDUNDANT_QUESTION',expected.acceptable_question_targets,actual_questions,module='question_generation')
    actual_risk=verdict.get('risk_status')
    if actual_risk!=expected.risk_status:error('RISK_DECISION',expected.risk_status,actual_risk,expected.decisive_event_refs,module='end_to_end',severity='critical' if expected.risk_status=='high' or actual_risk=='high' and expected.risk_status=='clear' else 'high')
    if prediction.get('analysis_status') in ('unsupported','error') or actual_risk is None:error('UNSUPPORTED_INPUT','processed_in_scope',prediction.get('analysis_status'),module='coverage',severity='high')
    if case.annotation_ambiguity:error('LABEL_AMBIGUOUS',case.annotation_ambiguity,None,cause='confirmed',module='annotation',severity='review_required')
    unknown_origins={}
    for p in pe.values():
        for pid in p.get('roles',{}).values():
            if pid=='recipient:unknown':unknown_origins.setdefault(pid,set()).add(ps[p['anchor_id']]['message_id'])
    if any(len(messages)>1 for messages in unknown_origins.values()):error('COREFERENCE','separate unresolved participant IDs',str(unknown_origins),cause='confirmed',module='unknown_participant_representation')
    attrs_ok=all(correct==total for correct,total in attrs.values())
    right_risk_wrong_basis=actual_risk==expected.risk_status and (not attrs_ok or not mechanism_ok or bool(missing|extra) or role_correct<role_total)
    structurally_supported=attrs_ok and not missing and not extra and role_correct==role_total and mechanism_ok and question_ok and not post_invalid
    return {'case_id':case.case_id,'domain':case.domain,'split':case.split,'family_id':case.family_id,'draft':case.review_status=='draft','ambiguous':bool(case.annotation_ambiguity),
      'checkpoint_vocabulary_covered':all(v is None or v in ATTRS[k] for e in expected.events for k,v in e.attributes.items()),
      'expected_risk':expected.risk_status,'predicted_risk':actual_risk,'analysis_status':prediction.get('analysis_status','error'),
      'right_level_wrong_basis':right_risk_wrong_basis,'supported_success':actual_risk==expected.risk_status and structurally_supported,
      'semantic_human_review':'not_performed','attributes':attrs,'roles':{'correct':role_correct,'total':role_total},
      'spans':prf(len({span_key(s) for s in gs.values() if s['label']=='action'}&{span_key(s) for s in ps.values() if s['label']=='action'}),len({span_key(s) for s in ps.values() if s['label']=='action'}-{span_key(s) for s in gs.values() if s['label']=='action'}),len({span_key(s) for s in gs.values() if s['label']=='action'}-{span_key(s) for s in ps.values() if s['label']=='action'})),
      'relations':{label:prf(len({r for r in gold_rel&pred_rel if r[2]==label}),len({r for r in extra if r[2]==label}),len({r for r in missing if r[2]==label})) for label in RELATIONS},
      'wrong_relation_direction':wrong_direction,'cross_transaction_relations':cross_scope,'matched_endpoint_relations':matched_pair_rel,
      'evidence':{'pre_invalid':pre_invalid,'pre_total':len(raw['spans']) if raw is not None else None,'post_invalid':post_invalid,'post_total':len(graph['spans'])},
      'questions_compatible':question_ok,'mechanism_compatible':mechanism_ok,'errors':issues}

def aggregate(rows,include_scope=True):
    matrix={g:{p:0 for p in RISKS} for g in RISKS};unknown=Counter();status=Counter();per={}
    for r in rows:
        if r['predicted_risk'] in RISKS:matrix[r['expected_risk']][r['predicted_risk']]+=1
        else:unknown[r['expected_risk']]+=1
        status[r['analysis_status']]+=1
    for g in RISKS:
        tp=matrix[g][g];fp=sum(matrix[x][g] for x in RISKS if x!=g);fn=sum(matrix[g][x] for x in RISKS if x!=g)+unknown[g]
        per[g]={**prf(tp,fp,fn),'reference_support':sum(matrix[g].values())+unknown[g]}
    fs=[v['f1'] for v in per.values() if v['reference_support'] and v['f1'] is not None]
    pre=[r['evidence'] for r in rows if r['evidence']['pre_total'] is not None];n=len(rows)
    result={'n':n,'confusion_matrix':matrix,'unclassified_by_reference':dict(unknown),'per_risk':per,'macro_f1':mean(fs) if fs else None,
      'macro_labels':[k for k,v in per.items() if v['reference_support']],
      'coverage':div(sum(r['predicted_risk'] in RISKS for r in rows),n),'supported_success_count':sum(r['supported_success'] for r in rows),'end_to_end_supported_success_rate':div(sum(r['supported_success'] for r in rows),n),
      'clear_as_high':matrix['clear']['high'],'high_missed':sum(matrix['high'][p] for p in RISKS if p!='high')+unknown['high'],
      'false_high_on_clear':{'count':matrix['clear']['high'],'denominator':per['clear']['reference_support'],'rate':div(matrix['clear']['high'],per['clear']['reference_support'])},
      'high_miss':{'count':sum(matrix['high'][p] for p in RISKS if p!='high')+unknown['high'],'denominator':per['high']['reference_support'],'rate':div(sum(matrix['high'][p] for p in RISKS if p!='high')+unknown['high'],per['high']['reference_support'])},
      'right_level_wrong_basis':sum(r['right_level_wrong_basis'] for r in rows),'status_counts':dict(status),'status_rates':{k:div(v,n) for k,v in status.items()},
      'evidence':{'before_invalid':sum(e['pre_invalid'] for e in pre),'before_denominator':sum(e['pre_total'] for e in pre),'before_rate':div(sum(e['pre_invalid'] for e in pre),sum(e['pre_total'] for e in pre)),
        'after_invalid':sum(r['evidence']['post_invalid'] for r in rows),'after_denominator':sum(r['evidence']['post_total'] for r in rows),'after_rate':div(sum(r['evidence']['post_invalid'] for r in rows),sum(r['evidence']['post_total'] for r in rows))},
      'attributes':{k:{'correct':sum(r['attributes'][k][0] for r in rows),'total':sum(r['attributes'][k][1] for r in rows),'accuracy':div(sum(r['attributes'][k][0] for r in rows),sum(r['attributes'][k][1] for r in rows))} for k in ATTRS},
      'roles':{'correct':sum(r['roles']['correct'] for r in rows),'total':sum(r['roles']['total'] for r in rows),'accuracy':div(sum(r['roles']['correct'] for r in rows),sum(r['roles']['total'] for r in rows))},
      'span_action':prf(sum(r['spans']['tp'] for r in rows),sum(r['spans']['fp'] for r in rows),sum(r['spans']['fn'] for r in rows)),
      'relations':{k:prf(sum(r['relations'][k]['tp'] for r in rows),sum(r['relations'][k]['fp'] for r in rows),sum(r['relations'][k]['fn'] for r in rows)) for k in RELATIONS},
      'cross_transaction_relations':sum(r['cross_transaction_relations'] for r in rows),'redundant_or_missing_question_cases':sum(not r['questions_compatible'] for r in rows),
      'transaction_link_error_rate':div(sum(r['cross_transaction_relations'] for r in rows),sum(r['matched_endpoint_relations'] for r in rows)),
      'question_mismatch_rate':div(sum(not r['questions_compatible'] for r in rows),n),
      'draft_count':sum(r['draft'] for r in rows),'ambiguous_count':sum(r['ambiguous'] for r in rows),'human_semantic_review_count':0}
    if include_scope:
        scoped=[r for r in rows if r.get('checkpoint_vocabulary_covered',True)]
        result['checkpoint_vocabulary_covered_count']=len(scoped)
        result['outside_checkpoint_vocabulary_count']=len(rows)-len(scoped)
        result['within_checkpoint_vocabulary']=aggregate(scoped,include_scope=False)
    return result
