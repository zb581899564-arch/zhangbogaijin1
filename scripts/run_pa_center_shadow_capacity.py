"""Observe already-paid CENTER-compatible lineage shadows and exact whole-root decisions, zero FE."""
from collections import Counter
from datetime import datetime
import json

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from pa_population_replay import Replay
from pa_population_state_checks import physical

SOURCE = ROOT / "runs/pa-role-acceptance-probe-20261106-011839-887122"


def center_accept(objectives, parent, archive):
    weak = all(a <= b for a, b in zip(objectives, parent))
    dominated = bool(np.any(np.all(archive <= objectives, axis=1) & np.any(archive < objectives, axis=1)))
    return weak or not dominated


class ShadowCapacity(Replay):
    def __init__(self, catalog):
        super().__init__(catalog)
        self.shadows, self.root_counts, self.examples = [], Counter(), []
        self.all_center_alias_checks = 0

    def event(self, event):
        super().event(event)
        if event["kind"] == "initial":
            self.shadows.append(event)
        elif event["kind"] == "reencode":
            slot = event["slot"]
            if self.shadows[slot]["id"] == event["beforeId"]:
                self.shadows[slot] = event

    def root_opportunity(self, event, parent, working, shadow):
        counts = self.root_counts
        counts["centerRootReads"] += 1
        changed = physical(working, self.catalog) != physical(shadow, self.catalog)
        if working["role"] == "CENTER":
            assert not changed and working["id"] == shadow["id"]
            counts["centerSourceAliasChecks"] += 1
            return
        counts["professionalRootReads"] += 1
        counts["differentPhysicalShadow"] += changed
        a = center_accept(working["objectives"], parent["objectives"], self.archive)
        b = center_accept(shadow["objectives"], parent["objectives"], self.archive)
        assert a == event["accepted"]
        label = "bothAccepted" if a and b else "workingOnly" if a else "shadowOnly" if b else "bothRejected"
        counts[label] += 1
        if a != b and len(self.examples) < 12:
            self.examples.append({"candidateFE": event["paidFE"], "sourceSlot": event["donorSlot"],
                                  "receiverSlot": event["slot"], "workingBornFE": working["paidFE"],
                                  "shadowBornFE": shadow["paidFE"], "label": label})

    def mix(self, event):
        slot = event["slot"]
        parent = self.population[slot]
        if len(self.subsets[event["subset"]]) == len(parent["resources"]) and parent["role"] == "CENTER":
            source = event["donorSlot"]
            self.root_opportunity(event, parent, self.population[source], self.shadows[source])
        super().mix(event)
        shadow = self.shadows[slot]
        # Notification is explicitly from the archive before this already-paid candidate's insertion.
        if all(a <= b for a, b in zip(event["objectives"], shadow["objectives"])) or not event["archiveDominated"]:
            self.shadows[slot] = event
        if parent["role"] == "CENTER":
            assert self.shadows[slot]["id"] == self.population[slot]["id"]
            self.all_center_alias_checks += 1


def analyze(folder, mode):
    catalog, = rows(folder / "catalog.jsonl")
    receipt, = rows(folder / "receipt.jsonl")
    replay = ShadowCapacity(catalog["tuples"])
    with (folder / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            replay.event(json.loads(line))
    assert replay.paid == receipt["successfulFE"] and replay.digest.hexdigest() == receipt["paidSHA256"]
    assert set(map(tuple, replay.archive)) == set(map(tuple, receipt["internalArchive"]))
    counts = dict(replay.root_counts)
    if mode == "CENTER":
        assert counts.get("professionalRootReads", 0) == 0
        assert counts["centerSourceAliasChecks"] == counts["centerRootReads"]
    opportunities = counts.get("professionalRootReads", 0)
    net = (counts.get("shadowOnly", 0) - counts.get("workingOnly", 0)) / opportunities if opportunities else 0.
    changed = counts.get("differentPhysicalShadow", 0) / opportunities if opportunities else 0.
    return {"mode": mode, "rootCounts": counts, "netShadowAcceptanceFraction": net,
            "differentPhysicalShadowFraction": changed, "centerWorkingShadowAliasChecks": replay.all_center_alias_checks,
            "paidFEReconstructed": replay.paid, "paidSHA256": replay.digest.hexdigest(), "examples": replay.examples,
            "capacityCondition": bool(opportunities and net >= .05 and changed >= .20)}


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-center-shadow-capacity-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        plan = {"version": "PA_CENTER_SHADOW_ROOT_CAPACITY-v1", "registered": "2026-11-06", "source": str(SOURCE),
                "scope": "Already-paid native two-generationFOUR/CENTERfixtures, not scientific50ktraces",
                "shadow": "Perowner mostrecent candidate accepted by CENTERweakParetoORoldarchive-not-dominated, whether specialist workingstream accepted it or not; no effecton originalwork",
                "comparison": "At existing CENTERrootreads, compare known workandshadowcompletegenomesagainst sameactualparentandoldarchive; no invented partialcandidate/objective",
                "capacityCondition": "BothFOURinstances require >=20% professionalroots with differentphysicalshadow and >=5percentagepoints netshadowOnly-minus-workingOnlyacceptance. Engineeringresource screen only, not causalperformanceorcontributiongate",
                "negativeControl": "CENTERmode shadows must be exactaliases ofworkingstates and allrootdonors; no random or populationstatechanges",
                "limits": "Acceptanceopportunity is not subsequentprogramquality; wholeknownstates only. No newdonor, model, memorystate insearch, decoderorFE; no sourceproduction freebie",
                "newSearchFE": 0, "newDecoderCalls": 0}
        write_once(root / "protocol.json", plan)
        results = []
        for stem in ("20_8_5_1", "100_2_3_1"):
            for mode in ("FOUR", "CENTER"):
                result = {"stem": stem, **analyze(SOURCE / stem / ("ENGINE-" + mode) / "audit", mode)}
                results.append(result)
                print("PA_CENTER_SHADOW_CAPACITY", stem, result, flush=True)
        supported = all(r["capacityCondition"] for r in results if r["mode"] == "FOUR")
        write_once(root / "analysis.json", {"fixtures": results, "capacityConditionMet": supported,
                                          "newSearchFE": 0, "newDecoderCalls": 0, "goalAchieved": False})
        write_once(root / "status.json", {"status": "COMPLETE", "capacityConditionMet": supported,
                                         "newSearchFE": 0, "newDecoderCalls": 0})
        print("PA_CENTER_SHADOW_CAPACITY_COMPLETE", root, supported, flush=True)


if __name__ == "__main__":
    main()
