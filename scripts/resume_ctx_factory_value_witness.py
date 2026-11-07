"""Recover only the missing QA entry class, preserving all previous source replays and scores."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil
import sys
import time
import numpy as np

from run_long_budget_bridge import ROOT,read,write_once,execute,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from ctx_phase_analysis import metric
from ctx_factory_value_analysis import decide
from run_ctx_factory_value import finish_decision


def main(evidence):
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        started=time.perf_counter();previous=read(evidence/'protocol.json');counts=read(evidence/'offline-counts.json')
        assert read(evidence/'physics-acceptance.json')['status']=='PASS'
        assert 'ClassNotFoundException: research.dynamic.PoolAssemblyCheckRun' in (evidence/'witness.log').read_text('utf-8')
        assert not (evidence/'witness-validation.json').exists() and protected()==previous['protectedBefore']
        root=evidence/datetime.now().strftime('witness-recovery-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('FACTORY_WITNESS_RECOVERY',root,flush=True)
        accepted_names=('protocol.json','factory-records.jsonl','query-pools.jsonl','oracle-cases.json','oracle-enumeration.json',
                        'source-points.json','metric-context.json','backgrounds.json','witnesses.tsv','witnesses.json','offline-counts.json')
        accepted={name:digest(evidence/name) for name in accepted_names}
        write_once(root/'protocol.json',dict(version='FACTORY_VALUE_WITNESS_CLASSPATH_RECOVERY-v1',evidenceRoot=str(evidence.resolve()),
            reason='QA entry source was present in workspace but omitted from frozen capability classpath; original launch failed before any decode',
            priorWitnessFullDecodes=0,noNewOracleScoring=True,noNewSampling=True,noScientificGateChange=True,acceptedEvidence=accepted,
            protectedBefore=protected(),extraSearchFE=0))
        source=root/'source';classes=root/'classes';source.mkdir();classes.mkdir()
        shutil.copy2(ROOT/'src/algorithms/diagnostics/PoolAssemblyCheckRun.java',source)
        shutil.copy2(Path(__file__),source)
        base=(evidence/'classpath.txt').read_text('utf-8-sig').strip();cp=str(classes)+';'+base
        execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),str(source/'PoolAssemblyCheckRun.java')],root/'compile.log')
        write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()});write_once(root/'class-hashes.json',class_hashes(classes))
        (root/'classpath.txt').write_text(cp,encoding='utf-8')
        command=read(evidence/'witness-command.json');command[command.index('-cp')+1]=cp;command[-2]=str(root/'witness-validation.json')
        write_once(root/'witness-command.json',command);execute(command,root/'witness.log',timeout=600)
        qa=read(root/'witness-validation.json');assert qa['status']=='PASS'
        assert qa['attemptedOfflineDecodes']==qa['passedOfflineDecodes']==counts['distinctWitnessFullDecodeRequests']<=200
        identity=['java','-cp',cp,'research.dynamic.ClassResolutionProbe','research.dynamic.PoolAssemblyCheckRun',
                  *['org.uma.jmetal.util.research.model.'+n for n in ('DynamicDecoder','DynamicPhysics','DynamicSchedule','DynamicValidator')]]
        execute(identity,root/'loaded-identity.json');write_once(root/'identity-verified.json',verify_capture(read(root/'loaded-identity.json'),cp))
        context=read(evidence/'metric-context.json');norm=context['normalization'];reference=np.array(context['empiricalReference'])
        baseline={cycle:metric(front,norm,reference) for cycle,front in read(evidence/'backgrounds.json').items()}
        result=decide(read(evidence/'oracle-cases.json'),baseline);finish_decision(result,read(evidence/'source-points.json'))
        physics=read(evidence/'physics-acceptance.json');recovery=previous['engineeringRecovery']
        cumulative=recovery['priorKnownSourceFullDecodes']+physics['attemptedKnownSourceFullDecodes']+qa['attemptedOfflineDecodes']
        assert cumulative<=recovery['maximumCumulativeFullDecodes'] and protected()==previous['protectedBefore']
        for name,sha in accepted.items():assert digest(evidence/name)==sha
        result.update(evidenceRoot=str(evidence.resolve()),knownSourceFullDecodes=physics['attemptedKnownSourceFullDecodes'],
            newCompositionWitnessFullDecodes=qa['attemptedOfflineDecodes'],
            engineeringRecovery=dict(**recovery,actualCumulativeFullDecodes=cumulative),
            **{k:v for k,v in counts.items() if k not in ('extraSearchFE','sourcePoints','distinctWitnessFullDecodeRequests')},
            retainedControllerWallSeconds=read(evidence/'status.json')['wallSeconds'],witnessRecoveryWallSeconds=time.perf_counter()-started)
        write_once(root/'analysis.json',result);write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],extraSearchFE=0,goalAchieved=False))
        print('FACTORY_VALUE_RECOVERED',result['decision'],result['generalValue'],result['roleSupply'],flush=True)


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
