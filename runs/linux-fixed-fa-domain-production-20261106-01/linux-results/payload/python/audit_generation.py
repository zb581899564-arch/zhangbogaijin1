"""Independent complete legal catalog, RNG, coupled proposal and fixed-support checks."""
from common import ANCHOR,read
from structure import support,physical,membership


def domain_check(domain,before,stem,seed):
    source=(ANCHOR/'payload/inputs'/stem/(stem+'.txt')).read_text().splitlines()
    factories,stages,jobs=map(int,source[0].split())
    assert (jobs,stages,factories)==tuple(map(int,stem.split('_')[:3]))
    assert source[1].strip()=='number of machines at each stage in each factory:'
    catalog={};legal=[]
    for f in range(factories):
        m=list(map(int,source[2+f].split(',')))[0];w=m if m<=2 else m-1
        ids=[]
        for machine in range(m):
            for worker in range(w):
                i=len(catalog);catalog[i]=(f,machine,worker);ids.append(i)
        legal.append(ids)
    assert domain['catalog']==[dict(id=i,factory=f,machine=m,worker=w) for i,(f,m,w) in catalog.items()]
    fixed,options=support(before);jobsets=[sorted(j for j,factory in fixed.items() if factory==f) for f in range(factories)]
    alleles=[sorted({p['resources'][j] for p in before}) for j in range(jobs)]
    complements=[[v for v in legal[fixed[j]] if v not in alleles[j]] for j in range(jobs)]
    assert domain['initialSupport']==[dict(job=j,factory=fixed[j],support=alleles[j],complement=complements[j]) for j in range(jobs)]
    eligible=[f for f,values in enumerate(jobsets) if len(values)>=2]
    assert domain['eligibleFactories']==eligible and domain['rngSeed']==seed^0x4f2a91
    assert domain['factories']==[dict(factory=f,jobs=jobsets[f],legalResourceIds=legal[f],eligible=f in eligible) for f in range(factories)]
    return dict(catalog=catalog,legal=legal,jobs=jobsets,complement=complements,eligible=eligible,options=options)


def double(rng):return (rng.next_bits(26)*(1<<27)+rng.next_bits(27))/float(1<<53)


def joint(parent,arm,rng,domain):
    assert domain['eligible'],'The preregistered actual sources must have eligible factories'
    f=domain['eligible'][rng.next_int(len(domain['eligible']))];jobs=domain['jobs'][f]
    first=rng.next_int(len(jobs));second=rng.next_int(len(jobs)-1)
    if second>=first:second+=1
    a,b=jobs[first],jobs[second];rank1,rank2,key1,key2=[double(rng) for _ in range(4)]
    missing=arm=='NOVEL' and not domain['complement'][a]
    candidates=domain['complement'][a] if arm=='NOVEL' and not missing else domain['legal'][f]
    r1=candidates[int(rank1*len(candidates))];r2=domain['legal'][f][int(rank2*len(domain['legal'][f]))]
    resources=list(parent['resources']);keys=list(parent['keys'])
    noop=resources[a]==r1 and resources[b]==r2 and keys[a]==key1 and keys[b]==key2
    resources[a]=r1;resources[b]=r2;keys[a]=key1;keys[b]=key2
    meta=dict(generator=arm,factory=f,jobs=[a,b],rank1=rank1,rank2=rank2,key1=key1,key2=key2,
        resource1=r1,resource2=r2,firstDomainSize=len(candidates),secondDomainSize=len(domain['legal'][f]),
        complementSize=len(domain['complement'][a]),noveltyUnavailable=bool(missing),noEligibleFactory=False,noOp=noop,randomDraws=7)
    return resources,keys,meta


def outside(row,domain):
    statuses=[membership(physical(row,f),domain['options'])[0] for f in range(len(domain['jobs']))]
    return 'OUTSIDE_RESOURCE' if 'OUTSIDE_RESOURCE' in statuses else ('OUTSIDE_KEY_ORDER' if 'OUTSIDE_KEY_ORDER' in statuses else 'INSIDE')
