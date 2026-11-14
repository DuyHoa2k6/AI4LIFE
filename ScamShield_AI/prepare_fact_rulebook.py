"""One-time, reviewable migration of declarative conditions; no dataset labels read."""
import json
from pathlib import Path
from backend.local_reasoning.facts import fact_type
root=Path(__file__).resolve().parent.parent/'data/v2'
old=json.loads((root/'rulebook.json').read_text(encoding='utf-8'))
rules=[]
for r in old['rules']:
    required={}
    for slot,c in r['required_facts'].items():
        required[slot]={'fact_types':[fact_type(t) for t in c['event_types']],
            'value':'FALSE' if c['polarities']==['negative'] else 'TRUE','speech_roles':c['speech_roles'],
            'temporal_states':c['temporal_states'],'attribution_kinds':c['attribution_kinds'],
            'authentication_meaning':'TRUE' if c['requires_authentication_meaning'] else None}
    relations=list(r['required_relations'])
    if r['rule_id']=='R-HANDOVER':relations.append({'type':'same_transaction','from_fact':'request','to_fact':'state'})
    rules.append(dict(rule_id=r['rule_id'],version='2.0',scope=r['scope'],required_conditions=required,
        required_relations=relations,exclusion_conditions=r['exclusions'],conclusion=r['conclusion'],
        safety_urgency=r['safety_urgency'],evidence_requirements=r['evidence_requirements'],
        missing_information=list(required),follow_up_template=r['follow_up_question_template'],
        explanation_template=r['explanation_template_id'],supported_conclusion=r['supported_conclusion'],unknown_exclusion_policy='limit_claim'))
rules.append(dict(rule_id='R-SCREEN-BANK',version='1.0',scope='same_scope_same_affected_party',
    required_conditions={'screen':{'fact_types':['screen_share_requested'],'value':'TRUE','speech_roles':['request']},
                         'bank':{'fact_types':['bank_information_requested'],'value':'TRUE','speech_roles':['request']}},
    required_relations=[{'type':'after','from_fact':'bank','to_fact':'screen'}],exclusion_conditions=[],conclusion='high',
    safety_urgency='preventive',evidence_requirements='all_required_facts_and_relations',
    missing_information=['screen','bank','after'],follow_up_template=None,explanation_template='TPL-SCREEN-BANK',
    supported_conclusion='screen_share_exposes_banking',unknown_exclusion_policy='undetermined'))
(root/'fact_rules.json').write_text(json.dumps({'version':'three-valued-rulebook-1.0','rules':rules},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
templates=json.loads((root/'templates.json').read_text(encoding='utf-8'))
templates['version']='controlled-templates-1.1'
templates['templates']['TPL-SCREEN-BANK']={'summary':'Người gửi yêu cầu chia sẻ màn hình rồi mở thông tin ngân hàng, có nguy cơ lộ dữ liệu tài chính và thao tác trên tài khoản.',
    'recommended_actions':['Dừng chia sẻ màn hình trước khi mở ứng dụng ngân hàng; xác minh yêu cầu qua đầu mối chính thức độc lập.'],
    'required_slots':['verified_quotes'],'fallback_template_id':'TPL-UNKNOWN'}
(root/'fact_templates.json').write_text(json.dumps(templates,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Generated typed fact rulebook and templates; original rulebook/templates unchanged.')
