"""Predeclared single-candidate coverage/expectation scoring, never fed back to the witness search."""
import numpy as np

from run_long_budget_bridge import read, rows, write_once, hypervolume
from research.composition_oracle.volume import UncoveredVolume
from explicit_resource_design import CHECKPOINTS, ORIGINS


def analyze(root, spec):
    stem = spec['stem']; folder = root / stem
    parents = rows(folder / 'witness/parents.jsonl')
    outcomes = rows(folder / 'witness/outcomes.jsonl')
    selected = read(folder / 'selected.json'); fronts = read(folder / 'source-fronts.json')
    receipt = rows(folder / 'witness/receipt.jsonl')[0]
    assert len(parents) == len(selected) == 64
    paid = [p['paidFE'] for p in parents] + [p['paidFE'] for p in outcomes]
    assert sorted(paid) == list(range(1, receipt['successfulFE'] + 1))
    assert receipt['chargedFullDecodes'] == receipt['independentTimelineValidations'] == receipt['successfulFE']
    assert receipt['offlineOriginalFullQA'] == 64 + sum(p['channel'] == 'FIRST' for p in outcomes)
    assert receipt['expectedOriginalPolicyRejections'] == sum(p['channel'] == 'LATER' for p in outcomes)
    normal = spec['normalization']; lower, scale = np.asarray(normal['lower']), np.asarray(normal['scale'])
    contexts, values, errors = {}, {}, []
    for checkpoint in CHECKPOINTS:
        background = np.asarray([p['objectives'] for origin in ORIGINS for p in fronts[f'{origin}:{checkpoint}']])
        background = (background - lower) / scale
        checkpoint_indexes = [i for i, p in enumerate(parents) if p['sourceFE'] == checkpoint]
        contexts[str(checkpoint)] = {}
        for ref in (1.25, 1.5, 2.):
            scorer = UncoveredVolume(background, (ref,) * 3)
            contexts[str(checkpoint)][str(ref)] = scorer.background_hv
            for index, parent in enumerate(parents):
                if parent['sourceFE'] != checkpoint: continue
                assert parent['id'] == selected[index]['id']
                assert parent['genome']['plan'] == []
                for key in ('JS', 'FA', 'MA', 'WA', 'objectives'):
                    assert parent['genome'][key] == selected[index]['parent'][key]
                cell = values.setdefault(parent['id'], {'id': parent['id'], 'origin': parent['origin'],
                         'sourceFE': checkpoint, 'stage': parent['stage'], 'references': {}, 'channels': {}})
                result = {}
                for channel in ('FIRST', 'LATER'):
                    candidates = [p for p in outcomes if p['id'] == parent['id'] and p['channel'] == channel]
                    points = np.asarray([p['genome']['objectives'] for p in candidates]).reshape(-1, 3)
                    gains = scorer.gains((points - lower) / scale)
                    result[channel] = {'bestSingleGain': float(max(gains, default=0.)),
                                       'meanSingleGain': float(np.mean(gains)) if len(gains) else 0.,
                                       'material': bool(max(gains, default=0.) >= scorer.background_hv * .001)}
                    if ref == 1.5:
                        cell['channels'][channel] = {'candidates': len(candidates),
                            'meanFormationEvaluationSeconds': float(np.mean([
                                (p['generationNanos'] + p['evaluationNanos']) / 1e9 for p in candidates]))
                            if candidates else None}
                        for candidate in candidates:
                            plan = candidate['genome']['plan']
                            if channel == 'LATER':
                                assert len(plan) == 1
                                assert plan[0] == [parent['job'], parent['stage'], candidate['machine'], candidate['worker']]
                                for key in ('JS', 'FA', 'MA', 'WA'):
                                    assert candidate['genome'][key] == parent['genome'][key]
                            else: assert plan == []
                    if len(points) and index in (checkpoint_indexes[0], checkpoint_indexes[-1]):
                        point = (points[0] - lower) / scale
                        independent = hypervolume(np.vstack([background, point]), (ref,) * 3) - scorer.background_hv
                        error = abs(independent - float(scorer.gains([point])[0])); errors.append(error)
                        assert error < 1e-11
                cell['references'][str(ref)] = result
    cells = list(values.values())
    means = {str(ref): {channel: {metric: float(np.mean([
        c['references'][str(ref)][channel][metric] for c in cells]))
        for metric in ('bestSingleGain', 'meanSingleGain')} for channel in ('FIRST', 'LATER')}
        for ref in (1.25, 1.5, 2.)}
    main = means['1.5']; grouped = []
    for checkpoint in CHECKPOINTS:
        for origin in ORIGINS:
            subset = [c for c in cells if c['sourceFE'] == checkpoint and c['origin'] == origin]
            grouped.append({'sourceFE': checkpoint, 'origin': origin, 'parents': len(subset),
                'laterMaterialParents': sum(c['references']['1.5']['LATER']['material'] for c in subset),
                'firstBestMean': float(np.mean([c['references']['1.5']['FIRST']['bestSingleGain'] for c in subset])),
                'laterBestMean': float(np.mean([c['references']['1.5']['LATER']['bestSingleGain'] for c in subset]))})
    material = sum(c['references']['1.5']['LATER']['material'] for c in cells)
    coverage = material >= 13 and all(g['laterMaterialParents'] >= 1 for g in grouped)
    quality = (main['FIRST']['bestSingleGain'] > 1e-12
               and main['LATER']['bestSingleGain'] >= 1.1 * main['FIRST']['bestSingleGain']
               and main['LATER']['meanSingleGain'] >= main['FIRST']['meanSingleGain'])
    checkpoint_gate = all(sum(g['laterBestMean'] for g in grouped if g['sourceFE'] == cp)
                          >= sum(g['firstBestMean'] for g in grouped if g['sourceFE'] == cp) for cp in CHECKPOINTS)
    sensitivity = all(means[str(ref)]['LATER']['bestSingleGain'] >= means[str(ref)]['FIRST']['bestSingleGain']
                      for ref in (1.25, 2.))
    ratios = [c['channels']['LATER']['meanFormationEvaluationSeconds'] /
              c['channels']['FIRST']['meanFormationEvaluationSeconds'] for c in cells
              if all(c['channels'][channel]['candidates'] for channel in ('FIRST', 'LATER'))]
    cost = float(np.median(ratios)) if ratios else None
    result = {'stem': stem, 'parents': 64, 'laterMaterialParents': material,
              'channelCandidates': {channel: sum(p['channel'] == channel for p in outcomes) for channel in ('FIRST', 'LATER')},
              'meanSingleGains': means, 'grouped': grouped, 'backgroundHV': contexts,
              'coverageGate': bool(coverage), 'qualityGate': bool(quality), 'checkpointGate': bool(checkpoint_gate),
              'sensitivityGate': bool(sensitivity), 'medianLaterVsFirstCallCost': cost,
              'costGate': bool(cost is not None and cost <= 1.25),
              'worthRepresentationSearchDesign': bool(coverage and quality and checkpoint_gate and sensitivity
                                                      and cost is not None and cost <= 1.25),
              'maxIndependentHVError': max(errors), 'cases': cells,
              'limits': 'Paid one-operation coverage and uniform one-candidate expectation. Oracle best '
                        'not a one-FE selector. Different candidate counts recorded. No complete algorithm, '
                        'role cooperation, fatigue specificity, same-time advantage or independent confirmation.'}
    write_once(folder / 'analysis.json', result)
    return result
