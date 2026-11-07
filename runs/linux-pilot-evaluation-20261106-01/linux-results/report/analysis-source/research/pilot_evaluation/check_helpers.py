"""Independent small-fixture oracles; not an alternative production metric."""
from itertools import combinations

import numpy as np


def assert_raises(error, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error:
        return
    raise AssertionError(f"Expected {error.__name__} from {function.__name__}")


def inclusion_exclusion_hv(front, reference):
    """Independent union-of-boxes oracle, exponential and fixture-sized only."""
    front, reference = np.asarray(front, dtype=float), np.asarray(reference, dtype=float)
    total = 0.0
    for size in range(1, len(front) + 1):
        for group in combinations(front, size):
            lower = np.max(group, axis=0)
            box = np.prod(np.maximum(reference - lower, 0.0))
            total += (-1) ** (size + 1) * box
    return float(total)
