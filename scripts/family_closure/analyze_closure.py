"""Conditional-capacity reports, independent HV checks, and decoded witnesses."""
import argparse
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from common import BASE,SEEDS,linux,read,write,sha
from closure_data import context,witness_indices,vectors
from frontier import engineering_checks as dp_checks
from volume import UncoveredVolume,engineering_checks as volume_checks

ANCHOR=BASE/'runs/linux-pilot-evaluation-20261106-01'
OLD=BASE/'runs/linux-mature-donor-20261106-01'


def check_witnesses(root,rows):
    assert 0<len(rows)<=60
    out=root/'witness-qa';out.mkdir();case=out/'cases.tsv'
    with case.open('x') as stream:
        stream.write('id\tobjectives\tJS\tFA\tMA\tWA\n')
        for identity,objectives,v in rows:
            stream.write('\t'.join([identity,','.join(map(str,objectives)),*(','.join(map(str,a)) for a in v)])+'\n')
    cp=(root/'build-02/classpath.txt').read_text().strip();inputs=ANCHOR/'payload/inputs/20_8_5_1'
    command=['nice','-n','10',str(BASE/'runtime/jdk17/bin/java'),'-Xmx2g','-cp',cp,'research.dynamic.PoolAssemblyCheckRun',
        str(inputs/'20_8_5_1.txt'),str(inputs/'RECONSTRUCTED-setup.txt'),str(inputs/'fatigue-input.txt'),str(case),str(out/'receipt.json')]
    write(out/'command.json',command);start=time.perf_counter()
    result=subprocess.run(command,text=True,capture_output=True);(out/'run.log').write_text(result.stdout+result.stderr)
    write(out/'process.json',dict(exitCode=result.returncode,seconds=time.perf_counter()-start))
    assert result.returncode==0,result.stdout+result.stderr
    receipt=read(out/'receipt.json');assert receipt['status']=='PASS' and receipt['attemptedOfflineDecodes']==len(rows)
    return receipt


def scores(data,reference,spec,scale,witnesses):
    from analysis_metrics import metrics,pair
    from audit_metrics import endpoint_metrics,raw_coverage,close as check
    from research.dynamic_benchmark.metrics import nondominated
    seed=data['seed'];a0=data['A0'];original=metrics(a0,reference,scale);results={};checks=0
    for name in ('finite','pool'):
        closure=data[name];points=closure['points'];normal=scale.normalize(points);gains={};single={}
        for radius in (1.25,1.5,2.0):
            scorer=UncoveredVolume(scale.normalize(a0),[radius]*3);gain=scorer.gains(normal);key=str(radius)
            check(scorer.background_hv,original['HV'][key],'A0 disjoint boxes');gains[key]=gain
            best=int(np.argmax(gain));union=metrics([*a0,points[best]],reference,scale)
            check(gain[best],union['HV'][key]-original['HV'][key],'best single HV');checks+=2
            single[key]=dict(index=best,objectives=points[best],absolute=float(gain[best]),
                relativePct=100*float(gain[best])/original['HV'][key])
        standalone=metrics(points,reference,scale);union=metrics([*a0,*points],reference,scale)
        for metric in (standalone,union):
            independent,_=endpoint_metrics(np.asarray(metric['front']),reference,spec['normalization'])
            for key in ('1.25','1.5','2.0'):check(metric['HV'][key],independent['HV'][key],'endpoint HV');checks+=1
        compared=pair(seed,standalone,original);union_pair=pair(seed,union,original)
        for entry,front in ((compared,standalone),(union_pair,union)):
            coverage=raw_coverage(front['front'],original['front'])
            for key in ('C_A_B','C_B_A','coveredA','coveredB','totalA','totalB'):assert entry['coverage'][key]==coverage[key]
        for index in witness_indices(points,gains):witnesses.append((f'{seed}-{name}-{index}',points[index],vectors(closure,index)))
        results[name]=dict(bestSingle=single,standalone=standalone,withA0=union,standaloneVersusA0=compared,
            withA0VersusA0=union_pair,localReduction=closure['reduction'],dpStages=closure['stages'],
            algebraicExpandedStates=closure['algebraicExpandedStates'],frontSize=len(points))
    return dict(seed=seed,A0=original,closures=results,audit=data['audit'],independentHVChecks=checks)


def main(root):
    linux();assert read(root/'science-acceptance.json')['passed']
    sys.path.insert(0,str(ANCHOR/'payload'));sys.path.insert(0,str(OLD/'analysis-code'))
    from analysis_metrics import frozen_scale
    from research.dynamic_benchmark.metrics import nondominated
    from research.pilot_evaluation import hypervolume
    start=time.perf_counter();out=root/'analysis';out.mkdir(exist_ok=False)
    checks=dict(dp=dp_checks(),volume=volume_checks(hypervolume))
    data=[context(root,seed) for seed in SEEDS]
    reference=nondominated(np.vstack([np.asarray(points) for d in data for points in (d['A0'],d['finite']['points'],d['pool']['points'])]))
    write(out/'closures.json',data);write(out/'reference.json',reference.tolist())
    spec=read(OLD/'protocol.json')['instances'][0];assert spec['stem']=='20_8_5_1';scale=frozen_scale(spec)
    write(out/'metric-inputs.json',dict(normalization=spec['normalization'],referenceSHA256=sha(out/'reference.json'),
        rule=read(root/'oracle-protocol.json')['commonReference'],kernels={n:sha(OLD/'analysis-code'/n) for n in ('analysis_metrics.py','audit_metrics.py')}))
    witnesses=[];results=[scores(d,reference,spec,scale,witnesses) for d in data]
    qa=check_witnesses(root,witnesses)
    material=sum(r['closures']['finite']['bestSingle']['1.5']['relativePct']>=.1 for r in results)
    decision='CAPACITY_WITNESS_PROPOSE_NEW_SEARCH_HYPOTHESIS' if material>=2 else 'STOP_ACCEPTANCE_ONLY_RESCUE_IN_FROZEN_DOMAIN'
    report=dict(instance='20_8_5_1',results=results,engineering=checks,witnessQA=qa,materialSources=material,
        decision=decision,seconds=time.perf_counter()-start,
        additionalMetricFE=0,additionalWitnessDecodes=len(witnesses),algorithmCompetitionClaim=False,
        qualifications=['Static support ignores acceptance and live donor loss; expressible superset only',
            'One predetermined family per source, three sources; no claim over all families or the100job domain',
            'Factory dyadic sums are algebraic conditional oracle values; decoded witnesses validate tolerance, not exact floating bits',
            'A0 union monotonicity is capacity evidence, not an independent superior method',
            '3,580 new objective evaluations are charged, algebraic expansions separately counted'])
    write(out/'report.json',report)
    for r in results:
        print('CAPACITY',r['seed'],{n:v['bestSingle']['1.5']['relativePct'] for n,v in r['closures'].items()},flush=True)
    print('DECISION',decision,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
