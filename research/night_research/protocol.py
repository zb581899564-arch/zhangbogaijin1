"""Explicit campaign contract; no candidate, seed or mechanism is chosen here."""
import copy
import math
import random
import re
from pathlib import Path

from research.semantic_repair.evidence import read

ROOT = Path(__file__).resolve().parents[2]
INPUT_SOURCE = ROOT / "runs/cooperation-roles-20261102-231315-641007"
CLASSIC_SOURCE = ROOT / "runs/expansion-screen-20261102-001934-525927/execution-manifest.json"
RULE_SOURCE = ROOT / "research/dynamic_benchmark/expansion_screen_v1.json"
PLAN = ROOT / "docs/实验比较协议.md"
CLASSICS = {"NSGA2_4V": 0, "SPEA2_4V": 1, "MOEAD_4V": 0, "NSGA2_VNS_4V": 1}
INSTANCE_TIMES = [("20_2_3_1", 3), ("20_8_5_1", 4), ("100_2_3_1", 5),
                  ("100_8_3_1", 9), ("200_5_3_1", 12), ("200_8_5_1", 19)]
RULE_KEYS = ("green_all_required", "red_any_sufficient_after_validity")


def make_protocol(config):
    previous, rules = read(INPUT_SOURCE / "protocol.json"), read(RULE_SOURCE)
    if read(CLASSIC_SOURCE)["selectedClassicSettings"] != CLASSICS:
        raise ValueError("Previously selected classical settings changed")
    protocol = copy.deepcopy(config)
    protocol.update({"version": "night-research-v1", "instances": previous["instances"],
        "model": previous["model"], "external_comparators": list(CLASSICS),
        "runs": 30 * len(config["variants"]), "wall_cap_seconds": 3600,
        "one_jvm_at_a_time": True, "time_fractions": [.5, 1.], "fe_checkpoints": [15000],
        "checkpoint_evidence_schema": "snapshot-genomes-v1",
        "planned_search_seconds": 260 * len(config["variants"]),
        "metrics": {"primary_reference": [1.5] * 3,
            "sensitivity_references": [[1.25] * 3, [2.] * 3],
            "igdplus_reference": "Per instance all current methods and all five new seeds deadline-valid T ND union; offline empirical reference only",
            "aggregation": "Five seed means within instance; six instances equally weighted",
            "practical_win": ">=1% instance mean and >=3/5 positive paired seed differences; symmetric losses"},
        "continuation": "All owners required before classification; no incomplete-owner retry, tuning, seed replacement or automatic followup",
        "scope": "Development evidence and resource decision only; not novelty, formal step6 or publication qualification"})
    for key in RULE_KEYS:
        protocol[key] = copy.deepcopy(rules[key])
    validate_protocol(protocol)
    return protocol


def validate_protocol(protocol):
    if protocol.get("version") != "night-research-v1" or protocol.get("hypothesis") not in ("H1", "H2"):
        raise ValueError("Only the two explicitly authorized night hypotheses are supported")
    if [(r["stem"], r["time_seconds"]) for r in protocol["instances"]] != INSTANCE_TIMES:
        raise ValueError("The six development instances and T budgets must remain fixed")
    previous = read(INPUT_SOURCE / "protocol.json")
    if protocol["instances"] != previous["instances"] or protocol["model"] != previous["model"]:
        raise ValueError("Materialized inputs, normalization and dynamic model must be reused exactly")
    variants = protocol["variants"]
    roles = [protocol[key] for key in ("candidate", "baseline", "matched_control", "strong_control")]
    if any(label not in variants for label in roles) or len(set(roles[:3])) != 3:
        raise ValueError("Explicit candidate, SHARE baseline and matched control labels are required")
    if roles[3] == roles[0] or any(re.fullmatch(r"[A-Za-z0-9_-]+", label) is None for label in variants):
        raise ValueError("Strong control must differ from candidate; labels must be safe single path components")
    if any(label in CLASSICS for label in roles):
        raise ValueError("A classical comparator cannot serve as an own-method control")
    baseline = variants[protocol["baseline"]]
    if baseline["mode"] != "SHARE_JOB_ALIGNED" or baseline["profile"] != "SO" or baseline["setting"] != 0:
        raise ValueError("Own baseline must be unchanged SHARE_JOB_ALIGNED / SO / setting0")
    for label, setting in CLASSICS.items():
        spec = variants.get(label, {})
        if spec != {"mode": label, "profile": "V2", "setting": setting, "extra_args": ["SNAPSHOT_GENOMES"]}:
            raise ValueError("Classical method must use its locked configuration without proprietary mechanisms: " + label)
    for label, spec in variants.items():
        if not isinstance(spec.get("mode"), str) or spec.get("profile") not in ("SO", "V2"):
            raise ValueError("Missing mode or semantic profile: " + label)
        if type(spec.get("setting")) is not int or spec["setting"] not in (0, 1, 2):
            raise ValueError("Every method must explicitly register its classic setting")
        if spec.get("extra_args") != ["SNAPSHOT_GENOMES"]:
            raise ValueError("Every night method must use the identical fixed checkpoint-genome evidence switch")
    seeds = protocol["algorithm_seeds"]
    if len(seeds) != 5 or len(set(seeds)) != 5 or any(type(s) is not int for s in seeds):
        raise ValueError("Exactly five unique new algorithm seeds are required")
    stop = protocol.get("absolute_stop_epoch")
    if not isinstance(stop, (int, float)) or not math.isfinite(stop):
        raise ValueError("An explicit absolute night-stop epoch is required")
    if protocol["wall_cap_seconds"] != 3600 or protocol["runs"] != 30 * len(variants):
        raise ValueError("The one-hour complete-matrix cap cannot change")
    if protocol.get("one_jvm_at_a_time") is not True or protocol.get("fe_checkpoints") != [15000]:
        raise ValueError("Single JVM and fixed FE15000 contract changed")
    rules = read(RULE_SOURCE)
    if any(protocol[key] != rules[key] for key in RULE_KEYS):
        raise ValueError("Current v1 admission thresholds may not be changed")
    if not isinstance(protocol.get("mechanism"), dict) or not protocol["mechanism"]:
        raise ValueError("The fixed hypothesis, intervention and ordinary-control rationale must be declared")
    for pair in protocol.get("additional_pairs", []):
        if len(pair) != 2 or pair[0] == pair[1] or any(label not in variants for label in pair):
            raise ValueError("Malformed predeclared additional comparison")
    names = []
    for interaction in protocol.get("interactions", []):
        names.append(interaction["name"])
        labels = interaction["positive"] + interaction["negative"] + [interaction["normalizer"]]
        if len(interaction["positive"]) != 2 or len(interaction["negative"]) != 2 or any(label not in variants for label in labels):
            raise ValueError("Malformed predeclared factorial interaction")
    if len(names) != len(set(names)):
        raise ValueError("Interaction names must be unique")


def jobs(protocol):
    validate_protocol(protocol)
    rng, result = random.Random(protocol["method_order_seed"]), []
    for instance in protocol["instances"]:
        for seed in protocol["algorithm_seeds"]:
            labels = list(protocol["variants"])
            rng.shuffle(labels)
            result.extend({"phase": protocol["hypothesis"], "instance": instance["stem"],
                "seed": seed, "variant": label, "seconds": instance["time_seconds"]} for label in labels)
    if len(result) != protocol["runs"] or len({(r["instance"], r["seed"], r["variant"]) for r in result}) != len(result):
        raise ValueError("The complete unique randomized-block matrix is required")
    return result


def trial_folder(root, job):
    return root / "trials" / job["phase"] / job["instance"] / str(job["seed"]) / job["variant"]
