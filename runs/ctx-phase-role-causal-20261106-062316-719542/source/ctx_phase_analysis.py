"""Registered joint metrics at the intervened cycle, no control promotion or feedback."""
import numpy as np
from run_long_budget_bridge import write_once,nondominated,hypervolume,igd_plus
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage


def metric(points,norm,reference):
    front=nondominated(points);normal=(front-norm['lower'])/norm['scale']
    return dict(front=front.tolist(),HV={str(r):hypervolume(normal,(r,)*3) for r in (1.25,1.5,2.)},IGDplus=igd_plus(normal,reference))


def paired(a,b):
    den=a['IGDplus']+b['IGDplus'];cov=bidirectional_coverage(a['front'],b['front'])
    return dict(HVEffectPct={k:100*(a['HV'][k]/b['HV'][k]-1) for k in a['HV']},
        IGDplusSymmetricWorseningPct=200*(a['IGDplus']-b['IGDplus'])/den if den else 0.,
        coverage=cov,Cdelta=cov['C_A_B']-cov['C_B_A'])


def checks(row,hv,igd,c):
    return dict(HV=row['HVEffectPct']['1.5']>=hv,IGDplus=row['IGDplusSymmetricWorseningPct']<=igd,Cdelta=row['Cdelta']>=c)


def analyze_seed(records,norm,reference):
    values={}
    for arm,(_,_,events) in records.items():
        p=events['populations'];assert p[10,'SURVIVORS']['fe']==248700
        values[arm]={}
        for phase in ('PRE_GLOBAL','POST_GLOBAL','POST_LOCAL','SURVIVORS'):
            values[arm][phase]=metric([s['objectives'] for s in p[10,phase]['points']],norm,reference)
        values[arm]['ALL_PAID']=metric(p[10,'SURVIVORS']['allPaid'],norm,reference)
    comparisons={}
    for a,b in (('CR','RR'),('CR','CC'),('RC','RR'),('CC','RC'),('RR','RC')):
        comparisons[a+'_vs_'+b]={phase:paired(values[a][phase],values[b][phase]) for phase in values[a]}
    primary=comparisons['CR_vs_RR'];role=comparisons['CR_vs_CC'];primary_checks={};role_checks={}
    for phase in ('POST_LOCAL','SURVIVORS','ALL_PAID'):
        primary_checks[phase]=checks(primary[phase],-.1,-5. if phase=='POST_LOCAL' else 0.,.05 if phase=='POST_LOCAL' else 0.)
    role_checks['POST_LOCAL']=checks(role['POST_LOCAL'],.5,0.,0.);role_checks['ALL_PAID']=checks(role['ALL_PAID'],0.,0.,0.)
    return dict(values=values,comparisons=comparisons,primaryChecks=primary_checks,localRoleChecks=role_checks,
        primaryPass=all(all(r.values()) for r in primary_checks.values()),localRolePass=all(all(r.values()) for r in role_checks.values()))


def write_result(root,results,fees):
    passed=all(r['primaryPass'] and r['localRolePass'] for r in results)
    result=dict(seeds=results,**fees,pass_=passed,decision='CAUSAL_SIGNAL_ONLY_NEW_FULL_PROTOCOL_REQUIRED' if passed else 'STOP_FIXED_PHASE_ROLE_DECOUPLING',
        sameTimeTested=False,defaultMainlineChanged=False,previousStopsUnchanged=True,goalAchieved=False)
    write_once(root/'analysis.json',result);return result
