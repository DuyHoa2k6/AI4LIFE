"""Group-aware split planning; unreviewed and independent cases are excluded."""
import hashlib
import unicodedata


def plan(cases,allow_draft=False):
    selected=[c for c in cases if c.metadata.split!='independent' and (allow_draft or c.metadata.review_status=='reviewed')]
    parent=list(range(len(selected)));keys={}
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):parent[find(a)]=find(b)
    for i,c in enumerate(selected):
        m=c.metadata
        text=' '.join(unicodedata.normalize('NFC','\n'.join(x.text for x in c.input.messages)).casefold().split())
        groups=[('scenario',m.scenario_id),('variant',m.variant_group_id),('source',m.source_group_id),('text',text)]
        for key in groups:
            if not key[1]:continue
            if key in keys:union(i,keys[key])
            else:keys[key]=i
    components={}
    for i,c in enumerate(selected):components.setdefault(find(i),[]).append(c.metadata.case_id)
    assignments={}
    for ids in components.values():
        number=int(hashlib.sha256(('|'.join(sorted(ids))+'|split-v2').encode()).hexdigest()[:8],16)%100
        split='train' if number<70 else 'dev' if number<85 else 'test'
        assignments.update({cid:split for cid in ids})
    return {'assignments':assignments,'excluded':len(cases)-len(selected),'groups':len(components),
            'usable_for_training':not allow_draft,'note':'Planning only; independent set must be held outside tuning. Draft inclusion is a dry run, not training authorization.'}
