"""Equal-paid-pool static retention; no alternate search trajectory or free archive injection."""
import numpy as np
from run_long_budget_bridge import read, rows, write_once, execute, hypervolume


def replay_known(root,cp,stem,known):
    fields=('JS','FA','MA','WA');lines=['id\tobjectives\tJS\tFA\tMA\tWA']
    for i,point in enumerate(known.values()):
        lines.append('\t'.join([str(i),','.join(map(str,point['objectives'])),*(','.join(map(str,point[k])) for k in fields)]))
    path=root/stem/'paid-pool-genomes.tsv';path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    inp=root/stem/'inputs';result=root/stem/'paid-pool-qa.json'
    execute(['java','-Xmx2g','-cp',cp,'research.dynamic.PoolAssemblyCheckRun',str(inp/f'{stem}.txt'),
             str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(path),str(result),'EXACT'],root/stem/'paid-pool-qa.log')
    report=read(result);assert report['status']=='PASS' and report['passedOfflineDecodes']==len(known) and report['exactObjectiveBitsRequired']
    return report['passedOfflineDecodes']


def analyze_instance(root,cp,spec,seeds):
    stem,norm=spec['stem'],spec['normalization'];cells=[];known={}
    normalized=lambda values:(np.asarray(values).reshape(-1,3)-norm['lower'])/norm['scale']
    for seed in seeds:
        snapshots=rows(root/stem/str(seed)/'ON/global-working-pools.jsonl');assert len(snapshots)==12
        for snapshot in snapshots:
            points=snapshot['points'];objectives=normalized([p['objectives'] for p in points])
            assert all(0<p['earliestKnownPaidFE']<=snapshot['paidFE'] for p in points)
            for p in points:
                key=tuple(tuple(p[k]) for k in ('JS','FA','MA','WA'))
                if key in known:assert known[key]['objectives']==p['objectives']
                else:known[key]=p
            expected=snapshot['familyQuotas'];hv={}
            for method,key in (('ACTUAL','actualIndices'),('WITHIN_ALL','withinAllIndices'),('GLOBAL_ALL','globalAllIndices')):
                indices=snapshot[key];assert len(indices)==len(set(indices))==100
                assert np.bincount([points[i]['category'] for i in indices],minlength=5).tolist()==expected
                hv[method]=float(hypervolume(objectives[indices],(1.5,)*3))
            archive_hv=float(hypervolume(normalized(snapshot['knownArchive']),(1.5,)*3));assert archive_hv>0
            assert all(value<=archive_hv+1e-10 for value in hv.values())
            deltas={control:100*(hv['GLOBAL_ALL']-hv[control])/archive_hv for control in ('ACTUAL','WITHIN_ALL')}
            cells.append({'seed':seed,'role':snapshot['role'],'step':snapshot['step'],'paidFE':snapshot['paidFE'],
                'internalWorkingHV':hv,'knownPaidArchiveHV':archive_hv,'deltaPctOfPaidArchiveHV':deltas,
                'materialVsBoth':all(v>=.1 for v in deltas.values())})
    assert len(cells)==24
    material=[c for c in cells if c['materialVsBoth']]
    roles=sorted({c['role'] for c in material});sources=sorted({c['seed'] for c in material})
    means={control:float(np.mean([c['deltaPctOfPaidArchiveHV'][control] for c in cells])) for control in ('ACTUAL','WITHIN_ALL')}
    supported=len(material)/len(cells)>=.2 and len(roles)>=2 and len(sources)>=2 and all(v>=0 for v in means.values())
    qa=replay_known(root,cp,stem,known)
    result={'stem':stem,'cells':cells,'materialWindows':len(material),'totalWindows':len(cells),'materialRoles':roles,
        'materialSeeds':sources,'meanDeltaPctOfPaidArchiveHV':means,'offlinePaidGenomeFullQA':qa,
        'worthIndependentSharedWorkingProbe':bool(supported),
        'scope':'Within-generation static internal retention on identical paid candidates and unchanged family quotas. '
                'The external paid archive already contains these points; no new external HV was discovered. '
                'Does not prove continuation value, role specificity, fatigue specificity, novelty, or time advantage.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,cp,specs,seeds):
    result=[analyze_instance(root,cp,s,seeds) for s in specs]
    output={'instances':[{k:v for k,v in r.items() if k!='cells'} for r in result],
        'worthIndependentSharedWorkingProbe':all(r['worthIndependentSharedWorkingProbe'] for r in result),
        'offlinePaidGenomeFullQA':sum(r['offlinePaidGenomeFullQA'] for r in result)}
    write_once(root/'analysis.json',output);return output
