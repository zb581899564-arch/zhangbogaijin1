"""Execute the frozen neutral-view model/proposal audit, with a forbidden objective backend."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,write_once,execute,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture
from qpa_neutral_geometry_data import prepare
from qpa_neutral_geometry_analysis import summarize

CONTRACT=ROOT/'research/gomea_reference_audit/QPA_NEUTRAL_GEOMETRY_V1.json'


def build(root,plan):
    source=root/'source';classes=root/'classes';source.mkdir();classes.mkdir()
    for p in (ROOT/'src/algorithms/diagnostics/qpa_geometry').glob('*.java'):shutil.copy2(p,source)
    for name in ('run_qpa_neutral_geometry.py','qpa_neutral_geometry_data.py','qpa_neutral_geometry_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(Path(plan['sourceQpa'])/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*[str(p) for p in source.glob('*.java')]],root/'compile.log')
    cp=str(classes)+';'+base;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()});write_once(root/'class-hashes.json',class_hashes(classes));return cp


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();pilot=Path(plan['sourcePilot'])
        assert read(pilot/'independent-final-audit.json')['passed'] and digest(pilot/'independent-final-audit.json')==plan['sourcePilotAuditSHA256']
        root=ROOT/'runs'/datetime.now().strftime('qpa-neutral-geometry-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('QPA_NEUTRAL_GEOMETRY_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before,
            execution=dict(paNoiseSeed=2026110601,referenceSeed=2026110602,proxyGuardSeed=2026110603,
                           interleavingPRNG='Python random.Random(seed).shuffle on factory label multiset',
                           modelCarriers='Known physically identical points; guardlimit1 unused, objective backend forbidden',initialModelCarriers=8800)))
        try:
            populations=prepare(root,plan);cp=build(root,plan)
            for stem in ('20_8_5_1','100_2_3_1'):
                out=root/stem;out.mkdir();shutil.copytree(pilot/stem/'inputs',out/'inputs')
                write_once(out/'input-hashes.json',{p.name:digest(p) for p in (out/'inputs').iterdir()})
                cmd=['java','-Xms32m','-Xmx2g','-Dresearch.pa.traceIdentity=false','-cp',cp,
                    'org.uma.jmetal.util.research.modelglobal.QpaNeutralGeometryRun',str(out/'inputs'/(stem+'.txt')),
                    str(out/'inputs/RECONSTRUCTED-setup.txt'),str(root/(stem+'-views.tsv')),str(root/'pairs.tsv'),str(out)]
                write_once(out/'command.json',cmd);print('NEUTRAL_MODEL_AND_INTEGER_PROPOSALS',stem,flush=True);execute(cmd,out/'run.log',timeout=600)
                receipt=read(out/'receipt.json');assert receipt['status']=='PASS'
                for key in ('attemptedSearchFE','successfulSearchFE','failedSearchFE','objectiveBackendCalls','dynamicDecoderCalls'):assert receipt[key]==0
                write_once(out/'identity-verified.json',verify_capture(receipt['identity'],cp))
            assert protected()==before and class_hashes(root/'classes')==read(root/'class-hashes.json')
            result=summarize(root,populations,plan)
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),receipts={s:read(root/s/'receipt.json') for s in ('20_8_5_1','100_2_3_1') if (root/s/'receipt.json').exists()},goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],newSearchFE=0,newDecoderCalls=0,goalAchieved=False))
        print('NEUTRAL_GEOMETRY_COMPLETE',result['decision'],result['unscoredCompleteProposalConstructions'],flush=True)
        for population in result['populations']:
            print(population['population'],population['evolved'],population['lowFOSJaccardViews'],population['aggregatePhysicalProposalChangedFraction'],flush=True)


if __name__=='__main__':main()
