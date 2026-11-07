"""Existing candidate evidence only: no synthesis, decoding or new search."""
import argparse
from collections import Counter
from pathlib import Path
import time
import numpy as np
from common import RUN, SOURCE, MATURE, STEMS, SEEDS, ARMS, FACTORY, prepare, read, write, rows
from features import weakly_covered, summarize_features
from gain_trace import account, escape_depth, frozen_complement


def entry_report(before, background, scale):
    out = []
    for p in before:
        equal = any(np.array_equal(a,p['objectives']) for a in background)
        strict = sum(all(a <= p['objectives']) and any(a < p['objectives']) for a in background)
        certificates = [weakly_covered(background,frozen_complement(p,f))
                        for f in range(len(p['factoryMakespan']))]
        out.append(dict(slot=p['slot'],role=p['role'],objectives=p['objectives'],
                        equalA0Point=equal,strictDominators=int(strict),
                        normalizedUniformEscapeDepth=escape_depth(p['objectives'],background,scale.width),
                        zeroLocalCostImpossibility=certificates))
    return out


def local_potential(folder, background):
    before = read(folder/'before.json')
    live = {r['slot']:r for r in before}
    counts = Counter()
    for p, s in zip(rows(folder/'paid.jsonl'),rows(folder/'steps.jsonl')):
        parent = live[s['slot']]
        changed = [f for f in range(len(parent['factoryMakespan'])) if
                   any(p[k][f] != parent[k][f] for k in FACTORY)]
        novel = not weakly_covered(background,p['objectives'])
        for f in changed:
            delta = [p[k][f]-parent[k][f] for k in FACTORY]
            local_dom = all(v<=0 for v in delta) and any(v<0 for v in delta)
            counts['localChanged'] += 1
            counts['localParetoImproved'] += local_dom
            counts['localParetoImprovedButCoveredA0'] += local_dom and not novel
            counts['zeroLocalCostCertifiedBlocked'] += weakly_covered(background,frozen_complement(parent,f))
        if s['accepted']:
            live[s['slot']] = p
    return dict(counts)


def main(root):
    prepare()
    from analysis_metrics import frozen_scale
    output = root/'details'
    output.mkdir()
    specs = {s['stem']:s for s in read(MATURE/'protocol.json')['instances']}
    start=time.perf_counter()
    summary=[]
    for stem in STEMS:
        scale=frozen_scale(specs[stem])
        for seed in SEEDS:
            a0=np.asarray(read(SOURCE/'inputs-v2'/stem/str(seed)/'0/background.json'))
            for arm in ARMS:
                folder=RUN/'science'/stem/str(seed)/arm
                name=f'{stem}-{seed}-{arm}'
                features=list(rows(root/'survey'/(name+'-features.jsonl')))
                witnesses=read(root/'survey'/(name+'-witnesses.json'))
                accounting=account(folder,features,witnesses,a0,scale)
                entry=entry_report(read(folder/'before.json'),a0,scale)
                local=local_potential(folder,a0)
                write(output/(name+'.json'),dict(accounting=accounting,entry=entry,local=local))
                summary.append(dict(instance=stem,seed=seed,arm=arm,entry=entry,local=local,
                    totalHVPctA0=accounting['totalHVPctA0'],groups=accounting['groupAccounting'],
                    freshEvents=len(accounting['gains']),
                    positiveUniqueVectors=len({tuple(w['candidate']['objectives']) for w in witnesses}),
                    coveredParentBreakthroughs=sum(w['record']['fresh'] and w['record']['parentCoveredByA0'] for w in witnesses)))
                print('DETAIL',name,local,accounting['totalHVPctA0'],flush=True)
    write(output/'summary.json',dict(cases=summary,seconds=time.perf_counter()-start,
          newSearchFE=0,newDecodes=0,scope='Retrospective; chronological marginal gain is direct attribution, not causal contribution'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
