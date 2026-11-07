"""Chronological HV accounting and matched-parent descriptions of paid records."""
from collections import Counter, defaultdict
import numpy as np
from common import FACTORY, rows
from features import weakly_covered, physical_signature, summarize_features


def frozen_complement(parent, factory):
    others = [f for f in range(len(parent['factoryMakespan'])) if f != factory]
    return [max((parent['factoryMakespan'][f] for f in others), default=0.),
            sum(parent['factoryEnergy'][f] for f in others),
            sum(parent['factoryCost'][f] for f in others)]


def escape_depth(obj, background, width):
    # Exact geometric depth for uniform normalized improvements in all 3 objectives.
    # This is neither a feasible schedule bound nor a learned score.
    return max(0., float(np.max(np.min((np.asarray(obj) - background) / width, axis=1))))


def account(folder, features, witnesses, background, scale):
    from analysis_metrics import hv
    paid = list(rows(folder / 'paid.jsonl'))
    archive = np.asarray(background, dtype=float)
    initial_hv = hv(scale.normalize(archive), 1.5)
    current_hv = initial_hv
    gains = []
    by_fe = {r['fe']: r for r in features}
    for candidate in paid:
        if not candidate['fresh']:
            continue
        obj = np.asarray(candidate['objectives'])
        assert not weakly_covered(archive, obj)
        archive = np.vstack([archive[~np.all(obj <= archive, axis=1)], obj])
        next_hv = hv(scale.normalize(archive), 1.5)
        gain = next_hv - current_hv
        assert gain >= -1e-12
        meta = by_fe.get(candidate['fe'])
        gains.append(dict(fe=candidate['fe'], stage=candidate['stage'],
            role=candidate['role'], objectives=candidate['objectives'],
            HVAbsolute=max(0., gain), HVPctA0=100*max(0., gain)/initial_hv,
            meta=meta))
        current_hv = next_hv
    final = np.asarray(__import__('common').read(folder / 'front.json'))
    assert sorted(map(tuple, archive)) == sorted(map(tuple, final))
    assert abs(sum(r['HVAbsolute'] for r in gains) - (current_hv-initial_hv)) < 1e-11
    groups = defaultdict(lambda: dict(events=0, HVAbsolute=0., HVPctA0=0.))
    for r in gains:
        m = r['meta']
        labels = ['role.' + r['role'], 'stage.' + r['stage']]
        if m:
            labels += ['structure.' + ('RESOURCE_ORDER' if m['resourceAndOrder'] else
                        'ORDER' if m['orderOnly'] else 'RESOURCE' if m['resourceOnly'] else 'NOOP'),
                       'parent.' + ('COVERED' if m['parentCoveredByA0'] else 'UNCOVERED'),
                       'accepted.' + str(m['accepted']),
                       'factory.' + ','.join(map(str,m['affectedFactories']))]
        for label in labels:
            groups[label]['events'] += 1
            groups[label]['HVAbsolute'] += r['HVAbsolute']
            groups[label]['HVPctA0'] += r['HVPctA0']
    candidates = {r['fe']: r for r in paid}
    controls = []
    for w in witnesses:
        m = w['record']
        if not m['fresh']:
            continue
        matches = [r for r in features if r['parentId'] == m['parentId']
                   and r['affectedFactories'] == m['affectedFactories'] and not r['a0Novel']]
        controls.append(dict(fe=m['fe'], parentId=m['parentId'],
                             positive=m, negativeSameParentFactory=summarize_features(matches),
                             negativeFE=[r['fe'] for r in matches]))
    # Keep all gains, plus a fixed top-three descriptive case selection (not a test set).
    top = sorted(gains, key=lambda r:(-r['HVAbsolute'],r['fe']))[:3]
    witness_map = {w['record']['fe']: w for w in witnesses}
    cases = []
    for g in top:
        if g['fe'] not in witness_map:
            continue
        w = witness_map[g['fe']]
        chain = [candidates[fe] for fe in w['record']['ancestry']]
        meaningful = []
        for c in chain:
            if not by_fe[c['fe']]['physicalNoop']:
                meaningful.append(dict(by_fe[c['fe']], objectives=c['objectives']))
        cases.append(dict(gain=g, evidence=w, acceptedPhysicalAncestry=meaningful))
    return dict(gains=gains, groupAccounting=dict(groups), topCases=cases,
                totalHVPctA0=100*(current_hv-initial_hv)/initial_hv,
                matchedParentComparisons=controls, finalArchiveReconstructed=True)
