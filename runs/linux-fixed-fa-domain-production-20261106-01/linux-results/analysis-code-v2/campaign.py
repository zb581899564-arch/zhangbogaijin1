"""Build and run the frozen domain experiment sequentially; no adaptive performance peeking."""
import argparse
from pathlib import Path
import subprocess
import sys
from common import BASE,SOURCE,MATURE,ANCHOR,STEMS,SEEDS,ARMS,JAVA,PRODUCTION,linux,read,write,sha,lines,execute


def build(root,source):
    out=root/'build-01';out.mkdir();classes=out/'classes';classes.mkdir()
    java=sorted(source.glob('*.java'));assert len(java)>=3
    cp=(SOURCE/'probe-build-01/classpath.txt').read_text().strip()
    cmd=[str(BASE/'runtime/jdk17/bin/javac'),'-encoding','UTF-8','--release','8','-implicit:none','-cp',cp,'-d',str(classes),*map(str,java)]
    write(out/'command.json',cmd);p=subprocess.run(cmd,capture_output=True,text=True)
    (out/'build.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr
    (out/'classpath.txt').write_text(str(classes)+':'+cp)
    dependencies={}
    for entry in cp.split(':'):
        path=Path(entry)
        dependencies[entry]={str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file()} if path.is_dir() else sha(path)
    write(out/'identity.json',dict(sources={p.name:sha(p) for p in java},dependencies=dependencies,
        classes={str(p.relative_to(classes)):sha(p) for p in classes.rglob('*.class')},
        java=subprocess.check_output([str(JAVA),'-version'],text=True,stderr=subprocess.STDOUT),
        python=sys.version,inheritedClasspath=cp))


def run(root,stem,seed,arm,category,label,production,limit,observer=True,fail=None):
    cp=(root/'build-01/classpath.txt').read_text().strip()
    folder=root/category/stem/str(seed)/label;inputs=ANCHOR/'payload/inputs'/stem
    cmd=['nice','-n','10',JAVA,'-Xms128m','-Xmx2g','-Dresearch.pilot.physics=true',
         f'-Dresearch.domain.productionFE={production}',f'-Dresearch.domain.limit={limit}',f'-Dresearch.domain.observer={str(observer).lower()}']
    if fail is not None:cmd.append(f'-Dresearch.pilot.failAt={fail}')
    cmd+=['-cp',cp,'research.dynamic.DomainProductionRun',inputs/(stem+'.txt'),inputs/'RECONSTRUCTED-setup.txt',
          inputs/'fatigue-input.txt',folder,SOURCE/'inputs-v2'/stem/str(seed)/'0',arm,str(seed),'0']
    execute(cmd,folder,1 if fail else 0)
    receipt=read(folder/'receipt.json');attempt=fail if fail else limit;success=attempt-int(bool(fail))
    assert (receipt['attempted'],receipt['successful'],receipt['failed'])==(attempt,success,int(bool(fail)))
    assert receipt['physicsQA']['fullTimelineChecks']==success
    assert (receipt['productionPaid'],receipt['assemblyPaid'])==(min(success,production),int(success>production))
    return folder,receipt


def engineering(root):
    receipts=[]
    for stem in STEMS:
        for seed in SEEDS:
            out,r=run(root,stem,seed,'GOM','engineering','BRIDGE',511,512);receipts.append(r)
            old=SOURCE/'science'/stem/str(seed)/'0/ROLE'
            assert r['paidSHA256']==read(old/'receipt.json')['paidSHA256']
            for name in ('before.json','models.json','after.json','front.json','assembly.json','initial-pools.json','final-pools.json'):
                assert read(out/name)==read(old/name),f'Frozen GOM bridge {name}'
        seed=SEEDS[0]
        for arm in ARMS[1:]:
            out,r=run(root,stem,seed,arm,'engineering',arm,63,64);receipts.append(r)
            if stem!=STEMS[0]:continue
            for cutoff in (1,2,63):
                child,cr=run(root,stem,seed,arm,'engineering',f'{arm}_CUT_{cutoff}',63,cutoff);receipts.append(cr)
                for name in ('paid.jsonl','steps.jsonl'):assert lines(child/name)==lines(out/name)[:cutoff]
                assert not read(child/'assembly.json')['performed']
            quiet,qr=run(root,stem,seed,arm,'engineering',f'{arm}_QUIET',63,64,False);receipts.append(qr)
            assert qr['paidSHA256']==r['paidSHA256']
            for name in ('before.json','models.json','domain.json','after.json','front.json','assembly.json','final-pools.json'):
                assert read(quiet/name)==read(out/name),f'Observer changed {name}'
            assert lines(quiet/'paid.jsonl')==lines(quiet/'steps.jsonl')==[]
    out,r=run(root,STEMS[0],SEEDS[0],'NOVEL','engineering','NOVEL_FAIL_2',63,64,fail=2);receipts.append(r)
    assert 'EXPECTED_PAID_FAILURE' in r['error']
    reference=root/'engineering'/STEMS[0]/str(SEEDS[0])/'NOVEL'
    for name in ('paid.jsonl','steps.jsonl'):assert lines(out/name)==lines(reference/name)[:1]
    assert sum(r['attempted'] for r in receipts)==3590
    write(root/'engineering-complete.json',dict(passed=True,runs=len(receipts),attempted=3590,successful=3589,failed=1))
    print('ENGINEERING_COMPLETE',len(receipts),flush=True)


def science(root):
    assert read(root/'engineering-independent-audit.json')['passed']
    results=[]
    for stem in STEMS:
        for seed in SEEDS:
            for arm in ARMS:
                out,r=run(root,stem,seed,arm,'science',arm,PRODUCTION,PRODUCTION+1)
                old=SOURCE/'science'/stem/str(seed)/'0/ROLE'
                for name in ('before.json','models.json','initial-pools.json'):assert read(out/name)==read(old/name)
                results.append(dict(instance=stem,seed=seed,arm=arm,successful=r['successful']))
                print('DOMAIN_RUN_DONE',stem,seed,arm,r['successful'],flush=True)
    assert sum(r['successful'] for r in results)==73728
    write(root/'science-complete.json',dict(passed=True,runs=results,successful=73728,failed=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source',type=Path);p.add_argument('--phase',choices=['build','engineering','science'],required=True)
    a=p.parse_args();linux()
    if a.phase=='build':build(a.root,a.source)
    elif a.phase=='engineering':engineering(a.root)
    else:science(a.root)
