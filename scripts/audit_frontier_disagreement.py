"""Zero-new-FE source-region and single-point-quality audit of already-complete searches."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once
from research.semantic_repair.evidence import digest
from frontier_disagreement_sources import NATURAL, TASK, cases, load
from frontier_disagreement_geometry import arithmetic_fixtures, compare


def main():
    assert all(read(p / 'status.json')['status'] == 'COMPLETE' for p in (NATURAL, TASK))
    root = ROOT / 'runs' / datetime.now().strftime('frontier-disagreement-%Y%m%d-%H%M%S-%f'); root.mkdir()
    print('FRONTIER_DISAGREEMENT_ROOT', root, flush=True)
    plan = cases()
    write_once(root / 'protocol.json', {'sources': [str(NATURAL), str(TASK)],
        'scope': 'Explicitly post-hoc, zero new search FE and decoder calls; no new candidate or performance gate.',
        'question': 'Separate net HV from bidirectional missing volume, size of best single known repair, '
                    'worst additive epsilon shortfall and three objective-axis partitions. Do not infer physical cause.',
        'strata': 'NAT/REPLAY and FE/trueTIME stay separate; short task13300FEs separate from long500k. '
                  'No pooling seeds/regimes, no new primary endpoint and no rescue of stopped task architecture.',
        'methods': 'Exact 3D HVref1.5 original frozen scales. Each pair joint ND supplies only descriptive '
                   'quartile cuts independently for C/E/W. Slabs must sum separately to full signed gap '
                   'and missing volumes. Single known point gain from its uncovered dominated box, '
                   'verified against direct union HV; no point inserted in any search archive. '
                   'Directed additive epsilon=max_target min_front max_objective positive normalized shortfall; '
                   'its worst gap is independent of target duplication, unlike empirical mean IGD+.',
        'cases': [{k: str(v) if isinstance(v, Path) else v for k, v in c.items()} for c in plan]})
    for name in ('audit_frontier_disagreement.py', 'frontier_disagreement_sources.py', 'frontier_disagreement_geometry.py'):
        shutil.copy2(Path(__file__).with_name(name), root / name)
    paths = {c[side] / name for c in plan for side in ('left', 'right')
             for name in ('anytime.jsonl', 'run-receipt.jsonl')}
    write_once(root / 'input-hashes.json', {str(p): digest(p) for p in sorted(paths)})
    write_once(root / 'arithmetic-acceptance.json', arithmetic_fixtures())
    results = []
    try:
        for c in plan:
            left, lp = load(c, 'left'); right, rp = load(c, 'right')
            row = {'stem': c['spec']['stem'], 'stratum': c['stratum'], 'seed': c['seed'],
                   'leftName': c['leftName'], 'rightName': c['rightName'],
                   'leftSource': lp, 'rightSource': rp, **compare(left, right)}
            results.append(row)
            print('FRONTIER_CASE', row['stem'], row['stratum'], row['seed'],
                  'leftHVpct', row['leftVsRightHVPct'], 'missingPct', row['leftMissingRightPctOfOwnHV'],
                  'bestSingleShare', row['leftMissing']['bestSingleShareOfMissingVolume'], flush=True)
        write_once(root / 'analysis.json', {'cases': results, 'searchFE': 0, 'decoderCalls': 0,
                                            'priorStoppingDecisionsUnchanged': True, 'goalAchieved': False})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'completedCases': len(results),
                                         'error': repr(error), 'searchFE': 0, 'decoderCalls': 0})
        raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'cases': len(results),
                                     'searchFE': 0, 'decoderCalls': 0, 'candidateImplemented': False})
    print('FRONTIER_DISAGREEMENT_COMPLETE', len(results), flush=True)


if __name__ == '__main__': main()
