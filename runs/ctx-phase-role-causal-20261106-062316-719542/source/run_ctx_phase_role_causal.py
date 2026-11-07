"""Execute the frozen one-cycle2x2 causal protocol without changing any default algorithm."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
import shutil
import numpy as np

from run_long_budget_bridge import ROOT,read,write_once,controller_lock,nondominated
from ctx_phase_build import CONTRACT,PROBE,build
from ctx_phase_support import PILOT,counts,run_one,invariants
from ctx_phase_analysis import analyze_seed,write_result
from run_qpa_complete_engineering import protected
from research.semantic_repair.evidence import digest
from qpa_capability_analysis import endpoint


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);assert digest(PROBE/'pipeline-analysis.json')==plan['sourceAnalysisSHA256']
        root=ROOT/'runs'/datetime.now().strftime('ctx-phase-role-causal-%Y%m%d-%H%M%S-%f');root.mkdir();before=protected()
        print('CTX_PHASE_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before))
        shutil.copytree(PROBE/plan['instance']/'inputs',root/'inputs')
        write_once(root/'input-hashes.json',{p.name:digest(p) for p in (root/'inputs').iterdir() if p.is_file()})
        try:
            native,changed=build(root);all_records={};verified=[]
            for seed in plan['seeds']:
                records={}
                for arm in ('NATIVE','RR','RC','CR','CC'):records[arm]=run_one(root,native if arm=='NATIVE' else changed,seed,arm,plan)
                verified.append(dict(seed=seed,**invariants(records,plan)));all_records[seed]=records
            actual=counts(root);assert actual['attemptedFE']==actual['successfulFE']==plan['plannedActualFE']<=plan['maximumActualAttemptedFE'] and actual['failedFE']==0
            assert protected()==before
            for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
            write_once(root/'engineering-acceptance.json',dict(passed=True,seeds=verified,**actual))
            pilot_plan=read(PILOT/'protocol.json');spec=next(s for s in pilot_plan['instances'] if s['stem']==plan['instance']);norm=spec['normalization']
            fronts=[np.array(endpoint(PILOT/plan['instance']/str(s)/('FE500K-'+a),'FE500K',500000)['front']) for s in pilot_plan['seeds'] for a in pilot_plan['arms']]
            reference=nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts]))
            results=[dict(seed=seed,**analyze_seed(all_records[seed],norm,reference)) for seed in plan['seeds']]
            result=write_result(root,results,actual)
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**counts(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],**actual,goalAchieved=False))
        print('CTX_PHASE_COMPLETE',result['decision'],actual,flush=True)


if __name__=='__main__':main()
