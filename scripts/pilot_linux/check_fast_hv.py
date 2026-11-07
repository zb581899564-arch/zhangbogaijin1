"""Offline HV equivalence on fixtures and every real checkpoint; zero search FE."""
from pathlib import Path
import argparse
import math
import platform
import sys
import time
import numpy as np
import moocore

for parent in Path(__file__).resolve().parents:
    if (parent/'research/pilot_evaluation').is_dir():
        sys.path.insert(0,str(parent));break

from exact_hv import exact_hv
from run_support import read,rows,write
from research.dynamic_benchmark.metrics import hypervolume
from research.pilot_evaluation import ObjectiveScale,stage_hv_telescope


def check(root):
    if platform.system()!='Linux':raise RuntimeError('Linux only')
    start=time.perf_counter();count=0;maximum=0.0
    plan=read(root/'protocol.json')
    for spec in plan['instances']:
        scale=np.asarray(spec['normalization']['scale'])
        for path in sorted((root/'science'/spec['stem']).glob('*/*/anytime.jsonl')):
            for row in rows(path):
                if not row['reached'] or row['checkpointKind']!='FE':continue
                front=np.asarray(row['front'])/scale
                for r in [1.25,1.5,2.0]:
                    a,b=exact_hv(front,[r]*3),hypervolume(front,[r]*3)
                    maximum=max(maximum,abs(a-b));count+=1
                    assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-12),(path,r,a,b)
    generator=np.random.default_rng(20261106)
    events=[dict(event=i+1,objectives=p.tolist(),stage=('GLOBAL' if i%2 else 'LOCAL'),source='fixture',sharing=False)
            for i,p in enumerate(generator.uniform(-.1,1.6,(100,3)))]
    events.extend([dict(events[0],event=101),dict(event=102,objectives=[0.,0.,0.],stage='LOCAL',source='fixture',sharing=False)])
    options=dict(scale=ObjectiveScale((0,0,0),(1,1,1)),hv_reference=[1.5]*3)
    slow=stage_hv_telescope(events,**options)
    fast=stage_hv_telescope(events,**options,hv_calculator=exact_hv)
    for a,b in zip(slow['events'],fast['events']):
        assert math.isclose(a['hv_after'],b['hv_after'],rel_tol=1e-11,abs_tol=1e-12)
        assert math.isclose(a['delta_hv'],b['delta_hv'],rel_tol=1e-9,abs_tol=1e-12)
    write(root/'exact-hv-acceptance.json',dict(passed=True,checkpointComparisons=count,chronologicalFixtureEvents=len(events),
          maxAbsoluteDifference=maximum,moocore=moocore.__version__,seconds=time.perf_counter()-start,newSearchFE=0,newDecoderCalls=0,
          source='https://multi-objective.github.io/moocore/python/reference/generated/moocore.hypervolume.html'))
    print('EXACT_HV_ACCEPTED',count,maximum,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);check(p.parse_args().root.resolve())
