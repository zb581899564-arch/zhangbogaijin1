"""Zero-search independent metrics, recorded role counts and physical/survivor reconstruction."""
from pathlib import Path
import sys
from collections import Counter
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,nondominated
from ctx_phase_support import load_events,PILOT
from ctx_pipeline_analysis import cycle_summary
from ctx_gom_capability_support import heavy_folder
from qpa_capability_analysis import endpoint
from research.expansion_audit.metrics import grid_hv
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from run_qpa_complete_engineering import protected


def scalar_igd(front,reference):
    return float(np.mean([np.linalg.norm(np.maximum(front-p,0.),axis=1).min() for p in reference]))


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];result=read(root/'analysis.json')
    assert protected()==protocol['protectedBefore']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    classes=read(root/'class-hashes.json')
    assert class_hashes(root/'observer-classes')==classes['observer'] and class_hashes(root/'phase-classes')==classes['phase']
    for name,sha in read(root/'input-hashes.json').items():assert digest(root/'inputs'/name)==sha
    pilot=read(PILOT/'protocol.json');spec=next(s for s in pilot['instances'] if s['stem']==plan['instance']);norm=spec['normalization']
    ref=nondominated(np.vstack([(np.asarray(endpoint(PILOT/spec['stem']/str(s)/('FE500K-'+a),'FE500K',500000)['front'])-norm['lower'])/norm['scale'] for s in pilot['seeds'] for a in pilot['arms']]))
    catalog,=rows(heavy_folder(spec['stem'],'SHARE_CTX_GOM')/'catalog.jsonl');checks=[];maximum_hv_error=0.
    for item in result['seeds']:
        seed=item['seed'];native_events=load_events(root/str(seed)/'NATIVE')
        for arm in ('NATIVE','RR','RC','CR','CC'):
            folder=root/str(seed)/arm;receipt,=rows(folder/'run-receipt.jsonl');events=load_events(folder)
            assert receipt['attempted']==receipt['successful']==receipt['decoder']['dynamic.evaluations']==plan['runLimitFE']
            assert receipt['failed']==0
            for cycle in range(1,11):
                populations=events['populations'];e={phase:populations[cycle,phase] for phase in ('PRE_GLOBAL','POST_GLOBAL','POST_LOCAL','SURVIVORS')}
                e.update(selection=events['selection'][cycle],workspace=events['workspace'][cycle])
                cycle_summary(cycle,e,norm,ref,catalog['tuples'])
                if cycle<10:
                    for phase in e:
                        if phase not in ('selection','workspace'):assert e[phase]==native_events['populations'][cycle,phase]
                counts=Counter(p['preference'] for p in events['programs'] if p['cycle']==cycle)
                center_local=cycle==10 and arm in ('RC','CC')
                assert counts==(Counter(CENTER=100) if center_local else Counter(MAKESPAN=15,CENTER=55,ENERGY=15,WORKER_COST=15))
            center_global=arm in ('CR','CC')
            for group,role in ((1,'MAKESPAN'),(3,'ENERGY'),(4,'WORKER_COST')):
                assert receipt['search'][f'qgs.g{group}.preference.{role}']==(450 if center_global else 500)
                assert receipt['search'].get(f'qgs.g{group}.preference.CENTER',0)==(50 if center_global else 0)
            for stage,metric in item['values'][arm].items():
                normal=(np.asarray(metric['front'])-norm['lower'])/norm['scale']
                for r in (1.25,1.5,2.):
                    error=abs(grid_hv(normal,r)-metric['HV'][str(r)]);assert error<2e-10;maximum_hv_error=max(maximum_hv_error,error)
                assert abs(scalar_igd(normal,ref)-metric['IGDplus'])<2e-12
            checks.append(dict(seed=seed,arm=arm,tenCyclesPhysicalViewsAndSurvivalExact=True,firstNineCohortsEqual=True,effectivePhaseRoleCountsExact=True))
        for name,pairs in item['comparisons'].items():
            a,b=name.split('_vs_')
            for stage,pair in pairs.items():
                first=np.unique(np.array(item['values'][a][stage]['front']),axis=0);second=np.unique(np.array(item['values'][b][stage]['front']),axis=0)
                ab=sum(any(all(x<=y for x,y in zip(p,q)) for p in first) for q in second)
                ba=sum(any(all(x<=y for x,y in zip(p,q)) for p in second) for q in first)
                c=pair['coverage'];assert (ab,len(second),ba,len(first))==(c['coveredB'],c['totalB'],c['coveredA'],c['totalA'])
        assert item['primaryPass']==all(all(c.values()) for c in item['primaryChecks'].values())
        assert item['localRolePass']==all(all(c.values()) for c in item['localRoleChecks'].values())
    assert result['pass_']==all(s['primaryPass'] and s['localRolePass'] for s in result['seeds'])
    write_once(root/'independent-final-audit.json',dict(passed=True,checks=checks,maximumIndependentHVError=maximum_hv_error,
        allScalarIGDAndCoveredCountsAgree=True,defaultProtectedSourcesUnchanged=True,newSearchFE=0,newDecoderCalls=0))
    print('CTX_PHASE_AUDIT_PASSED',len(checks),maximum_hv_error)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())
