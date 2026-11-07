"""Authoritative N_K_F_id filename contract and materialized F K N header check."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Dimensions:
    jobs: int
    stages: int
    factories: int


def dimensions(name):
    stem = str(name).replace("\\", "/").rsplit("/", 1)[-1].removesuffix(".txt")
    parts = stem.split("_")
    if len(parts) != 4 or any(not part.isdigit() for part in parts):
        raise ValueError("Expected the registered N_K_F_id instance filename")
    jobs, stages, factories, _ = map(int, parts)
    if min(jobs, stages, factories) < 1:
        raise ValueError("Instance dimensions must be positive")
    return Dimensions(jobs=jobs, stages=stages, factories=factories)


def verify_materialized_header(path, stem=None):
    expected = dimensions(stem if stem is not None else path.name)
    with path.open(encoding="utf-8-sig") as stream:
        actual = tuple(map(int, stream.readline().strip().split()))
    if actual != (expected.factories, expected.stages, expected.jobs):
        raise ValueError("Materialized F K N header differs from the N_K_F_id contract: " + str(path))
    return expected
