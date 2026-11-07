"""Zero-query algebra: replace only FA statistics, retaining native post-QGS order terms."""
import argparse
import math
import subprocess
import time
from collections import Counter
import numpy as np
from common import *


def entropy(values):
    counts=Counter(values);n=len(values)
    return -sum((c/n)*math.log(c/n) for c in counts.values())


def independent_hybrid(pre, post, keys, factories):
    n,jobs=pre.shape;cutoff=n//factories;p=1/factories
    masses=[math.comb(n,k)*p**k*(1-p)**(n-k) for k in range(n+1)]
    lower=[math.fsum(masses[:k+1]) for k in range(n+1)]
    upper=[math.fsum(masses[k+1:]) for k in range(n+1)]
    marginal=[entropy(pre[:,j]) for j in range(jobs)]
    matrix=np.zeros((jobs,jobs))
    for a in range(jobs):
        for b in range(a+1,jobs):
            count=int(np.count_nonzero(pre[:,a]==pre[:,b]));attracts=count*factories>n
            statistic=1-(upper[count]/upper[cutoff] if attracts else lower[count]/lower[cutoff])
            if attracts:
                same=post[:,a]==post[:,b];size=int(same.sum());internal=0.
                if size:
                    probability=float(np.mean(keys[same,a]<keys[same,b]))
                    order=1 if probability in (0,1) else 1+probability*math.log2(probability)+(1-probability)*math.log2(1-probability)
                    internal=order*(1-float(np.mean((keys[same,a]-keys[same,b])**2)))
                value=statistic*(2/3+(1/3)*internal)
            else:
                external=(marginal[a]+marginal[b]-entropy(list(zip(pre[:,a],pre[:,b]))))/math.log(factories)
                value=statistic*(2/3+(1/3)*external)
            matrix[a,b]=matrix[b,a]=value
    return matrix


def main(root):
    assert read(root/'analysis-v2/acceptance.json')['passed']
    catalog=read(SUPPORT/'sources/models.json')['catalog'];factories=max(t[0] for t in catalog)+1
    pre,post,views={},{},{}
    for r in stream(SHARE):
        if not 5<=r.get('cycle',0)<=10:continue
        if r['kind']=='population' and r['phase']=='PRE_GLOBAL':pre[r['cycle']]=r
        if r['kind']=='population' and r['phase']=='POST_GLOBAL':post[r['cycle']]=r
        if r['kind']=='workspace':views[r['cycle']]=r
    entries={};tsv=[]
    for cycle in range(5,11):
        before=[p for p in pre[cycle]['points'] if p['family']==-1]
        after=[s for s in views[cycle]['states'] if s['family']==-1]
        assert len(before)==len(after)==80
        fa_before=[]
        for p in before:
            fa=[None]*100
            for j,f in zip(p['JS'],p['FA']):fa[j]=f
            fa_before.append(fa)
        fa_after=[[catalog[r][0] for r in p['resources']] for p in after]
        keys=[p['keys'] for p in after]
        entries[str(cycle)]=(np.asarray(fa_before),np.asarray(fa_after),np.asarray(keys))
        for a,b,k in zip(fa_before,fa_after,keys):
            tsv.append('\t'.join([str(cycle),','.join(map(str,a)),','.join(map(str,b)),','.join(map(str,k))]))
    out=root/'model-probe';out.mkdir();(out/'inputs.tsv').write_text('\n'.join(tsv)+'\n')
    cp=(SUPPORT/'build/classpath.txt').read_text().strip();classes=out/'classes';classes.mkdir()
    source=root/'code/HistoryLinkage.java';javac=BASE/'runtime/jdk17/bin/javac';java=BASE/'runtime/jdk17/bin/java'
    compile_command=[str(javac),'-encoding','UTF-8','--release','8','-implicit:none','-cp',cp,'-d',str(classes),str(source)]
    run_command=['nice','-n','10',str(java),'-cp',str(classes)+':'+cp,'research.dynamic.HistoryLinkage',
                 str(out/'inputs.tsv'),str(out/'raw.json'),str(factories)]
    write(out/'commands.json',dict(compile=compile_command,run=run_command))
    for label,command in [('compile',compile_command),('model',run_command)]:
        result=subprocess.run(command,capture_output=True,text=True);(out/(label+'.log')).write_text(result.stdout+result.stderr)
        assert result.returncode==0,result.stderr
    sys.path.insert(0,str(SUPPORT/'source/audit'))
    from audit_models import expected_matrix,hierarchy
    reference={m['context']:m for m in read(SUPPORT/'sources/models.json')['models']}
    summary=[]
    for r in read(out/'raw.json')['contexts']:
        a,b,k=entries[r['context']];native=np.asarray(r['nativeMatrix']);hybrid=np.asarray(r['hybridMatrix'])
        native_error=float(np.max(np.abs(native-expected_matrix(b,k,factories))))
        hybrid_error=float(np.max(np.abs(hybrid-independent_hybrid(a,b,k,factories))))
        assert native_error<3e-12 and hybrid_error<3e-12
        hierarchy(native,r['nativeFOS']);hierarchy(hybrid,r['hybridFOS'])
        source_fe=str(post[int(r['context'])]['fe'])
        if source_fe in reference:
            assert r['nativeMatrix']==reference[source_fe]['dependency'] and r['nativeFOS']==reference[source_fe]['subsets']
        native_groups={tuple(v) for v in r['nativeFOS'] if 1<len(v)<100}
        other_groups={tuple(v) for v in r['hybridFOS'] if 1<len(v)<100}
        summary.append(dict(cycle=int(r['context']),postFE=int(source_fe),matrixMeanAbsChange=float(np.abs(native-hybrid).mean()),
             matrixMaxAbsChange=float(np.abs(native-hybrid).max()),nativeNontrivialBlocks=len(native_groups),
             commonNontrivialBlocks=len(native_groups&other_groups),changedBlocks=len(native_groups-other_groups),
             nativeIndependentError=native_error,hybridIndependentError=hybrid_error))
    write(out/'summary.json',dict(passed=True,contexts=summary,newFE=0,newDecoderQA=0,newCandidates=0,
          meaning='algebraic model opportunity only, not value of counterfactual schedules',
          sourceSHA256=sha(source),classSHA256={str(p.relative_to(classes)):sha(p) for p in classes.rglob('*.class')}))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)
