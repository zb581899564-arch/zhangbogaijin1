"""Paid preflight: full default trajectory equivalence, common fresh initialization and plain/deep separation."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
from datetime import datetime
import shutil
from pathlib import Path

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock
from pa_capability_support import build,run_case,initial_key,fees,ARMS,ENGINE,SOURCE


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        root=ROOT/'runs'/datetime.now().strftime('pa-capability-interfaces-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PA_CAPABILITY_INTERFACES_ROOT',root,flush=True);completed=[];equivalence=[]
        write_once(root/'protocol.json',{'purpose':'Interfaces/observation equivalence only, no scientific ranking',
            'seed':13630003,'plannedSuccessfulFE':59400,'equivalence':'Both existing2generation complete paid digests with hashes/fullQA disabled, new identity subset policy defaults',
            'initialization':'6arms x2instances x100newly generated paid initial vectors, same existing initializer, family guards released for ordinary methods',
            'initialRoles':'PA creation order slots0..14M,15..69CENTER,70..84E,85..99W; stable across generations, no post-outcome sorting',
            'plainVsDeep':'5200FE each on20case, plain must have0localFE and deep must havepositive localFE after5000globaloffspring',
            'clock':'All arm-specific constructors run inside the common RunContext clock; no scientific time claim',
            'defaultMainlineChanged':False,'goalAchieved':False})
        try:
            cp=build(root)
            for stem in ('20_8_5_1','100_2_3_1'):shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
            for stem,limit in [('20_8_5_1',7900),('100_2_3_1',39900)]:
                source=SOURCE/stem/'11730007/sources.tsv'
                out,receipt=run_case(root,cp,stem,'PA_JOINT','PARITY',limit,13630003,audit=True,source_tsv=source);completed.append((out,receipt))
                old,=rows(ENGINE/stem/'main/audit/receipt.jsonl')
                assert receipt['paidSHA256']==old['paidSHA256'] and receipt['search']['completeGenerations']==2
                equivalence.append({'stem':stem,'successfulFE':limit,'paidSHA256':receipt['paidSHA256'],'allPaidEncodingsAndObjectivesEqual':True})
            for stem in ('20_8_5_1','100_2_3_1'):
                expected=None
                for arm in ARMS:
                    out,receipt=run_case(root,cp,stem,arm,'INIT-'+arm,100,13630003,audit=True);completed.append((out,receipt))
                    key=initial_key(out);assert len(key)==100
                    if expected is None:expected=key
                    else:assert key==expected,'Common initialization mismatch'
            for arm in ('NSGA2_PLAIN','NSGA2_DEEP'):
                out,receipt=run_case(root,cp,'20_8_5_1',arm,'DUE-'+arm,5200,13630003,audit=True);completed.append((out,receipt))
                local=sum(receipt['search'].get(stage+'.evaluations',0) for stage in ('inter','intra'))
                assert (local==0) if arm=='NSGA2_PLAIN' else (local>0)
            actual=fees(completed);assert actual['successfulFE']==59400 and actual['failedAttempts']==0
            write_once(root/'analysis.json',{'interfacePass':True,'equivalence':equivalence,'commonInitial100EqualAllArmsBothInstances':True,
                'plainDeepSeparationProved':True,**actual,'scientificPerformanceProved':False,'goalAchieved':False})
        except BaseException as error:
            write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','error':repr(error),'completedRuns':len(completed),**fees(completed)});raise
        write_once(root/'status.json',{'status':'COMPLETE','interfacePass':True,**actual,'goalAchieved':False})
        print('PA_CAPABILITY_INTERFACES_COMPLETE',actual,flush=True)


if __name__=='__main__':main()
