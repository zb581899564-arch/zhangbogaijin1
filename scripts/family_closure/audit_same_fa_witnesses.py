"""Post-diagnostic, zero-FE audit of all previously paid same-FA checkpoint witnesses."""
import argparse
from pathlib import Path
from common import SOURCE,linux,read,write,lines,sha
from structure import support,physical,membership


def dominates(a,b):return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))


def main(root):
    linux();boundary=read(root/'domain-boundary-audit.json');results=[]
    for context in boundary['results']:
        stem,seed=context['instance'],context['seed'];before=root/'contexts'/stem/str(seed)/'before.json'
        points=read(before);fixed,options=support(points);factories=sorted(set(fixed.values()))
        source=SOURCE/'sources'/stem/str(seed)/'checkpoint-solutions.jsonl';witnesses=[]
        for p in lines(source):
            if p['checkpointKind']!='FE' or p['checkpointFE']!=context['paidReferenceCheckpoint']:continue
            if dict(zip(p['JS'],p['FA']))!=fixed:continue
            assert p['bornFE']<=p['checkpointFE']<=context['sourceBeforeFE']
            status={str(f):membership(physical(p,f),options)[0] for f in factories}
            witnesses.append(dict(objectives=p['objectives'],bornFE=p['bornFE'],factoryMembership=status,
                allFactoriesInside=all(v=='INSIDE' for v in status.values()),
                matureDonorsStrictlyDominated=sum(dominates(p['objectives'],x['objectives']) for x in points),
                strictlyDominatedByMatureDonor=any(dominates(x['objectives'],p['objectives']) for x in points)))
        assert len(witnesses)==context['sameFamilyFAReferencePoints']
        results.append(dict(instance=stem,seed=seed,sourceSHA256=sha(source),beforeSHA256=sha(before),
            count=len(witnesses),inside=sum(w['allFactoriesInside'] for w in witnesses),
            witnessesDominatingAnyMature=sum(w['matureDonorsStrictlyDominated']>0 for w in witnesses),witnesses=witnesses))
    write(root/'same-fa-witnesses.json',dict(passed=True,newFE=0,newDecodes=0,results=results,
        stage='Exploratory follow-up to the domain-boundary audit, not a preregistered performance endpoint',
        selection='All same-FA points at the latest already-paid FE checkpoint preceding each of six source states',
        limitation='Existing archive points are not new archive improvements; membership evidence cannot establish a useful history donor mechanism'))
    print('SAME_FA_WITNESSES',[(r['instance'],r['seed'],r['count'],r['inside'],r['witnessesDominatingAnyMature']) for r in results])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
