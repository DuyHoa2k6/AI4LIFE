"""Attach technical/source observations to the fact audit without re-reading text."""
from datetime import datetime,timezone
from ..urls import STRONG
from .fact_schema import FactRecord,RuleEvaluation,Truth


def attach(result):
    trace=result.fact_trace
    if trace is None:return
    known={f.fact_id:f for f in trace.facts};now=datetime.now(timezone.utc)
    def add(**kw):
        f=FactRecord(observed_at=now,**kw);trace.facts.append(f);known[f.fact_id]=f;return f
    for url in result.url_analysis:
        ref='technical:url:'+url.link_id
        trace.external_evidence[ref]={'kind':'url_observation','data':url.model_dump(mode='json')}
        detected=Truth.UNKNOWN if url.status!='parsed' else Truth.TRUE if any(s.code in STRONG for s in url.signals) else Truth.FALSE
        add(fact_id='check:url:'+url.link_id,fact_type='strong_url_signal_detected',value=detected,scope_id='message:'+url.message_id,
            source='technical_check',evidence_refs=[ref])
    for use in result.url_uses:
        deps=['fact:'+fid for fid in use.finding_refs if 'fact:'+fid in known]+['check:url:'+use.link_id]
        if len(deps)<2 or any(d not in known for d in deps):continue
        refs=list(dict.fromkeys(r for d in deps for r in known[d].evidence_refs))
        f=add(fact_id='support:url:'+use.link_id,fact_type='url_supports_requested_action',value=Truth.TRUE,
            scope_id=known[deps[0]].scope_id,participant_ids=known[deps[0]].participant_ids,source='derived',evidence_refs=refs,
            dependency_refs=deps,rule_id='R-URL-GROUNDED-REQUEST')
        trace.rule_evaluations.append(RuleEvaluation(rule_id=f.rule_id,version='1.0',status='MATCHED',fact_refs=[f.fact_id]+deps,
            evidence_refs=refs,scope_id=f.scope_id,exclusion_state=Truth.FALSE))
    for source in result.source_matches:
        ref='official:'+source.source_id
        trace.external_evidence[ref]={'kind':'approved_behavior_passage','data':source.model_dump(mode='json')}
        check=add(fact_id='check:'+ref,fact_type='approved_behavior_passage_used',value=Truth.TRUE,scope_id=None,
            source='technical_check',evidence_refs=[ref])
        deps=['fact:'+eid for eid in source.event_refs if 'fact:'+eid in known]+[check.fact_id]
        if len(deps)<2:continue
        add(fact_id='support:'+ref,fact_type='official_behavior_support',value=Truth.TRUE,scope_id=known[deps[0]].scope_id,
            source='derived',evidence_refs=list(dict.fromkeys(r for d in deps for r in known[d].evidence_refs)),
            dependency_refs=deps,rule_id='RAG-APPROVED-BEHAVIOR-SUPPORT')
