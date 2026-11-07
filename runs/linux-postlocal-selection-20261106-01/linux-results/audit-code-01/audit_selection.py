"""Independent FULL_ROLE/FULL_ALL ranking, duplicate crowding and quota survival."""
from collections import Counter
import math

from audit_core import OBJECTIVE_ROLE, ROLES, check_population, raw_hash, require


def nondominated_ranks(points):
    remaining = list(range(len(points)))
    ranks = [None] * len(points)
    level = 0
    while remaining:
        front = [i for i in remaining if not any(
            all(a <= b for a, b in zip(points[j], points[i])) and points[j] != points[i]
            for j in remaining)]
        require(bool(front), "Nondominated sorting produced an empty front")
        for index in front:
            ranks[index] = level
        removed = set(front)
        remaining = [i for i in remaining if i not in removed]
        level += 1
    return ranks


def crowding(points, ranks):
    distances = [0.0] * len(points)
    for rank in sorted(set(ranks)):
        copies = {}
        for index, point in enumerate(points):
            if ranks[index] == rank:
                copies.setdefault(tuple(point), []).append(index)
        unique = [indices[0] for indices in copies.values()]
        for objective in range(3):
            # Stable repeated sorts match ties in the established policy.
            unique.sort(key=lambda i: points[i][objective])
            span = points[unique[-1]][objective] - points[unique[0]][objective]
            if span == 0:
                continue
            distances[unique[0]] = distances[unique[-1]] = math.inf
            for previous, index, following in zip(unique, unique[1:], unique[2:]):
                distances[index] += (points[following][objective] - points[previous][objective]) / span
        for indices in copies.values():
            for index in indices:
                distances[index] = distances[indices[0]]
    return distances


def select_indices(parents, children, role, policy):
    require(policy in ("FULL_ROLE", "FULL_ALL") and len(parents) == len(children),
            "Invalid selection policy or parent/child sizes")
    pool = parents + children
    points = [row["raw"]["objectives"] for row in pool]
    require(all(row["role"] == role for row in pool), "Selection pool crosses roles")
    ranks = nondominated_ranks(points)
    distances = crowding(points, ranks)
    objective = OBJECTIVE_ROLE.get(role) if policy == "FULL_ROLE" else None
    def key(index):
        prefix = () if objective is None else (points[index][objective],)
        return prefix + (ranks[index], -distances[index], index)
    order = sorted(range(len(pool)), key=key)
    remaining = Counter(p["family"] for p in parents)
    seen, selected, output = set(), set(), []
    for sweep in range(2):
        for index in order:
            family = pool[index]["family"]
            identity = family, tuple(points[index])
            if index in selected or remaining[family] == 0 or (sweep == 0 and identity in seen):
                continue
            output.append(index)
            selected.add(index)
            seen.add(identity)
            remaining[family] -= 1
    require(len(output) == len(parents) and not any(remaining.values()), "Selection quota underfilled")
    return output


def member_identity(row):
    return (row["role"], row["family"], row["origin"], row["sourceIndex"],
            row["sourcePaidByFE"], raw_hash(row["raw"]))


def verify_selection(record, expected_parents, expected_children, policy):
    check_population(expected_parents)
    check_population(expected_children)
    require(record["policy"] == policy, "Wrong selection policy")
    groups = record["groups"]
    require([group["role"] for group in groups] == list(ROLES), "Selection role order differs")
    selected, checks = [], []
    for group in groups:
        role = group["role"]
        parents = [p for p in expected_parents if p["role"] == role]
        children = [p for p in expected_children if p["role"] == role]
        for key, expected in (("parents", parents), ("children", children)):
            require([member_identity(p) for p in group[key]] == [member_identity(p) for p in expected],
                    "Selection " + key + " ancestry or working state differs")
        indices = select_indices(parents, children, role, policy)
        require(group["selectedPoolIndices"] == indices, "Independent survivor indices differ")
        pool = parents + children
        selected.extend(pool[i] for i in indices)
        checks.append(dict(role=role, candidates=len(pool), selected=len(indices),
                           selectedChildren=sum(i >= len(parents) for i in indices)))
    check_population(selected)
    return selected, checks
