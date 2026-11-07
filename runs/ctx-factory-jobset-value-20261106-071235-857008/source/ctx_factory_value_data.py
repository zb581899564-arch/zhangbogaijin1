"""Chronological already-paid cohort inputs; no terminal-front or outcome-based sampling."""
import json
import numpy as np

from run_long_budget_bridge import read,write_once,nondominated
from ctx_phase_support import PILOT
from qpa_capability_analysis import endpoint


def load_source(folder):
    populations={};admissions=[]
    with (folder/'pipeline.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line)
            if event['fe']>224590:break
            if event['kind']=='admission' and event['fe']<=224590:admissions.append((event['fe'],event['point']['objectives']))
            elif event['kind']=='population' and event['cycle']<=10:populations[event['cycle'],event['phase']]=event
    for cycle,phase in ((0,'INITIAL'),(1,'PRE_GLOBAL'),(10,'PRE_GLOBAL')):assert (cycle,phase) in populations
    for cycle in range(1,10):
        for phase in ('POST_GLOBAL','POST_LOCAL','SURVIVORS'):assert (cycle,phase) in populations
    for event in populations.values():
        if 'allPaid' in event:
            actual=nondominated([p for fe,p in admissions if fe<=event['fe']])
            assert set(map(tuple,actual))==set(map(tuple,event['allPaid']))
    return populations,admissions


def vector_key(point):
    return tuple(tuple(point[name]) for name in ('JS','FA','MA','WA'))


def prepare(root,plan):
    from pathlib import Path
    sources={name:load_source(Path(plan['source'+name])) for name in ('S','U')}
    assert sources['S'][0][0,'INITIAL']['points']==sources['U'][0][0,'INITIAL']['points']
    points={};ids={};events=[]

    def population(source,cycle,phase):
        event=sources[source][0][cycle,phase];tokens=[]
        for point in event['points']:
            key=vector_key(point)
            if key not in ids:
                pid=f'p{len(ids):06d}';ids[key]=pid;points[pid]=point
            pid=ids[key];assert points[pid]['objectives']==point['objectives']
            tokens.append(f"{pid}:{point['family']}")
        events.append('\t'.join((source,phase,str(cycle),str(event['fe']),','.join(tokens))))

    for source in ('S','U'):population(source,0,'INITIAL')
    backgrounds={}
    for cycle in range(1,11):
        for source in ('S','U'):population(source,cycle,'PRE_GLOBAL')
        if cycle in (1,10):
            start=sources['S'][0][cycle,'PRE_GLOBAL']['fe'];assert start==sources['U'][0][cycle,'PRE_GLOBAL']['fe']
            fe=start+750;assert fe==plan['actualRequestFE'][0 if cycle==1 else 1]
            events.append('\t'.join(('-', 'QUERY',str(cycle),str(fe),'')))
            backgrounds[str(cycle)]=nondominated([p for _,adm in sources.values() for f,p in adm if f<=fe]).tolist()
        if cycle<10:
            for phase in ('POST_GLOBAL','POST_LOCAL','SURVIVORS'):
                for source in ('S','U'):population(source,cycle,phase)
    assert len(points)<=plan['maximumKnownSourceFullDecodes']
    write_once(root/'source-points.json',points);write_once(root/'backgrounds.json',backgrounds)
    write_tsv(root/'known-points.tsv',points)
    (root/'events.tsv').write_text('\n'.join(events)+'\n',encoding='utf-8')
    pilot=read(PILOT/'protocol.json');norm=next(s['normalization'] for s in pilot['instances'] if s['stem']==plan['instance'])
    fronts=[np.array(endpoint(PILOT/plan['instance']/str(seed)/('FE500K-'+arm),'FE500K',500000)['front'])
            for seed in pilot['seeds'] for arm in pilot['arms']]
    reference=nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts]))
    write_once(root/'metric-context.json',dict(normalization=norm,empiricalReference=reference.tolist(),source=str(PILOT),
        fixedSampling='Java actually loaded FamilyContexts.grouping selects first/last CENTRAL within each family; physical request aliases merged',
        sourceCohortsStop='PRE_GLOBAL cycle10; no later GLOBAL/LOCAL point enters either library',extraSearchFE=0))
    return points


def write_tsv(path,points):
    lines=['id\tobjectives\tJS\tFA\tMA\tWA']
    for pid,point in points.items():
        lines.append('\t'.join([pid,*[','.join(map(str,point[k])) for k in ('objectives','JS','FA','MA','WA')]]))
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def assemble(parts,records):
    point={name:[] for name in ('JS','FA','MA','WA')};energy=labor=0.;makespan=0.
    for factory,rid in enumerate(parts):
        row=records[rid];assert row['factory']==factory
        point['JS'].extend(row['jobs']);point['FA'].extend([factory]*len(row['jobs']))
        point['MA'].extend(row['machines']);point['WA'].extend(row['workers'])
        makespan=max(makespan,row['objectives'][0])
        for value in row['energy']:energy+=value
        for value in row['labor']:labor+=value
    assert sorted(point['JS'])==list(range(len(point['JS'])))
    point['objectives']=[makespan,energy,labor];return point
