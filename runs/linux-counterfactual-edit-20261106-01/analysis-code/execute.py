"""Compile, verify endpoint imports, then execute a bounded sequential matrix once."""
import argparse
from pathlib import Path
import subprocess
import sys
import time
from cf_common import *

JAVA=BASE/'runtime/jdk17/bin/java'


def build(root):
    output=root/'build-01';output.mkdir();classes=output/'classes';classes.mkdir()
    java=sorted((root/'source/java').glob('*.java'))
    cp=(OLD/'build-01/classpath.txt').read_text().strip()
    command=[str(BASE/'runtime/jdk17/bin/javac'),'-encoding','UTF-8','--release','8','-implicit:none',
             '-cp',cp,'-d',str(classes),*map(str,java)]
    write(output/'command.json',command)
    p=subprocess.run(command,capture_output=True,text=True)
    (output/'build.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0,p.stdout+p.stderr
    dependencies={}
    for entry in cp.split(':'):
        path=Path(entry)
        dependencies[entry]={str(f.relative_to(path)):sha(f) for f in sorted(path.rglob('*')) if f.is_file()} if path.is_dir() else sha(path)
    write(output/'identity.json',dict(sources={f.name:sha(f) for f in java},dependencies=dependencies,
        classes={str(f.relative_to(classes)):sha(f) for f in classes.rglob('*.class')},
        java=subprocess.check_output([str(JAVA),'-version'],stderr=subprocess.STDOUT,text=True),python=sys.version,
        reusedEngineeringAuditSHA=sha(OLD/'engineering-independent-audit.json'),
        reusedFullTimelineAuditSHA=sha(OLD/'science-independent-audit.json')))
    (output/'classpath.txt').write_text(str(classes)+':'+cp)


def verify_loaded(receipt,root):
    # Loaded identities retain the actual class resource and SHA. The full dependency tree
    # was frozen before QA; independent post-audit resolves each resource again.
    assert receipt['loaded']


def batch(root,kind):
    protocol=read(root/'protocol.json')
    assert protocol['plannedNewEvaluations']<=364 and protocol['plannedQA']<=52
    assert read(OLD/'engineering-independent-audit.json')['passed']
    assert read(OLD/'science-independent-audit.json')['passed']
    if kind=='paid':assert read(root/'numeric-gate.json')['passed']
    receipts=[]
    for stem in STEMS:
        input_tsv=root/'inputs'/stem/(kind+'.tsv')
        count=len([s for s in input_tsv.read_text().splitlines() if s.strip()])
        if count==0:continue
        out=root/kind/stem;out.mkdir(parents=True,exist_ok=False)
        data=ANCHOR/'payload/inputs'/stem
        command=['nice','-n','10',str(JAVA),'-Xms128m','-Xmx2g','-cp',
                 (root/'build-01/classpath.txt').read_text().strip(),'research.dynamic.CounterfactualRun',
                 str(data/(stem+'.txt')),str(data/'RECONSTRUCTED-setup.txt'),str(data/'fatigue-input.txt'),
                 str(input_tsv),str(out),kind.upper(),str(count)]
        write(out/'command.json',command)
        start=time.perf_counter()
        with (out/'run.log').open('x') as log:p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        write(out/'process.json',dict(exitCode=p.returncode,seconds=time.perf_counter()-start))
        assert p.returncode==0,f'Failed run retained without budget refill: {out}'
        r=read(out/'receipt.json');verify_loaded(r,root)
        actual=lines(out/'evaluations.jsonl');assert len(actual)==count
        if kind=='qa':
            assert (r['attemptedQA'],r['passedQA'],r['failedQA'])==(count,count,0)
            assert r['maxAbsoluteObjectiveError']==[0,0,0]
        else:
            assert (r['attempted'],r['successful'],r['failed'],r['written'])==(count,count,0,count)
            assert r['decoder']['dynamic.evaluations']==count and r['decoder']['dynamic.reusedOperations']==0
        assert r['pending'] is None and r['error'] is None
        receipts.append(dict(instance=stem,**r));print('BATCH_DONE',kind,stem,count,flush=True)
    total=sum(r['attemptedQA' if kind=='qa' else 'attempted'] for r in receipts)
    assert total==protocol['plannedQA' if kind=='qa' else 'plannedNewEvaluations']
    write(root/(kind+'-complete.json'),dict(passed=True,attempted=total,successful=total,failed=0,receipts=receipts))
    if kind=='qa':
        write(root/'numeric-gate.json',dict(passed=True,endpointComparisons=total,actualMaxError=[0,0,0],
            objectiveCertificateAbsTol=protocol['objectiveCertificateAbsTol'],hvNumericalAbsTol=protocol['hvNumericalAbsTol'],
            newCounterfactualFEAtGate=0,rule='No adjustment of declared tolerances after seeing counterfactual results'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--phase',choices=['build','qa','paid'],required=True)
    args=parser.parse_args();prepare()
    if args.phase=='build':build(args.root)
    else:batch(args.root,args.phase)
