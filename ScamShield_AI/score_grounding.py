"""Sparse semantic expectations, independent of runtime patterns and verdicts."""
import argparse,json
from pathlib import Path

RISK={
 'receive_document':['clear'],'receive_money':['clear'],'send_guide':['clear'],'send_credentials':['high'],
 'prohibition':['clear'],'not_yet':['clear'],'conditional_loss':['high'],'no_requirement':['clear'],'deny_request':['clear'],
 'exit_alone':['need_context','suspicious'],'reported_pressure':['need_context','suspicious','high'],
 'paid_a_hold_b':['clear'],'unpaid_a':['suspicious'],'ambiguous_transaction':['need_context'],
 'verify_first':['clear','need_context'],'pay_first':['suspicious'],'review_only':['need_context'],
 'missing_purpose':['need_context'],'known_purpose':['need_context'],'unknown_people':['need_context'],
 'named_pronoun':['need_context'],'ambiguous_pronoun':['need_context'],'passport_debt':['high'],'quoted_warning':['clear'],
 'U01':['clear','need_context'],'U02':['clear','need_context'],'U03':['clear'],'U04':['clear'],
 'U05':['clear','need_context'],'U06':['clear','need_context'],'U07':['need_context','suspicious','high'],'U08':['need_context']}


def main():
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args()
    rows=json.loads((args.folder/'predictions.json').read_text(encoding='utf-8'));results=[]
    for row in rows:
        cid=row['id'];data=row['local'];events=data.get('annotations',{}).get('events',[]);relations=data.get('annotations',{}).get('relations',[])
        mentions=data.get('annotations',{}).get('mentions',[]);response=row['runs'][0]['response']
        checks={}
        def norm(e):return (e.get('semantic') or {}).get('normalized_action')
        types={e['event_type'] for e in events};norms={norm(e) for e in events}
        req=[e for e in events if e['speech_role']=='request' and e['polarity']=='positive']
        def put(layer,name,value):checks[layer+':'+name]=bool(value)
        if cid in ('receive_document','review_only','U01'):
            put('object','no_false_money_receipt','receive_funds' not in types)
            put('object','document_receipt_present','receive_document' in norms)
        if cid=='receive_document':put('speech','not_yet_document_report',any(norm(e)=='receive_document' and e['polarity']=='negative' and e['temporal_state']=='pending' for e in events))
        if cid=='receive_money':
            put('object','no_false_payment','transfer_funds' not in types);put('object','one_receipt',sum(e['event_type']=='receive_funds' for e in events)==1)
        if cid in ('send_guide','U02'):
            put('object','guide_not_credentials_or_login',not types&{'login','provide_credentials'})
            put('object','send_document_present','send_document' in norms)
        if cid=='send_credentials':put('object','credentials_present','provide_credentials' in types)
        if cid in ('prohibition','not_yet','no_requirement','deny_request','U03'):
            put('speech','no_active_request',not req)
        if cid=='not_yet':put('speech','not_yet_report',any(e['speech_role']=='claim' and e['temporal_state']=='pending' and e['polarity']=='negative' for e in events))
        if cid=='conditional_loss':
            put('speech','loss_consequence_present','loss_consequence' in norms)
            put('speech','no_blanket_denial',not any(e['speech_role']=='denial' for e in events))
            put('relation','conditional_loss_link',any(r['rule_id']=='GROUND-CONDITIONAL-LOSS' for r in relations))
        if cid in ('reported_pressure','U07'):
            put('people','reporter_not_threatener',any(norm(e)=='loss_consequence' and e['speech_role']=='reported' and e['semantic'].get('requester_id')!=e['semantic'].get('speaker_id') for e in events))
        if cid=='exit_alone':put('relation','no_invented_current_confinement',not any(e['event_type'] in ('restrict_movement','retain_identity_documents') for e in events))
        if cid=='unpaid_a':
            by_id={e['event_id']:e for e in events}
            put('transaction','unpaid_handover_correct_order',any(r['type']=='before' and r['scope_id'].endswith('don a') and by_id.get(r['from_id'],{}).get('event_type')=='handover_asset' and by_id.get(r['to_id'],{}).get('polarity')=='negative' for r in relations))
        if cid=='ambiguous_transaction':
            by_id={e['event_id']:e for e in events}
            put('transaction','no_guessed_transaction_link',not any(r['type'] in ('before','prerequisite_for','same_transaction') and {by_id.get(r['from_id'],{}).get('event_type'),by_id.get(r['to_id'],{}).get('event_type')}=={'receive_funds','handover_asset'} for r in relations))
        if cid=='pay_first':
            by_id={e['event_id']:e for e in events}
            put('relation','payment_before_verification',any(r['type']=='before' and by_id.get(r['from_id'],{}).get('event_type')=='transfer_funds' and by_id.get(r['to_id'],{}).get('event_type')=='avoid_verification' for r in relations))
        if cid in ('paid_a_hold_b','U04'):
            code='don a' if cid=='paid_a_hold_b' else 'don c'
            put('transaction','paid_order_receipt',any(e['event_type']=='receive_funds' and e['scope_id'].endswith(code) for e in events))
            put('transaction','correct_handover_link',any(r['rule_id']=='REL-REPORTED-PAYMENT-FIRST' and r['scope_id'].endswith(code) for r in relations))
            put('question','no_redundant_payment_question',not response.get('follow_up_questions'))
        if cid in ('verify_first','U05'):
            put('speech','no_immediate_payment',not any(e['event_type']=='transfer_funds' for e in req))
            put('relation','verify_is_prerequisite',any(r['rule_id']=='GROUND-VERIFY-BEFORE-PAYMENT' for r in relations))
        if cid=='review_only':put('object','verify_action_present','verify_information' in norms)
        if cid=='missing_purpose':put('question','neutral_purpose_question',any('thanh toán việc gì' in q for q in response.get('follow_up_questions',[])) and not any('rút' in q for q in response.get('follow_up_questions',[])))
        if cid=='known_purpose':put('question','known_purpose_not_asked',not any('thanh toán việc gì' in q or 'rút' in q for q in response.get('follow_up_questions',[])))
        if cid in ('unknown_people','U06'):
            put('people','distinct_mentions',len(mentions)>=2 and len({m['mention_id'] for m in mentions})==len(mentions))
        if cid=='named_pronoun':put('people','unique_pronoun',any(m['role']=='pronoun' and m['resolution']=='unique_antecedent' for m in mentions))
        if cid=='ambiguous_pronoun':put('people','ambiguous_pronoun_not_merged',any(m['role']=='pronoun' and m['participant_id'] is None and len(m['candidate_ids'])==2 for m in mentions))
        if cid=='passport_debt':put('relation','exit_payment_link',any(r['type']=='release_conditioned_on_payment' for r in relations))
        if cid=='quoted_warning':put('speech','no_active_quoted_request',not req)
        if cid=='U08':put('object','unknown_object_not_money','send_unknown' in norms and 'transfer_funds' not in types)
        risk_ok=response.get('risk_status') in RISK[cid]
        results.append({'id':cid,'risk':response.get('risk_status'),'allowed_risk':RISK[cid],'risk_correct':risk_ok,'checks':checks,
            'layer_correct':all(checks.values()),'processing_status':response.get('analysis_status')})
    layers={}
    for r in results:
        for name,value in r['checks'].items():
            layer=name.split(':')[0];layers.setdefault(layer,{'passed':0,'total':0});layers[layer]['total']+=1;layers[layer]['passed']+=int(value)
    summary={'cases':len(results),'risk_correct':sum(r['risk_correct'] for r in results),'layer_correct':sum(r['layer_correct'] for r in results),
        'risk_correct_but_semantic_wrong':[r['id'] for r in results if r['risk_correct'] and not r['layer_correct']],
        'semantic_failures':{r['id']:[k for k,v in r['checks'].items() if not v] for r in results if not r['layer_correct']},'layers':layers,
        'scope':'Sparse authored semantic acceptance checks; not exhaustive or independent accuracy.'}
    (args.folder/'semantic_review.json').write_text(json.dumps({'summary':summary,'cases':results},ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Kiểm tra riêng mức cảnh báo và dữ kiện','','Các check là chú giải sparse, không phải chấm đầy đủ mọi sự kiện.','',
        '| Ca | Risk | Risk đúng kỳ vọng | Dữ kiện/quan hệ/câu hỏi đạt check | Trạng thái |','|---|---|---|---|---|']
    for r in results:lines.append(f"| {r['id']} | {r['risk']} | {r['risk_correct']} | {r['layer_correct']} | {r['processing_status']} |")
    (args.folder/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
