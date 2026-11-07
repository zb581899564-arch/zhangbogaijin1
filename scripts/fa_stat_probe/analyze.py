"""Score only after all fixed fees and independent physical audit are complete."""
import argparse
import numpy as np
from common import *
from score import hv,paired,outcome,decision,accepts


def fixtures():
    unit=np.ones(3)
    assert metrics([[.2,.2,.2]],[[.3,.3,.3]],unit)['IGDplus']==0
    assert abs(metrics([[.4,.4,.4]],[[.3,.3,.3]],unit)['IGDplus']-np.sqrt(.03))<1e-14
    assert abs(metrics([[0,0,0]],[[0,0,0],[1,1,1]],unit)['IGD']-np.sqrt(3)/2)<1e-14
    assert coverage([[1,1,1]],[[1,1,1]])['C']==1
    assert coverage([[0,1,1]],[[1,0,1]])['C']==coverage([[1,0,1]],[[0,1,1]])['C']==0
    assert not accepts('MAKESPAN',[1,0,0],[1,1,1],[[0,0,0]])
    assert accepts('CENTER',[1,1,1],[2,2,2],[[0,0,0]])
    assert not accepts('CENTER',[2,1,1],[1,2,2],[[1,1,1]])


def independent_c(a,b):
    return sum(any(all(x<=y for x,y in zip(p,q)) for p in a) for q in b)


def main(root):
    assert read(root/'independent-audit.json')['passed'];fixtures()
    started=time.monotonic();out=root/'analysis';out.mkdir()
    entries,_,_=load_sources();queries={q['id']:q for q in stream(root/'prepared/queries.jsonl')}
    actual={r['id']:r for f in sorted((root/'paid').iterdir()) for r in stream(f/'evaluations.jsonl')}
    assert len(actual)==1152
    references={background:nd([p for e in entries for p in e[background]]+[r['objectives'] for r in actual.values()])
                for background in ('S_archive','A0')}
    for name,reference in references.items():
        write(out/(name+'-reference.json'),dict(points=reference.tolist(),scale=SCALE,lower=[0,0,0],
              rule=f'ND(all3 {name} backgrounds + all1152 candidates), offline only'))
    sys.path.insert(0,str(ANCHOR));from research.dynamic_benchmark.metrics import hypervolume,igd_plus
    summaries=[];comparisons=[];front_records=[];singles=[];role_records=[]
    max_hv_error=max_igd_error=0.;c_checks=0
    for e in entries:
        for background,reference in references.items():
            fronts={};accepted={}
            for arm in ARMS:
                front,accepted_front,summary,single=outcome(e,arm,background,queries,actual,reference)
                summaries.append(summary);fronts[arm]=front;accepted[arm]=accepted_front;singles.extend(single)
                front_records.append(dict(context=e['id'],background=background,arm=arm,
                    points=front.tolist(),acceptedPoints=accepted_front.tolist()))
                for ref in (1.25,1.5,2.0):
                    error=abs(hv(front,ref)-hypervolume(front/SCALE,[ref]*3));max_hv_error=max(max_hv_error,error)
                    assert error<1e-11
                err=abs(summary['final']['IGDplus']-igd_plus(front/SCALE,reference/SCALE))
                max_igd_error=max(max_igd_error,err);assert err<1e-12
                if background=='S_archive':
                    for role in ROLES:
                        selected=[q for q in queries.values() if q['context']==e['id'] and q['arm']==arm and q['role']==role]
                        points=[actual[q['id']]['objectives'] for q in selected]
                        role_records.append(dict(context=e['id'],arm=arm,role=role,FE=32,
                            **metrics([*e[background],*points],reference,SCALE),deltaHV=hv([*e[background],*points])-hv(e[background])))
            for control in ('POST_FA','RANDOM_FOS'):
                result=paired(fronts['PRE_FA_STATS'],fronts[control],reference)
                for a,b,key in [(fronts['PRE_FA_STATS'],fronts[control],'C_A_B'),(fronts[control],fronts['PRE_FA_STATS'],'C_B_A')]:
                    assert independent_c(a,b)==result[key]['covered'];c_checks+=1
                comparisons.append(dict(context=e['id'],background=background,control=control,**result,
                    acceptedOnlyComparison=paired(accepted['PRE_FA_STATS'],accepted[control],reference)))
    verdict=decision(comparisons)
    for name,value in [('summaries',summaries),('comparisons',comparisons),('fronts',front_records),('roles',role_records),('decision',verdict)]:write(out/(name+'.json'),value)
    csv_write(out/'single-candidates.csv',singles)
    csv_write(out/'quality-table.csv',[dict(context=s['context'],arm=s['arm'],background=s['background'],FE=s['FE'],
              **s['final'],deltaHV=s['deltaHV'],HVgainPercent=s['relativeGainHVpercent'],accepted=s['accepted'],fresh=s['fresh']) for s in summaries])
    csv_write(out/'paired-table.csv',[dict(context=c['context'],background=c['background'],control=c['control'],
        HVpercent=c['HVpercent'],IGDplusImprovementPercent=c['IGDplusImprovementPercent'],IGDplusAbsoluteReduction=c['IGDplusAbsoluteReduction'],
        C_A_B=c['C_A_B']['C'],coveredB=c['C_A_B']['covered'],totalB=c['C_A_B']['denominator'],
        C_B_A=c['C_B_A']['C'],coveredA=c['C_B_A']['covered'],totalA=c['C_B_A']['denominator']) for c in comparisons])
    write(out/'numeric-audit.json',dict(passed=True,independentHVChecks=54,maxHVError=max_hv_error,
          independentIGDplusChecks=18,maxIGDplusError=max_igd_error,independentCoverageCountChecks=c_checks,
          actualMetricDirectionAverageAndAcceptanceFixturesPassed=True,newDecoderCalls=0,seconds=time.monotonic()-started))
    print('DECISION',json.dumps(verdict),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)
