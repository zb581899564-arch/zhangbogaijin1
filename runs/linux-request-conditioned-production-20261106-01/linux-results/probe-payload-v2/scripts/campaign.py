"""Sequential foreground engineering and fixed-budget science; no automatic expansion."""
import argparse
from pathlib import Path
from common import ANCHOR, JAVA, STEMS, SEEDS, linux, process, read, write
from protocol import ARMS


def run(root, stem, seed, q, arm, *, engineering=False, label=None, limit=512, fail=False, observer=True, build='probe-build-01'):
    category='engineering' if engineering else 'science'
    out=root/category/stem/str(seed)/str(q)/(label or arm)
    source=ANCHOR/'payload/inputs'/stem
    command=['nice','-n','10',str(JAVA),'-Xms32m','-Xmx2g',
        '-Dresearch.request.limit='+str(limit),'-Dresearch.request.observer='+str(observer).lower(),
        '-Dresearch.pilot.physics='+str(engineering).lower()]
    if fail:command.append('-Dresearch.pilot.failAt=2')
    command+=['-cp',(root/build/'classpath.txt').read_text().strip(),
        'research.dynamic.RequestProductionRun',str(source/(stem+'.txt')),str(source/'RECONSTRUCTED-setup.txt'),
        str(source/'fatigue-input.txt'),str(out),str(root/'inputs-v2'/stem/str(seed)/str(q)),arm,str(seed),str(q)]
    process(command,out,expected=1 if fail else 0)
    receipt=read(out/'receipt.json')
    assert receipt['attempted']==(2 if fail else limit)
    assert receipt['successful']==(1 if fail else limit) and receipt['failed']==int(fail)
    assert receipt['productionPaid']==min(receipt['successful'],511)
    assert receipt['assemblyPaid']==int(not fail and limit==512)
    if engineering:assert receipt['physicsQA']['fullTimelineChecks']==receipt['successful']
    return out,receipt


def engineering(root,build):
    plan=dict(attemptedFE=7176,expectedFailures=2,
        cases=[dict(instance=s,seed=SEEDS[0],requestIndex=0) for s in STEMS],
        perCase='ROLE/REQUEST/ORDINARY/SHUFFLED each512; REQUEST repeat512 and observationOff512; REQUEST cut1/2/511; failure2',
        aggregation='Median of three request-paired effects within each source seed, then median/range/signs across three source seeds',
        noScienceBeforeIndependentEngineeringAudit=True)
    write(root/'engineering-plan.json',plan)
    results=[]
    for stem in STEMS:
        records={}
        for arm in ARMS:
            records[arm]=run(root,stem,SEEDS[0],0,arm,engineering=True,build=build)
        for label,observer in [('REPEAT',True),('OBSERVER_OFF',False)]:
            records[label]=run(root,stem,SEEDS[0],0,'REQUEST',engineering=True,label=label,observer=observer,build=build)
        for label,(out,receipt) in records.items():
            assert read(out/'before.json')==read(records['ROLE'][0]/'before.json')
            assert read(out/'models.json')==read(records['ROLE'][0]/'models.json')
        for label in ('REPEAT','OBSERVER_OFF'):
            assert records[label][1]['paidSHA256']==records['REQUEST'][1]['paidSHA256']
            for name in ('after.json','front.json','final-pools.json','assembly.json'):
                assert read(records[label][0]/name)==read(records['REQUEST'][0]/name)
        reference=(records['REQUEST'][0]/'steps.jsonl').read_text().splitlines()
        for limit in (1,2,511):
            out,_=run(root,stem,SEEDS[0],0,'REQUEST',engineering=True,label='CUT_'+str(limit),limit=limit,build=build)
            assert (out/'steps.jsonl').read_text().splitlines()==reference[:limit]
            assert not read(out/'assembly.json')['performed']
        out,_=run(root,stem,SEEDS[0],0,'REQUEST',engineering=True,label='FAIL_2',fail=True,build=build)
        assert (out/'steps.jsonl').read_text().splitlines()==reference[:1]
        results.append(dict(instance=stem,passed=True,repeatExact=True,observerExact=True,cutoffsExact=True))
        print('REQUEST_ENGINEERING_PASS',stem,flush=True)
    write(root/'engineering-acceptance.json',dict(passed=True,contexts=results,independentAuditPending=True))


def science(root,build):
    assert read(root/'engineering-acceptance.json')['passed']
    assert read(root/'engineering-independent-audit.json')['passed']
    assert read(root/'request-audit-v2.json')['passed']
    for i,stem in enumerate(STEMS):
        for j,seed in enumerate(SEEDS):
            for q in range(3):
                shift=(i+j+q)%4
                for arm in ARMS[shift:]+ARMS[:shift]:
                    run(root,stem,seed,q,arm,build=build)
            print('REQUEST_SCIENCE_SOURCE_COMPLETE',stem,seed,flush=True)
    receipts=[read(p) for p in root.glob('science/*/*/*/*/receipt.json')]
    assert len(receipts)==72 and sum(r['successful'] for r in receipts)==36864
    assert sum(r['failed'] for r in receipts)==0
    write(root/'science-complete.json',dict(passed=True,runs=72,successful=36864,failed=0,statisticsPending=True))


if __name__=='__main__':
    linux();parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--action',choices=['engineering','science'],required=True)
    parser.add_argument('--build',default='probe-build-01')
    args=parser.parse_args();globals()[args.action](args.root,args.build)
