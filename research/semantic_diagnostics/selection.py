"""Full-pool PDDR and rank/crowding, with identical optional category quotas."""
import numpy as np


def dominance(points):
    a = np.asarray(points, dtype=float)
    return np.all(a[:, None, :] <= a[None, :, :], axis=2) & np.any(a[:, None, :] < a[None, :, :], axis=2)


def pddr(points):
    matrix = dominance(points)
    return matrix.sum(axis=0) + 1 / (matrix.sum(axis=1) + 1)


def crowded_order(points):
    points = np.asarray(points, dtype=float)
    matrix = dominance(points)
    incoming = matrix.sum(axis=0)
    current = np.flatnonzero(incoming == 0).tolist()
    result = []
    while current:
        distance = np.zeros(len(points))
        if len(current) <= 2:
            distance[current] = np.inf
        else:
            for objective in range(3):
                order = sorted(current, key=lambda i: (points[i, objective], i))
                low, high = points[order[0], objective], points[order[-1], objective]
                distance[order[0]] = distance[order[-1]] = np.inf
                if high > low:
                    for k in range(1, len(order) - 1):
                        distance[order[k]] += (points[order[k+1], objective] - points[order[k-1], objective]) / (high - low)
        result.extend(sorted(current, key=lambda i: (-distance[i], i)))
        following = []
        for i in current:
            for j in np.flatnonzero(matrix[i]):
                incoming[j] -= 1
                if incoming[j] == 0:
                    following.append(int(j))
        current = following
    return result


def truncate(order, capacity, categories, quotas):
    if quotas is None:
        return order[:capacity]
    used, selected = [0] * len(quotas), []
    for i in order:
        category = categories[i]
        if used[category] < quotas[category]:
            used[category] += 1
            selected.append(i)
    if len(selected) != capacity:
        raise ValueError("Counterfactual quota capacity differs from the actual pool")
    return selected


def cutoff_tie_size(scores, selected, categories, quotas):
    groups = range(len(quotas)) if quotas is not None else [0]
    kept = set(selected)
    total = 0
    for category in groups:
        population = [i for i in range(len(scores)) if quotas is None or categories[i] == category]
        survivors = [i for i in population if i in kept]
        if not survivors:
            continue
        boundary = max(scores[i] for i in survivors)
        tied = [i for i in population if scores[i] == boundary]
        if any(i in kept for i in tied) and any(i not in kept for i in tied):
            total += len(tied)
    return total
