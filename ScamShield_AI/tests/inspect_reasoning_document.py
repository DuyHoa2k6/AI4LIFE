"""Read saved debug traces only; never calls inference or changes runtime."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'reports/reasoning_document_20261114'
rows=[json.loads(x) for x in (out/'debug_traces.jsonl').read_text(encoding='utf-8').splitlines()]
compact=[]
for row in rows:
    r=row['response'];a=r.get('annotations',{});spans={s['span_id']:s for s in a.get('spans',[])}
    events=[]
    for e in a.get('events',[]):
        events.append({k:e.get(k) for k in ['event_id','event_type','object','polarity','speech_role','actor_id','affected_party_id','scope_id','extractor_rule_id']})
        events[-1]['quotes']=[{'message_id':spans[s]['message_id'],'quote':spans[s]['quote']} for s in e.get('evidence_refs',[]) if s in spans]
    assessment=r.get('assessment',{});graph=a.get('graph_trace',{})
    compact.append({'id':row['case_id'],'status':r.get('analysis_status'),'risk':assessment.get('risk_status'),'summary':assessment.get('summary'),'rules':assessment.get('applicable_rule_ids'),'questions':assessment.get('follow_up_questions'),'missing':assessment.get('missing_information'),'events':events,'relations':a.get('relations',[]),'graph_rejected':graph.get('rejected',[]),'discarded_events':graph.get('validation_discarded_event_ids',[]),'mechanisms':graph.get('mechanisms',[]),'interpretation':r.get('interpretation'),'knowledge_status':r.get('knowledge_status'),'sources':len(r.get('source_matches',[])),'url_count':len(r.get('url_analysis',[]))})
(out/'diagnostic_summary.json').write_text(json.dumps(compact,ensure_ascii=False,indent=2),encoding='utf-8')
for c in compact:
    print(json.dumps({**{k:v for k,v in c.items() if k not in ('events','relations','interpretation')},'events':[{'type':e['event_type'],'object':e['object'],'polarity':e['polarity'],'speech_role':e['speech_role'],'actor':e['actor_id'],'affected':e['affected_party_id'],'quotes':e['quotes']} for e in c['events']],'relations':[(e['type'],e['from_id'],e['to_id']) for e in c['relations']]},ensure_ascii=False))
