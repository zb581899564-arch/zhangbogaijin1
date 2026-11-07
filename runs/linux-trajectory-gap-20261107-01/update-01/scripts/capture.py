"""Sequential fixed-FE capture, deterministic engineering gate, no new search policy."""
from pathlib import Path
import argparse
import os
import subprocess
import time
from common import *


def checkpoint_key(folder):
    return {(p['checkpointKind'],p['checkpoint'],p['bornFE'],tuple(p['objectives']),
             *(tuple(p[k]) for k in ('JS','FA','MA','WA')))
            for p in rows(folder/'checkpoint-solutions.jsonl') if p['checkpointKind']=='FE'}


def run(root, arm, limit, observing):
    plan=read(root/'protocol.json')
    assert limit in (plan['engineeringFEPerArm'],plan['captureFEPerArm'])
    out=root/('capture' if observing else 'engineering')/arm
    out.mkdir(parents=True,exist_ok=False)
    old=root/'payload/historical'/plan['instance']/str(plan['seed'])/arm
    original=read(old/'command.json')
    options=original[1:original.index('-cp')]
    options=[x for x in options if not x.startswith('-Dresearch.pa.auditPaid=')]
    options+=['-Dresearch.pa.auditPaid=true','-Dresearch.trajectory.observe='+str(observing).lower()]
    cp=(root/'build-01'/('classpath.txt' if observing else 'baseline-classpath.txt')).read_text()
    inp=ANCHOR/'inputs'/plan['instance']
    command=['nice','-n','10',str(BASE/'runtime/jdk17/bin/java'),*options,'-cp',cp,
        'research.dynamic.GomCapabilityRun',str(inp/(plan['instance']+'.txt')),str(inp/'RECONSTRUCTED-setup.txt'),
        str(inp/'fatigue-input.txt'),str(out),arm,str(limit),str(plan['seed']),'Infinity']
    write(out/'command.json',command)
    write(out/'load-before.json',dict(load=os.getloadavg(),epoch=time.time()))
    start=time.monotonic()
    with (out/'run.log').open('x') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
    write(out/'process.json',dict(exitCode=result.returncode,wallSeconds=time.monotonic()-start,loadAfter=os.getloadavg()))
    if result.returncode:raise RuntimeError('Failure retained: '+str(out))
    receipt,=rows(out/'run-receipt.jsonl');trace,=rows(out/'trajectory-receipt.jsonl')
    assert receipt['successful']==receipt['attempted']==limit and receipt['failed']==0 and receipt['error'] is None
    assert trace['paidRows']==limit and trace['paidSHA256']==receipt['paidSHA256']
    assert initial(out)==initial(old)
    qa=read(out/'checkpoint-validation.json')
    assert qa['status']=='passed' and qa['allReachedPointsCovered']
    if observing:
        engineering,=rows(root/'engineering'/arm/'trajectory-receipt.jsonl')
        assert trace['prefixSHA256']['30000']==engineering['paidSHA256'], 'Observer trajectory divergence'
        assert checkpoints(out)==checkpoints(old), 'Old front trajectory divergence'
        assert checkpoint_key(out)==checkpoint_key(old), 'Old paid representatives divergence'
    old_identity,=rows(old/'loaded-identity.jsonl');identity,=rows(out/'loaded-identity.jsonl')
    changed={'GomCapabilityRun','CanonicalHmopso','GomLocalProgram','ClassicAlgorithm','PaPopulation'} if observing else {'GomCapabilityRun'}
    for name, info in old_identity.items():
        if isinstance(info,dict) and 'sha256' in info and name.rsplit('.',1)[-1] not in changed:
            assert identity[name]['sha256']==info['sha256'], name
    write(out/'acceptance.json',dict(passed=True,actualFE=limit,failed=0,offlineQADecodes=qa['uniqueOfflineDecodes'],
        initialEqualsOld=True,oldPublicCheckpointsAndBornGenomesEqual=observing,
        first30000PaidDigestEqualsFrozenSearch=observing,readOnlyObservationNanos=trace['observationNanos'],
        changedClasses=sorted(changed),sameTimeClaim=False))
    print('CAPTURE_ACCEPTED',arm,limit,'trace',observing,'wall',time.monotonic()-start,flush=True)


def main(root):
    linux()
    for arm in ARMS:run(root,arm,30000,False)
    for arm in ARMS:run(root,arm,500000,True)
    accepted=[read(p) for p in root.glob('*/**/acceptance.json') if p.parent.name in ARMS]
    assert len(accepted)==6
    total=sum(x['actualFE'] for x in accepted);qa=sum(x['offlineQADecodes'] for x in accepted)
    assert total==1590000 and qa<=60000
    write(root/'capture-complete.json',dict(captureFE=1500000,engineeringFE=90000,totalActualFE=total,
        failures=0,offlineQADecodes=qa,allSixAccepted=True,noNewSeed=True,noMainlineChange=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);main(p.parse_args().root.resolve())
