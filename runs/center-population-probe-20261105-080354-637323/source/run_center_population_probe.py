"""Pre-registered whole-central-population lifecycle screen; no local-operator or shared-selector change."""
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,igd_plus,nondominated,controller_lock
from natural_local_support import command,verify
from run_snapshot_anchor_audit import override
from center_population_build import ENTRY,build

SOURCE=ROOT/'runs/natural-regime-bench-20261105-073626-086353'
SEEDS=(12450003,12450033)
METHODS={'OFF':'OFF','FIXED_EA':'FIXED','UNIFORM_EA':'UNIFORM','TOURNAMENT_EA':'TOURNAMENT','NSGA':'OFF'}


def run(root,cp,stem,seed,arm,limit=5100,audit=False):
    work=root/stem/str(seed);out=work/arm;out.mkdir(parents=True)
    # Common helper expects inputs at root/stem/inputs; labels may contain a seed directory.
    cmd=command(root,cp,stem,f'{seed}/{arm}','NSGA_STRICT' if arm=='NSGA' else 'STRICT_FULL',
                'record',seed,limit=limit,audit=audit)
    cmd[cmd.index('research.dynamic.NaturalLocalRun')]='research.dynamic.CenterPopulationRun'
    cmd=override(cmd,'research.center.population',METHODS[arm])
    write_once(out/'command.json',cmd);print('CENTER_POPULATION_CELL',stem,seed,arm,limit,flush=True)
    execute(cmd,out/'run.log',timeout=300)
    receipt=verify(out,float('inf'),limit,'record')
    info=rows(out/'center-population.json')[0]
    if arm in ('FIXED_EA','UNIFORM_EA','TOURNAMENT_EA'):
        counts=info['counts'];assert counts['paid']==counts['composeCalls']==2750
        assert counts['completedBatches']==50 and sum(counts[k] for k in ('ordinaryPaid','composedPaid') if k in counts)==2750
        assert receipt['search'].get('qgs.g2.updates',0)==0
        assert all(receipt['search'][f'qgs.g{g}.updates']==50 for g in (1,3,4))
        assert counts['firstParentsPerBatchTotal']==2750 if arm=='FIXED_EA' else counts['firstParentsPerBatchTotal']<2750
    elif arm=='OFF':assert all(receipt['search'][f'qgs.g{g}.updates']==50 for g in (1,2,3,4)) or limit>5100
    if limit==5100:
        assert receipt['search']['global.evaluations']==5000
        assert receipt['search'].get('inter.evaluations',0)==receipt['search'].get('intra.evaluations',0)==0
    return out,receipt


def engineering(root,cp):
    execute(['java','-cp',cp,'org.uma.jmetal.util.research.classic.CenterPopulationChecks'],root/'mating-checks.log')
    work=root/'engineering';stem='20_8_5_1';seed=12390003
    shutil.copytree(SOURCE/stem/'inputs',work/stem/'inputs')
    out,receipt=run(work,cp,stem,seed,'OFF',limit=500000)
    old=SOURCE/stem/'FE-FULL_NAT';prior=rows(old/'run-receipt.jsonl')[0]
    for name in ('initial-population.jsonl','local-ledger.csv'):
        assert (out/name).read_bytes()==(old/name).read_bytes(),name
    def fe_fronts(folder):
        return [(r['checkpoint'],r['front']) for r in rows(folder/'anytime.jsonl') if r['checkpointKind']=='FE']
    assert fe_fronts(out)==fe_fronts(old)
    assert receipt['search']==prior['search'] and receipt['decoder']==prior['decoder']
    def genes(folder):
        return [{k:r[k] for k in ('checkpointKind','checkpoint','JS','FA','MA','WA','objectives','bornFE')}
                for r in rows(folder/'checkpoint-solutions.jsonl') if r['checkpointKind']=='FE']
    assert genes(out)==genes(old)
    # Baseline performance has no paid digest: a separate audit-enabled baseline and OFF run establish full paid equivalence.
    compare=root/'paid-engineering';shutil.copytree(SOURCE/stem/'inputs',compare/stem/'inputs')
    patched,a=run(compare,cp,stem,seed,'OFF',audit=True)
    baseline=compare/stem/str(seed)/'BASELINE';baseline.mkdir()
    cmd=command(compare,(ENTRY/'classpath.txt').read_text('utf-8'),stem,f'{seed}/BASELINE','STRICT_FULL','record',seed,limit=5100,audit=True)
    write_once(baseline/'command.json',cmd);execute(cmd,baseline/'run.log')
    b=verify(baseline,float('inf'),5100,'record')
    assert a['paidSHA256']==b['paidSHA256'] and a['search']==b['search'] and a['decoder']==b['decoder']
    write_once(root/'engineering-gate.json',{'status':'PASS','longOFFSuccessfulFE':receipt['successful'],
        'longFrozenFrontsGenomesLedgerCountersEqual':True,'shortFullPaidSequenceEqual':True,'shortAuditFE':a['successful']+b['successful'],
        'zeroDecodeMatingFixture':True,'limits':'Long natural baseline has no paid digest; full paid sequence proven only for short engineering pair.'})
    return [(out,receipt),(patched,a),(baseline,b)]


def analyze(root,specs):
    results=[];positive={c:0 for c in ('OFF','FIXED_EA','UNIFORM_EA')}
    for spec in specs:
        stem,norm=spec['stem'],spec['normalization'];cells=[]
        for seed in SEEDS:
            folders={arm:root/stem/str(seed)/arm for arm in METHODS}
            fronts={arm:(np.asarray(next(r for r in rows(folder/'anytime.jsonl') if r['checkpointKind']=='FE' and r['checkpoint']==5100)['front'])-norm['lower'])/norm['scale'] for arm,folder in folders.items()}
            ref=nondominated(np.vstack(list(fronts.values())))
            for arm,front in fronts.items():
                r=rows(folders[arm]/'run-receipt.jsonl')[0]
                cells.append({'seed':seed,'arm':arm,'HV':{str(v):float(hypervolume(front,(v,)*3)) for v in (1.25,1.5,2.0)},
                    'IGDplus':float(igd_plus(front,ref)),'searchSeconds':r['searchSeconds'],
                    'center':rows(folders[arm]/'center-population.json')[0]})
        index={(c['seed'],c['arm']):c for c in cells};effects={};costs={};aux={};sensitive={}
        for control in METHODS:
            if control=='TOURNAMENT_EA':continue
            effects[control]=[];costs[control]=[];aux[control]=[];sensitive[control]=[]
            for seed in SEEDS:
                a,b=index[(seed,'TOURNAMENT_EA')],index[(seed,control)]
                e=100*(a['HV']['1.5']/b['HV']['1.5']-1);effects[control].append(e)
                if control in positive:positive[control]+=int(e>0)
                costs[control].append(a['searchSeconds']/b['searchSeconds'])
                aux[control].append(200*(a['IGDplus']-b['IGDplus'])/(a['IGDplus']+b['IGDplus']) if a['IGDplus']+b['IGDplus'] else 0.)
                sensitive[control].append({str(v):100*(a['HV'][str(v)]/b['HV'][str(v)]-1) for v in (1.25,2.0)})
        quality=np.median(effects['OFF'])>=.5 and all(np.median(effects[c])>=.2 for c in ('FIXED_EA','UNIFORM_EA')) and np.median(effects['NSGA'])>=-2
        robust=all(x[str(v)]>=(-5 if c=='NSGA' else 0) for c in sensitive for x in sensitive[c] for v in (1.25,2.0))
        auxiliary=all(np.median(aux[c])<=5 for c in ('OFF','NSGA'))
        cost=all(np.median(costs[c])<=1.25 for c in ('OFF','FIXED_EA'))
        results.append({'stem':stem,'cells':cells,'HVEffectsPct':effects,'searchCostRatios':costs,
            'IGDplusSymmetricWorseningPct':aux,'referenceEffectsPct':sensitive,
            'qualityGate':bool(quality),'sensitivityGate':bool(robust),'auxiliaryGate':bool(auxiliary),'costGate':bool(cost),
            'supported':bool(quality and robust and auxiliary and cost)})
    result={'instances':results,'pairedPositiveCounts':positive,
        'worthClosedLoop':all(r['supported'] for r in results) and all(n>=3 for n in positive.values()),
        'scope':'First global stage only, two existing development instances and two new seeds. No local search or same-time superiority claim. No control promotion after primary failure.'}
    write_once(root/'analysis.json',result);return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('center-population-probe-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('CENTER_POPULATION_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'seeds':SEEDS,'methods':METHODS,'candidate':'TOURNAMENT_EA',
                'plannedDiagnosticFE':102000,'plannedEngineeringFE':510200,
                'question':'Does population-level reproductive feedback in CENTER add value beyond changing its kernel and fresh-birth memory alone?',
                'changed':'CENTER only: same-category parents, actual setting0 classic kernel, fresh child history, no CENTER Q agent. '
                          'FIXED first parent is original slot; UNIFORM draws both uniformly; TOURNAMENT draws both by actual NSGA union ranks/crowding. '
                          'Original FULL_ROLE survival remains and is not renamed NSGA. Union scores carried into next category-restricted tournaments, not truncated rescoring.',
                'preserved':'Other3QGS roles50steps each, physical15/55/15/15, original families and perbatch quotas, original compose once pertargetslot '
                            'with selected firstparent asreceiver, original local search untouched but never reached at5100. No cross-role donor, LP, path or selector.',
                'controls':'OFF currentFULL; FIXED_EA samekernel/freshbirth without population parent pressure; UNIFORM_EA population reproduction without ranked pressure; '
                           'actual NSGA100population/5000globalbirths. NSGA has no family sharing. Common100initialgenomes and physicalparameters.',
                'gate':'Bothinstances medianHV1.5 TOURNAMENT vsOFF>=0.5%, vsFIXED/UNIFORM>=0.2%, vsNSGA>=-2%. '
                       'Across4instance-seed pairs >=3positive versus eachOFF/FIXED/UNIFORM. Ref1.25/2 eachpair nonnegative vsall3 and>=-5%vsNSGA. '
                       'Median symmetricIGD+worsening<=5%vsOFF/NSGA ineachinstance. Median actualsearchcost ratio<=1.25vsOFF/FIXED ineachinstance. '
                       'Allnecessary, pass permits wholealgorithm closed-loop only. Failure stops thisfixed lifecycle, no seed/pressure/family/memory tuning or control promotion.',
                'engineering':'ZeroDecoder union-score/category/RNG fixtures. OFF500k reproduce available old fronts/genomes/ledger/counters; '
                              'short5100 OFF/base auditpair must have fullpaidSHA identical. Allattempts charged, endpoint genomesfullQAseparate. '
                              'No longSHA claim where oldbaseline had audit disabled.',
                'limits':'Developmentglobal-onlymechanism, not completealgorithm/fatigue-specificnovelty or same-time proof. '
                         'Earlier conditionalparentweighting failed; this tests50batch nonlinear reproduction, not resampled one-step donor weights. '
                         'No production edits, model expansion, localdownloads, transfer or push.'})
            cp=build(root);completed.extend(engineering(root,cp))
            for i,spec in enumerate(specs):
                stem=spec['stem'];shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
                for j,seed in enumerate(SEEDS):
                    arms=list(METHODS);offset=(i+j)%len(arms)
                    for arm in arms[offset:]+arms[:offset]:
                        out,receipt=run(root,cp,stem,seed,arm);completed.append((out,receipt))
                    initials=[(root/stem/str(seed)/arm/'initial-population.jsonl').read_bytes() for arm in METHODS]
                    assert all(value==initials[0] for value in initials)
            result=analyze(root,specs)
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedRuns':len(completed),
            'successfulFECompleted':sum(r['successful'] for _,r in completed),'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','runs':len(completed),'successfulFE':sum(r['successful'] for _,r in completed),
        'attemptedFE':sum(r['attempted'] for _,r in completed),'unexpectedEvaluationFailures':0,
        'checkpointFullDecoderQA':sum(read(out/'checkpoint-validation.json')['uniqueOfflineDecodes'] for out,_ in completed),
        'worthClosedLoop':result['worthClosedLoop']})
    print('CENTER_POPULATION_COMPLETE',result['worthClosedLoop'],flush=True)


if __name__=='__main__':main()
