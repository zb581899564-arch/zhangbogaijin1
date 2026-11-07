"""Small strict input contracts shared by the offline pilot reporters."""
import math
import numbers

import numpy as np


def points(value, dimensions=3, *, allow_empty=True):
    array = np.asarray(value, dtype=float)
    if array.size == 0 and array.shape == (0,):
        array = array.reshape(0, dimensions)
    if array.ndim != 2 or array.shape[1] != dimensions:
        raise ValueError(f"Expected an N by {dimensions} objective matrix")
    if not np.isfinite(array).all():
        raise ValueError("Objectives must be finite")
    if not allow_empty and not len(array):
        raise ValueError("Expected a nonempty objective matrix")
    return array


def vector(value, dimensions=3):
    array = np.asarray(value, dtype=float)
    if array.shape != (dimensions,) or not np.isfinite(array).all():
        raise ValueError(f"Expected a finite length-{dimensions} vector")
    return array


def finite(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def integer(value, name, minimum=0):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral):
        raise ValueError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return int(value)


def label(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def run_fronts(fronts, dimensions):
    if not hasattr(fronts, "items") or not fronts:
        raise ValueError("Supply a nonempty mapping of unique run IDs to fronts")
    result = {}
    for run_id, front in fronts.items():
        key = str(run_id)
        label(key, "run_id")
        if key in result:
            raise ValueError("Run IDs collide after conversion to strings")
        result[key] = points(front, dimensions)
    return result
