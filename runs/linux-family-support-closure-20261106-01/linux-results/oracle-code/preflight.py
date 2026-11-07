"""Zero-FE source-domain audit preceding any new objective query."""
import argparse
from collections import Counter
import itertools
import math
from pathlib import Path
import time
from common import SOURCE,SEEDS,STEMS,linux,read,write,sha,lines
from structure import support,physical,membership,enumerate_factory,validate_membership


def source_paths(stem,seed):
    base=SOURCE/'science'/stem/str(seed)/'0'
    return base, SOURCE/'inputs-v2'/stem/str(seed)/'0'


def freeze(root):
    assert read(SOURCE/'delivery-acceptance.json')['passed']
    plan=dict(version='FINITE_FAMILY_SUPPORT_CLOSURE-v1',instances=STEMS,seeds=SEEDS,
        source=str(SOURCE),sourceAcceptanceSHA256=sha(SOURCE/'delivery-acceptance.json'),
        sample='All six previously fixed source families, q0 ROLE before state. No quality-based request or family selection',
        hypothesis='Can changing acceptance find useful schedules inside the finite inherited resource-key domain, or is useful structure outside that domain?',
        difference='Not old whole-factory retained-pool product closure; enumerate within-factory job-level resource/key mixtures of the actual five mature donors',
        fixed='Original family assignment, physical model, initial five resource-key pairs per job, no key refresh, no new allele',
        reachableQualification='Static support superset. Ignores acceptance and loss of donor alleles; not a proof that live finite-population dynamics can reach every support member',
        stages=['Zero-FE structural membership and complete20case enumeration','Separately frozen charged decoder oracle only after preflight passes'],
        enumerate='20case each of all15factories; at most250000 latent assignments total and100000 deduplicated physical candidates',
        largeCase='100case membership of already-paid production and actual request pool only; exhaustive closure explicitly unavailable',
        preflightNewFE=0,preflightNewDecodes=0,oracleMaximumFE=100000,
        oracleScoring='Conditional capacity oracle, not same-budget algorithm. All new decoder evaluations charged; algebraic factory products separately counted; no unpaid oracle front injected into a search run',
        continuation='A material static-support oracle witness on at least2/3 20case sources permits proposing a new search hypothesis; does not reinstate any stopped operator or establish 100case value',
        materialWitness='Best single whole-schedule witness HV increase >=0.1% of common A0 at ref1.5, robust direction at1.25/2; common-reference IGD+/IGD and weak C reported without treating archive union monotonicity as independent evidence',
        noCapacity='If complete closure adds no material capacity, stop acceptance-only rescue within this fixed domain; do not generalize to model or all four-group algorithms',
        preserved='Four roles,QGS,original sharing,mainline,all old stops; no Goal or expansion')
    write(root/'protocol.json',plan)


def one(root,stem,seed):
    base,inputs=source_paths(stem,seed)
    points=read(base/'ROLE/before.json');fixed,options=support(points)
    factories=sorted(set(fixed.values()));factor_records=[];enumeration={};latent_total=0
    out=root/'contexts'/stem/str(seed);out.mkdir(parents=True,exist_ok=False)
    write(out/'before.json',points)
    for f in factories:
        jobs=sorted(j for j,ff in fixed.items() if ff==f)
        latent=math.prod(len(options[j]) for j in jobs)
        physical_upper=math.factorial(len(jobs))*math.prod(len({(m,w) for _,m,w in options[j]}) for j in jobs)
        entry=dict(factory=f,jobs=jobs,latentAssignments=latent,resourceOnlyPhysicalUpperBound=physical_upper,
                   resourceAllelesPerJob={str(j):len({(m,w) for _,m,w in options[j]}) for j in jobs})
        if stem.startswith('20_'):
            states,count=enumerate_factory(jobs,options);latent_total+=count;enumeration[f]=states
            entry['uniquePhysicalStates']=len(states)
            for chain in states:assert membership(chain,options)[0]=='INSIDE'
            with (out/f'factory-{f}.jsonl').open('x') as stream:
                import json
                for i,(chain,choices) in enumerate(states.items()):
                    value=dict(id=i,factory=f,jobs=[v[0] for v in chain],machines=[v[1] for v in chain],
                               workers=[v[2] for v in chain],sourceChoiceBySortedJob=list(choices),sortedJobs=jobs)
                    stream.write(json.dumps(value,separators=(',',':'))+'\n')
        factor_records.append(entry)
    original_pairs=[{(p['resources'][j],p['keys'][j]) for p in points} for j in range(len(fixed))]
    paid_count=0
    for arm in ('ROLE','REQUEST','ORDINARY','SHUFFLED'):
        assert read(base/arm/'before.json')==points
        for row in lines(base/arm/'steps.jsonl'):
            assert all((row['resources'][j],row['keys'][j]) in original_pairs[j] for j in range(len(fixed)))
            for f in factories:
                chain=physical(row,f);assert membership(chain,options)[0]=='INSIDE'
                if enumeration:assert chain in enumeration[f]
            paid_count+=1
    pool_rows=[]
    for line in (inputs/'pools.tsv').read_text().splitlines():
        a=line.split('\t');f=int(a[0]);objects=list(map(float,a[2].split(',')))
        chain=tuple(zip(*(list(map(int,a[k].split(','))) for k in (3,4,5))))
        status,choices=membership(chain,options)
        parent_local=[(p['factoryMakespan'][f],p['factoryEnergy'][f],p['factoryCost'][f]) for p in points]
        dominates=sum(all(x<=y for x,y in zip(objects,p)) and any(x<y for x,y in zip(objects,p)) for p in parent_local)
        pool_rows.append(dict(factory=f,status=status,objectives=objects,dominatesInitialDonors=dominates,
                              jobs=[v[0] for v in chain],machines=[v[1] for v in chain],workers=[v[2] for v in chain],sourceChoices=choices))
    result=dict(instance=stem,seed=seed,family=points[0]['family'],sourceBeforeSHA256=sha(base/'ROLE/before.json'),
        backgroundSHA256=sha(inputs/'background.json'),factories=factor_records,paidCandidatesChecked=paid_count,
        paidCandidatesInStaticSupport=paid_count,poolMembership=dict(Counter(p['status'] for p in pool_rows)),
        poolRecords=pool_rows,latentEnumerated=latent_total,
        uniqueLocalCandidates=sum(len(s) for s in enumeration.values()),
        exhaustive=bool(enumeration),globalPhysicalProduct=math.prod(len(s) for s in enumeration.values()) if enumeration else None)
    write(out/'structure.json',result);return result


def main(root):
    linux();root.mkdir(parents=True,exist_ok=False);freeze(root);started=time.perf_counter()
    fixtures=validate_membership()
    results=[one(root,s,seed) for s in STEMS for seed in SEEDS]
    latent=sum(r['latentEnumerated'] for r in results);unique=sum(r['uniqueLocalCandidates'] for r in results)
    assert latent<=250000 and unique<=100000
    write(root/'preflight.json',dict(passed=True,contexts=results,latentAssignments=latent,
        uniqueLocalCandidates=unique,membershipFixtureCases=fixtures,
        newSearchFE=0,newDecodes=0,seconds=time.perf_counter()-started))
    print('FINITE_SUPPORT_PREFLIGHT_PASS',latent,unique,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
