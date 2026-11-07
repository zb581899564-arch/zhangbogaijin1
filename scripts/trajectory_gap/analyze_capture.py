"""Offline direct output, schedule reuse and working-state accounting; no search feedback."""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import csv
import time
from common import *


def interval(fe):
    return '000100-100000' if fe <= 100000 else '100000-250000' if fe <= 250000 else '250000-500000'


def edit_kind(f, r, o):
    if f < 0:return 'INITIAL'
    if f:return 'FA_CHANGED'
    if r and o:return 'RESOURCE_AND_ORDER'
    if r:return 'RESOURCE_ONLY'
    if o:return 'ORDER_ONLY'
    return 'IDENTICAL_VECTORS'


def load_candidates(folder):
    records=[]; key_ids={}; keys=[]
    def code(text):
        if not text:return -1
        if text not in key_ids:key_ids[text]=len(keys);keys.append(text)
        return key_ids[text]
    with (folder/'trajectory-paid.csv').open() as stream:
        for expected,p in enumerate(csv.DictReader(stream),1):
            assert int(p['fe'])==expected
            records.append((expected,p['phase'],p['role'],int(p['family']),code(p['key']),
                code(p['parent']),code(p['donor']),code(p['teacher']),bool(int(p['admitted'])),bool(int(p['duplicate'])),
                edit_kind(int(p['faChanged']),int(p['resourceChanged']),int(p['positionChanged'])),
                (float(p['Cmax']),float(p['TEC']),float(p['TWC']))))
    assert len(records)==500000
    return records,key_ids


def scan_arm(root, arm, reference):
    started=time.monotonic();folder=root/'capture'/arm
    records,keys=load_candidates(folder);events=rows(folder/'trajectory-events.jsonl')
    accepts={int(e['fe']):e['keep'] for e in events if e['kind']=='accept'}
    assert len(accepts)==sum(e['kind']=='accept' for e in events)
    front=np.empty((0,3));previous_hv=0.;scale=np.asarray(SCALES['100_2_3_1'])
    first_paid={};last_use={};use_as_parent=Counter();productive_use=Counter();unknown_uses=Counter()
    output=defaultdict(lambda:Counter(FE=0,admitted=0,duplicate=0,accepted=0,acceptKnown=0,directHV=0.,finalPoints=0))
    admitted_rows=[];objective_birth={};final={tuple(p) for p in checkpoints(folder)[500000]}
    for fe,phase,role,family,key,parent,donor,teacher,admitted,duplicate,edit,objectives in records:
        for relation,k in [('parent',parent),('donor',donor),('teacher',teacher)]:
            if k<0:continue
            last_use[k]=fe
            if k not in first_paid:unknown_uses[relation]+=1
        if parent>=0:
            use_as_parent[parent]+=1
            if admitted:productive_use[parent]+=1
        first_paid.setdefault(key,fe)
        group=(interval(fe),phase,role,family,edit)
        item=output[group];item['FE']+=1;item['admitted']+=admitted;item['duplicate']+=duplicate
        if fe in accepts:item['acceptKnown']+=1;item['accepted']+=accepts[fe]
        if admitted:
            point=np.asarray(objectives)
            assert not np.any(np.all(front<=point,axis=1)), (arm,fe,'archive flag disagrees')
            front=np.vstack((front[~np.all(point<=front,axis=1)],point))
            hv=float(moocore.hypervolume(front/scale,ref=[1.5]*3));delta=hv-previous_hv
            assert delta>=-1e-12
            item['directHV']+=delta;previous_hv=hv
            objective_birth.setdefault(objectives,fe)
            if objective_birth[objectives]==fe and objectives in final:item['finalPoints']+=1
            admitted_rows.append((fe,phase,role,key,accepts.get(fe),delta,objectives in final))
    assert {tuple(p) for p in front}==final
    assert abs(sum(v['directHV'] for v in output.values())-metrics(front,reference,scale)['HV'])<1e-10
    lineage=defaultdict(lambda:Counter(admitted=0,acceptedKnown=0,accepted=0,reusedLater=0,
                                      usedAsParent=0,productiveParent=0,final=0,directHV=0.))
    for fe,phase,role,key,accepted,delta,final_point in admitted_rows:
        item=lineage[(interval(fe),phase,role)];item['admitted']+=1
        item['acceptedKnown']+=accepted is not None;item['accepted']+=accepted is True
        item['reusedLater']+=last_use.get(key,0)>fe
        item['usedAsParent']+=use_as_parent[key]>0
        item['productiveParent']+=productive_use[key]>0
        item['final']+=final_point;item['directHV']+=delta
    populations=[];previous={}
    for e in events:
        if e['kind']!='population' or e['label']=='QGS_BATCH_SELECTED':continue
        values=[p['objectives'] for p in e['points']]
        if not values:continue
        result=metrics(values,reference,scale);label=e['label']
        populations.append(dict(arm=arm,fe=e['fe'],cycle=e['cycle'],label=label,**result))
        previous[label]=result
    summaries=[dict(arm=arm,window=k[0],phase=k[1],role=k[2],family=k[3],edit=k[4],**v) for k,v in output.items()]
    flows=[dict(arm=arm,window=k[0],phase=k[1],role=k[2],**v) for k,v in lineage.items()]
    # Bounds are diagnostic only: no future archive/label enters search.
    return summaries,flows,populations,dict(arm=arm,paid=500000,acceptanceRecords=len(accepts),
        unknownRawParentUses=unknown_uses,uniqueScheduleKeys=len(first_paid),final=metrics(front,reference,scale),
        exactFinalFrontRebuilt=True,hvTelescopePassed=True,analysisSeconds=time.monotonic()-started,
        limitations=['Exact schedule hash reuse is not a causal genealogy',
                    'Neutral reencoding can create a raw key with no paid occurrence; counted as unknown',
                    'After-use counts near the endpoint are horizon censored',
                    'No time ranking from observed runs'])


def main(root):
    linux();assert read(root/'capture-complete.json')['allSixAccepted']
    out=root/'step2';out.mkdir()
    reference=read(root/'step1/100_2_3_1-reference.json')
    accounting=[];flows=[];populations=[];checks=[]
    for arm in ARMS:
        a,b,c,d=scan_arm(root,arm,reference);accounting.extend(a);flows.extend(b);populations.extend(c);checks.append(d)
        print('ANALYZED',arm,d,flush=True)
    csv_write(out/'direct-output.csv',accounting);csv_write(out/'schedule-use.csv',flows);csv_write(out/'working-populations.csv',populations)
    write(out/'acceptance.json',dict(arms=checks,newSearchFE=0,newDecoderQA=0,referenceSet='step1 fixed historical all-method all-seed final union'))
    compact=[]
    for arm in ARMS:
        for window in ('000100-100000','100000-250000','250000-500000'):
            selected=[x for x in accounting if x['arm']==arm and x['window']==window]
            for phase in sorted({x['phase'] for x in selected}):
                values=[x for x in selected if x['phase']==phase]
                item=dict(arm=arm,window=window,phase=phase,**{k:sum(x[k] for x in values) for k in
                    ('FE','admitted','duplicate','acceptKnown','accepted','directHV','finalPoints')})
                compact.append(item)
    csv_write(out/'phase-summary.csv',compact)
    print('PHASE_SUMMARY',json.dumps(compact),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);main(p.parse_args().root.resolve())
