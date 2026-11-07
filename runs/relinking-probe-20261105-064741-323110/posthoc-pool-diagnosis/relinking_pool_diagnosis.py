"""Post-hoc union and concentration checks; original recipient-level gate stays unchanged."""
from pathlib import Path
from collections import defaultdict
import shutil
import sys
import numpy as np
from run_long_budget_bridge import read, rows, write_once, nondominated
from research.composition_oracle.volume import UncoveredVolume
from relinking_analysis import METHODS


def hv(points,reference=1.5):
    return UncoveredVolume(nondominated(points),(reference,)*3).background_hv


def diagnose(root,spec):
    stem,norm=spec['stem'],spec['normalization'];analysis=read(root/stem/'analysis.json')
    pairs=read(root/stem/'pairs.json');pair_ids={p['pairId']:p for p in pairs}
    grouped=defaultdict(list)
    for row in rows(root/stem/'probe/outcomes.jsonl'):
        grouped[(pair_ids[row['pair']]['contextId'],row['method'])].append(row['objectives'])
    normalize=lambda values:(np.asarray(values,dtype=float).reshape(-1,3)-norm['lower'])/norm['scale']
    contexts=[]
    for context in read(root/stem/'contexts.json'):
        background=normalize(context['background']);base=hv(background);methods={}
        for method in METHODS:
            points=grouped[(context['contextId'],method)]
            assert len(points)==24*int(stem.split('_')[0])
            joint=hv(np.vstack([background,normalize(points)]))-base
            own=[p for p in analysis['pairs'] if p['context']==context['contextId']]
            summed=sum(p['methods'][method]['unionAddedHV']['1.5'] for p in own)
            methods[method]={'jointContextAddedHV':max(0.,float(joint)),'jointAddedHVPctOfBackground':100*max(0.,float(joint))/base,
                'sumOfIndividualPathGains':summed,'jointToSumRatio':max(0.,float(joint))/summed if summed>1e-12 else None}
        contexts.append({'context':context['contextId'],'seed':context['seed'],'step':context['step'],
            'backgroundHV':base,'successfulOffspringPerMethod':len(points),'methods':methods})
    role_summary=[]
    for role in ('MAKESPAN','ENERGY','WORKER_COST'):
        own=[p for p in analysis['pairs'] if p['teacherRole']==role]
        role_summary.append({'teacherRole':role,'pairs':len(own),'methods':{m:{
            'meanPathUnionAddedHV':float(np.mean([p['methods'][m]['unionAddedHV']['1.5'] for p in own])),
            'positivePairs':sum(p['methods'][m]['unionAddedHV']['1.5']>1e-12 for p in own)} for m in METHODS}})
    concentration={}
    for method in METHODS:
        ordered=sorted([c['methods'][method]['meanUnionAddedHV']['1.5'] for c in analysis['cells']],reverse=True);total=sum(ordered)
        concentration[method]={'positiveRecipients':sum(v>1e-12 for v in ordered),'top1Share':ordered[0]/total if total else None,
                               'top5Share':sum(ordered[:5])/total if total else None}
    source_pairs=analysis['pairs'];cover_repair_different=sum(abs(p['methods']['COVER_PATH']['unionAddedHV']['1.5']-
        p['methods']['REPAIR_PATH']['unionAddedHV']['1.5'])>1e-11 for p in source_pairs)
    return {'stem':stem,'contexts':contexts,'roleSummary':role_summary,'concentration':concentration,
        'coverRepairDifferentPathHV':cover_repair_different,'totalPairs':len(source_pairs),
        'meanJointContextAddedHV':{m:float(np.mean([c['methods'][m]['jointContextAddedHV'] for c in contexts])) for m in METHODS},
        'jointContextWinsVsClassic':sum(c['methods']['COVER_PATH']['jointContextAddedHV']>c['methods']['CLASSIC']['jointContextAddedHV']+1e-12 for c in contexts),
        'newSearchFE':0,'additionalDecodes':0,
        'limits':'Post-hoc description only. Six correlated contexts and role-selected genotypes are not independent confirmation '
                 'or causal supply credit. Cannot promote a failed arm, change parent breadth gate, select donors/order/length or claim whole-loop gain.'}


def main():
    root=Path(sys.argv[1]).resolve();out=root/'posthoc-pool-diagnosis';out.mkdir();shutil.copy2(__file__,out/Path(__file__).name)
    result={'instances':[diagnose(root,s) for s in read(root/'protocol.json')['instances']],'originalGateUnchanged':True}
    write_once(out/'diagnosis.json',result)
    for r in result['instances']:
        print(r['stem'],'jointMeans',r['meanJointContextAddedHV'],'winsClassic',r['jointContextWinsVsClassic'],
              'coverRepairDifferentPaths',r['coverRepairDifferentPathHV'],'concentration',r['concentration'])
        for role in r['roleSummary']:print(role['teacherRole'],{m:v['meanPathUnionAddedHV'] for m,v in role['methods'].items()})


if __name__=='__main__':main()
