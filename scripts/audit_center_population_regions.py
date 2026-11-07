"""Post-hoc geometry and complete retained-run accounting; no decoder, candidate or search feedback."""
from datetime import datetime
import numpy as np
from run_long_budget_bridge import ROOT,read,rows,write_once,hypervolume,nondominated

SOURCE=ROOT/'runs/center-population-probe-20261105-080512-453517'
RETAINED=[ROOT/'runs'/f'center-population-probe-20261105-{suffix}' for suffix in
          ('080354-637323','080503-204765','080512-453517')]
ARMS=('OFF','FIXED_EA','UNIFORM_EA','TOURNAMENT_EA','NSGA')


def volume(points,axis=0,upper=1.5):
    ref=np.full(3,1.5);ref[axis]=upper
    return float(hypervolume(points,ref))


def analyze(spec,seeds):
    stem,norm=spec['stem'],spec['normalization']
    fronts={}
    for seed in seeds:
        for arm in ARMS:
            points=rows(SOURCE/stem/str(seed)/arm/'anytime.jsonl')
            front=next(p['front'] for p in points if p['checkpointKind']=='FE' and p['checkpoint']==5100)
            fronts[(seed,arm)]=(np.asarray(front)-norm['lower'])/norm['scale']
    common=nondominated(np.vstack(list(fronts.values())))
    cuts={axis:[0.,*map(float,np.quantile(common[:,axis],[.25,.5,.75])),1.5] for axis in range(3)}
    assert all(values==sorted(values) for values in cuts.values())
    results=[]
    for seed in seeds:
        main,nsga=(fronts[(seed,arm)] for arm in ('TOURNAMENT_EA','NSGA'))
        both=nondominated(np.vstack([main,nsga]));main_hv,nsga_hv,both_hv=map(volume,(main,nsga,both))
        parts=[]
        for axis in range(3):
            own=[]
            for lo,hi in zip(cuts[axis],cuts[axis][1:]):
                a=volume(main,axis,hi)-volume(main,axis,lo)
                b=volume(nsga,axis,hi)-volume(nsga,axis,lo)
                own.append({'lower':lo,'upper':hi,'mainHV':a,'nsgaHV':b,'signedNsgaMinusMain':b-a})
            assert abs(sum(p['signedNsgaMinusMain'] for p in own)-(nsga_hv-main_hv))<1e-10
            parts.append({'axis':axis,'slabs':own,'firstSlabShareOfPositiveNetGap':
                own[0]['signedNsgaMinusMain']/(nsga_hv-main_hv) if nsga_hv-main_hv>1e-10 else None})
        coverage=lambda left,right:float(np.mean([np.any(np.all(left<=p,axis=1)) for p in right]))
        results.append({'seed':seed,'mainHV':main_hv,'nsgaHV':nsga_hv,'jointHV':both_hv,
            'mainMissingNsgaVolume':both_hv-main_hv,'nsgaMissingMainVolume':both_hv-nsga_hv,
            'mainMissingNsgaPctOfMainHV':100*(both_hv-main_hv)/main_hv,
            'nsgaMissingMainPctOfNsgaHV':100*(both_hv-nsga_hv)/nsga_hv,
            'mainWeakCoverageOfNsgaPoints':coverage(main,nsga),'nsgaWeakCoverageOfMainPoints':coverage(nsga,main),
            'mainMinimum':main.min(axis=0).tolist(),'nsgaMinimum':nsga.min(axis=0).tolist(),'axisPartitions':parts})
    return {'stem':stem,'empiricalAxisCuts':cuts,'pairs':results}


def accounting():
    result=[]
    for root in RETAINED:
        receipts=[rows(p)[0] for p in root.rglob('run-receipt.jsonl')]
        result.append({'root':str(root),'runReceipts':len(receipts),'successfulFE':sum(r['successful'] for r in receipts),
            'attemptedFE':sum(r['attempted'] for r in receipts),'failedFE':sum(r['failed'] for r in receipts),
            'checkpointFullDecoderQA':sum(read(p)['uniqueOfflineDecodes'] for p in root.rglob('checkpoint-validation.json')),
            'status':read(root/'status.json')})
    return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('center-population-regions-%Y%m%d-%H%M%S-%f');root.mkdir()
    protocol=read(SOURCE/'protocol.json')
    write_once(root/'protocol.json',{'source':str(SOURCE),'instances':protocol['instances'],'seeds':protocol['seeds'],
        'scope':'Explicitly post-hoc geometry of already-paid 5100FE fronts; not a new gate, causal proof or promotion.',
        'regions':'Per-instance NDunion of all5arms/2seeds defines eachobjective quartiles; integrate HV in4disjointslabs independently onC/E/W. '
                  'Do not sum slabs across axes or equate pointcoverage with HV. Jointvolume separates bothdirections of missingcoverage.',
        'accounting':'Read all receipts in2retainedengineering failures and1completedroot. Never overwrite oldstatus. '
                     'Originalfirstroot completed500k but itscontroller completedRuns was0 because comparatorfailed before engineeringreturn. '
                     'Secondroot was0FE FileExistsError while attemptingwrite-once verify, no oldfile altered. Reuse500k only once.',
        'cost':'Zero search FE and decoder calls, no new genome or searchfeedback.'})
    result={'instances':[analyze(s,protocol['seeds']) for s in protocol['instances']],
            'retainedAccounting':accounting(),'searchFE':0,'decoderCalls':0}
    result['actualSuccessfulFEAllRetained']=sum(v['successfulFE'] for v in result['retainedAccounting'])
    result['actualCheckpointQAAllRetained']=sum(v['checkpointFullDecoderQA'] for v in result['retainedAccounting'])
    write_once(root/'analysis.json',result)
    print('CENTER_POPULATION_REGIONS_ROOT',root,flush=True)
    for instance in result['instances']:
        print(instance['stem'],[(p['seed'],p['mainMissingNsgaPctOfMainHV'],p['nsgaMissingMainPctOfNsgaHV'],
              p['axisPartitions'][0]['firstSlabShareOfPositiveNetGap']) for p in instance['pairs']],flush=True)


if __name__=='__main__':main()
