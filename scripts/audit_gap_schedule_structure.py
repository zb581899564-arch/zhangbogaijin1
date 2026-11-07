"""Zero-search-FA/resource/order distance audit to observed enhanced-classic dominators."""
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np

from run_long_budget_bridge import ROOT, read, write_once
from research.semantic_repair.evidence import digest
from gap_structure_sources import NAT, FRESH, cases, checkpoint
from gap_structure_matching import match, fixtures


def analyze(case):
    left, right = checkpoint(case, 'left'), checkpoint(case, 'right');matches = []
    for i, parent in enumerate(left):
        selected = match(parent, right, np.asarray(case['spec']['normalization']['scale']))
        matches.append({'parentIndex': i, 'match': selected})
    valid = [p['match'] for p in matches if p['match'] is not None]
    quantile = lambda field: {'median': float(np.median([v[field] for v in valid])),
        'min': float(min(v[field] for v in valid)), 'max': float(max(v[field] for v in valid))} if valid else None
    return {'stem': case['spec']['stem'], 'seed': case['seed'], 'stratum': case['stratum'],
        'kind': case['kind'], 'endpoint': case['endpoint'], 'leftSource': str(case['left']), 'rightSource': str(case['right']),
        'parentFrontPoints': len(left), 'targetFrontPoints': len(right), 'matchedStrictlyDominatedParents': len(valid),
        'dominatedFraction': len(valid) / len(left),
        'dominatedParentsWithSomeSameFAObservedDominator': sum(v['anyDominatorSameCompleteFA'] for v in valid),
        'minimumChangedFactoryJobs': quantile('minimumChangedFactoryJobs'),
        'selectedChangedBundleJobs': quantile('selectedChangedBundleJobs'),
        'selectedWithinFactoryInversionFraction': quantile('withinFactoryInversionFraction'),
        'matches': matches, 'parentGenomes': left, 'targetGenomes': right}


def main():
    root = ROOT / 'runs' / datetime.now().strftime('gap-schedule-structure-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('GAP_SCHEDULE_STRUCTURE_ROOT', root, flush=True);plan = cases()
    write_once(root / 'protocol.json', {'sources': [str(NAT), str(FRESH)],
        'scope': 'Explicitly post-hoc known-genome diagnosis, zero new searchFE and decoder calls, not a new efficacy gate.',
        'sourceStrata': 'Bothinstances, native500kFE/trueT oldseed12390003 and originalOFF100kFE/trueT '
                       'two freshseeds13190007/37; no conditional-ON method or pooled budget comparison.',
        'matching': 'Every FULLfront point, without resampling. All strict Pareto dominating NSGApoints '
                    'eligible. Choose minimum changed factory job count, then changed(FA,MA,WA)job bundles, '
                    'then normalized objectiveEuclidean distance, then stable rawobjectiveorder. Report '
                    'all absence/missing. Factory/resources mapped byjob, not vectorposition. For chosen '
                    'target, Kendall disagreements projected independently onto each parent factory.',
        'limits': 'Observed target absence at sameFA does not prove there is no better schedule at '
                  'thatFA or that FAcauses the algorithm gap. Resource ids across changedfactory are '
                  'descriptive rawlabels only, not interchangeable machine/worker types. No grafted '
                  'solution, teacher, scoring API or new operator implemented. No claims of novel '
                  'cooperation, fatigue mechanism or statistical independence of front points.',
        'interpretation': 'Determine whether any later causal schedule-factor probe is needed; no '
                          'implicit authorization to revive stopped linked-guides/teacher/FA-release '
                          'mechanisms. All previous gates unchanged; default mainline protected.'})
    for name in ('audit_gap_schedule_structure.py', 'gap_structure_sources.py', 'gap_structure_matching.py'):
        shutil.copy2(Path(__file__).with_name(name), root / name)
    files = {c[side] / name for c in plan for side in ('left', 'right')
             for name in ('anytime.jsonl', 'checkpoint-solutions.jsonl', 'run-receipt.jsonl')}
    write_once(root / 'input-hashes.json', {str(p): digest(p) for p in sorted(files)})
    write_once(root / 'arithmetic-acceptance.json', fixtures());results = []
    try:
        for c in plan:
            row = analyze(c);path = root / row['stem'] / f'{row["seed"]}-{row["stratum"]}.json';path.parent.mkdir(exist_ok=True)
            write_once(path, row)
            summary = {k: v for k, v in row.items() if k not in ('matches', 'parentGenomes', 'targetGenomes')};results.append(summary)
            print('GAP_SCHEDULE_STRUCTURE_CASE', row['stem'], row['stratum'], row['seed'],
                  'matched', row['matchedStrictlyDominatedParents'], 'sameFA', row['dominatedParentsWithSomeSameFAObservedDominator'],
                  'FAchanges', row['minimumChangedFactoryJobs'], flush=True)
        write_once(root / 'analysis.json', {'cases': results, 'searchFE': 0, 'decoderCalls': 0,
                                            'causalAttributionEstablished': False, 'goalAchieved': False})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error),
                                         'completedCases': len(results), 'searchFE': 0, 'decoderCalls': 0});raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'cases': len(results), 'searchFE': 0, 'decoderCalls': 0})
    print('GAP_SCHEDULE_STRUCTURE_COMPLETE', len(results), flush=True)


if __name__ == '__main__':main()
