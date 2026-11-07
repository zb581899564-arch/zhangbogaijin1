"""Chronological telescope and nested sharing fixtures; no decoder calls."""
import math

from .check_helpers import assert_raises, inclusion_exclusion_hv
from .indicators import ObjectiveScale
from .stages import stage_hv_telescope


def _events():
    definitions = [("initialization", "initial", False, [0.8, 0.8, 0.8]),
                   ("evolution", "variation", False, [0.7, 0.8, 0.8]),
                   ("local_search", "cross_group", True, [0.7, 0.7, 0.8]),
                   ("local_search", "same_candidate", False, [0.7, 0.7, 0.8]),
                   ("evolution", "cross_group", True, [0.2, 0.2, 0.2]),
                   ("evolution", "outside_box", False, [1.2, 0.1, 0.1])]
    return [{"event": index, "completed_at": float(index), "stage": stage,
             "source": source, "sharing": sharing, "objectives": objectives}
            for index, (stage, source, sharing, objectives) in enumerate(definitions, 1)]


def check_chronological_telescope():
    events = _events()
    options = {"scale": ObjectiveScale((0, 0, 0), (1, 1, 1)),
               "hv_reference": [1, 1, 1], "initial_front": [[0.9, 0.9, 0.9]]}
    result = stage_hv_telescope(events, **options)
    expected = inclusion_exclusion_hv(options["initial_front"] + [row["objectives"] for row in events], [1, 1, 1])
    assert math.isclose(result["final_hv"], expected, abs_tol=1e-12)
    assert math.isclose(result["total_delta_hv"], result["final_hv"] - result["initial_hv"], abs_tol=1e-12)
    assert math.isclose(result["sum_event_delta_hv"], result["sum_stage_delta_hv"], abs_tol=1e-12)
    assert result["event_count"] == 6
    assert result["events"][3]["delta_hv"] == result["events"][5]["delta_hv"] == 0.0
    local = result["by_stage"]["local_search"]
    assert local["event_count"] == 2 and local["sharing"]["event_count"] == 1
    assert math.isclose(local["delta_hv"], local["sharing"]["delta_hv"], abs_tol=1e-12)
    assert math.isclose(local["delta_hv"], sum(row["delta_hv"] for row in local["by_source"].values()), abs_tol=1e-12)
    assert sum(stage["sharing"]["delta_hv"] for stage in result["by_stage"].values()) > 0
    assert "sharing" not in result and result["causal_claim"] is False
    prefix = stage_hv_telescope(events, until_event=3, **options)
    timed = stage_hv_telescope(events, until_time=3.0, **options)
    assert prefix["event_count"] == timed["event_count"] == 3
    assert prefix["final_hv"] == timed["final_hv"]
    assert math.isclose(prefix["final_hv"], 0.3 * 0.3 * 0.2, abs_tol=1e-12)
    assert prefix["final_hv"] < result["final_hv"]
    empty = stage_hv_telescope(events, until_event=0, **options)
    assert empty["event_count"] == 0 and empty["final_hv"] == empty["initial_hv"]
    compact = stage_hv_telescope(events, keep_events=False, **options)
    assert compact["events"] == [] and compact["final_hv"] == result["final_hv"]


def check_stage_validation():
    events = _events()
    options = {"scale": ObjectiveScale((0, 0, 0), (1, 1, 1)), "hv_reference": [1, 1, 1]}
    assert_raises(ValueError, stage_hv_telescope, [events[1], events[0]], **options)
    backward = [events[0], {**events[1], "completed_at": 0.5}]
    assert_raises(ValueError, stage_hv_telescope, backward, **options)
    assert_raises(ValueError, stage_hv_telescope, [{**events[0], "sharing": "false"}], **options)
    assert_raises(ValueError, stage_hv_telescope, [{**events[0], "stage": "SHARING"}], **options)
    assert_raises(ValueError, stage_hv_telescope, [{**events[0], "objectives": [1, 2]}], **options)
    untimed = [{key: value for key, value in events[0].items() if key != "completed_at"}]
    assert_raises(ValueError, stage_hv_telescope, untimed, until_time=1, **options)
