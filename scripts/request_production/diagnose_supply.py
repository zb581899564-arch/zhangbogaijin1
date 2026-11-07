"""Count paid physical repetition and useful supply without producing new candidates."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import time
from common import linux, read, write


def physical(point):
    groups=defaultdict(list)
    for j,f,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA']):
        groups[f].append((j,m,w))
    return tuple((f,tuple(groups[f])) for f in sorted(groups))


def diagnose(root):
    linux();assert read(root/'science-independent-audit.json')['passed']
    started=time.perf_counter();rows=[]
    for path in sorted(root.glob('science/*/*/*/*/receipt.json')):
        folder=path.parent;stem,seed,q,arm=folder.relative_to(root/'science').parts
        before=read(folder/'before.json');live={p['slot']:physical(p) for p in before}
        seen=set(live.values());unique=set();noop=0;fresh=0;steps=0
        with (folder/'steps.jsonl').open() as stream:
            for line in stream:
                p=json.loads(line);key=physical(p);steps+=1
                noop+=key==live[p['slot']];unique.add(key);fresh+=p['fresh']
                if p['accepted']:live[p['slot']]=key
        assert steps==511
        rows.append(dict(instance=stem,seed=int(seed),requestIndex=int(q),arm=arm,productionFE=steps,
            samePhysicalAsParent=noop,uniquePaidProduction=len(unique),
            uniqueBeyondInitialFive=len(unique-seen),freshReportingArchiveAdmissions=fresh))
    grouped=[]
    for stem in sorted({r['instance'] for r in rows}):
        for arm in ('ROLE','REQUEST','ORDINARY','SHUFFLED'):
            subset=[r for r in rows if r['instance']==stem and r['arm']==arm]
            grouped.append(dict(instance=stem,arm=arm,requests=len(subset),
                **{k:sum(r[k] for r in subset) for k in ('productionFE','samePhysicalAsParent','uniquePaidProduction','uniqueBeyondInitialFive','freshReportingArchiveAdmissions')}))
    write(root/'report/production-diagnostics.json',dict(rows=rows,summary=grouped,
        uniqueCountScope='Unique within request then summed, not global unique schedules across correlated requests',
        archiveAdmissionScope='Direct chronological production admissions; not causal contribution or retained final gain',
        newSearchFE=0,newDecodes=0,seconds=time.perf_counter()-started))
    print(json.dumps(grouped),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    diagnose(p.parse_args().root)
