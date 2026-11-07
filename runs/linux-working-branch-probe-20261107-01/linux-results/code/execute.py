"""Compile in isolation, run unscored fixtures, then the one authorized QA/science batch."""
import argparse
from common import *


def build(root):
    out=root/'build';out.mkdir();classes=out/'classes';classes.mkdir()
    cp=(SUPPORT/'build/classpath.txt').read_text().strip();sources=sorted((root/'source').glob('*.java'))
    execute([str(BASE/'runtime/jdk17/bin/javac'),'-encoding','UTF-8','--release','8','-implicit:none',
             '-cp',cp,'-d',str(classes),*map(str,sources)],out/'compile')
    (out/'classpath.txt').write_text(str(classes)+':'+cp)
    write(out/'identity.json',dict(sources={p.name:sha(p) for p in sources},
        classes={str(p.relative_to(classes)):sha(p) for p in classes.rglob('*.class')},
        frozenDependencyIdentity=str(SUPPORT/'build/identity.json'),frozenDependencyIdentitySHA256=sha(SUPPORT/'build/identity.json'),
        python=sys.version,java=subprocess.check_output([str(JAVA),'-version'],stderr=subprocess.STDOUT,text=True),
        inputHashes={p:sha(p) for p in input_args()},protocolSHA256=sha(root/'protocol.md')))


def fixtures(root):
    execute(java(root,'research.dynamic.WorkingBranchFixture')+input_args()[:2]+[str(root/'prepared')],root/'logic-fixture')
    assert 'WORKING_BRANCH_FIXTURE_PASSED seeds=36 evaluations=0 decoderCalls=0' in (root/'logic-fixture/run.log').read_text()
    execute(java(root,'research.dynamic.SupportFixture')+input_args()[:2]+[str(root/'prepared/native-fixture.tsv')],root/'mix-fixture')
    assert 'SUPPORT_FIXTURE_PASSED 1656 evaluations=0' in (root/'mix-fixture/run.log').read_text()
    write(root/'engineering-gate.json',dict(passed=True,acceptanceAndPrivateArchiveFixtures=True,mixingFixtures=1656,newFE=0,newQA=0))


def qa(root):
    assert read(root/'engineering-gate.json')['passed'];out=root/'qa'
    execute(java(root,'research.dynamic.CounterfactualRun')+input_args()+[str(root/'prepared/seeds.tsv'),str(out),'QA','36'],out)
    r=read(out/'receipt.json');assert (r['attemptedQA'],r['passedQA'],r['failedQA'])==(36,36,0)
    assert r['maxAbsoluteObjectiveError']==[0,0,0] and r['pending'] is None and r['error'] is None
    write(root/'qa-complete.json',dict(passed=True,actualQA=36,failedQA=0))


def science(root):
    assert read(root/'qa-complete.json')['passed'];out=root/'science'
    execute(java(root,'research.dynamic.WorkingBranchRun')+input_args()+[str(root/'prepared'),str(out)],out)
    r=read(out/'receipt.json')
    assert (r['attempted'],r['successful'],r['failed'],r['written'],r['programs'])==(1536,1536,0,1536,84)
    assert r['pending'] is None and r['error'] is None
    assert r['decoder']['dynamic.evaluations']==1536 and r['decoder']['dynamic.reusedOperations']==0
    write(root/'accounting.json',dict(passed=True,attempted=1536,successful=1536,failed=0,QA=36,failedQA=0,
          paidInitialSeeds=84,successorMixes=1452,privatePrograms=84,sourceRerunFE=0,allFullDecoder=True,sameTimeClaim=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('phase',choices=['build','fixtures','qa','science'])
    args=p.parse_args();linux();globals()[args.phase](args.root)
