"""Held-source-seed-out one-action selection on a fully charged, fixed outcome pool."""
import time
import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, hypervolume
from action_feedback_design import ROLES
from action_feedback_models import fit_policies, role_reward
from research.composition_oracle.volume import UncoveredVolume


def effect(candidate, control):
    return 100 * (candidate / control - 1) if control > 1e-12 else None


def analyze(root, spec):
    stem, normalization = spec['stem'], spec['normalization']
    folder = root / stem
    parents, selected = rows(folder / 'probe/parents.jsonl'), read(folder / 'selected.json')
    outcomes = rows(folder / 'probe/outcomes.jsonl')
    assert len(parents) == len(selected) == 192 and len(outcomes) == 192 * 36
    objective = np.zeros((192, 9, 4, 3))
    costs = np.zeros((192, 9, 4))
    observed = set()
    for outcome in outcomes:
        index = int(outcome['id'][1:]); action, rep = outcome['action'], outcome['rep']
        assert (index, action, rep) not in observed
        observed.add((index, action, rep))
        objective[index, action, rep] = outcome['candidate']['objectives']
        costs[index, action, rep] = (outcome['generationNanos'] + outcome['evaluationNanos']) / 1e9
    parent_objective = np.asarray([parent['parent']['objectives'] for parent in parents])
    assert np.all(parent_objective > 0)
    for index, (actual, expected) in enumerate(zip(parents, selected)):
        assert actual['id'] == expected['id'] == f'p{index}'
        assert actual['role'] == expected['role'] and actual['factory'] == expected['factory']
        assert actual['parent'] == {key: expected['parent'][key] for key in actual['parent']}
    signed = (parent_objective[:, None, None, :] - objective) / parent_objective[:, None, None, :]
    targets = signed.mean(axis=2)
    predicted, folds, fit_costs = fit_policies(parents, selected, targets)
    actual_reward = np.asarray([np.maximum(0, role_reward(signed[i], parent['role'])).mean(axis=1)
                                for i, parent in enumerate(parents)])
    choices = {name: np.argmax(np.asarray([role_reward(values[i], parent['role'])
                                           for i, parent in enumerate(parents)]), axis=1)
               for name, values in predicted.items()}
    choices['FIRST'] = np.zeros(192, dtype=int)
    choices['ORACLE'] = np.argmax(actual_reward, axis=1)
    reward = {name: actual_reward[np.arange(192), choice] for name, choice in choices.items()}
    reward['UNIFORM'] = actual_reward.mean(axis=1)
    contexts = {c['contextId']: c for c in read(folder / 'contexts.json')}
    scale, lower = np.asarray(normalization['scale']), np.asarray(normalization['lower'])
    hv_gains = {str(ref): np.zeros((192, 9)) for ref in (1.25, 1.5, 2.)}
    checks = []
    for id, context in contexts.items():
        indexes = [i for i, parent in enumerate(parents) if parent['context'] == id]
        background = (np.asarray(context['background']) - lower) / scale
        points = (objective[indexes].reshape(-1, 3) - lower) / scale
        for ref in (1.25, 1.5, 2.):
            scorer = UncoveredVolume(background, (ref,) * 3)
            hv_gains[str(ref)][indexes] = scorer.gains(points).reshape(len(indexes), 9, 4).mean(axis=2)
            # Independently verify observed candidates, not only synthetic fixtures.
            baseline = hypervolume(background, (ref,) * 3)
            for point in (points[0], points[-1]):
                difference = hypervolume(np.vstack([background, point]), (ref,) * 3) - baseline
                error = abs(float(scorer.gains([point])[0]) - difference)
                assert error < 1e-11
                checks.append(error)
    hv = {ref: {name: float(np.mean(gains[np.arange(192), choice]))
                for name, choice in choices.items()} for ref, gains in hv_gains.items()}
    for ref, gains in hv_gains.items(): hv[ref]['UNIFORM'] = float(gains.mean())
    means = {name: float(value.mean()) for name, value in reward.items()}
    effects = {name: effect(means['SHARED'], value) for name, value in means.items()
               if name not in ('SHARED', 'ORACLE')}
    matched = effect(means['MATCHED_SHARED'], means['OWN'])
    informative = (actual_reward.max(axis=1) > 1e-8) & (np.ptp(actual_reward, axis=1) > 1e-8)
    strata = []
    for key in ('role', 'sourceSeed'):
        for value in sorted({parent[key] for parent in parents}):
            mask = [parent[key] == value for parent in parents]
            strata.append({'key': key, 'value': value,
                           'meanReward': {name: float(values[mask].mean()) for name, values in reward.items()}})
    quality = int(sum(informative)) >= 64 and all(
        effects[name] is not None and effects[name] >= threshold for name, threshold in
        (('OWN', 10), ('UNIFORM', 10), ('ROLE_MEAN', 5), ('POOLED_MEAN', 5)))
    transfer = matched is not None and matched >= 5
    robust = (all(s['meanReward']['SHARED'] > s['meanReward']['OWN'] for s in strata if s['key'] == 'sourceSeed')
              and sum(s['meanReward']['SHARED'] >= s['meanReward']['OWN'] for s in strata if s['key'] == 'role') >= 3)
    archive = all(scores[control] > 1e-12 and scores['SHARED'] >= scores[control] - 1e-14
                  for scores in hv.values() for control in ('OWN', 'UNIFORM'))
    fatigue = (effects['BASIC_SHARED'] is not None and effects['BASIC_SHARED'] >= 2
               and all(scores['SHARED'] >= scores['BASIC_SHARED'] - 1e-14 for scores in hv.values()))
    # Measure complete prediction choices again without fitting or outcomes, for diagnostic cost only.
    started = time.perf_counter()
    np.argmax(np.asarray([role_reward(predicted['SHARED'][i], parent['role'])
                          for i, parent in enumerate(parents)]), axis=1)
    choice_seconds = time.perf_counter() - started
    learning_seconds = sum(c['seconds'] for c in fit_costs if c['policy'] == 'SHARED') + choice_seconds
    feature_seconds = sum(parent['featureNanos'] for parent in parents) / 1e9
    selected_cost = costs[np.arange(192), choices['SHARED']].mean(axis=1)
    details = [{'id': parent['id'], 'context': parent['context'], 'role': parent['role'],
                'sourceSeed': parent['sourceSeed'], 'informative': bool(informative[i]),
                'chosenActions': {name: int(value[i]) for name, value in choices.items()},
                'expectedPositiveReward': {name: float(value[i]) for name, value in reward.items()}}
               for i, parent in enumerate(parents)]
    result = {'stem': stem, 'parents': 192, 'folds': folds, 'informativeParents': int(sum(informative)),
              'meanPositiveReward': means, 'sharedEffectsPct': effects,
              'matchedSharedVsOwnPct': matched, 'singleCandidateHV': hv, 'strata': strata,
              'qualityGate': bool(quality), 'matchedTransferGate': bool(transfer),
              'robustnessGate': bool(robust), 'archiveGate': bool(archive),
              'fatigueInformationGate': bool(fatigue),
              'worthNativeClosedLoopDesign': bool(quality and transfer and robust and archive),
              'fitCosts': fit_costs, 'featureSeconds': feature_seconds,
              'sharedLearningSeconds': learning_seconds,
              'sharedFeatureLearningCostRatio': float((feature_seconds + learning_seconds) / selected_cost.sum()),
              'meanSelectedFormationEvaluationSeconds': float(selected_cost.mean()),
              'maxIndependentHVError': max(checks), 'cases': details,
              'limits': 'Offline one-step preference reward, not actual CENTER PDDR or continued VNS; '
                        'no unseen-action labels, repeated draw union, online or same-time advantage, '
                        'fatigue specificity, independent confirmation or novel full algorithm.'}
    write_once(folder / 'analysis.json', result)
    return result
