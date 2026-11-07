"""Offline joint indicators after the entire fixed candidate batch and audit finish."""
import argparse
import numpy as np
import moocore
from common import *
from score import comparison, outcomes, trigger_and_structure, decide, hv


def main(root):
    assert read(root/'independent-audit.json')['passed']
    start = time.monotonic();output=root/'analysis';output.mkdir()
    entries = read(root/'prepared/entries.json')
    queries = {q['id']:q for q in stream(root/'prepared/queries.jsonl')}
    actual = {r['id']:r for folder in sorted((root/'paid').iterdir()) for r in stream(folder/'evaluations.jsonl')}
    assert len(actual)==len(queries)==4608
    reference = nd([p for e in entries for p in e['A0']]+[r['objectives'] for r in actual.values()])
    write(output/'reference.json', dict(rule='ND union of all three A0 and every candidate, offline only',
                                      points=reference.tolist(), scale=SCALE, lower=[0,0,0]))
    sys.path.insert(0, str(ANCHOR))
    from research.dynamic_benchmark.metrics import hypervolume, check_metrics
    check_metrics()
    assert coverage([[1,1,1]],[[1,1,1]])['C']==1
    assert coverage([[0,1,1]],[[1,0,1]])['C']==coverage([[1,0,1]],[[0,1,1]])['C']==0
    summaries, comparisons, single, fronts, trigger, roles = [], [], [], [], [], []
    catalog=read(root/'sources/models.json')['catalog']
    max_hv_error=0.
    for e in entries:
        trigger.append(trigger_and_structure(e, queries, actual, catalog))
        for background in ('A0','S_archive'):
            arm_fronts={}
            for arm in ARMS:
                front, summary, singles=outcomes(e,arm,queries,actual,reference,background)
                summaries.append(summary);arm_fronts[arm]=front
                fronts.append(dict(context=e['id'],background=background,arm=arm,points=front.tolist()))
                if background=='A0':
                    single.extend(singles)
                    for ref in (1.25,1.5,2.0):
                        error=abs(hv(front,ref)-hypervolume(front/SCALE,[ref]*3));max_hv_error=max(max_hv_error,error)
                        assert error<1e-11
                    for role in ROLES:
                        subset=[actual[q['id']]['objectives'] for q in queries.values()
                                if q['context']==e['id'] and q['arm']==arm and q['role']==role]
                        roles.append(dict(context=e['id'],arm=arm,role=role,FE=len(subset),
                            deltaHV=hv([*e['A0'],*subset])-hv(e['A0']),**metrics([*e['A0'],*subset],reference,SCALE)))
            for a,b in (('PA_RESOURCE','S_RESOURCE'),('PA_SHUFFLED','S_RESOURCE'),('PA_RESOURCE','PA_SHUFFLED')):
                comparisons.append(dict(context=e['id'],background=background,comparison=a+'_vs_'+b,
                                        **comparison(arm_fronts[a],arm_fronts[b],reference)))
    entry_quality=[dict(context=e['id'],shareFE=e['fe'],paModelFE=e['paModelFE'],
        S=metrics([p['objectives'] for p in e['S']],reference,SCALE),
        PA=metrics([p['objectives'] for p in e['PA']],reference,SCALE),
        PA_vs_S=comparison([p['objectives'] for p in e['PA']],[p['objectives'] for p in e['S']],reference)) for e in entries]
    decision=decide(comparisons,trigger)
    for name,value in [('summaries',summaries),('comparisons',comparisons),('fronts',fronts),('triggers',trigger),
                       ('entry-quality',entry_quality),('role-capacity',roles),('decision',decision)]:
        write(output/(name+'.json'),value)
    csv_write(output/'single-candidates.csv',single)
    csv_write(output/'quality-table.csv',[dict(context=s['context'],arm=s['arm'],background=s['background'],
         FE=s['FE'],**s['final'],deltaHV=s['deltaHV'],gainPercent=s['relativeGainHVpercent'],fresh=s['freshCandidates']) for s in summaries])
    csv_write(output/'paired-table.csv',[dict(context=c['context'],background=c['background'],comparison=c['comparison'],
         HVpercent=c['HVpercent'],IGDplusImprovementPercent=c['IGDplusImprovementPercent'],
         C_A_B=c['C_A_B']['C'],coveredB=c['C_A_B']['covered'],totalB=c['C_A_B']['denominator'],
         C_B_A=c['C_B_A']['C'],coveredA=c['C_B_A']['covered'],totalA=c['C_B_A']['denominator']) for c in comparisons])
    write(output/'numeric-audit.json',dict(passed=True,independentHVComparisons=27,maxHVAbsoluteError=max_hv_error,
          HVandIGDplusFixturesPassed=True,weakCoverageEqualityAndNoncoverageFixturesPassed=True,
          referenceCount=len(reference),newDecoderCalls=0,seconds=time.monotonic()-start))
    print(json.dumps(decision),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)
