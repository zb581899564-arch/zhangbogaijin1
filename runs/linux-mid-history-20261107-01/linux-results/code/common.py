"""Read-only Linux analysis of already-paid middle-window states."""
from pathlib import Path
import importlib.util
import json
import sys

BASE = Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
GAP = BASE/'runs/linux-trajectory-gap-20261107-01'
SUPPORT = BASE/'runs/linux-mid-support-20261107-01'
SHARE = SUPPORT/'historical-share/pipeline.jsonl'
spec = importlib.util.spec_from_file_location('gap_common', GAP/'update-01/scripts/common.py')
gap = importlib.util.module_from_spec(spec);spec.loader.exec_module(gap)
read, rows, write, sha = gap.read, gap.rows, gap.write, gap.sha
nd, metrics, coverage, csv_write = gap.nondominated, gap.metrics, gap.coverage, gap.csv_write
SCALE = gap.SCALES['100_2_3_1']
ROLES = ['MAKESPAN']*15+['CENTER']*55+['ENERGY']*15+['WORKER_COST']*15


def linux():
    assert sys.platform == 'linux' and sys.version_info[:2] == (3,11)


def stream(path):
    with Path(path).open(encoding='utf-8-sig') as f:
        for line in f:
            if line.strip():yield json.loads(line)


def fronts(points):
    return nd([p['objectives'] for p in points])


def compare(before, after, reference):
    a,b=fronts(after),fronts(before)
    ma,mb=metrics(a,reference,SCALE),metrics(b,reference,SCALE)
    den=ma['IGDplus']+mb['IGDplus']
    return dict(before=mb,after=ma,HVpercent=100*(ma['HV']/mb['HV']-1),
                IGDplusImprovementPercent=200*(mb['IGDplus']-ma['IGDplus'])/den if den else 0.,
                C_after_before=coverage(a,b),C_before_after=coverage(b,a))
