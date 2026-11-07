"""Analyze only the frozen 60 queries and four old recipients on Linux."""
import argparse
from pathlib import Path
import time
import numpy as np
from transfer_common import *
from transfer_metrics import strict_better, group_metrics, export_groups, table, decision


def candidate_gains(queries, backgrounds, scale):
    from analysis_metrics import hv
    from volume import UncoveredVolume
    objectives = [q['objectives'] for q in queries]
    checks = 0
    for name, points in backgrounds.items():
        for radius in (1.5, 1.25, 2.0):
            scorer = UncoveredVolume(scale.normalize(points), [radius] * 3)
            values = scorer.gains(scale.normalize(objectives))
            baseline = hv(scale.normalize(points), radius)
            for q, gain in zip(queries, values):
                exact = hv(scale.normalize([*points, q['objectives']]), radius) - baseline
                assert abs(exact - gain) < 1e-11
                checks += 1
                q.setdefault('gains', {}).setdefault(name, {})[str(radius)] = dict(
                    absolute=float(gain), relativePct=float(100 * gain / baseline))
    return checks


def block_records(queries, sources, receivers):
    blocks = []
    for source in sources:
        for receiver in receivers:
            values = {q['arm']: q for q in queries if q['source'] == source and q['receiver'] == receiver}
            p, f = values['PRUNED']['objectives'], values['FULL']['objectives']
            blocks.append(dict(source=source, receiver=receiver, role=receivers[receiver]['role'],
                prunedStrictlyDominatesFull=strict_better(p, f), fullStrictlyDominatesPruned=strict_better(f, p),
                equalObjectives=p == f,
                prunedStrictlyDominatesParent=strict_better(p, receivers[receiver]['objectives']),
                parentStrictlyDominatesPruned=strict_better(receivers[receiver]['objectives'], p),
                prunedHVPositive=values['PRUNED']['gains']['A0']['1.5']['absolute'] > 1e-12,
                objectiveVectors={arm: q['objectives'] for arm, q in values.items()},
                objectivesPrunedMinusFull=(np.asarray(p)-f).tolist(),
                ordinaryDominatedByPruned={arm: strict_better(p, q['objectives'])
                                          for arm, q in values.items() if arm.startswith('RANDOM')},
                armHVgainPct={arm: q['gains']['A0']['1.5']['relativePct'] for arm, q in values.items()}))
    return blocks


def grouped(queries, sources, receivers, a0, reference, scale):
    filters = {'ALL': lambda q: True}
    filters.update({s: lambda q, sid=s: q['source'] == sid for s in sources})
    filters.update({r: lambda q, rid=r: q['receiver'] == rid for r in receivers})
    result = {}
    for name, include in filters.items():
        points = {arm: [q['objectives'] for q in queries if q['arm'] == arm and include(q)] for arm in ARMS}
        result[name] = group_metrics(points, a0, reference, scale, SEED)
    return result


def main(root):
    prepare()
    assert read(root / 'completion.json')['passed'] and read(root / 'paid-audit.json')['passed']
    from analysis_metrics import frozen_scale, metrics, pair
    from research.dynamic_benchmark.metrics import nondominated, hypervolume
    start = time.perf_counter()
    output = root / 'analysis'
    output.mkdir()
    sources = {s['id']: s for s in read(root / 'sources.json')}
    receivers = {r['id']: r for r in read(root / 'receivers.json')}
    evaluated = {r['id']: r for r in lines(root / 'paid/evaluations.jsonl')}
    queries = [dict(q, objectives=evaluated[q['id']]['objectives']) for q in read(root / 'queries.json')]
    a0 = next(iter(sources.values()))['A0']
    known = read(root / 'known-background.json')
    reference = nondominated([*a0, *(q['objectives'] for q in queries)]).tolist()
    write(output / 'reference.json', reference)
    spec = next(s for s in read(MATURE / 'protocol.json')['instances'] if s['stem'] == STEM)
    scale = frozen_scale(spec)
    checks = candidate_gains(queries, dict(A0=a0, known=known), scale)
    blocks = block_records(queries, sources, receivers)
    groups = grouped(queries, sources, receivers, a0, reference, scale)
    export_groups(output, groups)
    independent_sets = 0
    for scored in [groups['ALL']['baseline'], *groups['ALL']['metrics'].values()]:
        for radius in (1.5, 1.25, 2.0):
            value = hypervolume(scale.normalize(scored['front']), [radius]*3)
            assert abs(value-scored['HV'][str(radius)]) < 1e-10
            independent_sets += 1
    known_base = metrics(known, reference, scale)
    known_effects = {}
    for arm in ARMS:
        points = [q['objectives'] for q in queries if q['arm'] == arm]
        scored = metrics([*known, *points], reference, scale)
        known_effects[arm] = dict(metrics=scored, versusKnown=pair(SEED, scored, known_base))
    verdict = decision(blocks, groups, sources)
    rows = []
    for q in queries:
        rows.append(dict(id=q['id'], source=q['source'], receiver=q['receiver'], arm=q['arm'],
            Cmax=q['objectives'][0], TEC=q['objectives'][1], TWC=q['objectives'][2],
            resourceEdits=len(q['changedFields']['resources']), keyEdits=len(q['changedFields']['keys']),
            orderInversions=q['factoryOrderInversions'], neutralPhysical=q['neutralPhysical'],
            HVgainAboveA0Pct=q['gains']['A0']['1.5']['relativePct'],
            HVgainAboveKnownPct=q['gains']['known']['1.5']['relativePct']))
    table(output / 'all-60-queries.csv', rows)
    write(output / 'query-details.json', queries)
    write(output / 'blocks.json', blocks)
    write(output / 'known-envelope-metrics.json', known_effects)
    summary = dict(verdict=verdict, paid=60, qa=4, failed=0,
        blocks=[{k:v for k,v in b.items() if k not in ('objectiveVectors',)} for b in blocks],
        queryPositiveCounts={arm: sum(q['arm']==arm and q['gains']['A0']['1.5']['absolute']>1e-12 for q in queries) for arm in ARMS},
        overallVersusA0=groups['ALL']['versusA0'], prunedComparisons=groups['ALL']['prunedComparisons'],
        knownEnvelopeEffects={arm:v['versusKnown'] for arm,v in known_effects.items()},
        independentCandidateHVChecks=checks, independentSetHVChecks=independent_sets,
        newAnalysisDecoderCalls=0, seconds=time.perf_counter()-start)
    write(output / 'summary.json', summary)
    print('TRANSFER_RESULT', verdict, 'positiveQueries', summary['queryPositiveCounts'],
          'seconds', summary['seconds'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
