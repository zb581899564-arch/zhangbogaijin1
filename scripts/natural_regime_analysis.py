"""Separate fixed-FE and true-time evidence for the original random-factory natural/replay regimes."""
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume, igd_plus, nondominated
from natural_local_support import ledger_rows


def at_budget(folder,budget,seconds):
    kind,checkpoint=('FE',500000) if budget=='FE' else ('TIME',seconds)
    return next(r for r in rows(folder/'anytime.jsonl') if r['checkpointKind']==kind and r['checkpoint']==checkpoint and r['reached'])


def difference(a,b):
    return float(100*(a/b-1)) if b>1e-12 else None


def analyze_instance(root,spec):
    protocol=read(root/'protocol.json');stem,norm=spec['stem'],spec['normalization'];seconds=spec['time_seconds']
    normal=lambda values:(np.asarray(values,dtype=float).reshape(-1,3)-norm['lower'])/norm['scale']
    levels=[]
    for budget in ('FE','TIME'):
        points={method:at_budget(root/stem/f'{budget}-{method}',budget,seconds) for method in protocol['methods']}
        fronts={method:normal(p['front']) for method,p in points.items()};empirical=nondominated(np.vstack(list(fronts.values())))
        observations=[]
        for method,front in fronts.items():
            folder=root/stem/f'{budget}-{method}';receipt,=rows(folder/'run-receipt.jsonl');ledger=ledger_rows(folder/'local-ledger.csv')
            observations.append({'method':method,'HV':{str(ref):float(hypervolume(front,(ref,)*3)) for ref in (1.25,1.5,2.0)},
                'IGDplus':float(igd_plus(front,empirical)),'rawObjectiveMin':(front*norm['scale']+norm['lower']).min(axis=0).tolist(),
                'frontSize':len(front),'successfulFE':receipt['successful'],'attemptedFE':receipt['attempted'],
                'timeInterruptedAttempts':receipt['timeInterruptedAttempts'],'searchSeconds':receipt['searchSeconds'],
                'checkpointFE':points[method]['fe'],'checkpointElapsedSeconds':points[method]['elapsedSeconds'],
                'stageFE':{key:receipt['search'].get(key+'.evaluations',0) for key in ('initialization','global','inter','intra')},
                'localVisitsOpened':max((r['visit'] for r in ledger),default=0),'localSlots':len(ledger),
                'forcedRestarts':sum(r['restarts'] for r in ledger),
                'rawGenerationCounter':receipt['search'].get('generations'),'completedDeepLocalBlocks':receipt['search'].get('deepLocal.completedBlocks'),
                'QgsUpdatesByPhysicalGroup':{key:value for key,value in receipt['search'].items() if key.startswith('qgs.') and key.endswith('.updates')},
                'checkpointQA':read(folder/'checkpoint-validation.json')['uniqueOfflineDecodes']})
        index={r['method']:r for r in observations};comparisons=[]
        for control in protocol['methods']:
            if control=='FULL_NAT':continue
            a,b=index['FULL_NAT'],index[control];den=a['IGDplus']+b['IGDplus']
            comparisons.append({'control':control,'HVEffectsPct':{str(ref):difference(a['HV'][str(ref)],b['HV'][str(ref)]) for ref in (1.25,1.5,2.0)},
                                'IGDplusSymmetricWorseningPct':200*(a['IGDplus']-b['IGDplus'])/den if den else 0.})
        compared={c['control']:c for c in comparisons}
        primary=lambda label:compared[label]['HVEffectsPct']['1.5']
        identify=all(primary(c) is not None for c in compared)
        competitiveness=identify and primary('NSGA_NAT')>=-1
        baselines=identify and all(primary(c)>=1 for c in ('LI_NAT','SHARE_BASE_NAT'))
        own=identify and primary('FULL_REPLAY')>=1
        duties=identify and primary('UNIFORM_NAT')>=1
        sharing=identify and primary('SYNC_NAT')>=-.5
        robust=identify and all(compared[c]['HVEffectsPct'][str(ref)] is not None and
            compared[c]['HVEffectsPct'][str(ref)]>=(-2 if c=='NSGA_NAT' else 0)
            for c in ('FULL_REPLAY','LI_NAT','SHARE_BASE_NAT')+('NSGA_NAT',) for ref in (1.25,2.0))
        auxiliary=all(compared[c]['IGDplusSymmetricWorseningPct']<=5 for c in ('FULL_REPLAY','NSGA_NAT','LI_NAT','SHARE_BASE_NAT'))
        levels.append({'budget':budget,'observations':observations,'comparisons':comparisons,
            'competitiveVsMatchedNsga':bool(competitiveness),'beatsLiAndSharingBase':bool(baselines),
            'naturalVsFixedGainGate':bool(own),'fourDutyGate':bool(duties),'sharingNoninferiorGate':bool(sharing),
            'referenceSensitivityGate':bool(robust),'auxiliaryGate':bool(auxiliary),
            'efficacyGate':bool(competitiveness and baselines and own and robust and auxiliary)})
    result={'stem':stem,'levels':levels,'sourceSeed':protocol['seed'],'efficacyGate':all(l['efficacyGate'] for l in levels),
        'fourDutyGate':all(l['fourDutyGate'] for l in levels),'sharingNoninferiorGate':all(l['sharingNoninferiorGate'] for l in levels),
        'limits':'Single newseed, two existingdevelopment instances. Natural regimes share LS rules, not realized local quotas. '
                 'TrueTIME fronts and separate500kFE runs; no postdeadline fronts, published-author replication or novelty claim.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,specs):
    results=[analyze_instance(root,s) for s in specs]
    sharing_gains=[]
    for result in results:
        sharing_gains.extend(next(c for c in l['comparisons'] if c['control']=='SYNC_NAT')['HVEffectsPct']['1.5'] for l in result['levels'])
    sharing=all(r['sharingNoninferiorGate'] for r in results) and all(v is not None for v in sharing_gains) and max(sharing_gains)>=.2
    worth=all(r['efficacyGate'] and r['fourDutyGate'] for r in results) and sharing
    out={'instances':results,'sharingGate':bool(sharing),'worthFreshSeedScreen':bool(worth),
        'scope':'Pre-registered one-seed diagnostic of the latest frozen search under natural stopping. '
                'A pass permits newseed development screening only; full goal/independent confirmation not achieved.'}
    write_once(root/'analysis.json',out);return out
