"""The predeclared 150+60 matrix and unchanged historical numerical inputs."""
import copy
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / "runs/expansion-screen-20261102-001934-525927"
VARIANTS = {
    "V2": {"mode": "BASELINE", "profile": "V2", "phase": "factorial"},
    "S_ONLY": {"mode": "BASELINE", "profile": "S", "phase": "factorial"},
    "O_ONLY": {"mode": "BASELINE", "profile": "O", "phase": "factorial"},
    "SO": {"mode": "BASELINE", "profile": "SO", "phase": "factorial"},
    "NSGA2_CONTROL": {"mode": "NSGA2_4V", "profile": "V2", "phase": "factorial"},
    "SYNC_FIX": {"mode": "SYNC", "profile": "SO", "phase": "cooperation"},
    "SHARE_FIX": {"mode": "SHARE", "profile": "SO", "phase": "cooperation"},
}
PHASES = ("factorial", "cooperation")
REFERENCES = (1.25, 1.5, 2.0)


def make_protocol(previous):
    """Copy scientific constants, never a prior detector or prior quality result."""
    protocol = {
        "version": "semantic-repair-v1",
        "purpose": "Predeclared repair factorial and fixed-SO cooperation diagnosis",
        "historical_input_protocol": str(PREVIOUS / "protocol.json"),
        "instances": copy.deepcopy(previous["instances"]),
        "algorithm_seeds": list(previous["algorithm_seeds"]),
        "model": copy.deepcopy(previous["model"]),
        "variants": copy.deepcopy(VARIANTS),
        "phases": {phase: [label for label, spec in VARIANTS.items() if spec["phase"] == phase]
                   for phase in PHASES},
        "runs": 210,
        "campaign_wall_cap_seconds": 5400,
        "one_jvm_at_a_time": True,
        "classic_setting": 0,
        "classic_calibration": "None; NSGA2_4V setting0 locked before runs",
        "time_fractions": [.5, 1.0],
        "fe_checkpoints": [15000],
        "fe_role": "Diagnostic; censored checkpoints stay null and empty",
        "common_diagnostics": True,
        "semantic_contract": {
            "S": "Snapshot global-post N before local search; pool global-post then local-post (2N records), one whole-pool PDDR; no initial parents",
            "stable_ties": "Original candidate order; global-post block before local-post; no new diversity tie-break",
            "O": "Per guide six independent pre-drawn triggers; three closed segments; FA event always redraws MA/WA; invalid resources uniformly redrawn",
            "segments": "Two independent uniform endpoints0..N-1, equality allowed, sorted inclusive; donor read-only",
            "resource_sampling": "Uniform valid identifiers; original value allowed; FA mutation draws position, factory, machine, worker in that order",
            "common_feasibility": "Unchanged final SchedulingEncoding.repair; nonempty-factory rule/model/decoder/objectives unchanged",
            "cooperation": "Whole200-pool PDDR scores then category truncation [free80,family0:5,family1:5,family2:5,family3:5] in both SYNC_FIX and SHARE_FIX",
            "history": "Independent global snapshot; descend forks branch while retaining lineage; both branches may survive with separate ND personal histories",
            "diagnostics": "All7 versions paid observer; distinctness after restore/repair sampled every256 global proposals; exact shared origins capped4096",
            "pool_capture": "First2 and last immutable paid pools, at most3; reference/numeric capture insideT, full encoding export outsideT but within campaign cap",
        },
        "diagnostic_cost_boundary": {
            "auditSeconds": "Search-internal bounded numeric/reference capture; included in each registered T",
            "poolExportSeconds": "Post-search encoding/JSON materialization; offline cost, included in the original campaign wall cap",
            "wrapperWallSeconds": "JVM startup, search, replay and export measured together; controller validation measured separately",
        },
        "run_arguments": {"incremental": True, "small": False, "compact": True,
                          "traceLimit": 0, "checkpointPolicy": "SCREEN"},
        "metrics": {
            "primary_reference": [1.5] * 3,
            "sensitivity_references": [[1.25] * 3, [2.0] * 3],
            "igdplus_reference": "Per-instance nondominated union of all7 variants x all5 seeds deadline-valid T archives; approximate, offline only",
            "seed_aggregation": "Mean of five repeats per instance; six instances are the paired units",
            "practical_win": "mean-HV effect >=1% and >=3/5 positive paired seed differences",
            "practical_loss": "mean-HV effect <=-1% and >=3/5 negative paired seed differences",
            "interaction": "HV_SO-HV_S_ONLY-HV_O_ONLY+HV_V2; seed percent uses that seed's V2 denominator",
            "p_value_gate": False,
            "denominator_floor": 1e-12,
        },
        "scope": "Development repair evidence only; no original270 traffic-light decision and no step6 qualification",
        "continuation_rule": "Complete and correct factorial phase -> predeclared cooperation phase; never select by quality",
        "fixed_repaired_baseline": "SO",
        "historical_results": "Context only; no historical outcomes enter metrics or timing comparisons",
    }
    expected = len(protocol["instances"]) * len(protocol["algorithm_seeds"]) * len(VARIANTS)
    if expected != protocol["runs"]:
        raise ValueError("The authorized six-instance/five-seed/seven-version matrix changed")
    protocol["planned_search_seconds"] = sum(row["time_seconds"] for row in protocol["instances"]) * 5 * 7
    return protocol


def jobs(protocol, phase):
    rng = random.Random(8110007 if phase == "factorial" else 8110008)
    result = []
    for instance in protocol["instances"]:
        for seed in protocol["algorithm_seeds"]:
            labels = list(protocol["phases"][phase])
            rng.shuffle(labels)
            for label in labels:
                result.append({"instance": instance["stem"], "seed": seed, "variant": label,
                               "seconds": instance["time_seconds"], "phase": phase})
    return result


def trial_folder(root, job):
    return root / "trials" / job["phase"] / job["instance"] / str(job["seed"]) / job["variant"]
