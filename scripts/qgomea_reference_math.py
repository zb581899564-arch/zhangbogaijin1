"""Independent integer-permutation mathematics and fixed native reference cases; no objective search."""
from itertools import permutations
import random


def inverse(positions):
    assert sorted(positions) == list(range(len(positions)))
    order = [None] * len(positions)
    for job, position in enumerate(positions):
        order[position] = job
    return order


def position_mix(parent, donor, subset, reference):
    """Place the receiver's selected relative positions at the donor reference, then fill holes in old order."""
    n = len(parent)
    selected = [donor[reference] + parent[job] - parent[reference] for job in subset]
    shift = -min(selected) if min(selected) < 0 else n - 1 - max(selected) if max(selected) >= n else 0
    selected = [position + shift for position in selected]
    order = [None] * n
    for job, position in zip(subset, selected):
        assert order[position] is None
        order[position] = job
    remaining = iter(job for job in inverse(parent) if job not in subset)
    order = [next(remaining) if job is None else job for job in order]
    return inverse(order), selected


def order_mix(parent, donor, subset):
    positions = sorted(parent[job] for job in subset)
    jobs = sorted(subset, key=lambda job: donor[job])
    result = parent.copy()
    for job, position in zip(jobs, positions):
        result[job] = position
    return result


def make_cases(path):
    count = 0
    def emit(stream, parent, donor, subset, reference):
        nonlocal count
        count += 1
        vectors = [parent, donor, subset, [reference]]
        stream.write(str(count) + "\t" + "\t".join(",".join(str(v + 1) for v in values) for values in vectors) + "\n")
    with path.open("x", encoding="utf-8") as stream:
        emit(stream, [0], [0], [0], 0)
        for n in (2, 3, 4):
            for parent in permutations(range(n)):
                for donor in permutations(range(n)):
                    for bits in range(1, 1 << n):
                        subset = [j for j in range(n) if bits & (1 << j)]
                        for reference in subset:
                            emit(stream, list(parent), list(donor), subset, reference)
        rng = random.Random(2026110601)
        for n in (5, 8, 20, 100):
            for i in range(50):
                parent, donor = list(range(n)), list(range(n))
                rng.shuffle(parent); rng.shuffle(donor)
                size = n if i < 4 else rng.randint(1, min(n, 8))
                subset = sorted(rng.sample(range(n), size))
                emit(stream, parent, donor, subset, rng.choice(subset))
    assert count == 19081
    return count


def integers(text):
    return [int(value) - 1 for value in text.split(",")]


def verify_native(cases_path, results_path):
    checked = root_identity = order_singleton_identity = 0
    with cases_path.open() as inputs, results_path.open() as outputs:
        for raw, observed in zip(inputs, outputs):
            fields, saved = raw.rstrip().split("\t"), observed.rstrip().split("\t")
            assert fields[0] == saved[0]
            parent, donor, subset, reference_values = map(integers, fields[1:])
            reference = reference_values[0]
            assert int(saved[1]) - 1 == reference
            position, virtual = position_mix(parent, donor, subset, reference)
            order = order_mix(parent, donor, subset)
            sequential = order_mix(position, donor, subset)
            expected = [virtual, position, order, sequential, inverse(parent)]
            assert all(integers(actual) == value for actual, value in zip(saved[2:], expected)), fields[0]
            assert sorted(position) == sorted(order) == sorted(sequential) == list(range(len(parent)))
            if len(subset) == len(parent):
                assert position == parent and order == donor
                root_identity += 1
            if len(subset) == 1:
                assert order == parent
                order_singleton_identity += 1
            checked += 1
        assert next(inputs, None) is None and next(outputs, None) is None
    assert checked == 19081
    return {"nativeCases": checked, "independentIntegerOutputsMatched": checked * 5,
            "positionRootIdentityChecks": root_identity, "orderSingletonIdentityChecks": order_singleton_identity,
            "newDynamicSearchFE": 0, "dynamicDecoderCalls": 0}
