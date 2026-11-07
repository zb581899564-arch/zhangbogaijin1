"""Prospective pilot contract, independent of outcomes."""
import json
from pathlib import Path

SEEDS = [16110003, 16110037, 16110069]
ARMS = ['FULL', 'GLOBAL_ONLY', 'LOCAL_ONLY']


def contract(payload):
    anchor = json.loads((payload / 'anchor-contract.json').read_text('utf-8-sig'))
    original = anchor.get('contract', anchor)
    return {
        'version': 'LINUX_PILOT_PHASE_DIAGNOSTIC-v1', 'registered': '2026-11-06',
        'anchor': 'ctx-gom-capability-20261106-051509-678987/SHARE_CTX_GOM',
        'instances': original['instances'], 'seeds': SEEDS, 'arms': ARMS,
        'fePerRun': 500000, 'scienceRuns': 18, 'scienceFE': 9000000,
        'checkpoints': [100, 10000, 50000, 100000, 250000, 500000],
        'engineeringSeed': 14910003, 'engineeringGate': 'Frozen-vs-new and observer-off paid digest equality; init; phase fees/lifecycle; timeline; cutoff/failure; math fixtures',
        'runtime': {'jdkMajor': 17, 'javaRelease': 8, 'python': '3.11', 'platform': 'Linux', 'simultaneousJVMs': 1},
        'order': 'instance then seed; rotate FULL/GLOBAL_ONLY/LOCAL_ONLY by instanceIndex+seedIndex',
        'phaseAblation': 'Budget opportunity-cost comparison; no intrinsic causal percentage. Disabled phase consumes neither FE nor its random calls.',
        'localOnly': 'Retain family/pool/population lifecycle; QGS and composition calls absent with the global phase.',
        'globalOnly': 'Skip entire local begin/reencoding/model/program; survivor pool contains 100 global snapshots, no duplicated offspring.',
        'reference': 'Per-instance nondominated union of all 9 final fronts, computed after full batch. Never available to search.',
        'normalization': 'Frozen per-instance scales inherited exactly; lower zero',
        'hvReferences': [1.5, 1.25, 2.0],
        'indicators': ['HV', 'IGDplus', 'IGD', 'exact weak C both directions', 'Cmax/TEC/TWC extrema with full vectors'],
        'eaf': 'No 50% display at n=3; export all individual fronts and paired values. At n>=5 use fixed common-reference quartile conditional slices.',
        'thresholds': {'hvSignalPercent': 1, 'igdPlusSymmetricSignalPercent': 5, 'cReverseFlagPercentagePoints': 10, 'costSignalPercent': 10},
        'interpretation': 'No weighted total, no majority vote, no significance claim. At least two seed improvements for repeatable signal; inspect regional tradeoffs.',
        'attribution': 'Chronological admitted-point HV differences, sharing nested within GLOBAL. INITIAL + GLOBAL + LOCAL = final; lifecycle has no FE.',
        'cost': 'Inclusive search time and phase costs; observation and offline QA separate; no same-time quality claim in this batch.',
        'failure': 'Retain failed attempt, actual fees and last valid front. No seed/budget/endpoint replacement. Stop on unexpected fault.',
        'goalAutomaticallyResumed': False, 'defaultMainlineChanged': False, 'windowsTimesPooled': False,
        'next': 'Finish this diagnosis before registering one next mechanism; no automatic 2x2 or expansion.'
    }


def freeze(payload, out):
    value = contract(payload)
    path = out / 'protocol.json'
    if path.exists():
        assert json.loads(path.read_text()) == value, 'Frozen protocol changed'
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    return value
