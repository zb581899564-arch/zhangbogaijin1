"""Read-only accounting/class audit and visibility of specialist bridge states."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from pa_specialist_bridge_build import INTERFACE
from pa_capability_support import SOURCE, fees
from pa_role_policy_audit import acceptance_pair
from research.semantic_repair.evidence import digest

PROBE = ROOT / "runs/pa-specialist-bridge-probe-20261105-212900-801483"
ENGINE = ROOT / "runs/pa-population-engineering-20261105-164116-698339"


def check_paid_runs():
    completed, checked = [], []
    population_hash = read(PROBE / "class-hashes.json")["org/uma/jmetal/util/research/modelglobal/PaPopulation.class"]
    for path in sorted(PROBE.rglob("run-receipt.jsonl")):
        folder = path.parent
        stem = folder.relative_to(PROBE).parts[0]
        receipt, = rows(path)
        assert receipt["successful"] == receipt["attempted"] == receipt["decoder"]["dynamic.evaluations"]
        assert receipt["failed"] == receipt["timeInterruptedAttempts"] == 0
        identity, = rows(folder / "loaded-identity.jsonl")
        previous, = rows(INTERFACE / stem / "PARITY/loaded-identity.jsonl")
        count = 0
        for name, prior in previous.items():
            if isinstance(prior, dict) and "sha256" in prior:
                expected = population_hash if name.endswith(".PaPopulation") else prior["sha256"]
                assert identity[name]["sha256"] == expected, (folder, name)
                count += 1
        assert identity["javaVersion"] == previous["javaVersion"] == "17.0.12"
        validation = read(folder / "checkpoint-validation.json")
        assert validation["status"] == "passed" and validation["allReachedPointsCovered"]
        completed.append((folder, receipt))
        checked.append({"run": str(folder.relative_to(PROBE)), "successfulFE": receipt["successful"],
            "delegateEvaluationsEqual": True, "recordedClassIdentitiesChecked": count,
            "fullQA": validation["uniqueOfflineDecodes"]})
    assert len(checked) == 32
    total = fees(completed)
    assert total["successfulFE"] == total["attemptedFE"] == 764800 and total["failedAttempts"] == 0
    inputs = {}
    for stem in ("20_8_5_1", "100_2_3_1"):
        for path in sorted((PROBE / stem / "inputs").glob("*")):
            if path.is_file():
                assert digest(path) == digest(SOURCE / stem / "inputs" / path.name)
                inputs[str(path.relative_to(PROBE))] = digest(path)
    return {"runs": checked, **total, "inputsMatchFrozenSource": inputs,
        "recordedClassIdentitiesAllMatch": True, "additionalSearchFE": 0, "decoderCalls": 0}


def visibility(stem):
    path = ENGINE / stem / "main/audit/events.jsonl"
    aliases, states = {}, {}
    read_any, read_cross, models, endpoints = set(), set(), set(), set()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            if event["kind"] == "reencode" and event["beforeId"] in aliases:
                aliases[event["id"]] = aliases[event["beforeId"]]
            elif event["kind"] == "model":
                models.update(aliases[p["id"]] for p in event["population"] if p["id"] in aliases)
            elif event["kind"] == "programEnd":
                if event["result"]["id"] in aliases:
                    endpoints.add(aliases[event["result"]["id"]])
            elif event["kind"] == "step":
                if event["donorId"] in aliases:
                    origin = aliases[event["donorId"]]
                    read_any.add(origin)
                    if states[origin]["role"] != event["role"]:
                        read_cross.add(origin)
                own, center = acceptance_pair(event["role"], event["parentObjectives"], event["objectives"], event["archiveDominated"])
                assert own == event["accepted"]
                if own and not center:
                    origin = event["paidFE"]
                    aliases[event["id"]] = origin
                    states[origin] = {"role": event["role"], "bornFE": origin, "generation": event["generation"], "slot": event["slot"]}
    totals = Counter(row["role"] for row in states.values())
    source_summary = []
    for role in ("MAKESPAN", "ENERGY", "WORKER_COST"):
        keys = {fe for fe, row in states.items() if row["role"] == role}
        source_summary.append({"role": role, "acceptedSpecialistOnly": len(keys),
            "everAnyDonor": len(keys & read_any), "everCrossRoleDonor": len(keys & read_cross),
            "everEnteredModel": len(keys & models), "everProgramEndpoint": len(keys & endpoints),
            "neverCrossRoleDonor": len(keys - read_cross),
            "neitherCrossRoleDonorNorModel": len(keys - read_cross - models)})
    return {"stem": stem, "eventSHA256": digest(path), "acceptedSpecialistOnly": sum(totals.values()),
        "everCrossRoleDonor": len(read_cross), "neverCrossRoleDonor": len(states) - len(read_cross),
        "neitherCrossRoleDonorNorModel": len(set(states) - read_cross - models), "byRole": source_summary,
        "limits": "No cross-role/model exposure is not no use: all accepted states continue the same-slot trajectory. Engineering fixtures only, no causal value of hidden states."}


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        assert read(PROBE / "status.json")["status"] == "COMPLETE"
        root = ROOT / "runs" / datetime.now().strftime("pa-specialist-bridge-review-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        print("PA_BRIDGE_REVIEW_ROOT", root, flush=True)
        write_once(root / "protocol.json", {"source": str(PROBE), "engineering": str(ENGINE),
            "purpose": "Independent accounting/class check plus exploratory transient-state visibility counts",
            "sampling": "All32probe runs and both complete engineering mains; no cutoff prefix counts",
            "visibility": "Latest specialist-only acceptance state, plus physical-neutral reencoding aliases; direct donor/model/endpoint exposure only",
            "newSearchFE": 0, "decoderCalls": 0, "noNewPerformanceGate": True})
        shutil.copy2(Path(__file__), root / Path(__file__).name)
        try:
            checked = check_paid_runs()
            flows = [visibility(stem) for stem in ("20_8_5_1", "100_2_3_1")]
            write_once(root / "accounting.json", checked)
            write_once(root / "visibility.json", {"instances": flows, "newSearchFE": 0, "decoderCalls": 0,
                "hiddenStateValueProved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "newSearchFE": 0, "decoderCalls": 0, "goalAchieved": False})
        print("PA_BRIDGE_REVIEW_COMPLETE", [(r["stem"], r["acceptedSpecialistOnly"], r["neverCrossRoleDonor"]) for r in flows], flush=True)


if __name__ == "__main__":
    main()
