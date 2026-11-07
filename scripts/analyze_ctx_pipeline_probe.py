"""Rebuild complete recorded cycles and locate paid final-point availability without feedback."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,nondominated
from qpa_capability_analysis import endpoint
from ctx_gom_capability_support import heavy_folder
from ctx_gom_replay import raw_hash
from analyze_ctx_gom_stage_geometry import label,local_segments
from ctx_pipeline_analysis import cycle_summary,availability_summary

SOURCE=ROOT/'runs/ctx-gom-capability-20261106-051509-678987'
STEM='100_2_3_1';SEED=14910003


def targets_for(arm):
    target={};path=SOURCE/STEM/str(SEED)/('FE500K-'+arm)/'checkpoint-solutions.jsonl';segments=local_segments(STEM,arm)
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            p=json.loads(line)
            if p['checkpointKind']=='FE' and p['checkpoint']==500000:
                cycle=(p['bornFE']-101)//24860+1 if p['bornFE']>100 else 0
                target[raw_hash(p)]=dict(objectives=p['objectives'],bornFE=p['bornFE'],birthCycle=cycle,
                    origin=label(p['bornFE'],segments),censoredAtBudget=cycle>20)
    return target


def analyze_arm(folder,arm,norm,reference,catalog):
    targets=targets_for(arm);objective_keys={tuple(v['objectives']):k for k,v in targets.items()};found=set()
    cycles={};summaries=[];pending=[];last_survivors=None;counts=Counter();tail=None
    with (folder/'pipeline.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            e=json.loads(line);kind=e['kind'];counts[kind]+=1;cycle=e.get('cycle')
            if kind=='admission':
                p=e['point'];key=p['key']
                if tuple(p['objectives']) in objective_keys:
                    assert key==objective_keys[tuple(p['objectives'])]
                    target=targets[key];assert e['fe']==target['bornFE'];found.add(key)
                    if e['stage']=='LOCAL':pending.append(key)
            elif kind=='program':
                for key in pending:
                    targets[key]['returnedByBirthProgram']=e['point']['key']==key
                    targets[key]['birthProgramEndFE']=e['fe']
                pending=[]
            elif kind in ('workspace','selection'):
                cycles.setdefault(cycle,{})[kind]=e
            elif kind=='population':
                phase=e['phase'];keys={p['key'] for p in e['points']}
                for key in keys&targets.keys():
                    t=targets[key];t.setdefault('firstCohortFE',e['fe'])
                    if cycle==t['birthCycle'] and phase=='POST_LOCAL':t['atLocalExit']=True
                    if cycle==t['birthCycle'] and phase=='SURVIVORS':t['atSurvivors']=True
                for p in e['memory']:
                    key=p['key']
                    if key in targets:
                        t=targets[key];t.setdefault('firstTeacherMemoryFE',e['fe'])
                        if cycle==t['birthCycle'] and phase=='SURVIVORS':t['inTeacherMemoryAtBirthCycle']=True
                if phase=='INITIAL':assert e['fe']==100 and len(e['points'])==100
                else:cycles.setdefault(cycle,{})[phase]=e
                if phase=='PRE_GLOBAL' and last_survivors is not None:
                    assert [(p['key'],p['branch']) for p in e['points']]==last_survivors
                if phase=='SURVIVORS':
                    summaries.append(cycle_summary(cycle,cycles.pop(cycle),norm,reference,catalog))
                    last_survivors=[(p['key'],p['branch']) for p in e['points']]
            elif kind=='finish':tail=e
            else:raise AssertionError(kind)
    assert found==set(targets) and not pending and len(summaries)==20 and tail['fe']==500000 and tail['passes']==20
    assert set(cycles)=={21} and set(cycles[21])=={'PRE_GLOBAL'}
    return dict(arm=arm,cycles=summaries,finalPointAvailability=availability_summary(targets),
        finalPointDetails=[dict(key=k,**v) for k,v in targets.items()],eventCounts=dict(counts),
        partialFinalCycle='Cycle21hasPRE_GLOBALonly;notimputedcomplete',allFinalAdmissionsMatched=True,
        allCyclesPDDRQuotaFeesAndPhysicalViewsValidated=True)


def main(root):
    assert read(root/'acceptance.json')['passed'];plan=read(SOURCE/'protocol.json');spec=next(s for s in plan['instances'] if s['stem']==STEM)
    normal=spec['normalization'];fronts=[np.asarray(endpoint(SOURCE/STEM/str(s)/('FE500K-'+a),'FE500K',500000)['front'],float) for s in plan['seeds'] for a in plan['arms']]
    reference=nondominated(np.vstack([(p-normal['lower'])/normal['scale'] for p in fronts]))
    catalog,=rows(heavy_folder(STEM,'SHARE_CTX_GOM')/'catalog.jsonl')
    results=[analyze_arm(root/STEM/(arm+'-OBSERVED'),arm,normal,reference,catalog['tuples']) for arm in ('SHARE_CTX_GOM','UNIFORM_CTX_GOM')]
    write_once(root/'pipeline-analysis.json',dict(instances=results,referenceSize=len(reference),newSearchFE=0,newDecoderCalls=0,
        caution='Availability of full exact states only; own continuation and latent genes may retain information; observation does not prove gain from an archive selector or different survivor',
        defaultMainlineChanged=False,goalAchieved=False));print('CTX_PIPELINE_ANALYSIS_PASSED',root)


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
