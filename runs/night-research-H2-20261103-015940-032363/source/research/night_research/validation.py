"""Small shared shape checks for bounded night evidence."""
import math


def integer(value, name, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError("Invalid integer evidence: " + name)
    return value


def nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("Invalid nonnegative evidence: " + name)
    return value


def objectives(value, name):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("Invalid objective triple: " + name)
    for number in value:
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError("Nonfinite objective: " + name)
    return value


def indices(value, name, size, upper):
    if not isinstance(value, list) or len(value) != size or len(set(value)) != size:
        raise ValueError("Invalid unique index list: " + name)
    for item in value:
        integer(item, name, 0, upper - 1)
    return value
