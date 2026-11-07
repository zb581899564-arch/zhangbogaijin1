"""Zero-decode boundary audit; distinguishes frozen FA and lost resource support."""
import argparse
from collections import Counter
from pathlib import Path
from common import BASE,SOURCE,SEEDS,STEMS,linux,read,write,lines
from structure import physical


def by_job(point):return {j:(f,m,w) for j,f,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA'])}


def one(root,stem,seed):
    folder=root/'contexts'/stem/str(seed);points=read(folder/'before.json');family=points[0]['family']
    originals=list(lines(SOURCE/'sources'/stem/str(seed)/'initial-population.jsonl'))
    assert len(originals)==100
    initial=originals[5*family:5*family+5];fixed={j:f for j,(f,m,w) in by_job(points[0]).items()}
    for p in [*initial,*points]:assert {j:f for j,(f,m,w) in by_job(p).items()}==fixed
    def alleles(population):
        mapped=list(map(by_job,population))
        return {j:{g[j][1:] for g in mapped} for j in fixed}
    a,b=alleles(initial),alleles(points)
    rows=[dict(job=j,initialResourceCount=len(a[j]),matureResourceCount=len(b[j]),
        initialAllelesLost=len(a[j]-b[j]),newAllelesPresent=len(b[j]-a[j])) for j in sorted(fixed)]
    cutoff=min(p['sourcePaidByFE'] for p in points)
    checkpoints=[p for p in lines(SOURCE/'sources'/stem/str(seed)/'checkpoint-solutions.jsonl')
                 if p['checkpointKind']=='FE' and p['checkpointFE']<=cutoff]
    last=max(p['checkpointFE'] for p in checkpoints);front=[p for p in checkpoints if p['checkpointFE']==last]
    distances=[]
    for p in front:
        fa={j:f for j,(f,m,w) in by_job(p).items()}
        distances.append(sum(fa[j]!=fixed[j] for j in fixed))
    return dict(instance=stem,seed=seed,family=family,unchangedInitialFA=True,sourceBeforeFE=cutoff,
        initialSingleResourceJobs=sum(len(x)==1 for x in a.values()),matureSingleResourceJobs=sum(len(x)==1 for x in b.values()),
        initialAllelesLost=sum(r['initialAllelesLost'] for r in rows),newAllelesPresent=sum(r['newAllelesPresent'] for r in rows),jobs=rows,
        paidReferenceCheckpoint=last,referencePoints=len(front),sameFamilyFAReferencePoints=sum(d==0 for d in distances),
        nearestReferenceFAJobChanges=min(distances),
        limitation='A different FA in known good solutions does not prove changing FA is necessary. Initial allele loss does not prove lost alleles were useful.')


def main(root):
    linux();rows=[one(root,s,seed) for s in STEMS for seed in SEEDS]
    write(root/'domain-boundary-audit.json',dict(passed=True,newSearchFE=0,newDecodes=0,results=rows,
        diagnosis='Current five-state support is conditional on unchanged initial FA, surviving resource alleles and inherited keys. Closure failure cannot separate these causes.',
        nextQuestion='Do new resource or order structures under the SAME FA have measurable potential, before considering any family renewal?',
        exclusion='No automatic revival of past ContextRenewal ELITE/RANDOM, family release, archive restart or typed-allele unbinding.'))
    print('DOMAIN_BOUNDARY_PASS',[(r['instance'],r['seed'],r['initialSingleResourceJobs'],r['matureSingleResourceJobs'],r['sameFamilyFAReferencePoints']) for r in rows])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
