"""Frozen six-source zero-FE capacity audit; every source decision stays untouched."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil
import time
import sys
import scipy
import numpy

from run_long_budget_bridge import ROOT,read,write_once,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import resolve_class
from pa_archive_parent_replay import analyze

CONTRACT=ROOT/'research/gomea_reference_audit/PA_ARCHIVE_PARENT_CAPACITY_V1.json'


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();root=ROOT/'runs'/datetime.now().strftime('pa-archive-parent-capacity-%Y%m%d-%H%M%S-%f')
        root.mkdir();print('PA_ARCHIVE_PARENT_CAPACITY_ROOT',root,flush=True);start=time.monotonic()
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before))
        source=root/'source';source.mkdir()
        for name in (Path(__file__).name,'pa_archive_parent_math.py','pa_archive_parent_replay.py','pa_regional_replay.py','pa_population_replay.py','pa_population_state_checks.py'):
            shutil.copy2(Path(__file__).with_name(name),source)
        write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
        engine=Path(plan['sourceEngineering']);science=Path(plan['precedingScience'])
        assert digest(engine/'independent-final-audit.json')==plan['sourceEngineeringAuditSHA256']
        assert digest(science/'independent-final-audit.json')==plan['precedingScienceAuditSHA256']
        engineering_plan=read(engine/'protocol.json')['contract'];opportunity=read(Path(engineering_plan['opportunityRoot'])/'protocol.json')['contract']
        scales={s['instance']:s['scale'] for s in opportunity['cases']};cases=[]
        cp=(engine/'classpath.txt').read_text('utf-8-sig').strip()
        write_once(root/'runtime.json',dict(python=sys.version,executable=sys.executable,numpy=numpy.__version__,scipy=scipy.__version__,
            sourceExternalArchiveClass=resolve_class(cp,'org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive'),
            externalArchiveSourceSHA256=digest(ROOT/'runs/night-research-H1-20261103-010138-848045/source/src/java/runtime/ThreeObjectiveArchive.java')))
        try:
            for index,spec in enumerate(plan['cases']):
                folder=Path(spec['source'])
                for name,sha in spec['sourceHashes'].items():assert digest(folder/name)==sha
                assert read(folder/'regional-independent-replay.json')['passed']
                case=analyze(spec,scales[spec['instance']],plan)
                name=f"case-{index+1}-{spec['instance']}-{spec['mode']}.json";write_once(root/name,case)
                row={k:case[k] for k in ('instance','mode','primary','paidRowsReplayed','knownMixedGenomesRebuilt','neutralViewsVerified','sourcePaidSHA256','summary')}
                row['evidence']=name;cases.append(row)
                print('ARCHIVE_PARENT_CASE',spec['instance'],spec['mode'],case['summary'],flush=True)
            assert protected()==before
            general=all(c['summary']['generalPass'] for c in cases if c['primary']);special=all(c['summary']['specialistSupplyPass'] for c in cases if c['primary'])
            result=dict(cases=cases,generalCapacityPass=general,specialistCapacityPass=special,
                decision='STOP_FIXED_ARCHIVE_PARENT_CAPACITY' if not general else 'GENERAL_AND_SPECIAL_CAPACITY_ONLY' if special else 'ORDINARY_ARCHIVE_CAPACITY_ONLY_NO_SPECIAL_SUPPLY',
                existingPaidRowsReplayed=sum(c['paidRowsReplayed'] for c in cases),knownMixedGenomesRebuilt=sum(c['knownMixedGenomesRebuilt'] for c in cases),
                centerPrograms=sum(c['summary']['centerPrograms'] for c in cases),seconds=time.monotonic()-start,
                newSearchFE=0,newObjectiveQueries=0,newDecoderCalls=0,defaultMainlineChanged=False,previousStopsUnchanged=True,goalAchieved=False)
            assert result['existingPaidRowsReplayed']==plan['limits']['existingPaidRowsToReplay'] and result['centerPrograms']==plan['limits']['centerPrograms']
            write_once(root/'analysis.json',result)
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),completedCases=len(cases),newSearchFE=0,newDecoderCalls=0,goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],newSearchFE=0,newDecoderCalls=0,goalAchieved=False))
        print('PA_ARCHIVE_PARENT_CAPACITY_COMPLETE',result['decision'],result['existingPaidRowsReplayed'],flush=True)


if __name__=='__main__':main()
