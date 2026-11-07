"""Conditional single-offspring evidence; never substitute it for closed-loop performance."""
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume

VIEWS = ('RAW', 'RANDOM', 'ALIGNED')
KERNELS = ('QGS', 'CLASSIC')


def effect(candidate, control):
    return 100 * (candidate / control - 1) if control > 1e-12 else None


def analyze_instance(root, spec, reps):
    stem, norm = spec['stem'], spec['normalization']
    manifest = read(root / stem / 'cases.json')['cases']
    records = rows(root / stem / 'probe/outcomes.jsonl')
    indexed = {(r['case'], r['method'], r['rep']): r for r in records}
    assert len(indexed) == len(records) == len(manifest) * 6 * reps
    normalized = lambda x: (np.asarray(x) - norm['lower']) / norm['scale']
    cells = []
    for source in manifest:
        background = normalized(source['background'] +
            [source[k]['objectives'] for k in ('parent', 'personal', 'global')])
        baseline = float(hypervolume(background, (1.5,) * 3))
        assert baseline > 1e-12
        methods = {}
        for kernel in KERNELS:
            raw = [indexed[(source['caseId'], kernel + '_RAW', rep)] for rep in range(reps)]
            for view in VIEWS:
                name = kernel + '_' + view
                selected = [indexed[(source['caseId'], name, rep)] for rep in range(reps)]
                gains = [max(0., float(hypervolume(np.vstack([background,
                    normalized([r['child']['objectives']])]), (1.5,) * 3)) - baseline) for r in selected]
                methods[name] = {
                    'meanAddedHV': float(np.mean(gains)),
                    'meanAddedHVPctOfBackground': 100 * float(np.mean(gains)) / baseline,
                    'gains': gains,
                    'meanProposalPlusEvaluationSeconds': float(np.mean([
                        r['preparationSeconds'] + r['generationSeconds'] + r['evaluationSeconds'] for r in selected])),
                    'physicalChangeVsRawFraction': float(np.mean([
                        a['physicalKey'] != b['physicalKey'] for a, b in zip(selected, raw)])),
                    'meanInputSwaps': float(np.mean([sum(r[k][0] for k in ('personalInputPath', 'globalInputPath')) for r in selected])),
                    'meanInputNeutralSwaps': float(np.mean([sum(r[k][1] for k in ('personalInputPath', 'globalInputPath')) for r in selected]))}
        cells.append({'case': source['caseId'], 'role': source['role'], 'sourceSeed': source['sourceSeed'],
            'paidSourceFE': source['paidFE'], 'baselineHV': baseline, 'methods': methods,
            'informative': any(max(methods['QGS_' + v]['gains']) > 1e-10 for v in VIEWS)})
    means = {m: float(np.mean([c['methods'][m]['meanAddedHV'] for c in cells])) for m in cells[0]['methods']}
    relative_means = {m: float(np.mean([c['methods'][m]['meanAddedHVPctOfBackground'] for c in cells])) for m in means}
    informative = sum(c['informative'] for c in cells)
    role_effects = {}
    for role in sorted({c['role'] for c in cells}):
        selected = [c for c in cells if c['role'] == role]
        values = {v: float(np.mean([c['methods']['QGS_' + v]['meanAddedHV'] for c in selected])) for v in VIEWS}
        role_effects[role] = {'meanAddedHV': values, 'effectVsRawPct': effect(values['ALIGNED'], values['RAW']),
            'alignedAtLeastRaw': values['ALIGNED'] >= values['RAW'] - 1e-12}
    ratios = [c['methods']['QGS_ALIGNED']['meanProposalPlusEvaluationSeconds'] /
              c['methods']['QGS_RAW']['meanProposalPlusEvaluationSeconds'] for c in cells]
    qgs_effects = {v: effect(means['QGS_ALIGNED'], means['QGS_' + v]) for v in ('RAW', 'RANDOM')}
    quality = informative >= 16 and qgs_effects['RAW'] is not None and qgs_effects['RAW'] >= 10 \
        and qgs_effects['RANDOM'] is not None and qgs_effects['RANDOM'] >= 5 \
        and sum(r['alignedAtLeastRaw'] for r in role_effects.values()) >= 3 \
        and all(r['effectVsRawPct'] is None or r['effectVsRawPct'] >= -10 for r in role_effects.values())
    result = {'stem': stem, 'cases': cells, 'informativeCases': informative, 'totalCases': len(cells),
        'meanSelectedAddedHV': means, 'meanAddedHVPctOfBackground': relative_means,
        'qgsAlignedEffectsPct': qgs_effects, 'roleEffects': role_effects,
        'classicAlignedEffectVsRawPct': effect(means['CLASSIC_ALIGNED'], means['CLASSIC_RAW']),
        'medianQgsAlignedCostVsRaw': float(np.median(ratios)), 'qualityGate': bool(quality),
        'necessaryCostGate': bool(np.median(ratios) <= 1.10),
        'meanPhysicalChangeVsRaw': {m: float(np.mean([c['methods'][m]['physicalChangeVsRawFraction'] for c in cells])) for m in means}}
    write_once(root / stem / 'analysis.json', result)
    return {k: v for k, v in result.items() if k != 'cases'}


def analyze(root):
    protocol = read(root / 'protocol.json')
    result = [analyze_instance(root, s, protocol['reps']) for s in protocol['instances']]
    output = {'instances': result, 'worthFreshClosedLoop': all(r['qualityGate'] and r['necessaryCostGate'] for r in result),
        'scope': 'New offspring on reused development contexts. Conditional per-offspring gain at equal evaluated counts; '
                 'not independent method trajectories, same-time superiority, novelty, or a new full algorithm.'}
    write_once(root / 'analysis.json', output)
    return output
