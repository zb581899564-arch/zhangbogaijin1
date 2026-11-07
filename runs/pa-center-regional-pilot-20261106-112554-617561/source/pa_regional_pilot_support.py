"""Guarded nine-arm dispatch and accepted-heavy/native-control light bridges."""
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment

from run_long_budget_bridge import read,rows,write_once,execute
from run_snapshot_anchor_audit import override
from frozen_classpath_identity import verify_capture
from ctx_gom_capability_support import counts,checked
from pa_capability_support import initial_key
from pa_role_pilot_support import supplied_initials
from qpa_capability_analysis import endpoint


def check_moead(folder,receipt,limit,reference):
    d=receipt['search'];assert receipt['referenceAdapter']==reference and not receipt['localSearchInvoked']
    assert receipt['executedAlgorithm']=='org.uma.jmetal.util.research.classic.'+('MoeadReferenceAlgorithm' if reference else 'OrdinaryMoeadAlgorithm')
    assert d.get('inter.evaluations',0)==d.get('intra.evaluations',0)==d.get('jointLocal.evaluations',0)==0
    assert d['initialization.evaluations']==min(limit,100) and d.get('global.evaluations',0)==max(0,limit-100)
    if limit>=100:
        assert d['weightCount']==100 and not d['weightConstructionConsumesRng'] and d['maximumReplacementsPerChild']<=2
        assert d.get('idealPaidUpdates',0)==max(0,limit-100)
        initial=np.array([p['objectives'] for p in initial_key(folder)])
        assert np.allclose(d['objectiveScaleFrozen'],np.abs(initial).mean(axis=0),rtol=0,atol=2e-10)
        front=np.array(endpoint(folder,'FE',limit)['front']);assert d['paidIdeal']==front.min(axis=0).tolist()


def check_policy(folder,mode,scale,limit,real):
    helper=read(folder/'regional-summary.json');command=read(folder/'command.json');verify_capture(helper['identity'],command[command.index('-cp')+1])
    policy=helper['policy'];targets=rows(folder/'regional-targets.jsonl')
    if real not in ('PA_JOINT','PA_EQUAL'):assert not policy and not targets;return
    if mode=='OFF':assert policy['mode']=='OFF' and policy['observedPaid']==0 and not targets;return
    assert policy['mode']==mode and policy['observedPaid']==limit and policy['targetsReady']
    initial=initial_key(folder);n=len(initial[0]['JS']);program=2*n-1;complete,remainder=divmod(limit-100,100*program)
    center=complete*55*program+min(max(0,remainder-15*program),55*program)
    assert policy['centerComparisons']==center and policy['boundaryComparisons']==limit-100-center
    weights=np.array([(a,b,c) for a in range(1,11) for b in range(1,11) for c in range(1,11) if a+b+c==12])
    points=np.array([p['objectives'] for p in initial]);ideal=points.min(axis=0)
    cost=(weights[None,:,:]*((points[15:70,None,:]-ideal)/scale)).max(axis=2);r,c=linear_sum_assignment(cost)
    target,=targets;assert target['paidFE']==100 and target['columns']==c.tolist() and target['directions']==weights.tolist() and target['ideal']==ideal.tolist()
    assert abs(target['assignmentCost']-float(cost[r,c].sum()))<2e-12
    assert policy['ideal']==np.min(endpoint(folder,'FE',limit)['front'],axis=0).tolist()


def run_one(root,cp,plan,spec,arm,seed,label,limit,old=False,reference=False,supplied=None):
    assert counts(root)['attemptedFE']+limit<=plan['maximumTotalAttemptedFE']
    real,mode=plan['armDefinitions'][arm];template='NSGA2_DEEP' if real=='MOEAD_4V' else real
    command=read(Path(plan['controlSource'])/spec['stem']/'14910003'/('FE500K-'+template)/'command.json');at=command.index('research.dynamic.GomCapabilityRun')
    command[at]='research.dynamic.PlainMoeadRun' if real=='MOEAD_4V' else 'research.dynamic.GomCapabilityRun' if old else 'research.dynamic.PaRegionalCapabilityRun'
    command[command.index('-cp')+1]=cp;out=root/spec['stem']/label;out.mkdir(parents=True)
    for offset,name in enumerate((spec['stem']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),1):command[at+offset]=str(root/spec['stem']/'inputs'/name)
    command[at+4:at+9]=[str(out),real,str(limit),str(seed),'Infinity']
    options={'research.paRegional.mode':mode,'research.paRegional.scale':','.join(map(str,spec['normalization']['scale'])),
        'research.pa.auditPaid':'true','research.pa.traceIdentity':'false','research.ctxFork.localInput':'POST'}
    if supplied:options['research.pa.sourceTSV']=str(supplied)
    if real=='MOEAD_4V':options['research.moead.reference']=str(reference).lower();options['research.ctxGom.enabled']='false'
    for key,value in options.items():command=override(command,key,value)
    write_once(out/'command.json',command);print('PA_REGIONAL_PILOT_RUN',spec['stem'],label,limit,flush=True)
    execute(command,out/'run.log',timeout=900);receipt=checked(out,cp,limit,float('inf'))
    assert receipt['attempted']==receipt['successful']==receipt['decoder']['dynamic.evaluations']==limit and receipt['paidSHA256']
    if real=='MOEAD_4V':check_moead(out,receipt,limit,reference)
    elif not old:check_policy(out,mode,np.asarray(spec['normalization']['scale']),limit,real)
    return out,receipt


def bridge(root,cp,base,plan):
    engine=Path(plan['engineeringRoot']);checks=[]
    for spec in plan['instances']:
        stem=spec['stem'];supplied=engine/stem/'inputs/sources.tsv'
        for arm,mode in (('PA_JOINT','OFF'),('REGIONAL','REGIONAL'),('NO_SPECIALIST','NO_SPECIALIST')):
            folder,new=run_one(root,cp,plan,spec,arm,13630003,'BRIDGE-'+arm,spec['engineeringFE'],supplied=supplied)
            old,=rows(engine/stem/mode/'receipt.jsonl')
            assert new['paidSHA256']==old['paidSHA256'] and initial_key(folder)==supplied_initials(supplied)
            assert sorted(map(tuple,endpoint(folder,'FE',spec['engineeringFE'])['front']))==sorted(tuple(p['objectives']) for p in old['lastValidFront'])
            checks.append(dict(instance=stem,arm=arm,fullTwoGenerationHeavyLightSHAAndFrontEqual=True))
        initial=None
        for arm in plan['bridgeControls']:
            a,ra=run_one(root,base,plan,spec,arm,13630003,'BRIDGE-OLD-'+arm,5102,old=True)
            b,rb=run_one(root,cp,plan,spec,arm,13630003,'BRIDGE-NEW-'+arm,5102)
            assert ra['paidSHA256']==rb['paidSHA256'] and initial_key(a)==initial_key(b)
            assert endpoint(a,'FE',5102)['front']==endpoint(b,'FE',5102)['front']
            if initial is None:initial=initial_key(a)
            assert initial==initial_key(a)
            checks.append(dict(instance=stem,arm=arm,frozenControlWholePaidSHAAndFrontEqual=True))
        masters={}
        for reference in (True,False):
            tag='REFERENCE' if reference else 'CURRENT'
            folder,receipt=run_one(root,cp,plan,spec,'MOEAD_4V',13630003,'BRIDGE-MOEAD-'+tag,5102,reference=reference)
            assert initial_key(folder)==initial;masters[reference]=(folder,receipt)
            for limit in plan['moeadCutoffs']:run_one(root,cp,plan,spec,'MOEAD_4V',13630003,'BRIDGE-MOEAD-'+tag+'-cut'+str(limit),limit,reference=reference)
        assert masters[True][1]['paidSHA256']==masters[False][1]['paidSHA256']
        assert endpoint(masters[True][0],'FE',5102)['front']==endpoint(masters[False][0],'FE',5102)['front']
        for limit in plan['moeadCutoffs']:
            a=root/stem/('BRIDGE-MOEAD-REFERENCE-cut'+str(limit));b=root/stem/('BRIDGE-MOEAD-CURRENT-cut'+str(limit))
            ar,=rows(a/'run-receipt.jsonl');br,=rows(b/'run-receipt.jsonl');assert ar['paidSHA256']==br['paidSHA256']
        checks.append(dict(instance=stem,arm='MOEAD_4V',independentlySourcedAdaptersWholePaidSHAInitialsFrontAndCutsEqual=True))
    actual=counts(root);assert actual['attemptedFE']==actual['successfulFE']==plan['plannedBridgeFE'] and actual['runs']==46
    write_once(root/'bridge-acceptance.json',dict(passed=True,checks=checks,**actual))
