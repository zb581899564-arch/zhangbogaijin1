"""Execute the registered offline factory-jobset value gate, with zero new search FE."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil
import time

from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import resolve_class,verify_capture
from paired_survival_bench import class_hashes
from ctx_factory_value_data import prepare
from ctx_factory_value_analysis import oracle
from ctx_role_factory_contract import factory_parts

CONTRACT=ROOT/'research/gomea_reference_audit/CTX_FACTORY_JOBSET_VALUE_V1.json'


def build(root,base):
    source=root/'source';classes=root/'classes';source.mkdir();classes.mkdir()
    for p in (ROOT/'src/algorithms/diagnostics/factory_value').glob('*.java'):shutil.copy2(p,source)
    for name in ('ctx_factory_value_data.py','ctx_factory_value_analysis.py','run_ctx_factory_value.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*[str(p) for p in source.glob('*.java')]],root/'compile.log')
    cp=str(classes)+';'+base;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    execute(['java','-version'],root/'jdk-version.log')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json',class_hashes(classes));return cp


def finish_decision(result,points):
    rows_=result['comparisons'];byid={r['request']:r for r in rows_}
    context_ids={factory_parts(points[byid[q]['parent']])[0] for q in result['generalValue']['materialRequestIDs']}
    result['generalValue']['distinctReceivingFAContexts']=len(context_ids)
    general=result['generalValue']['fraction']>=.2 and len(context_ids)>=2
    result['generalValuePass']=general
    result['decision']='ALLOW_SEPARATE_SECOND_SEED_REPLICATION_ONLY' if general and result['roleSupplyPass'] else (
        'ORDINARY_CONDITIONAL_VALUE_ONLY_NO_FOUR_ROLE_CLAIM' if general else 'STOP_FIXED_JOBSET_COHORT_MEMORY_VALUE')


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        started=time.perf_counter();plan=read(CONTRACT);before=protected()
        root=ROOT/'runs'/datetime.now().strftime('ctx-factory-jobset-value-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('CTX_FACTORY_VALUE_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before))
        try:
            sources={s:Path(plan['source'+s]) for s in ('S','U')}
            commands={s:read(p/'command.json') for s,p in sources.items()}
            cp_base=commands['S'][commands['S'].index('-cp')+1]
            print('SOURCE_CONFIG', {s:[v for v in c if v.startswith('-Dresearch.group.mode=')] for s,c in commands.items()},flush=True)
            names=['org.uma.jmetal.util.research.cooperation.'+n for n in ('FactoryPool','FactoryRecord','FamilyContexts')]
            names+=['org.uma.jmetal.util.research.model.'+n for n in ('DynamicDecoder','DynamicPhysics','DynamicSchedule','DynamicValidator')]
            for name in names:
                assert resolve_class(cp_base,name)['sha256']==resolve_class(commands['U'][commands['U'].index('-cp')+1],name)['sha256']
            write_once(root/'source-identities.json',{s:{n:digest(sources[s]/n) for n in ('pipeline.jsonl','run-receipt.jsonl','command.json')} for s in sources})
            phase=Path(plan['phaseStopSource']);shutil.copytree(phase/'inputs',root/'inputs')
            write_once(root/'input-hashes.json',{p.name:digest(p) for p in (root/'inputs').iterdir()})
            points=prepare(root,plan);cp=build(root,cp_base);print('KNOWN_POINT_REPLAYS',len(points),flush=True)
            java=['java','-Xms32m','-Xmx2g','-cp',cp]
            inputs=[str(root/'inputs'/name) for name in (plan['instance']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt')]
            command=[*java,'org.uma.jmetal.util.research.cooperation.FactoryValueRun',*inputs,str(root/'known-points.tsv'),str(root/'events.tsv'),str(root)]
            write_once(root/'physics-command.json',command);execute(command,root/'physics.log',timeout=600)
            physics=read(root/'physics-acceptance.json');assert physics['status']=='PASS'
            assert physics['attemptedKnownSourceFullDecodes']==physics['passedKnownSourceFullDecodes']==len(points)
            write_once(root/'identity-verified.json',verify_capture(physics['classIdentity'],cp))
            print('FACTORY_POOLS_READY',physics['deduplicatedRequests'],physics['cases'],flush=True)
            result=oracle(root);finish_decision(result,points)
            witness_command=[*java,'research.dynamic.PoolAssemblyCheckRun',*inputs,str(root/'witnesses.tsv'),str(root/'witness-validation.json'),'EXACT']
            write_once(root/'witness-command.json',witness_command);execute(witness_command,root/'witness.log',timeout=600)
            witnesses=read(root/'witness-validation.json');counts=read(root/'offline-counts.json')
            assert witnesses['status']=='PASS' and witnesses['passedOfflineDecodes']==counts['distinctWitnessFullDecodeRequests']
            assert witnesses['attemptedOfflineDecodes']<=plan['maximumNewCompositionWitnessDecodes']
            assert len(points)+witnesses['attemptedOfflineDecodes']<=plan['maximumTotalFullDecodes']
            assert protected()==before and class_hashes(root/'classes')==read(root/'class-hashes.json')
            for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
            result.update(knownSourceFullDecodes=len(points),newCompositionWitnessFullDecodes=witnesses['attemptedOfflineDecodes'],
                **{k:v for k,v in counts.items() if k not in ('extraSearchFE','sourcePoints','distinctWitnessFullDecodeRequests')},
                wallSeconds=time.perf_counter()-started)
            write_once(root/'analysis.json',result)
            write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],extraSearchFE=0,goalAchieved=False))
            print('CTX_FACTORY_VALUE_COMPLETE',result['decision'],result['generalValue'],result['roleSupply'],flush=True)
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),extraSearchFE=0,goalAchieved=False));raise


if __name__=='__main__':main()
