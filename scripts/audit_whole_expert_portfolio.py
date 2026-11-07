"""Zero-search blind half-budget whole-expert envelope, with ordinary same-method restart controls."""
from datetime import datetime
from itertools import combinations
from pathlib import Path
import shutil
import numpy as np
from run_long_budget_bridge import ROOT,read,rows,write_once,igd_plus,nondominated
from fa_admission_volume import volume

OLD=ROOT/'runs/makespan-tie-screen-20261105-025223-471920'
NAT=ROOT/'runs/natural-regime-bench-20261105-073626-086353'
SEEDS=(10950003,10950033,10950063)


def checkpoint(folder,fe,norm):
    row=next(r for r in rows(folder/'anytime.jsonl') if r['checkpointKind']=='FE' and r['checkpoint']==fe)
    assert row['reached'] and row['fe']==fe and not row.get('censored',False)
    points=(np.asarray(row['front'],dtype=float)-norm['lower'])/norm['scale'];assert np.isfinite(points).all() and np.all(points>=0)
    return points


def verify_source(folder,mode,old=False):
    r=rows(folder/'run-receipt.jsonl')[0]
    assert r['mode']==mode and r['successful']==r['attempted']==500000 and r['failed']==0 and r['stopReason']=='FE_LIMIT'
    if old:
        accepted=read(folder/'verified.json');assert accepted['successfulFE']==500000 and accepted['failedFE']==0
        assert accepted['sameInitials'] and accepted['samePhysicalLedger'] and accepted['finalArchiveMatches']
        assert rows(folder/'makespan-tie.jsonl')[0]['mode']=='STRICT'
        assert rows(folder/'group.jsonl')[0]['mode']==('FULL_ROLE' if mode=='SHARE_JOB_ALIGNED' else 'PAIR')
    final=next(p['front'] for p in rows(folder/'anytime.jsonl') if p['checkpointKind']=='FE' and p['checkpoint']==500000)
    genomes=rows(folder/('solutions.jsonl' if old else 'checkpoint-solutions.jsonl'))
    if not old:genomes=[g for g in genomes if g['checkpointKind']=='FE' and g['checkpoint']==500000]
    assert {tuple(p) for p in final}=={tuple(g['objectives']) for g in genomes}


def metrics(points,reference):
    return {'HV':{str(r):volume(points,(r,)*3) for r in (1.25,1.5,2.)},'IGDplus':float(igd_plus(points,reference)),'points':len(points)}


def difference(a,b):return float(100*(a/b-1)) if b>1e-12 else None


def old_instance(spec):
    stem,norm=spec['stem'],spec['normalization'];fronts={}
    for seed in SEEDS:
        for label,arm,mode in (('F','STRICT_FULL','SHARE_JOB_ALIGNED'),('N','NSGA_STRICT','NSGA2_4V')):
            folder=OLD/stem/str(seed)/arm;verify_source(folder,mode,True)
            for fe in (250000,500000):fronts[(seed,label,fe)]=checkpoint(folder,fe,norm)
        assert (OLD/stem/str(seed)/'STRICT_FULL/initial-population.jsonl').read_bytes()==(OLD/stem/str(seed)/'NSGA_STRICT/initial-population.jsonl').read_bytes()
    reference=nondominated(np.vstack([v for (s,m,fe),v in fronts.items() if fe==500000]));pairs=[]
    join=lambda *values:nondominated(np.vstack(values))
    for s,t in combinations(SEEDS,2):
        nrestart=metrics(join(fronts[(s,'N',250000)],fronts[(t,'N',250000)]),reference)
        frestart=metrics(join(fronts[(s,'F',250000)],fronts[(t,'F',250000)]),reference)
        heterogeneous=[metrics(join(fronts[(a,'F',250000)],fronts[(b,'N',250000)]),reference) for a,b in ((s,t),(t,s))]
        nfull=[metrics(fronts[(seed,'N',500000)],reference) for seed in (s,t)]
        ffull=[metrics(fronts[(seed,'F',500000)],reference) for seed in (s,t)]
        mean_hv={str(r):float(np.mean([v['HV'][str(r)] for v in heterogeneous])) for r in (1.25,1.5,2.)}
        mean_igd=float(np.mean([v['IGDplus'] for v in heterogeneous]));den=mean_igd+nrestart['IGDplus']
        pairs.append({'seedPair':[s,t],'heterogeneousOrientations':heterogeneous,'nsgaRestart':nrestart,'fullRestart':frestart,
            'singleNsga500k':nfull,'singleFull500k':ffull,
            'meanHeterogeneousVsNsgaRestartPct':{str(r):difference(mean_hv[str(r)],nrestart['HV'][str(r)]) for r in (1.25,1.5,2.)},
            'meanHeterogeneousVsSingleNsgaMeanPct':difference(mean_hv['1.5'],float(np.mean([v['HV']['1.5'] for v in nfull]))),
            'meanHeterogeneousVsSingleFullMeanPct':difference(mean_hv['1.5'],float(np.mean([v['HV']['1.5'] for v in ffull]))),
            'meanHeterogeneousVsFullRestartPct':difference(mean_hv['1.5'],frestart['HV']['1.5']),
            'IGDplusSymmetricWorseningVsNsgaRestartPct':200*(mean_igd-nrestart['IGDplus'])/den if den else 0.})
    primary=[p['meanHeterogeneousVsNsgaRestartPct']['1.5'] for p in pairs]
    informative=all(v is not None for v in primary)
    median=lambda field:float(np.median([p[field] for p in pairs]))
    gain=informative and np.median(primary)>=.5 and sum(v>0 for v in primary)>=2
    baseline=all(p['meanHeterogeneousVsSingleNsgaMeanPct'] is not None and p['meanHeterogeneousVsSingleFullMeanPct'] is not None for p in pairs) and median('meanHeterogeneousVsSingleNsgaMeanPct')>=0 and median('meanHeterogeneousVsSingleFullMeanPct')>=1
    robust=all(all(p['meanHeterogeneousVsNsgaRestartPct'][str(r)] is not None for p in pairs) and np.median([p['meanHeterogeneousVsNsgaRestartPct'][str(r)] for p in pairs])>=0 for r in (1.25,2.))
    auxiliary=median('IGDplusSymmetricWorseningVsNsgaRestartPct')<=5
    return {'stem':stem,'pairs':pairs,'medianVsNsgaRestartPct':float(np.median(primary)) if informative else None,
        'medianVsNsgaSingleMeanPct':median('meanHeterogeneousVsSingleNsgaMeanPct'),
        'medianVsFullSingleMeanPct':median('meanHeterogeneousVsSingleFullMeanPct'),
        'restartGate':bool(gain),'baselineGate':bool(baseline),'sensitivityGate':bool(robust),'auxiliaryGate':bool(auxiliary),
        'supported':bool(gain and baseline and robust and auxiliary)}


def natural_instance(spec):
    stem,norm=spec['stem'],spec['normalization'];methods=('FULL_NAT','NSGA_NAT','UNIFORM_NAT','SYNC_NAT');fronts={}
    for method in methods:
        folder=NAT/stem/('FE-'+method);mode=rows(folder/'run-receipt.jsonl')[0]['mode'];verify_source(folder,mode)
        for fe in (250000,500000):fronts[(method,fe)]=checkpoint(folder,fe,norm)
        genes=rows(folder/'checkpoint-solutions.jsonl')
        assert {tuple(g['objectives']) for g in genes if g['checkpointKind']=='FE' and g['checkpoint']==250000}=={tuple(v) for v in next(p['front'] for p in rows(folder/'anytime.jsonl') if p['checkpointKind']=='FE' and p['checkpoint']==250000)}
        assert all(g['bornFE']<=g['checkpointFE'] for g in genes if g['checkpointKind']=='FE')
    reference=nondominated(np.vstack([v for (m,fe),v in fronts.items() if fe==500000]));joint={}
    for method in ('FULL_NAT','UNIFORM_NAT','SYNC_NAT'):
        joint[method]=metrics(nondominated(np.vstack([fronts[(method,250000)],fronts[('NSGA_NAT',250000)]])),reference)
    full,nsga=(metrics(fronts[(m,500000)],reference) for m in ('FULL_NAT','NSGA_NAT'))
    h=joint['FULL_NAT'];vs_nsga=difference(h['HV']['1.5'],nsga['HV']['1.5']);vs_full=difference(h['HV']['1.5'],full['HV']['1.5'])
    duties=difference(h['HV']['1.5'],joint['UNIFORM_NAT']['HV']['1.5'])
    return {'stem':stem,'seed':12390003,'mixtures':joint,'singleFull500k':full,'singleNsga500k':nsga,
        'heterogeneousVsNsgaSinglePct':vs_nsga,'heterogeneousVsFullSinglePct':vs_full,'fourDutyMixtureEffectPct':duties,
        'sharingMixtureEffectPct':difference(h['HV']['1.5'],joint['SYNC_NAT']['HV']['1.5']),
        'supported':bool(vs_nsga is not None and vs_full is not None and duties is not None and vs_nsga>=0 and vs_full>=0 and duties>=.5),
        'missing':'No second natural seed: homogeneous independent restart control unavailable here. This case alone cannot promote a portfolio.'}


def main():
    root=ROOT/'runs'/datetime.now().strftime('whole-expert-portfolio-envelope-%Y%m%d-%H%M%S-%f');root.mkdir()
    specs=read(OLD/'protocol.json')['instances']
    write_once(root/'protocol.json',{'instances':specs,'oldSource':str(OLD),'naturalSource':str(NAT),'oldSeeds':SEEDS,
        'hypothesis':'Keep whole four-role search intact; do its paid fronts complement a strong classic beyond ordinary independent NSGA restarts?',
        'fixedRule':'ONLY equal250k+250k=500ktotalFE. Eachprefix includes100initialFE, duplicates charged, no sharedinitial discount. '
                    'Fixedsame-output-rule numericNDunion, not merging bothheterogeneousorientations asone500k method. No fraction/window/seed search.',
        'controls':'Oldreplay3seeds: all3unorderedpairs, twoheterogeneousorientations averaged aspairedreplicates; '
                   'ordinaryNSGA250k+NSGA250k andFULL250k+FULL250k restart controls, plusmeanofpaired500k single-run metrics. '
                   'Natural1seed: FULL/UNIFORM/SYNC250k+NSGA250k and500k singles; independentrestart missing explicitly.',
        'gate':'Botholdinstances medianpairheterogeneousHV>=+0.5%vsNSGArestart and>=2/3pairmeanspositive; '
               'vsNSGA500ksinglemean median>=0 andvsFULL500ksinglemean>=+1%; refs1.25/2 medianvsNSGArestart nonnegative; '
               'median symmetricIGD+worsening<=5%. Bothnaturalinstances hetero>=both500ksingles andFULLmixvsUNIFORMmix>=+0.5%. '
               'Allnecessary foractualpre-registeredportfolioengineering only. Failure stopsblindhalf-halfwhole-expert combination; nofraction/racingcontroller torescue.',
        'evidence':'Source500k receipts/strictmodes/verified initial&ledger/finalgenomes match; 250k numericalcheckpoint reached. '
                   'Oldprefixfullgenomes unavailable; exactretainednumericfrontonly. Naturalprefix includespaidgenomes/birthFE. '
                   'No new schedule or evaluator call, no candidate feedback.',
        'metrics':'Oldfixednormalization/HVrefs, IGD+old commonNDunionof6single500kfronts; naturalperinstanceNDunionof4single500kfronts. '
                  'OneFAmodel, oldreplayandnatural regimes separate, seedpairs/FAcontexts notindependentinstances.',
        'limits':'Idealized numericquality envelope with freearchive union. Realmerge/state/RNG/initialization clocks and sequentialexecution cost NOT validated; no same-time claim. '
                 'Genericportfolio is not establishednovelty or proof originalfourrole mechanism causescomplementarity. '
                 'No rawsource reproduction, newalgorithm implementation, model/mainline/sharedselector change or externaltransfer.',
        'searchFE':0,'decoderCalls':0})
    shutil.copy2(Path(__file__),root/Path(__file__).name);shutil.copy2(Path(__file__).with_name('fa_admission_volume.py'),root/'fa_admission_volume.py')
    for spec in specs:
        stem=spec['stem'];other=next(v for v in read(NAT/'protocol.json')['instances'] if v['stem']==stem)
        assert spec['normalization']==other['normalization']
        for name in (stem+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'):
            assert (OLD/stem/'inputs'/name).read_bytes()==(NAT/stem/'inputs'/name).read_bytes()
    old=[old_instance(s) for s in specs];natural=[natural_instance(s) for s in specs]
    result={'oldLedger':old,'natural':natural,'worthActualPortfolio':all(r['supported'] for r in old+natural),'searchFE':0,'decoderCalls':0}
    write_once(root/'analysis.json',result);write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'decoderCalls':0,'worthActualPortfolio':result['worthActualPortfolio']})
    print('WHOLE_EXPERT_PORTFOLIO_ROOT',root,flush=True)
    print('OLD',[(r['stem'],r['medianVsNsgaRestartPct'],r['supported']) for r in old],flush=True)
    print('NATURAL',[(r['stem'],r['heterogeneousVsNsgaSinglePct'],r['heterogeneousVsFullSinglePct'],r['fourDutyMixtureEffectPct'],r['supported']) for r in natural],flush=True)


if __name__=='__main__':main()
