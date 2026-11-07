"""Zero-query opportunity audit of global intermediate results in the GOM accept archive."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import time
import numpy as np
import moocore

BASE=Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
GAP=BASE/'runs/linux-trajectory-gap-20261107-01/capture/SHARE_CTX_GOM'
PIPE=BASE/'runs/linux-mid-support-20261107-01/historical-share/pipeline.jsonl'


def lines(path):
    with path.open() as f:
        for line in f:
            if line.strip():yield json.loads(line)


def offer(archive,point):
    if np.any(np.all(archive<=point,axis=1)):return archive
    return np.vstack((archive[~np.all(point<=archive,axis=1)],point))


def main(root):
    assert sys.platform=='linux';root.mkdir(exist_ok=False);start=time.monotonic()
    groups={n:{} for n in range(5,11)}
    for r in lines(PIPE):
        if r.get('cycle') in groups and r['kind']=='population' and r['phase'] in ('PRE_GLOBAL','POST_GLOBAL','POST_LOCAL'):
            groups[r['cycle']][r['phase']]=r
    pre={g['PRE_GLOBAL']['fe']:n for n,g in groups.items()};post={g['POST_GLOBAL']['fe']:n for n,g in groups.items()}
    endings={g['POST_LOCAL']['fe']:n for n,g in groups.items()}
    accepts={r['fe']:r['keep'] for r in lines(GAP/'trajectory-events.jsonl') if r['kind']=='accept'}
    full=np.empty((0,3));baselines={};working={};parents={};records=[];counts={n:dict(cycle=n,centerFE=0,centerRejected=0,
       freeCenterFE=0,freeCenterRejected=0,shadowOnly=0,freeShadowOnly=0,firstFlipFE=None) for n in groups}
    for row in csv.DictReader((GAP/'trajectory-paid.csv').open()):
        fe=int(row['fe']);point=np.array([float(row[k]) for k in ('Cmax','TEC','TWC')]);cycle=int(row['cycle'])
        if fe>248700:break
        if cycle in groups and row['phase']=='GOM_LOCAL':
            alt=working[cycle]
            if row['role']=='CENTER':
                parent=parents[row['parent']];weak=bool(np.all(point<=parent))
                # duplicate is a raw-genome hash flag, not objective equality.
                strict_old=bool(np.any(np.all(full<=point,axis=1)&np.any(full<point,axis=1)))
                expected=weak or not strict_old;assert expected==accepts[fe]
                strict_new=bool(np.any(np.all(alt<=point,axis=1)&np.any(alt<point,axis=1)))
                changed=(weak or not strict_new)!=expected
                c=counts[cycle];c['centerFE']+=1;c['centerRejected']+=not expected
                free=int(row['family'])==-1;c['freeCenterFE']+=free;c['freeCenterRejected']+=free and not expected
                if changed:
                    assert not expected and not weak
                    c['shadowOnly']+=1;c['freeShadowOnly']+=free
                    if c['firstFlipFE'] is None:c['firstFlipFE']=fe
                    records.append(dict(fe=fe,cycle=cycle,slot=int(row['slot']),family=int(row['family']),
                                        objectives=point.tolist(),parent=parent.tolist()))
            working[cycle]=offer(alt,point)
        parents[row['key']]=point
        if row['admitted']=='1':full=offer(full,point)
        if fe in pre:baselines[pre[fe]]=full.copy()
        if fe in post:
            n=post[fe];values=np.vstack((baselines[n],[p['objectives'] for p in groups[n]['POST_GLOBAL']['points']]))
            working[n]=np.unique(values,axis=0);working[n]=working[n][moocore.is_nondominated(working[n])]
            counts[n].update(preArchiveSize=len(baselines[n]),fullPostArchiveSize=len(full),filteredPostArchiveSize=len(working[n]))
    assert all(c['centerFE']>10000 for c in counts.values())
    result=dict(completed=True,contexts=list(counts.values()),totalShadowOnly=sum(c['shadowOnly'] for c in counts.values()),
       totalFreeShadowOnly=sum(c['freeShadowOnly'] for c in counts.values()),newFE=0,newDecoderCalls=0,newCandidates=0,
       caveat='Fixed observed proposal sequence only. After the first flip this is not an executable alternative trajectory.',
       inputHashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (PIPE,GAP/'trajectory-paid.csv',GAP/'trajectory-events.jsonl')},
       seconds=time.monotonic()-start)
    (root/'result.json').write_text(json.dumps(result,indent=2));(root/'opportunities.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(result),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
