"""Join observed physical slots to the frozen ledger and distinguish scalar impossibility from archive value."""
import csv
import numpy as np
from run_long_budget_bridge import rows, read, write_once, hypervolume
from research.composition_oracle.volume import UncoveredVolume


class SlotVolume:
    def __init__(self,norm):
        self.norm=norm;self.cache={};self.independent_error=0.;self.checks=0

    def value(self,points):
        key=tuple(map(tuple,points))
        if key not in self.cache:
            p=(np.asarray(points).reshape(-1,3)-self.norm['lower'])/self.norm['scale']
            value=UncoveredVolume(p,(1.5,)*3).background_hv
            if self.checks<4:
                error=abs(value-hypervolume(p,(1.5,)*3));assert error<1e-11
                self.independent_error=max(error,self.independent_error);self.checks+=1
            self.cache[key]=float(value)
        return self.cache[key]


def analyze_case(root,stem,method,norm):
    out=root/stem/method;records=rows(out/'critical-slots.jsonl');receipt,=rows(out/'critical-slot-receipt.jsonl')
    assert receipt['status']=='PASS' and receipt['globalPaidFE']==500000 and receipt['certificateViolations']==0
    with (out/'local-ledger.csv').open(encoding='utf-8') as f:
        ledger=[{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
    expected=[r for r in ledger if r['group']==0 and r['round']>=0]
    assert len(expected)==len(records)
    for actual,old in zip(records,expected):
        assert {k:actual[k] for k in ('visit','group','round','factory','paid','restarts')}==old
        assert actual['afterFE']-actual['beforeFE']==actual['paid']
        if actual['strictMakespanImprovementImpossible']:
            assert actual['afterObjectives'][0]==actual['beforeObjectives'][0] and actual['sameExitEncoding']
    total=sum(r['paid'] for r in records);assert total==receipt['observedSuccessfulFE']>0
    volume=SlotVolume(norm);cells=[]
    for record in records:
        before,after=volume.value(record['beforeArchive']),volume.value(record['afterArchive'])
        delta=after-before;assert delta>=-1e-11
        if abs(delta)<1e-12:delta=0.
        if record['archiveAdmissionEvents']==0:assert record['beforeArchive']==record['afterArchive'] and delta==0
        cells.append({k:record[k] for k in ('visit','round','factory','drawnFactory','fixed','limit','paid','beforeFE','afterFE',
            'strictMakespanImprovementImpossible','sameExitEncoding','archiveAdmissionEvents','returnedNormally')}|
            {'criticalFactories':[f for f,c in enumerate(record['factoryMakespan']) if c==max(record['factoryMakespan'])],
             'cmaxChange':record['afterObjectives'][0]-record['beforeObjectives'][0],'beforeArchiveHV':before,
             'afterArchiveHV':after,'archiveHVIncrement':delta})
    dead=[r for r in cells if r['strictMakespanImprovementImpossible']];dead_fee=sum(r['paid'] for r in dead)
    all_gain=sum(r['archiveHVIncrement'] for r in cells);dead_gain=sum(r['archiveHVIncrement'] for r in dead)
    result={'stem':stem,'method':method,'cells':cells,'Mslots':len(cells),'MintraSuccessfulFE':total,
        'impossibleSlots':len(dead),'impossibleSlotFE':dead_fee,'impossibleFEPct':100*dead_fee/total,
        'impossibleSlotsWithArchiveAdmissions':sum(r['archiveAdmissionEvents']>0 for r in dead),
        'impossibleSlotsWithPositiveHV':sum(r['archiveHVIncrement']>0 for r in dead),
        'allMintraArchiveHVIncrementSum':all_gain,'impossibleArchiveHVIncrementSum':dead_gain,
        'impossibleShareOfMintraHVIncrementPct':100*dead_gain/all_gain if all_gain>1e-12 else None,
        'slotFactoryDiffersFromDraw':sum(r['factory']!=r['drawnFactory'] for r in cells),
        'multiCriticalSlots':sum(len(r['criticalFactories'])>1 for r in cells),
        'worthMatchedCriticalRoutingProbe':100*dead_fee/total>=20,
        'independentHVCheckMaxError':volume.independent_error,
        'limits':'Read-only replay under frozen random-factory ledger. Scalar strict-improvement impossibility is not no multiobjective value. '
                 'HV increments are sequential archive increments, including possible future replacement; not causal algorithm gap or novelty. '
                 'No routing, budget or default changes; observation time not performance evidence.'}
    write_once(out/'critical-analysis.json',result);return result


def analyze(root,specs,methods):
    cases=[analyze_case(root,s['stem'],m,s['normalization']) for s in specs for m in methods]
    result={'cases':[{k:v for k,v in r.items() if k!='cells'} for r in cases],
            'worthMatchedCriticalRoutingProbe':all(r['worthMatchedCriticalRoutingProbe'] for r in cases)}
    write_once(root/'analysis.json',result);return result
