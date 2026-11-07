"""Input-only complexity and one-operation monotonicity bounds, without any new fitness label."""
from collections import defaultdict
from datetime import datetime
from fractions import Fraction
from pathlib import Path
import math
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once

METADATA=ROOT/'runs/native-branch-value-probe-20261105-042828-915271'
POOL=ROOT/'runs/pool-closure-oracle-20261105-044946-189385'
STEMS=('20_8_5_1','100_2_3_1')


def classes(stage,machines):
    groups=defaultdict(list);M,W=stage['machines'],stage['workers']
    for resource in range(M if machines else W):
        signature=[]
        if not machines:signature.extend(stage[key][resource] for key in ('alpha','mu','beta','h0'))
        for job in range(len(stage['base'])):
            for other in range(W if machines else M):
                pair=resource*W+other if machines else other*W+resource
                signature.extend(stage[key][job][pair] for key in ('base','energy','labor'))
        groups[tuple(signature)].append(resource)
    return list(groups.values())


def canonical_bindings(jobs,sizes):
    """Count restricted-growth resource words within each identical physical class."""
    states={(0,)*len(sizes):1}
    for _ in range(jobs):
        following=defaultdict(int)
        for used,ways in states.items():
            following[used]+=ways*sum(used)
            for group,size in enumerate(sizes):
                if used[group]>=size:continue
                after=list(used);after[group]+=1;following[tuple(after)]+=ways
        states=following
    return sum(states.values())


def monotonicity(metadata):
    total=potential=0;maximum=Fraction(0);location=None
    for f,factory in enumerate(metadata['factories']):
        for k,stage in enumerate(factory):
            for j,values in enumerate(stage['base']):
                for pair,b in enumerate(values):
                    w=pair%stage['workers']
                    q=Fraction.from_float(b)*Fraction.from_float(stage['beta'][w])*Fraction.from_float(stage['mu'][w])
                    total+=1;potential+=q>1
                    if q>maximum:maximum=q;location={'factory':f,'stage':k,'job':j,'pair':pair,'worker':w}
    return {'maxBaseBetaMu':float(maximum),'maximumExactNumerator':maximum.numerator,'maximumExactDenominator':maximum.denominator,
        'maximumLocation':location,'resourceChoicesTested':total,'potentialNegativeDerivativeChoices':potential,
        'allChoicesOneOperationCompletionMonotoneForAnyH0To1':maximum<=1,
        'scope':'For a fixed prior fatigue state and specified resources, c(s)=s+b(1+beta*h(s)), '
                'c_prime=1-b*beta*mu*h(s). q<=1 suffices for monotone completion for h<=1. '
                'q>1 only permits inversion at h>1/q, not proof it occurs or has search value. '
                'This says nothing about all future fatigue, exposure, or the value of voluntary rest in other objectives.'}


def analyze(stem):
    metadata=read(METADATA/stem/'physical-coefficients.json')
    for name in (f'{stem}.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'):
        assert (METADATA/stem/'inputs'/name).read_bytes()==(POOL/stem/'inputs'/name).read_bytes()
    data,=rows(POOL/stem/'source-pool-phases.jsonl')
    phase=next(s for s in data['snapshots'] if s['phase']=='G2_CENTER_ENTRY')
    physical=[]
    for f,factory in enumerate(metadata['factories']):
        stage=factory[0];machine=classes(stage,True);worker=classes(stage,False)
        physical.append({'factory':f,'machines':stage['machines'],'workers':stage['workers'],
            'machineClasses':machine,'workerClasses':worker})
    families=[]
    for family in phase['pool']['families']:
        sizes=[family['factoryByJob'].count(f) for f in range(len(physical))];counts=[]
        for f,n in enumerate(sizes):
            resources=physical[f]
            raw=math.factorial(n)*(resources['machines']*resources['workers'])**n
            reduced=math.factorial(n)*canonical_bindings(n,[len(c) for c in resources['machineClasses']]) \
                    *canonical_bindings(n,[len(c) for c in resources['workerClasses']])
            counts.append({'factory':f,'jobs':n,'rawCompleteFirstStageStates':raw,
                'sufficientSymmetryReducedStates':reduced,'under200000States':reduced<=200000})
        families.append({'family':family['family'],'factories':counts,'rawSum':sum(c['rawCompleteFirstStageStates'] for c in counts),
            'reducedSum':sum(c['sufficientSymmetryReducedStates'] for c in counts),
            'completeFamilyWithin500000PhysicalEvaluations':sum(c['sufficientSymmetryReducedStates'] for c in counts)<=500000})
    return {'stem':stem,'physicalResourceClasses':physical,'families':families,'oneOperationBound':monotonicity(metadata)}


def main():
    root=ROOT/'runs'/datetime.now().strftime('input-state-complexity-%Y%m%d-%H%M%S-%f');root.mkdir()
    write_once(root/'protocol.json',{'searchFE':0,'decoderCalls':0,'sources':[str(METADATA),str(POOL)],'instances':STEMS,
        'scope':'Input-only sizing of entire fixed-FA factory spaces and a necessary fatigue-inversion condition. '
                'No search, outcome sampling, fitness labels, operator changes or promotion of a failed mechanism.',
        'stateSpace':'For each of all4 old families, raw n!*(M*W)^n. Sufficient exact-physics resource classes by '
                     'base/energy/labor across all jobs and other resources, worker alpha/mu/beta/h0 included. '
                     'Stage0 label symmetry is only an enumeration quotient, not a new donor-normalization search proposal. '
                     'Reconstructed standby is constant1; later stages are independent of stage0 resource IDs.',
        'sizeFlags':'Per-factory<=200000 and whole-family sum<=500000 are computational planning flags only, '
                    'chosen before counts, not scientific performance or quality gates.',
        'monotonicity':'Exact rational product of exported double coefficients q=b*beta*mu; q<=1 suffices for '
                       'single-operation completion monotonicity for h<=1. q>1 is potential only; no actual state sampled.',
        'limits':'Finite signatures may miss additional symmetries. Objective equivalence under relabeling still needs '
                 'full physical QA before reduced enumeration. No single-FA reachability or algorithm advantage follows.'})
    shutil.copy2(Path(__file__),root/Path(__file__).name)
    assert canonical_bindings(3,[2])==4 and canonical_bindings(3,[1,1])==8 and canonical_bindings(2,[2,1])==5
    results=[analyze(s) for s in STEMS];write_once(root/'analysis.json',{'instances':results,'searchFE':0,'decoderCalls':0})
    write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'decoderCalls':0})
    print('INPUT_STATE_ROOT',root,flush=True)
    for r in results:
        print(r['stem'],'max_q',r['oneOperationBound']['maxBaseBetaMu'],
              'potential',r['oneOperationBound']['potentialNegativeDerivativeChoices'],
              'reduced_families',[f['reducedSum'] for f in r['families']],flush=True)


if __name__=='__main__':
    main()
