"""Zero-FE reachability of specific encoded resource tuples, not an objective-space impossibility proof."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
from datetime import datetime
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock,hypervolume
from pa_capability_support import ARMS,ENGINE

SOURCE=ROOT/'runs/pa-base-qualification-20261105-180835-751659'


def by_job(point):
    n=len(point['JS']);assert sorted(point['JS'])==list(range(n))
    assert all(len(point[k])==n for k in ('FA','MA','WA'))
    result=[None]*n
    for j,f,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA']):result[j]=(f,m,w)
    return result


def final_points(folder):
    return [p for p in rows(folder/'checkpoint-solutions.jsonl') if p['checkpointKind']=='FE' and p['checkpoint']==500000]


def context(spec,seed):
    stem=spec['stem'];folder=SOURCE/stem/str(seed);initial=rows(folder/'FE500K-PA_JOINT/initial-population.jsonl')
    assert len(initial)==100;n=len(initial[0]['JS']);alleles=[set() for _ in range(n)]
    catalog,=rows(ENGINE/stem/'main/audit/catalog.jsonl');domain=set(map(tuple,catalog['tuples']))
    for point in initial:
        for j,tuple_ in enumerate(by_job(point)):assert tuple_ in domain;alleles[j].add(tuple_)
    covered=[len(a)/len(domain) for a in alleles];norm=spec['normalization']
    normalize=lambda points:(np.array([p['objectives'] for p in points],float).reshape(-1,3)-norm['lower'])/norm['scale']
    own=final_points(folder/'FE500K-PA_JOINT');front=normalize(own);base=hypervolume(front,(1.5,)*3);observations=[]
    for arm in ARMS:
        points=final_points(folder/('FE500K-'+arm));inside=[];outside=[];missing=[]
        for point in points:
            absent=[j for j,t in enumerate(by_job(point)) if t not in alleles[j]]
            (outside if absent else inside).append(point);missing.append(len(absent))
        if arm.startswith('PA_'):assert not outside,'PA violated its resource-allele closure'
        full_gain=max(0.,hypervolume(np.vstack([front,normalize(points)]),(1.5,)*3)-base)
        inside_gain=max(0.,hypervolume(np.vstack([front,normalize(inside)]),(1.5,)*3)-base)
        outside_only=max(0.,full_gain-inside_gain)
        observations.append({'arm':arm,'finalPoints':len(points),'pointsWithUnseenJobTuple':len(outside),
            'fractionWithUnseenJobTuple':len(outside)/len(points),'meanUnseenJobsPerPoint':float(np.mean(missing)),
            'maximumUnseenJobs':max(missing),'unionGainOverPaHV':full_gain,'unionGainRelativePaPct':100*full_gain/base,
            'gainBeyondInsideDomainPoints':outside_only,
            'shareOfObservedGapRequiringThoseSpecificOutsideEncodings':outside_only/full_gain if full_gain>1e-15 else None,
            'notProofOfUnreachableObjectiveValues':True})
    return {'stem':stem,'seed':seed,'legalResourceTuplesPerJob':len(domain),'initialTupleCoverageByJob':covered,
        'meanInitialTupleCoverage':float(np.mean(covered)),'minInitialTupleCoverage':min(covered),'maxInitialTupleCoverage':max(covered),
        'observations':observations,'specificEncodedStateRestrictionProved':True,'causalPerformanceExplanationProved':False}


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        assert read(SOURCE/'status.json')['status']=='COMPLETE'
        root=ROOT/'runs'/datetime.now().strftime('pa-allele-domain-audit-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PA_ALLELE_DOMAIN_AUDIT_ROOT',root,flush=True)
        write_once(root/'protocol.json',{'source':str(SOURCE),'newSearchFE':0,'decoderCalls':0,
            'question':'Does atomic FMW donation restrict this ordinary adapter to initial per-job resource tuples; where do competing final encodings sit relative to that domain?',
            'proof':'Induction: initial tuple sets; each move copies a complete donor tuple for the same job or retains parent; reencoding changes no tuple; repair is asserted0. NeitherPAarm introduces new tuple alleles.',
            'sampling':'All prescribed500kterminal checkpoint points, all6arms, both registered instances andfreshseeds; no outcome-based subsampling',
            'limits':'Specific genotype reachability only. Alternative reachable genotype may realize same objectives. No full objective-domain or causal failure proof, no new variant or permission to tune stopped versions',
            'defaultMainlineChanged':False,'goalAchieved':False})
        try:
            plan=read(SOURCE/'protocol.json');results=[context(spec,seed) for spec in plan['instances'] for seed in plan['seeds']]
            write_once(root/'analysis.json',{'contexts':results,'paClosureChecksPass':True,'newSearchFE':0,'decoderCalls':0,
                'causalPerformanceExplanationProved':False,'newAlgorithmOrOperatorImplemented':False,'goalAchieved':False})
        except BaseException as error:
            write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','error':repr(error),'newSearchFE':0,'decoderCalls':0});raise
        write_once(root/'status.json',{'status':'COMPLETE','newSearchFE':0,'decoderCalls':0,'goalAchieved':False})
        print('PA_ALLELE_DOMAIN_AUDIT_COMPLETE',[(r['stem'],r['seed'],r['meanInitialTupleCoverage']) for r in results],flush=True)


if __name__=='__main__':main()
