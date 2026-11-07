"""Zero-FE independent metric checks, neutral-view linkage and conditional stop decision."""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import csv
import struct
import sys
import time
from common import *


def neutral_aliases(folder):
    """Only PA's position-preserving reencode boundary; no matching by objective proximity."""
    first=[]
    with (folder/'trajectory-paid.csv').open() as f:
        for row in csv.DictReader(f):
            if int(row['fe'])>100:break
            first.append({'key':row['key'],'objectives':[float(row[k]) for k in ('Cmax','TEC','TWC')]})
    before=first; aliases=defaultdict(list);models=0;count=0
    for e in rows(folder/'trajectory-events.jsonl'):
        if e['kind']!='population':continue
        if e['label']=='SURVIVORS':before=e['points']
        if e['label']!='PA_MODEL':continue
        models+=1;after=e['points'];assert len(before)==len(after)==100
        for index,(a,b) in enumerate(zip(before,after)):
            assert a['objectives']==b['objectives'], (e['fe'],index)
            aliases[int(e['fe'])].append((b['key'],a['key']))
            count+=a['key']!=b['key']
    return aliases,dict(models=models,positionsChecked=100*models,changedRawViews=count,
        evidence='Same PA population slot before and after frozen neutral reencoder, exact objectives; no objective-only matching',
        limit='This does not constitute a new independent physical timeline QA of every neutral view')


def corrected_reuse(folder, arm):
    aliases,audit=neutral_aliases(folder) if arm=='PA_JOINT' else ({},{'models':0})
    roots={};seen=set();last_use={};productive=set();admitted=[];unknown=Counter()
    def resolve(key):
        trail=[]
        while key in roots:trail.append(key);key=roots[key]
        for item in trail:roots[item]=key
        return key
    with (folder/'trajectory-paid.csv').open() as f:
        for row in csv.DictReader(f):
            fe=int(row['fe'])
            for after,before in aliases.get(fe-1,[]):
                a,b=resolve(after),resolve(before)
                if a!=b:
                    # The after-view is a raw neutral representation; an earlier paid alias is allowed.
                    roots[a]=b
                    if a in seen:seen.add(b)
            for relation in ('parent','donor','teacher'):
                if not row[relation]:continue
                k=resolve(row[relation]);last_use[k]=fe
                if k not in seen:unknown[relation]+=1
                if relation=='parent' and row['admitted']=='1':productive.add(k)
            key=resolve(row['key']);seen.add(key)
            if row['admitted']=='1':admitted.append((fe,row['phase'],row['role'],key))
    canonical_use={}
    for key,fe in last_use.items():
        k=resolve(key);canonical_use[k]=max(fe,canonical_use.get(k,0))
    productive={resolve(key) for key in productive}
    summary=defaultdict(Counter)
    for fe,phase,role,key in admitted:
        k=resolve(key);item=summary[(phase,role)];item['admitted']+=1
        item['laterUsed']+=canonical_use.get(k,0)>fe;item['productiveParent']+=k in productive
    assert not unknown, (arm,unknown)
    return [dict(arm=arm,phase=k[0],role=k[1],**v) for k,v in summary.items()],dict(arm=arm,unknownUses=dict(unknown),**audit)


def metric_audit(root):
    sys.path.insert(0,str(ANCHOR))
    from research.pilot_evaluation import hypervolume, igd_plus, igd
    reference=read(root/'step1/100_2_3_1-reference.json');scale=np.asarray(SCALES['100_2_3_1'])
    result=[]
    for arm in ARMS:
        values=checkpoints(root/'capture'/arm)
        for fe in (100000,250000,500000):
            front=np.asarray(values[fe]);observed=metrics(front,reference,scale)
            for ref in (1.25,1.5,2.):
                a=float(moocore.hypervolume(front/scale,ref=[ref]*3));b=hypervolume(front/scale,np.full(3,ref))
                assert abs(a-b)<1e-10
                result.append(dict(arm=arm,fe=fe,reference=ref,HV=a,independentHV=b,error=abs(a-b)))
            assert abs(observed['IGDplus']-igd_plus(front/scale,np.asarray(reference)/scale))<1e-12
            assert abs(observed['IGD']-igd(front/scale,np.asarray(reference)/scale))<1e-12
    return result


def main(root):
    linux();out=root/'step3';out.mkdir();start=time.monotonic()
    checks=metric_audit(root);flows=[];alias_audits=[]
    for arm in ARMS:
        a,b=corrected_reuse(root/'capture'/arm,arm);flows.extend(a);alias_audits.append(b)
    csv_write(out/'neutral-linked-schedule-use.csv',flows)
    write(out/'neutral-view-audit.json',alias_audits)
    write(out/'metric-audit.json',dict(HVChecks=checks,IGDandIGDplusChecks=9,passed=True,newDecodes=0))
    costs=[]
    for phase in ('engineering','capture'):
        for arm in ARMS:
            folder=root/phase/arm;r,=rows(folder/'run-receipt.jsonl');t,=rows(folder/'trajectory-receipt.jsonl')
            costs.append(dict(phase=phase,arm=arm,attempted=r['attempted'],successful=r['successful'],failed=r['failed'],
                searchSeconds=r['searchSeconds'],observationSeconds=t['observationNanos']/1e9,
                checkpointQA=read(folder/'checkpoint-validation.json')['uniqueOfflineDecodes']))
    csv_write(out/'actual-costs.csv',costs)
    write(out/'decision.json',dict(status='STOP_BEFORE_NEW_MECHANISM_CAUSAL_GAP_REMAINS',
        completed=['Existing twelve matched trajectories re-evaluated with common references',
                   'Three same-initial 500k Linux read-only captures and three 30k original-search controls',
                   'Direct output, exact schedule-use, acceptance, working-state and historical-duplicate triage'],
        findings=['The selected large-job failure is against PA, not matched NSGA',
                  'PA separation is strongest during 100k-250k; continued FA-changing joint production is associated with it',
                  'SHARE central archive-admitted local states are accepted and used; a generic accept-more patch is unsupported',
                  'Fixed family low direct output and poor later shared admission repeat known capacity facts'],
        rejectedRepeats=['Increase cross-factory swap frequency','Relax fixed-family donor access',
                         'Restore dynamic roles or global CENTER preference','Add post-local selector',
                         'Tune donor ratios, caps or resource/sequence edit sizes'],
        unresolved=['Whether stronger intermediate states, their retained resource support or continuous in-place evolution causes the gap',
                    'Historical exact-FA donor probes cannot identify this compound architecture difference',
                    'No paired counterfactual with the same mature state, model, support and budget has isolated a new factor'],
        nextDiscussion='Preserve four objective duties and validated sharing; isolate a specific outer-state lifecycle difference before proposing another mechanism. The present evidence does not justify another operator experiment.',
        thirdStepMeaning='The conditional gate was evaluated; no new mechanism implemented or performance claim made',
        newMechanismFE=0,totalActualFE=sum(x['attempted'] for x in costs),extraCheckpointQA=sum(x['checkpointQA'] for x in costs),
        mainlineChanged=False,expandedInstancesOrSeeds=False,offlineAnalysisSeconds=time.monotonic()-start))
    print('FINAL_AUDIT',json.dumps(alias_audits),flush=True)
    print('DECISION', (out/'decision.json').read_text(),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);main(p.parse_args().root.resolve())
