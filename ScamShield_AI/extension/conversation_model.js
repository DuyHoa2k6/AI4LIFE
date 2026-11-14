/* Pure in-memory normalization and export. No Chrome/network/storage dependencies. */
(() => {
  if(globalThis.SSConversationModel)return;
  const clone=x=>JSON.parse(JSON.stringify(x)),now=()=>new Date().toISOString();
  class Store{
    constructor(scope,limits={}){
      this.limits={messages:1000,bytes:2*1024*1024,edges:4000,...limits};this.records=new Map();this.people=new Map();this.edges=new Map();this.edgeCount=0;this.fallback=new Map();this.nodes=new WeakMap();this.counter=0;this.personCounter=0;this.full=false;this.warnings=new Set();
      this.session={schema_version:'scamshield-conversation-1.0',session_id:crypto.randomUUID(),platform:'scamshield-dom-fixture-v1',started_at:now(),stopped_at:null,capture_scope:clone(scope),conversation_reference:scope.conversation_reference||null};
      this.performance={batches:0,total_processing_ms:0,max_batch_ms:0,estimated_session_bytes:0};
    }
    participant(raw){
      if(raw.role==='unknown'||(!raw.platform_id&&!raw.group_id&&!raw.self&&!raw.system))return null;
      const key=raw.platform_id?'account:'+raw.platform_id:raw.system?'system':raw.self?'self':'group:'+raw.group_id;
      let p=this.people.get(key);
      if(!p){p={participant_id:'P'+(++this.personCounter),platform_participant_id:raw.platform_id||null,display_name:raw.name||null,role:raw.system?'system':raw.self?'self':'other',identity_resolution:raw.platform_id?'platform_dom_id':'dom_group_only',attribution_basis:raw.basis||[]};this.people.set(key,p);}
      if(raw.name)p.display_name=raw.name;return p.participant_id;
    }
    signature(r){return JSON.stringify([r.sender,r.time,r.text,r.quoted_content,r.attachments]);}
    ingest(batch){
      if(this.full)return;const start=performance.now(),ids=[],seen=new Set();
      const signatures=new Map();for(const r of batch){const sig=this.signature(r);signatures.set(sig,(signatures.get(sig)||0)+1);}
      for(const [index,raw] of batch.entries()){
        const sig=this.signature(raw);let id=raw.id?'platform:'+raw.id:null,ambiguous=false;
        if(!id){
          const node=this.nodes.get(raw.node);
          if(node?.sig===sig)id=node.id;
          else if(raw.time&&raw.sender.platform_id&&signatures.get(sig)===1){
            const prev=batch[index-1]?.id?'platform:'+batch[index-1].id:null,next=batch[index+1]?.id?'platform:'+batch[index+1].id:null;
            const matches=(this.fallback.get(sig)||[]).filter(candidate=>(prev&&this.edges.get(prev)?.has(candidate))||(next&&this.edges.get(candidate)?.has(next)));
            if(matches.length===1)id=matches[0];
          }
          if(!id){id='observed:'+(++this.counter);ambiguous=true;}
        }
        if(seen.has(id))continue;seen.add(id);
        const old=this.records.get(id),peopleBefore=this.people.size,sender=this.participant(raw.sender),stamp=now();
        const r={internal_message_id:id,platform_message_id:raw.id||null,sender_id:sender,unresolved_reference:sender?null:'U-'+id,
          sender_display_name:raw.sender.name||null,text:raw.deleted?'':raw.text,message_kind:raw.deleted?'recalled':raw.system?'system':raw.forwarded?'forwarded':'message',attachments:raw.deleted?[]:raw.attachments,
          reply_to:raw.reply_id?'platform:'+raw.reply_id:null,quoted_content:raw.deleted?[]:raw.quoted_content,
          displayed_time:raw.time||null,normalized_time:raw.normalized_time||null,first_seen_at:old?.first_seen_at||stamp,last_seen_at:stamp,
          segment_id:null,order_in_segment:null,edited:!!raw.edited||!!(old&&!raw.deleted&&old.text!==raw.text),deleted:!!raw.deleted,
          sender_resolution:sender?'dom_attribution':'unresolved',extraction_warnings:[...raw.warnings,...(!sender?['sender_unknown']:[]),...(ambiguous?['identity_uncertain_possible_duplicate']:[])],links:raw.deleted?[]:raw.links};
        // Check the complete prospective export, not only the length of text.
        const prospective=[...this.records.values()].filter(x=>x.internal_message_id!==id);prospective.push(r);
        const bytes=new TextEncoder().encode(JSON.stringify({session:this.session,participants:[...this.people.values()],messages:prospective})).length;
        if((!old&&this.records.size>=this.limits.messages)||bytes>this.limits.bytes){if(this.people.size>peopleBefore)for(const [key,p] of this.people)if(p.participant_id===sender)this.people.delete(key);this.full=true;this.warnings.add('memory_limit_reached');break;}
        this.records.set(id,r);this.performance.estimated_session_bytes=bytes;ids.push(id);
        if(raw.node)this.nodes.set(raw.node,{id,sig});
        if(!raw.id){const matches=this.fallback.get(sig)||[];if(!matches.includes(id))matches.push(id);this.fallback.set(sig,matches);}
      }
      // DOM adjacency within one observed batch is the only ordering authority.
      for(let i=1;i<ids.length;i++){const a=ids[i-1],b=ids[i];if(a!==b){if(!this.edges.has(a))this.edges.set(a,new Set());if(!this.edges.get(a).has(b)){if(this.edgeCount>=this.limits.edges){this.full=true;this.warnings.add('order_relation_limit');break;}this.edges.get(a).add(b);this.edgeCount++;}}}
      const elapsed=performance.now()-start;this.performance.batches++;this.performance.total_processing_ms+=elapsed;this.performance.max_batch_ms=Math.max(this.performance.max_batch_ms,elapsed);
    }
    snapshot(reason='preview'){
      const remaining=new Set(this.records.keys()),segments=[],output=[];let cycle=false;
      while(remaining.size){
        const stack=[remaining.values().next().value],group=new Set();
        while(stack.length){const id=stack.pop();if(group.has(id))continue;group.add(id);remaining.delete(id);
          for(const next of this.edges.get(id)||[])if(!group.has(next))stack.push(next);
          for(const [a,bs] of this.edges)if(bs.has(id)&&!group.has(a))stack.push(a);
        }
        const indegree=new Map([...group].map(id=>[id,0]));for(const a of group)for(const b of this.edges.get(a)||[])if(group.has(b))indegree.set(b,indegree.get(b)+1);
        const ordered=[];let branching=false;while(ordered.length<group.size){const roots=[...indegree].filter(([id,n])=>n===0&&!ordered.includes(id)).map(([id])=>id);if(!roots.length){cycle=true;break;}if(roots.length>1)branching=true;const id=roots[0];ordered.push(id);for(const b of this.edges.get(id)||[])if(indegree.has(b))indegree.set(b,indegree.get(b)-1);}
        const uncertain=ordered.length!==group.size||branching;if(uncertain)for(const id of group)if(!ordered.includes(id))ordered.push(id);
        const sid='S'+(segments.length+1);segments.push({segment_id:sid,message_ids:ordered,order_resolution:uncertain?'uncertain':'observed_dom',relative_to_other_segments:'unknown'});
        for(let i=0;i<ordered.length;i++){const r=clone(this.records.get(ordered[i]));r.segment_id=sid;r.order_in_segment=uncertain?null:i+1;
          if(r.reply_to&&!this.records.has(r.reply_to)){r.extraction_warnings.push('reply_target_not_observed');r.reply_to=null;}output.push(r);}
      }
      const payload={...clone(this.session),stopped_at:reason==='preview'?null:now(),snapshot_reason:reason,participants:clone([...this.people.values()]),messages:output,segments,
        coverage:{observed_only:true,complete_history:false,history_start_reached:'unknown',has_gaps:'unknown',unknown_senders:output.some(r=>!r.sender_id),uncertain_order:segments.length>1||cycle||this.warnings.has('order_relation_limit')||segments.some(s=>s.order_resolution==='uncertain'),media_not_extracted:output.some(r=>r.attachments.length),memory_limit_reached:this.full},
        diagnostics_summary:{warnings:[...this.warnings],message_count:output.length,participant_count:this.people.size,unknown_sender_count:output.filter(r=>!r.sender_id).length,performance:clone(this.performance)}};
      return payload;
    }
  }
  globalThis.SSConversationModel={Store};
})();
