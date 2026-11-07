"""Earliest paid archive-admission origins and three-indicator geometry; zero new search or decoder."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'

from collections import Counter
from datetime import datetime
import json
import shutil

import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock,nondominated,hypervolume,igd_plus
from qpa_capability_analysis import endpoint
from ctx_gom_capability_support import heavy_folder
from research.semantic_repair.evidence import digest
from ctx_stage_geometry_math import covered_by,origin_hv,origin_igd,fixtures

SOURCE=ROOT/'runs/ctx-gom-capability-20261106-051509-678987'
GROUPS=['MAKESPAN','CENTER','ENERGY','WORKER_COST']


def local_segments(stem,arm):
    segments=[]
    with (heavy_folder(stem,arm)/'gom-events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            e=json.loads(line)
            if e['kind']=='passEnd':break
            if e['kind']=='program':segments.append((e['physicalGroup'],len(e['order'])))
    assert len(segments)==100
    return [sum(size for group,size in segments if group==i) for i in range(1,5)]


def label(fe,segments,classic=False):
    assert 1<=fe<=500000
    if fe<=100:return 'INITIAL'
    perpass=sum(segments);position=(fe-101)%(5000+perpass)
    if position<5000:
        if classic:return 'GLOBAL'
        for group,size in zip(GROUPS,(750,2750,750,750)):
            if position<size:return 'GLOBAL_'+group
            position-=size
    else:
        position-=5000
        for group,size in zip(GROUPS,segments):
            if position<size:return 'LOCAL_'+group
            position-=size
    raise AssertionError('Unmapped paid attempt')


def labelled_front(folder,segments,classic):
    expected=np.asarray(endpoint(folder,'FE500K',500000)['front'],float);births={}
    with (folder/'checkpoint-solutions.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['checkpointKind']=='FE' and row['checkpoint']==500000:
                obj=tuple(row['objectives']);assert obj not in births and row['bornFE']<=row['checkpointFE']==500000
                births[obj]=row['bornFE']
    assert set(births)==set(map(tuple,expected))
    labels=[label(births[tuple(p)],segments,classic) for p in expected]
    receipt,=rows(folder/'run-receipt.jsonl');r=500000-100;cycles,tail=divmod(r,5000+sum(segments))
    expected_global=cycles*5000+min(5000,tail);expected_local=cycles*sum(segments)+max(0,tail-5000)
    assert receipt['search']['global.evaluations']==expected_global and receipt['search']['jointLocal.evaluations']==expected_local
    return expected,labels,dict(pointCount=len(expected),perPassLocalRoleFE=segments,completePasses=cycles,
        globalFE=expected_global,localFE=expected_local,terminalStage=label(500000,segments,classic),
        birthsByOrigin=dict(Counter(labels)),earliestBornFE=min(births.values()),latestBornFE=max(births.values()))


def analyze(root,plan):
    results=[]
    for spec in plan['instances']:
        stem,norm=spec['stem'],spec['normalization'];strong='NSGA_CTX_GOM' if stem.startswith('20_') else 'PA_JOINT'
        full={(s,a):np.asarray(endpoint(SOURCE/stem/str(s)/('FE500K-'+a),'FE500K',500000)['front'],float) for s in plan['seeds'] for a in plan['arms']}
        reference=nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in full.values()]))
        for seed in plan['seeds']:
            arms=['SHARE_CTX_GOM','UNIFORM_CTX_GOM']+(['NSGA_CTX_GOM'] if strong=='NSGA_CTX_GOM' else [])
            data={};provenance={}
            for arm in arms:
                segments=local_segments(stem,arm);folder=SOURCE/stem/str(seed)/('FE500K-'+arm)
                a,labels,source=labelled_front(folder,segments,arm=='NSGA_CTX_GOM')
                normal=(a-norm['lower'])/norm['scale'];ig=origin_igd(normal,labels,reference)
                assert abs(ig['IGDplus']-igd_plus(normal,reference))<2e-12
                data[arm]=(a,labels,normal);provenance[arm]=dict(**source,igdGeometry=ig)
            pairs=[('SHARE_CTX_GOM','UNIFORM_CTX_GOM'),('SHARE_CTX_GOM',strong),('UNIFORM_CTX_GOM','SHARE_CTX_GOM')]
            if strong=='NSGA_CTX_GOM':pairs.append((strong,'SHARE_CTX_GOM'))
            for arm,opponent in pairs:
                a,labels,normal=data[arm];b=full[seed,opponent];other=(b-norm['lower'])/norm['scale']
                hv=origin_hv(normal,labels,other);pool=nondominated(np.vstack([normal,other]))
                assert abs(hv['poolHV']-hypervolume(pool,(1.5,)*3))<2e-10
                assert abs(hv['otherHV']-hypervolume(other,(1.5,)*3))<2e-10
                covered=covered_by(a,b);bygroup={}
                for group in dict.fromkeys(labels):
                    mask=np.array([s==group for s in labels]);bygroup[group]=dict(points=int(mask.sum()),coveredByB=int(covered[mask].sum()),
                        standaloneExtraHV=hv['standalone'][group],exclusiveExtraHV=hv['exclusive'][group],
                        IGDplusLeaveOriginOutIncrease=provenance[arm]['igdGeometry']['leaveOutIncrease'][group])
                results.append(dict(instance=stem,seed=seed,A=arm,B=opponent,provenance=provenance[arm],
                    A_HV=hypervolume(normal,(1.5,)*3),B_HV=hv['otherHV'],novelHV=hv['novelHV'],
                    AcoveredByB=int(covered.sum()),BcoveredByA=int(covered_by(b,a).sum()),Bpoints=len(b),origins=bygroup))
            print('CTX_STAGE_GEOMETRY',stem,seed,'completed',flush=True)
    return dict(cases=results,newSearchFE=0,newDecoderCalls=0,defaultMainlineChanged=False,
        attribution='Earliest admitted objective representative only; no causal group/role value or hidden acceptance/survival inference',goalAchieved=False)


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        assert read(SOURCE/'independent-final-audit.json')['passed'];plan=read(SOURCE/'protocol.json')
        root=ROOT/'runs'/datetime.now().strftime('ctx-gom-stage-geometry-%Y%m%d-%H%M%S-%f');root.mkdir()
        write_once(root/'protocol.json',dict(version='CTX_GOM_STAGE_GEOMETRY-v1',source=str(SOURCE),sourceAnalysisSHA256=digest(SOURCE/'analysis.json'),
            scope='Paid endpoint-only observational source attribution; no new search or decoder',
            birthMeaning='Earliest paid admitted objective representative from immutable CheckpointGenomes, not every later duplicate genotype source',
            labels='Initialization, QGS physical global role and complete GOM physical local role. Uniform always prefers CENTER; NSGA global unlabelled',
            ledger='Read first complete paid heavy pass role/mask lengths and verify analytic cycles against each500k receipt; within-role family order immaterial',
            metrics='Existing common full500k empirical IGD+reference, frozen normalization and1.5HV; per-origin exact leave-out HV, standalone extraHV, IGD+leave-out and Ccoverage counts',
            limitations='Held-output geometry, not causal intervention; no operator/ratio/acceptance/survivor change or revival of stopped versions',newSearchFE=0,newDecoderCalls=0))
        for name in ('analyze_ctx_gom_stage_geometry.py','ctx_stage_geometry_math.py'):shutil.copy2(ROOT/'scripts'/name,root/name)
        write_once(root/'math-fixtures.json',fixtures());result=analyze(root,plan);write_once(root/'analysis.json',result)
        print('CTX_STAGE_GEOMETRY_ROOT',root,flush=True)


if __name__=='__main__':main()
