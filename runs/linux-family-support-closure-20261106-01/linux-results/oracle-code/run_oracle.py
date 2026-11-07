"""Freeze and execute the small charged oracle, including cutoff/failure acceptance."""
import argparse
from pathlib import Path
import subprocess
import time
from common import BASE,SOURCE,SEEDS,linux,read,write,sha,lines
from structure import physical

ANCHOR=BASE/'runs/linux-pilot-evaluation-20261106-01'
JAVA=BASE/'runtime/jdk17/bin/java'


def csv(values):return ','.join(map(str,values))


def assemble(chains):
    rows=[(j,f,m,w) for f,chain in enumerate(chains) for j,m,w in chain]
    return [list(v) for v in zip(*rows)]


def cases(root,seed):
    folder=root/'contexts/20_8_5_1'/str(seed);points=read(folder/'before.json')
    background=[physical(points[0],f) for f in range(5)];count=0
    target=folder/'cases.tsv'
    with target.open('x') as stream:
        for f in range(5):
            for record in lines(folder/f'factory-{f}.jsonl'):
                chains=list(background);chains[f]=list(zip(record['jobs'],record['machines'],record['workers']))
                v=assemble(chains);assert sorted(v[0])==list(range(20))
                assert dict(zip(v[0],v[1]))==dict(zip(points[0]['JS'],points[0]['FA']))
                stream.write('\t'.join([str(count),str(f),str(record['id']),*map(csv,v)])+'\n');count+=1
    assert count==read(folder/'structure.json')['uniqueLocalCandidates']
    return dict(seed=seed,count=count,path=str(target),sha256=sha(target))


def build(root,source):
    out=root/'build-01';out.mkdir();classes=out/'classes';classes.mkdir()
    files=sorted(source.glob('*.java'));assert len(files)==2
    inherited=(SOURCE/'probe-build-01/classpath.txt').read_text().strip()
    command=[str(BASE/'runtime/jdk17/bin/javac'),'-encoding','UTF-8','--release','8','-implicit:none',
             '-cp',inherited,'-d',str(classes),*map(str,files)]
    result=subprocess.run(command,text=True,capture_output=True)
    write(out/'command.json',command);(out/'build.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    cp=str(classes)+':'+inherited;(out/'classpath.txt').write_text(cp)
    deps={}
    for entry in inherited.split(':'):
        path=Path(entry)
        deps[entry]={str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file()} if path.is_dir() else sha(path)
    write(out/'identity.json',dict(sources={p.name:sha(p) for p in files},dependencies=deps,
        classes={str(p.relative_to(classes)):sha(p) for p in classes.rglob('*.class')},
        java=subprocess.check_output([str(JAVA),'-version'],stderr=subprocess.STDOUT,text=True)))
    return cp


def invoke(cp,case,out,limit,physics=True,fail=None):
    out.mkdir(parents=True,exist_ok=False);input_dir=ANCHOR/'payload/inputs/20_8_5_1'
    command=['nice','-n','10',str(JAVA),'-Xms128m','-Xmx2g',f'-Dresearch.pilot.physics={str(physics).lower()}']
    if fail:command.append(f'-Dresearch.pilot.failAt={fail}')
    command+=['-cp',cp,'research.dynamic.FamilySupportRun',str(input_dir/'20_8_5_1.txt'),
        str(input_dir/'RECONSTRUCTED-setup.txt'),str(input_dir/'fatigue-input.txt'),case['path'],str(out),str(limit),str(case['seed'])]
    write(out/'command.json',command);start=time.perf_counter()
    with (out/'run.log').open('x') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
    write(out/'process.json',dict(exitCode=result.returncode,seconds=time.perf_counter()-start))
    assert result.returncode==(1 if fail else 0),str(out)
    receipt=read(out/'receipt.json');expected=fail if fail else limit
    assert (receipt['attempted'],receipt['successful'],receipt['failed'])==(expected,expected-(1 if fail else 0),1 if fail else 0)
    records=list(lines(out/'paid.jsonl'));assert len(records)==receipt['successful']==receipt['written']
    assert [r['fe'] for r in records]==list(range(1,len(records)+1))
    assert receipt['physicsQA']['fullTimelineChecks']==(len(records) if physics else 0)
    if fail:assert 'EXPECTED_PAID_FAILURE' in receipt['error']
    return receipt


def main(root,source):
    linux();pre=read(root/'preflight.json');assert pre['passed']
    rows=[cases(root,seed) for seed in SEEDS]
    total=sum(c['count'] for c in rows);assert total==3580==pre['uniqueLocalCandidates']
    write(root/'oracle-protocol.json',dict(cases=rows,scienceFE=total,engineeringAttemptFE=7,
        expectedEngineeringSuccess=6,expectedEngineeringFailure=1,
        engineering='Prefix1/prefix2 with full timeline QA; prefix2 without observation; failure at evaluation2',
        paidTotalAttemptLimit=total+7,physicsQA='One independent full timeline per successful observed evaluation',
        witnessQA='At most60 deterministic complete assemblies; extra decodes reported separately; no search feedback',
        closure='Exact dyadic arithmetic of rounded local objectives; retain Pareto witnesses. Not exact real arithmetic of decoder global sums',
        floatingPolicy='Witness full decode relative tolerance1e-9; report absolute errors and do not claim bit equality for algebraic sums',
        commonReference='ND union of all three A0s, finite-support closures, and existing request-pool closures; fixed before metric computation',
        claimScope='Conditional capacity only. Not a fair algorithm competitor; oracle expenditure cannot be ignored',
        timeComparison=False))
    cp=build(root,source)
    checks=[]
    for name,limit,observe,fail in [('prefix1',1,True,None),('prefix2',2,True,None),('quiet2',2,False,None),('failure2',5,True,2)]:
        checks.append(invoke(cp,rows[0],root/'engineering'/name,limit,observe,fail))
    assert checks[1]['paidSHA256']==checks[2]['paidSHA256']
    assert checks[0]['paidSHA256']==checks[3]['paidSHA256']
    assert checks[0]['stopReason']==checks[1]['stopReason']=='FE_LIMIT'
    write(root/'engineering-acceptance.json',dict(passed=True,attempted=sum(x['attempted'] for x in checks),
        successful=sum(x['successful'] for x in checks),failed=sum(x['failed'] for x in checks),
        fullTimelineQA=sum(x['physicsQA']['fullTimelineChecks'] for x in checks),quietTrajectoryIdentical=True))
    receipts=[]
    for case in rows:
        receipt=invoke(cp,case,root/'science'/str(case['seed']),case['count']);receipts.append(receipt)
        print('ORACLE_CONTEXT_DONE',case['seed'],receipt['successful'],flush=True)
    write(root/'science-acceptance.json',dict(passed=True,successful=sum(r['successful'] for r in receipts),
        attempted=sum(r['attempted'] for r in receipts),failed=sum(r['failed'] for r in receipts),
        fullTimelineQA=sum(r['physicsQA']['fullTimelineChecks'] for r in receipts)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);a=p.parse_args();main(a.root,a.source)
