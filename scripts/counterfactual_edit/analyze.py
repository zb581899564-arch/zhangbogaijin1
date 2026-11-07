"""Report every counterfactual, conditional interaction and joint quality indicators."""
import argparse
from collections import Counter
from pathlib import Path
import time
import numpy as np
from cf_common import *
from cf_classify import certificate,fixtures,ORDINARY


def load_matrices(root,protocol):
    data={c['id']:{} for c in protocol['cases']}
    for phase in ('qa','paid'):
        for stem in STEMS:
            for row in lines(root/phase/stem/'evaluations.jsonl'):
                assert row['mask'] not in data[row['id']]
                data[row['id']][row['mask']]=row
    assert all(set(v)==set(range(16)) for v in data.values())
    return {k:[v[i] for i in range(16)] for k,v in data.items()}


def score_case(case,matrix,reference,scale,protocol):
    from analysis_metrics import metrics,pair,hv
    from volume import UncoveredVolume
    from research.dynamic_benchmark.metrics import nondominated
    original_final=read(OLD/'science'/case['instance']/str(case['seed'])/case['arm']/'front.json')
    backgrounds=dict(A0=case['A0'],beforeEvent=case['beforeEvent'],
                     knownEndpoints=nondominated([*case['A0'],matrix[0]['objectives'],matrix[15]['objectives']]).tolist(),
                     previousFinal=original_final)
    objectives=[r['objectives'] for r in matrix];gains={};gain_profiles={};checks=0
    for name,points in backgrounds.items():
        profile={}
        for radius in (1.25,1.5,2.0):
            scorer=UncoveredVolume(scale.normalize(points),[radius]*3)
            values=scorer.gains(scale.normalize(objectives))
            baseline=hv(scale.normalize(points),radius)
            for i in range(16):
                independent=hv(scale.normalize([*points,objectives[i]]),radius)-baseline
                assert abs(independent-values[i])<1e-11,(case['id'],name,radius,i)
                checks+=1
            profile[str(radius)]=dict(absolute=values.tolist(),
                     relativePct=(100*values/baseline).tolist(),backgroundHV=baseline)
        gain_profiles[name]=profile;gains[name]=profile['1.5']['absolute']
    cls=certificate(matrix,gains,np.asarray(protocol['objectiveCertificateAbsTol']),protocol['hvNumericalAbsTol'])
    named={**ORDINARY,'PARENT':0,'FULL':15}
    baseline=metrics([*case['A0'],objectives[15]],reference,scale)
    named_metrics={}
    for name,mask in named.items():
        scored=metrics([*case['A0'],objectives[mask]],reference,scale)
        named_metrics[name]=dict(mask=mask,metrics=scored,versusFull=pair(case['seed'],scored,baseline))
    interaction=(np.asarray(objectives[15])-objectives[3]-np.asarray(objectives[12])+objectives[0]).tolist()
    return dict(id=case['id'],instance=case['instance'],seed=case['seed'],arm=case['arm'],sourceFE=case['fe'],
        label=case['label'],role=case['step']['role'],parentId=case['step']['parentId'],jobs=case['jobs'],
        objectives=objectives,gainProfiles=gain_profiles,classification=cls,namedMetrics=named_metrics,
        resourceOrderInteraction=interaction,independentHVChecks=checks,
        interpretation='Finite diagnostic matrices and same-parent comparisons; not equal-FE algorithm performance')


def summarize(results):
    groups={}
    for label in ('POSITIVE','MATCHED_NEGATIVE','BACKGROUND_NEGATIVE'):
        entries=[r for r in results if r['label']==label];counts=Counter()
        for r in entries:
            c=r['classification']
            counts['strictBetterSubset']+=bool(c['strictBetterSubsets'])
            counts['strictBetterNewPhysicalSubset']+=bool(c['strictBetterNewPhysicalSubsets'])
            counts['onlyEquivalentFullRepresentation']+=bool(c['equalSameFullPhysical']) and not c['strictBetterSubsets']
            counts['harmfulAtomAtFull']+=bool(c['harmfulAtomsAtFull'])
            counts['ordinaryStrictlyBetter']+=any(v['strictBetter'] for v in c['ordinary'].values())
            counts['fullNecessaryBeforeEvent']+=c['necessity']['beforeEvent']['fullNecessary']
            counts['mixedResourceOrderCertificate']+=bool(c['resourceOrderMinimalCertificates'])
            counts['crossJobMixedCertificate']+=bool(c['crossJobResourceOrderCertificates'])
            counts['newQueriesAboveKnownEndpoints']+=max(r['gainProfiles']['knownEndpoints']['1.5']['absolute'][1:15])>1e-12
            counts['newQueriesAbovePreviousFinal']+=max(r['gainProfiles']['previousFinal']['1.5']['absolute'][1:15])>1e-12
        groups[label]=dict(cases=len(entries),counts=dict(counts))
    return groups


def main(root):
    prepare();assert read(root/'paid-independent-audit.json')['passed']
    from analysis_metrics import frozen_scale
    from research.dynamic_benchmark.metrics import nondominated
    output=root/'analysis';output.mkdir()
    start=time.perf_counter();protocol=read(root/'protocol.json');fixture=fixtures()
    matrices=load_matrices(root,protocol)
    cases={c['id']:read(root/'cases'/(c['id']+'.json')) for c in protocol['cases']}
    specs={s['stem']:s for s in read(MATURE/'protocol.json')['instances']};references={}
    for stem in STEMS:
        points=[]
        for cid,c in cases.items():
            if c['instance']==stem:points.extend(c['A0']);points.extend(r['objectives'] for r in matrices[cid])
        references[stem]=nondominated(points)
        write(output/(stem+'-reference.json'),references[stem].tolist())
    results=[]
    for cid,case in cases.items():
        r=score_case(case,matrices[cid],references[case['instance']],frozen_scale(specs[case['instance']]),protocol)
        write(output/(cid+'.json'),r);results.append(r)
        print('CASE_CLASSIFIED',cid,r['label'],r['classification'],flush=True)
    groups=summarize(results)
    report=dict(groups=groups,cases=results,fixtures=fixture,seconds=time.perf_counter()-start,
        newEvaluations=read(root/'paid-complete.json')['attempted'],qa=read(root/'qa-complete.json')['attempted'],
        independentHVChecks=sum(r['independentHVChecks'] for r in results),newAnalysisDecoderCalls=0,
        positiveSelectionBias='All positive cases originate in one already-known 100-job source; no generalization/transfer claim',
        unchangedSearchMainline=True,reference='Frozen per-instance construction; same reference for all named diagnostic sets')
    write(output/'report.json',report)
    print('COUNTERFACTUAL_GROUPS',groups,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
