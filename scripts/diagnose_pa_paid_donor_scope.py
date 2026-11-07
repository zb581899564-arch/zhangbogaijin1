"""Read-only source exposure, imported tuple support and already-known-front diagnostics."""
import argparse
import csv
from pathlib import Path

from run_long_budget_bridge import read, rows, write_once
from pa_paid_donor_data import at, initial_records
import numpy as np


def ledger_prefix(folder, limit):
    receipt, = rows(folder / "run-receipt.jsonl")
    search = receipt["search"]
    initial = search["initialization.evaluations"]
    global_fe = search["global.evaluations"]
    assert initial + global_fe == 5100
    with (folder / "local-ledger.csv").open(encoding="utf-8-sig", newline="") as stream:
        slots = list(csv.DictReader(stream))
    assert sum(int(slot["paid"]) for slot in slots) + initial + global_fe == receipt["successful"]
    remaining = limit - initial - global_fe
    groups, boundary = {}, None
    for slot in slots:
        consumed = min(remaining, int(slot["paid"]))
        group = slot["group"]
        groups[group] = groups.get(group, 0) + consumed
        remaining -= consumed
        boundary = {**slot, "consumedAtPrefix": consumed,
                    "partiallyConsumed": consumed < int(slot["paid"])}
        if not remaining:
            break
    assert not remaining and sum(groups.values()) + initial + global_fe == limit
    return {"prefixFE": limit, "initialFE": initial, "globalFE": global_fe,
            "localFEByPhysicalGroup": groups, "boundary": boundary}


def job_tuples(point):
    return {job: (factory, machine, worker)
            for job, factory, machine, worker in zip(point["JS"], point["FA"], point["MA"], point["WA"])}


def pool_support(initial, pool):
    initial_sets = [set() for _ in initial[0]["JS"]]
    donor_sets = [set() for _ in initial_sets]
    for data, support in ((initial, initial_sets), (pool, donor_sets)):
        for point in data:
            for job, value in job_tuples(point).items():
                support[job].add(value)
    novel = [len(donor - seen) for donor, seen in zip(donor_sets, initial_sets)]
    return {"jobs": len(novel), "jobsWithNovelTuple": sum(n > 0 for n in novel),
            "distinctNovelJobTuples": sum(novel),
            "totalDistinctDonorJobTuples": sum(map(len, donor_sets)),
            "note": "Resource repertoire only, not schedule reachability or objective quality"}


def already_known(source, receiver):
    source = np.unique(np.asarray(source, float), axis=0)
    receiver = np.unique(np.asarray(receiver, float), axis=0)
    equal = strict = 0
    for point in receiver:
        same = np.any(np.all(source == point, axis=1))
        dominated = np.any(np.all(source <= point, axis=1) & np.any(source < point, axis=1))
        assert not (same and dominated)  # Source is itself a non-dominated archive.
        equal += int(same)
        strict += int(dominated)
    return {"privateFrontSize": len(receiver), "strictlyDominatedBySource": strict,
            "equalToSource": equal, "notWeaklyCoveredBySource": len(receiver) - strict - equal,
            "strictlyDominatedFraction": strict / len(receiver),
            "scope": "Terminal private result front; does not count all accepted states or prove an acceptance bottleneck"}


def context(root, spec, seed):
    folder = root / spec["stem"] / str(seed)
    initial = initial_records(folder / "SOURCE_S")
    result = {"stem": spec["stem"], "seed": seed, "sources": []}
    for source in ("S", "U", "N"):
        source_folder = folder / ("SOURCE_" + source)
        prefix, genes = at(source_folder, 50000)
        provenance = read(folder / ("teachers-" + source + ".provenance.json"))
        pool = [genes[index] for index in provenance["selectedIndices"]]
        receivers = []
        for method, name in (("NONE", "PURE"), ("INIT", "INIT_GRAFT"),
                             ("GRAFT", "GRAFT_" + source), ("INHERIT", "INHERIT_" + source)):
            receiver, _ = at(folder / name, 50000)
            receivers.append({"method": method, **already_known(prefix["front"], receiver["front"])})
        result["sources"].append({"source": source, "sourcePrefixFrontSize": len(genes),
                                  "at50000": ledger_prefix(source_folder, 50000),
                                  "at100000": ledger_prefix(source_folder, 100000),
                                  "sampledPoolSupport": pool_support(initial, pool), "receiverFronts": receivers})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    plan = read(root / "protocol.json")
    result = {"status": "complete", "newSearchFE": 0, "newDecoderCalls": 0,
              "exploratoryDiagnosisOnly": True,
              "contexts": [context(root, spec, seed) for spec in plan["instances"] for seed in plan["seeds"]],
              "limitations": ["Original recipient-private archive is a design choice, not an implementation error",
                              "Final front redundancy is not a count of waste or a causal search explanation",
                              "Professional source means original role preferences; not all roles have performed local search by50000",
                              "No donor ratio, source timing or endpoint gate changed; failed protocol remains stopped"]}
    write_once(root / "source-scope-diagnosis.json", result)
    for item in result["contexts"]:
        for source in item["sources"]:
            print(item["stem"], item["seed"], source["source"],
                  source["at50000"]["localFEByPhysicalGroup"], source["sampledPoolSupport"],
                  [(r["method"], r["strictlyDominatedBySource"], r["privateFrontSize"], r["equalToSource"])
                   for r in source["receiverFronts"]])


if __name__ == "__main__":
    main()
