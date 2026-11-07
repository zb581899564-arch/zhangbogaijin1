"""Sequential reuse of the frozen full evaluator, retaining failures without refill."""
import argparse
from common import *


def identity(root):
    out=root/'build';out.mkdir()
    cp=(SUPPORT/'build/classpath.txt').read_text().strip();(out/'classpath.txt').write_text(cp)
    source_paths=[SUPPORT/'build/identity.json',HISTORY/'independent-audit.json',HISTORY/'model-probe/summary.json',
                  SUPPORT/'prepared/entries.json',SUPPORT/'sources/models.json',HISTORY/'model-probe/raw.json',
                  SUPPORT/'source/java/CounterfactualRun.java',SUPPORT/'source/java/SupportFixture.java']
    write(out/'identity.json',dict(classpath=cp,priorDependencyManifest=str(SUPPORT/'build/identity.json'),
         sources={str(p):sha(p) for p in source_paths},inputs={p:sha(p) for p in input_args()},
         code={str(p.relative_to(root)):sha(p) for p in (root/'code').glob('*.py')},
         java=subprocess.check_output([str(JAVA),'-version'],stderr=subprocess.STDOUT,text=True),python=sys.version,
         protocolSHA256=sha(root/'protocol.md'),newCompilation=False))


def batch(root,kind):
    assert read(root/'opportunity-gate.json')['passed'] and read(root/'prepared-audit.json')['passed']
    if kind=='paid':assert read(root/'qa-complete.json')['passed']
    receipts=[]
    for source in sorted((root/'prepared'/kind).glob('*.tsv')):
        count=len(source.read_text().splitlines());out=root/kind/source.stem
        execute(java(root,'research.dynamic.CounterfactualRun')+input_args()+
                [str(source),str(out),kind.upper(),str(count)],out)
        r=read(out/'receipt.json');assert r['error'] is None and r['pending'] is None
        assert sum(1 for _ in stream(out/'evaluations.jsonl'))==count
        if kind=='qa':
            assert (r['attemptedQA'],r['passedQA'],r['failedQA'])==(count,count,0)
            assert r['maxAbsoluteObjectiveError']==[0,0,0] and r['exactBits']
        else:
            assert (r['attempted'],r['successful'],r['failed'],r['written'])==(count,count,0,count)
            assert r['decoder']['dynamic.evaluations']==count and r['decoder']['dynamic.reusedOperations']==0
        receipts.append(dict(batch=source.stem,**r));print('BATCH_DONE',kind,source.stem,count,flush=True)
    total=sum(r['attemptedQA' if kind=='qa' else 'attempted'] for r in receipts)
    assert total==(24 if kind=='qa' else 1152)
    write(root/(kind+'-complete.json'),dict(passed=True,attempted=total,successful=total,failed=0,receipts=receipts))


def main(root):
    if not read(root/'opportunity-gate.json')['passed']:
        write(root/'final-state.json',dict(completed=True,decision='INSUFFICIENT_OPPORTUNITY',actualFE=0,actualQA=0))
        print('STOPPED_WITHOUT_EVALUATION',flush=True);return
    assert read(root/'prepared-audit.json')['passed'];identity(root)
    execute(java(root,'research.dynamic.SupportFixture')+input_args()[:2]+
            [str(root/'prepared/native-fixture.tsv')],root/'native-fixture')
    assert 'SUPPORT_FIXTURE_PASSED 1152 evaluations=0' in (root/'native-fixture/run.log').read_text()
    write(root/'native-gate.json',dict(passed=True,proposals=1152,newFE=0,newQA=0))
    batch(root,'qa');batch(root,'paid')
    write(root/'accounting.json',dict(passed=True,actualAttemptedFE=1152,successfulFE=1152,failedFE=0,
          actualQA=24,passedQA=24,failedQA=0,sourceRerunFE=0,candidateAndQAFullDecoder=True,
          sameTimeClaim=False,searchStateUpdated=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)
