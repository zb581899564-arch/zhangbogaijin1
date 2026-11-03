"""Real input-header regressions for N20/K2/F3 and N200/K8/F5."""
from copy import deepcopy
from .instance_contract import dimensions, verify_materialized_header
from .protocol import INPUT_SOURCE
from .checkpoint_checks import write_fixture, write_genomes
from .checkpoint_evidence import validate_checkpoint_evidence
from .observation_checks import fixture as context_fixture
from .observations import validate_observation as validate_context
from .transfer_checks import fixture as transfer_fixture
from .factory_transfer import validate_observation as validate_transfer


def _reject(callback):
    try:
        callback()
    except ValueError:
        return
    raise AssertionError("An out-of-range real-instance factory id was accepted")


def _checkpoint(folder, stem, shape):
    point = {"checkpointKind": "TIME", "checkpoint": 2., "elapsedSeconds": 1.9,
        "fe": 5, "front": [[2., 2., 2.]], "reached": True, "censored": False}
    summary = {"successful": 5, "timeLimitSeconds": 2.}
    genomes = write_fixture(folder, [point], summary)
    genomes[0].update({"JS": list(range(shape.jobs)), "FA": [i % shape.factories for i in range(shape.jobs)],
        "MA": [0] * shape.jobs, "WA": [0] * shape.jobs})
    write_genomes(folder, genomes)
    assert validate_checkpoint_evidence(folder, [point], summary, {"stem": stem})["coveredPoints"] == 1
    genomes[0]["FA"][0] = shape.factories
    write_genomes(folder, genomes)
    _reject(lambda: validate_checkpoint_evidence(folder, [point], summary, {"stem": stem}))


def _context(stem, shape):
    rows, summary = context_fixture()
    summary["instance"] = stem + ".txt"
    base = [i % shape.factories for i in range(shape.jobs)]
    previous = []
    for i in range(4):
        value = list(base)
        value[i] = (value[i] + 1) % shape.factories
        previous.append(value)
    rows[1].update({"previousFactoryAssignments": previous, "oldFactoryByJob": previous[0], "newFactoryByJob": base})
    assert validate_context(rows, summary, "ELITE")["deadlineValidSampledCompletedEvents"] == 1
    wrong = deepcopy(rows)
    wrong[1]["newFactoryByJob"][0] = shape.factories
    _reject(lambda: validate_context(wrong, summary, "ELITE"))


def _transfer(stem, shape):
    rows, summary = transfer_fixture()
    summary["instance"] = stem + ".txt"
    rows[1]["factory"] = shape.factories - 1
    assert validate_transfer(rows, summary, "PACKET_ROLE")["sampledDeadlineValidEvents"] == 1
    rows[1]["factory"] = shape.factories
    _reject(lambda: validate_transfer(rows, summary, "PACKET_ROLE"))


def run_dimension_checks(folder):
    result = []
    for stem, expected in (("20_2_3_1", (20, 2, 3)), ("200_8_5_1", (200, 8, 5))):
        shape = dimensions(stem)
        assert (shape.jobs, shape.stages, shape.factories) == expected
        assert verify_materialized_header(INPUT_SOURCE / "inputs" / stem / (stem + ".txt"), stem) == shape
        _checkpoint(folder, stem, shape)
        _context(stem, shape)
        _transfer(stem, shape)
        result.append({"instance": stem, "jobs": shape.jobs, "stages": shape.stages, "factories": shape.factories,
            "realMaterializedHeaderMatched": True, "maximumFactoryIdAccepted": shape.factories - 1,
            "checkpointContextAndTransferAgree": True, "outOfRangeFactoryRejected": True})
    return result
