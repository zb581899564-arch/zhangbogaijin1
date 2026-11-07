"""Independent field masks and live compatible donor reconstruction; reuse validated archive/model checks."""
from collections import Counter
import hashlib
import json

import numpy as np

from run_long_budget_bridge import read, rows, write_once
from pa_population_replay import Replay
from pa_population_state_checks import identity, paid_bytes, snapshot

KINDS = ("RESOURCE", "MACHINE", "WORKER", "ORDER")


def apply_mask(catalog, parent, donor, jobs, kind, basis, no_donor=False):
    resources, keys = parent["resources"].copy(), parent["keys"].copy()
    if no_donor: return resources, keys, False
    full = kind == "JOBS" or basis == "SHAM_BLOCK"
    reverse = {tuple(t): i for i, t in enumerate(catalog)}
    for job in jobs:
        a, b = catalog[resources[job]], catalog[donor["resources"][job]]
        if full:
            resources[job], keys[job] = donor["resources"][job], donor["keys"][job]
        elif kind == "RESOURCE": resources[job] = donor["resources"][job]
        elif kind == "MACHINE":
            assert a[0] == b[0]
            resources[job] = reverse[a[0], b[1], a[2]]
        elif kind == "WORKER":
            assert a[0] == b[0]
            resources[job] = reverse[a[0], a[1], b[2]]
        elif kind == "ORDER":
            assert a[0] == b[0]
            keys[job] = donor["keys"][job]
        else: raise ValueError(kind)
    missing = len({catalog[r][0] for r in resources}) != max(t[0] for t in catalog) + 1
    return (parent["resources"], parent["keys"], True) if missing else (resources, keys, False)


class TypedReplay(Replay):
    def __init__(self, catalog, basis, trace):
        super().__init__(catalog)
        self.basis, self.trace, self.kinds = basis, trace, []
        self.typed_counts = Counter()
        self.novelty = [set() for _ in range(len(catalog))]  # replaced at first initial

    def event(self, event):
        super().event(event)
        if event["kind"] == "initial":
            if len(self.population) == 1: self.novelty = [set() for _ in event["resources"]]
            for j, r in enumerate(event["resources"]): self.novelty[j].add(r)
        elif event["kind"] == "model":
            self.kinds = ["JOBS"] * len(self.subsets)
            if self.basis != "ATOM":
                n = len(self.population[0]["resources"])
                self.subsets += [[j] for kind in KINDS for j in range(n)]
                self.kinds += [kind for kind in KINDS for _ in range(n)]

    def mix(self, event):
        meta = json.loads(next(self.trace))
        assert self.phase == "MIXING" and event["generation"] == self.generation
        slot, donor_slot, subset_index = event["slot"], event["donorSlot"], event["subset"]
        if slot != self.current_slot:
            assert slot == self.current_slot + 1 and event["step"] == 0
            self.current_slot = slot; self.used_subsets.clear()
        assert event["step"] == len(self.used_subsets) and subset_index not in self.used_subsets
        self.used_subsets.add(subset_index)
        jobs, kind = self.subsets[subset_index], self.kinds[subset_index]
        for key in ("generation", "slot", "step", "donorSlot", "paidFE"): assert meta[key] == event[key]
        assert meta["termIndex"] == subset_index and meta["kind"] == kind and meta["jobs"] == jobs
        parent = self.population[slot]
        if kind in ("MACHINE", "WORKER", "ORDER"):
            f = self.catalog[parent["resources"][jobs[0]]][0]
            eligible = [i for i, p in enumerate(self.population) if i != slot and self.catalog[p["resources"][jobs[0]]][0] == f]
        else: eligible = [i for i in range(len(self.population)) if i != slot]
        assert meta["eligibleCount"] == len(eligible)
        if eligible:
            assert 0 <= meta["rank"] < len(eligible) and donor_slot == eligible[meta["rank"]]
            donor = self.population[donor_slot]
        else:
            assert donor_slot == meta["rank"] == -1
            donor = parent; self.typed_counts["noCompatibleDonor"] += 1
        for name, state in (("parent", parent), ("donor", donor)):
            assert event[name + "Id"] == state["id"] and event[name + "Hash"] == state["hash"]
        assert event["parentObjectives"] == parent["objectives"] and event["role"] == parent["role"]
        resources, keys, missing = apply_mask(self.catalog, parent, donor, jobs, kind, self.basis, not eligible)
        assert event["fallback"] == missing
        event["resources"], event["keys"] = resources, keys
        if missing or not eligible: assert event["objectives"] == parent["objectives"]
        self.birth(event); self.paid_event(event)
        target = {"MAKESPAN": 0, "ENERGY": 1, "WORKER_COST": 2}.get(event["role"])
        accept = (all(a <= b for a, b in zip(event["objectives"], parent["objectives"])) or not event["archiveDominated"]) if target is None else event["objectives"][target] < parent["objectives"][target]
        assert event["accepted"] == accept
        fresh, changed = donor["id"] in self.accepted_ids, donor["id"] in self.changed_ids
        assert event["donorAcceptedThisGeneration"] == fresh and event["donorChangedThisGeneration"] == changed
        self.fresh_reads += fresh; self.changed_reads += changed
        if accept:
            self.population[slot] = event; self.accepted_ids.add(event["id"]); self.accepted += 1
            if event["hash"] != parent["hash"]: self.changed_ids.add(event["id"])
        self.typed_counts[kind] += 1
        self.typed_counts["pointsWithInitialUnseenTuple"] += any(r not in self.novelty[j] for j, r in enumerate(resources))
        self.fallbacks += missing; self.unchanged += event["hash"] == parent["hash"]; self.fees["mixing"] += 1


def audit(folder, basis):
    catalog, = rows(folder / "catalog.jsonl"); receipt, = rows(folder / "receipt.jsonl")
    with (folder / "typed-steps.jsonl").open(encoding="utf-8") as trace:
        replay = TypedReplay(catalog["tuples"], basis, trace)
        with (folder / "events.jsonl").open(encoding="utf-8") as events:
            for line in events: replay.event(json.loads(line))
        assert not trace.read().strip()
    assert receipt["status"] == "COMPLETE" and receipt["successfulFE"] == receipt["attemptedFE"] == replay.paid == receipt["paidFullTimelineQA"]
    assert receipt["failedFE"] == 0 and receipt["paidSHA256"] == replay.digest.hexdigest()
    assert receipt["reencodingFullTimelineQA"] == replay.neutral
    for key, value in (("accepted", replay.accepted), ("fallbacks", replay.fallbacks), ("completeRawDuplicates", replay.duplicates),
                       ("currentGenerationDonorReads", replay.fresh_reads), ("changedCurrentGenerationDonorReads", replay.changed_reads),
                       ("completedGenerations", replay.generations), ("completedPrograms", replay.programs)):
        assert receipt[key] == value, (key, receipt[key], value)
    assert receipt["fees"] == dict(replay.fees)
    for saved, actual in zip(receipt["lastPopulation"], replay.population): snapshot(saved, actual)
    expected = set(map(tuple, replay.archive))
    assert set(map(tuple, receipt["internalArchive"])) == expected
    assert {tuple(p["objectives"]) for p in receipt["lastValidFront"]} == expected
    result = {"allPaidGenomesMasksDonorsAcceptanceAndArchiveReconstructed": True, "basis": basis,
        "successfulFE": replay.paid, "paidSHA256": replay.digest.hexdigest(), "programs": replay.programs,
        "generations": replay.generations, "modelChecks": replay.models, "typedCounts": dict(replay.typed_counts),
        "prefixPaidSHA256": {str(k): v for k, v in replay.prefixes.items()}, "newSearchFE": 0, "decoderCalls": 0}
    write_once(folder / "independent-typed-replay.json", result)
    return result


def audit_fixtures(folder, catalog_path):
    catalog, = rows(catalog_path); catalog = catalog["tuples"]
    initial, counts, novel = [], Counter(), Counter()
    digest = hashlib.sha256(); seen = []
    for event in rows(folder / "fixtures.jsonl"):
        point = event["state"]; assert point["hash"] == identity(point)
        digest.update(paid_bytes(point, catalog, point["paidFE"]))
        if event["kind"] == "initial":
            assert point["paidFE"] == len(initial) + 1
            initial.append(point)
            if not seen: seen = [set() for _ in point["resources"]]
            for j, r in enumerate(point["resources"]): seen[j].add(r)
        else:
            assert len(initial) == 100
            parent = initial[event["receiver"]]
            donor = parent if event["donor"] < 0 else initial[event["donor"]]
            assert event["poolScope"] == ("SINGLE_RECEIVER" if event["donor"] < 0 else "ALL_INITIAL")
            if event["donor"] >= 0: assert event["donor"] != event["receiver"]
            resources, keys, fallback = apply_mask(catalog, parent, donor, event["jobs"], event["type"], "TYPED", event["donor"] < 0)
            assert (resources, keys, fallback) == (point["resources"], point["keys"], event["fallback"])
            counts[event["type"]] += 1
            counts["noCompatibleDonor"] += event["donor"] < 0
            novel[event["type"]] += any(r not in seen[j] for j, r in enumerate(resources))
    receipt, = rows(folder / "receipt.jsonl")
    assert receipt["status"] == "COMPLETE" and receipt["successfulFE"] == receipt["attemptedFE"] == receipt["fullDecoderQA"] == 164
    assert receipt["failedFE"] == 0 and receipt["paidSHA256"] == digest.hexdigest()
    assert counts["noCompatibleDonor"] == 4 and all(counts[kind] == 16 for kind in KINDS)
    result = {"allFieldMasksAndPaidSequenceVerified": True, "successfulFE": 164, "fixtureCounts": dict(counts),
        "proposalsWithUnseenInitialTuple": dict(novel), "newSearchFE": 0, "decoderCalls": 0}
    write_once(folder / "independent-fixtures.json", result)
    return result
