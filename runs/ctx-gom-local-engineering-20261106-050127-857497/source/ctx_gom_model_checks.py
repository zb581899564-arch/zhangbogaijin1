"""Independent ordinary free-PA and single-factory linkage mathematics; cache only exact proven inputs."""
import hashlib
import json
import math

import numpy as np

from pa_population_model_checks import check_model
from qpa_state_checks import hierarchy

CACHE = {}


def check(event, population, catalog):
    jobs, slots = event['jobs'], event['slots']; n = len(catalog['tuples'])
    assert jobs == sorted(set(jobs)) and slots == sorted(set(slots))
    assert len(slots) in (80, 100) if event['family'] < 0 else len(slots) == 5
    members = [population[i] for i in slots]
    expected_masks = [[jobs[j] for j in subset] for subset in event['localSubsets']]
    assert event['subsets'] == expected_masks
    key = hashlib.sha256(json.dumps([event, [[p['resources'], p['keys']] for p in members]], sort_keys=True).encode()).hexdigest()
    if key in CACHE:
        return dict(CACHE[key], reusedExactMath=True)
    observed = np.array(event['dependency']); assert observed.shape == (len(jobs), len(jobs))
    if event['family'] < 0:
        assert jobs == list(range(catalog['jobs']))
        result = check_model({'dependency': event['dependency'], 'subsets': event['localSubsets']}, members, catalog['tuples'])
    else:
        assert all(catalog['tuples'][p['resources'][j]][0] == event['factory'] for p in members for j in jobs)
        keys = np.array([[p['keys'][j] for j in jobs] for p in members]); expected = np.zeros_like(observed)
        for a in range(len(jobs)):
            for b in range(a+1, len(jobs)):
                prob = float(np.mean(keys[:, a] < keys[:, b]))
                order = 1 if prob in (0., 1.) else 1+prob*math.log2(prob)+(1-prob)*math.log2(1-prob)
                expected[a, b] = expected[b, a] = order*(1-float(np.mean((keys[:, a]-keys[:, b])**2)))
        error = float(np.max(np.abs(expected-observed))); assert error < 3e-12
        result = {'pairs': len(jobs)*(len(jobs)-1)//2, 'maximumModelError': error,
                  'maximumChosenMeanDeficit': hierarchy(expected, event['localSubsets'])}
    CACHE[key] = result
    return dict(result, reusedExactMath=False)
