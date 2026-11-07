"""Zero-FE mapping parity against the actual native decomposition and independent Python."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from collections import Counter
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from pa_role_semantics_data import prepare,expected,ranking
from qpa_geometry_audit_inputs import JavaRandom

CONTRACT=ROOT/'research/gomea_reference_audit/PA_ROLE_SCHEDULE_SEMANTICS_V1.json'


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();pilot=Path(plan['sourcePilot']);geometry=Path(plan['sourceGeometry'])
        assert read(pilot/'independent-final-audit.json')['passed'] and digest(pilot/'independent-final-audit.json')==plan['pilotAuditSHA256']
        root=ROOT/'runs'/datetime.now().strftime('pa-role-schedule-semantics-%Y%m%d-%H%M%S-%f');root.mkdir();print('PA_ROLE_SCHEDULE_SEMANTICS_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before))
        populations=prepare(root,plan);source=root/'source';classes=root/'classes';source.mkdir();classes.mkdir()
        for name in ('PaRoleSchedule.java','PaRoleSemanticsRun.java'):shutil.copy2(ROOT/'src/algorithms/diagnostics/pa_roles'/name,source)
        for name in ('pa_role_semantics_data.py','run_pa_role_schedule_semantics.py'):shutil.copy2(Path(__file__).with_name(name),source)
        base=(pilot/'classpath.txt').read_text('utf-8-sig').strip();base=str(geometry/'classes')+';'+base
        execute(['java','-version'],root/'jdk-version.log')
        execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
        cp=str(classes)+';'+base;(root/'classpath.txt').write_text(cp,encoding='utf-8')
        write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()});write_once(root/'class-hashes.json',class_hashes(classes))
        observations=[];total=0
        for stem in ('20_8_5_1','100_2_3_1'):
            out=root/stem;out.mkdir();shutil.copytree(pilot/stem/'inputs',out/'inputs')
            command=['java','-Xms32m','-Xmx2g','-cp',cp,'org.uma.jmetal.util.research.modelglobal.PaRoleSemanticsRun',
                str(out/'inputs'/(stem+'.txt')),str(out/'inputs/RECONSTRUCTED-setup.txt'),str(root/(stem+'.tsv')),str(out)]
            write_once(out/'command.json',command);execute(command,out/'run.log',timeout=180)
            receipt=read(out/'receipt.json');verify_capture(receipt['identity'],cp)
            assert receipt['attemptedSearchFE']==receipt['objectiveBackendCalls']==receipt['dynamicDecoderCalls']==0
            for row in rows(out/'plans.jsonl'):
                population,=[p for p in populations if p['id']==row['population']];points=population['points']
                role,visit=expected(points,row['mode'],JavaRandom(plan['privateSeed']))
                assert row['roles']==role and row['visit']==visit and row['nativeVisit']==ranking(points)
                assert row['mainRNGBefore']==row['mainRNGAfter']
                assert sorted(visit)==list(range(100))
                if row['mode']=='FULL':
                    observations.append(dict(population=row['population'],evolved=population['evolved'],synthetic=population['synthetic'],
                        roleChanges=sum(a!=p['role'] for a,p in zip(role,points)),visitPositionChanges=sum(i!=v for i,v in enumerate(visit))))
                total+=1
        assert total==plan['bounds']['maximumPlans']==60 and protected()==before
        assert class_hashes(classes)==read(root/'class-hashes.json')
        evolved=[r for r in observations if r['evolved']];assert len(evolved)==2
        passed=all(r['roleChanges']>0 and r['visitPositionChanges']>0 for r in evolved)
        write_once(root/'analysis.json',dict(exactSemanticChecksPassed=True,necessaryNontrivialityPass=passed,observations=observations,
            plans=total,nativePartitions=10,knownRealCarriers=800,mathematicalRankingCarriers=200,newSearchFE=0,newDecoderCalls=0,
            decision='SEMANTIC_PARITY_ONLY_SEPARATE_ENGINEERING_REQUIRED' if passed else 'STOP_ROLE_SCHEDULE_NONTRIVIALITY',performanceProved=False,goalAchieved=False))
        write_once(root/'status.json',dict(status='COMPLETE',semanticParity=True,newSearchFE=0,newDecoderCalls=0,goalAchieved=False))
        print('PA_ROLE_SEMANTICS_PASS',total,observations,flush=True)


if __name__=='__main__':main()
