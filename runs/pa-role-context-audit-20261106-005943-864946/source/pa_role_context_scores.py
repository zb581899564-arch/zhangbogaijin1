"""Held-out structural scores, conditioning controls and transparent fold fallbacks."""
import numpy as np

METHODS = ("GLOBAL", "ROLE", "RANDOM_MATCHED", "OBJECTIVE_NEAREST_MATCHED")


def score(data, train, test):
    f, codes = data["factories"], data["codes"]
    assert len(train) and not set(train) & set(test)
    pairs, cells = codes.shape[1], f * f
    counts = np.bincount((codes[train] + data["offset"]).ravel(), minlength=pairs * cells).reshape(pairs, f, f)
    posterior = counts + .5  # One common Jeffreys cell pseudocount, not tuned per method.
    probability = posterior / (len(train) + .5 * cells)
    marginal_a, marginal_b = probability.sum(axis=2), probability.sum(axis=1)
    y = codes[test]
    pair_index = np.arange(pairs)
    log_joint = np.log(probability.reshape(pairs, cells)[pair_index, y])
    log_independent = np.log(marginal_a[pair_index, y // f]) + np.log(marginal_b[pair_index, y % f])
    same_count = data["same"][train].sum(axis=0)
    before_count = (data["same"][train] & data["before"][train]).sum(axis=0)
    p_before = (before_count + .5) / (same_count + 1.)
    order_log = np.where(data["before"][test], np.log(p_before), np.log1p(-p_before))
    order_mask = data["same"][test]
    return np.column_stack([-log_joint.mean(axis=1), (log_joint - log_independent).mean(axis=1),
                            -(order_log * order_mask).sum(axis=1), order_mask.sum(axis=1)])


def matched_controls(data, train, role_train, test, rng):
    size = len(role_train)
    random_scores = np.zeros((len(test), 4))
    for _ in range(16):
        selected = rng.choice(train, size=size, replace=False)
        random_scores += score(data, selected, test) / 16
    nearest = []
    for query in test:
        distances = ((data["objectives"][train] - data["objectives"][query])**2).sum(axis=1)
        selected = train[np.lexsort((train, distances))[:size]]
        nearest.append(score(data, selected, np.asarray([query]))[0])
    return random_scores, np.asarray(nearest)


def summarize(values, weights):
    total = float(weights.sum())
    order_count = float((weights * values[:, 3]).sum())
    return {"queryWeight": total, "rawQueries": len(values),
            "factoryPairNLL": float((weights * values[:, 0]).sum() / total),
            "jointVsIndependentGainNats": float((weights * values[:, 1]).sum() / total),
            "sameFactoryOrderNLL": float((weights * values[:, 2]).sum() / order_count) if order_count else None,
            "weightedOrderPairs": order_count}


def cross_validate(data, folds, weights, seed):
    assert len(set(folds)) > 1
    predictions = {method: np.zeros((len(folds), 4)) for method in METHODS}
    fallbacks = []
    rng = np.random.default_rng(seed)
    for fold in sorted(set(folds)):
        train, test = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        predictions["GLOBAL"][test] = score(data, train, test)
        for label in sorted(set(data["labels"][test])):
            queries = test[data["labels"][test] == label]
            selected = train[data["labels"][train] == label]
            if not len(selected):
                # Missing conditional model is visible, and all controls share the same global fallback.
                selected = train
                fallbacks.append({"fold": int(fold), "role": label, "queries": len(queries)})
            predictions["ROLE"][queries] = score(data, selected, queries)
            random_values, nearest_values = matched_controls(data, train, selected, queries, rng)
            predictions["RANDOM_MATCHED"][queries] = random_values
            predictions["OBJECTIVE_NEAREST_MATCHED"][queries] = nearest_values
    result = {"overall": {method: summarize(values, weights) for method, values in predictions.items()},
              "fallbacks": fallbacks, "roles": {}}
    for label in sorted(set(data["labels"])):
        indices = np.flatnonzero(data["labels"] == label)
        result["roles"][label] = {method: summarize(values[indices], weights[indices]) for method, values in predictions.items()}
    return result


def math_checks():
    # Analytic independent and linked binary pairs, rather than checking our formulas against themselves.
    data = {"factories": 2, "codes": np.tile(np.arange(4), (3, 1)).T.reshape(12, 1),
            "offset": np.array([0]), "same": np.zeros((12, 1), bool), "before": np.zeros((12, 1), bool)}
    data["codes"] = np.tile(np.arange(4), 3).reshape(12, 1)
    independent = score(data, np.arange(8), np.arange(8, 12))
    assert np.max(abs(independent[:, 0] - np.log(4))) < 1e-12
    assert np.max(abs(independent[:, 1])) < 1e-12
    data["codes"] = np.tile(np.array([0, 3]), 6).reshape(12, 1)
    linked = score(data, np.arange(8), np.arange(8, 12))
    assert (linked[:, 1] > 0).all() and np.isfinite(linked).all()
    return {"independentPairGainZero": True, "linkedPairGainPositive": True,
            "missingCofactoryOrderFinite": True, "newSearchFE": 0}
