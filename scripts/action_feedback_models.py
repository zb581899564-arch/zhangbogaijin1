"""One fixed vector regression; no tuning, outcome-dependent row selection or test fitting."""
import time
import numpy as np

from action_feedback_design import RIDGE, ROLES


def physical_key(point):
    return tuple(tuple((job, machine, worker) for job, f, machine, worker in
                       zip(point['JS'], point['FA'], point['MA'], point['WA']) if f == factory)
                 for factory in range(max(point['FA']) + 1))


def ridge_predict(features, targets, train, test, columns):
    prediction = np.zeros((len(test), 9, 3))
    started = time.perf_counter()
    source = features[train, :columns]
    location, spread = source.mean(axis=0), source.std(axis=0)
    spread[spread < 1e-12] = 1.
    x = np.column_stack([np.ones(len(train)), (source - location) / spread])
    xtest = np.column_stack([np.ones(len(test)), (features[test, :columns] - location) / spread])
    penalty = np.eye(columns + 1) * RIDGE
    penalty[0, 0] = 0.
    covariance = x.T @ x / len(train) + penalty
    for action in range(9):
        weight = np.linalg.solve(covariance, x.T @ targets[train, action] / len(train))
        prediction[:, action] = xtest @ weight
    return prediction, time.perf_counter() - started


def fit_policies(parents, selected, targets):
    features = np.asarray([parent['features'] for parent in parents])
    role = np.asarray([parent['role'] for parent in parents])
    source = np.asarray([parent['sourceSeed'] for parent in parents])
    keys = [physical_key(parent['parent']) for parent in parents]
    policies = {name: np.zeros_like(targets) for name in
                ('SHARED', 'OWN', 'MATCHED_SHARED', 'BASIC_SHARED', 'ROLE_MEAN', 'POOLED_MEAN')}
    costs, folds = [], []
    order = {value: index for index, value in enumerate((0, 7, 1, 6, 2, 5, 3, 4))}
    for heldout in sorted(set(source)):
        test = np.flatnonzero(source == heldout)
        forbidden = {keys[index] for index in test}
        train = np.asarray([index for index in range(len(parents))
                            if source[index] != heldout and keys[index] not in forbidden], dtype=int)
        if not len(train): raise AssertionError('No training rows after physical leakage exclusion')
        fold = {'heldoutSource': int(heldout), 'trainParents': len(train), 'testParents': len(test),
                'excludedPhysicalOverlap': int(sum(source != heldout) - len(train)), 'duties': []}
        for name, columns in (('SHARED', 16), ('BASIC_SHARED', 11)):
            policies[name][test], seconds = ridge_predict(features, targets, train, test, columns)
            costs.append({'fold': int(heldout), 'policy': name, 'seconds': seconds, 'decisions': len(test)})
        policies['POOLED_MEAN'][test] = targets[train].mean(axis=0)
        for duty in ROLES:
            own = train[role[train] == duty]
            receivers = test[role[test] == duty]
            assert len(own) >= 12 and len(receivers) == 24, 'Coverage failed; do not replace missing parents'
            balanced = sorted(train, key=lambda i: (order[selected[i]['localIndex']],
                                                      selected[i]['context'], ROLES.index(role[i])))[:len(own)]
            assert len(balanced) == len(own)
            for name, indexes in (('OWN', own), ('MATCHED_SHARED', np.asarray(balanced))):
                policies[name][receivers], seconds = ridge_predict(features, targets, indexes, receivers, 16)
                costs.append({'fold': int(heldout), 'duty': duty, 'policy': name,
                              'seconds': seconds, 'decisions': len(receivers)})
            policies['ROLE_MEAN'][receivers] = targets[own].mean(axis=0)
            fold['duties'].append({'duty': duty, 'ownTraining': len(own),
                                   'matchedTraining': len(balanced),
                                   'matchedDutyCounts': {r: int(sum(role[i] == r for i in balanced)) for r in ROLES}})
        folds.append(fold)
    return policies, folds, costs


def role_reward(values, role):
    index = {'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}.get(role)
    return np.sum(values, axis=-1) if index is None else values[..., index]
