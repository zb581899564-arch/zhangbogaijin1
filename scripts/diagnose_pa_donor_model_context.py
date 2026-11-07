"""Zero-FE descriptive replay of model support versus donors in completed engineering fixtures."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random

from run_long_budget_bridge import read, rows, write_once
from pa_paid_donor_replay import BorrowReplay


def entropy(values):
    counts = Counter(values)
    n = len(values)
    return -sum((c / n) * math.log(c / n) for c in counts.values())


def role_information(points, labels):
    groups = {label: [i for i, value in enumerate(labels) if value == label] for label in set(labels)}
    total = 0.
    for job in range(len(points[0]["resources"])):
        values = [point["resources"][job] for point in points]
        total += entropy(values) - sum(len(indices) / len(values) * entropy([values[i] for i in indices])
                                       for indices in groups.values())
    return total / len(points[0]["resources"])


def model_scope(generation, points, donors, catalog):
    labels = [point["role"] for point in points]
    actual = role_information(points, labels)
    rng = random.Random(0x5c37a19 + generation)
    null = []
    for _ in range(64):
        shuffled = labels.copy()
        rng.shuffle(shuffled)
        null.append(role_information(points, shuffled))
    support = [{point["resources"][j] for point in points} for j in range(len(points[0]["resources"]))]
    factory_support = [{catalog[resource][0] for resource in values} for values in support]
    novel = sum(donor["resources"][j] not in seen for donor in donors for j, seen in enumerate(support))
    factory_novel = sum(catalog[donor["resources"][j]][0] not in seen
                        for donor in donors for j, seen in enumerate(factory_support))
    factory_points = [{**point, "resources": [catalog[r][0] for r in point["resources"]]} for point in points]
    return support, factory_support, {"generation": generation, "livePoints": len(points), "memorySlots": len(donors),
                     "roleResourceInformationNatsPerJob": actual,
                     "roleFactoryInformationNatsPerJob": role_information(factory_points, labels),
                     "sameSizeShuffledRoleMean": sum(null) / len(null),
                     "sameSizeShuffledRoleMaximum": max(null),
                     "memoryTupleEntriesOutsideLiveSnapshotSupport": novel,
                     "memoryFactoryEntriesOutsideLearnedMarginalSupport": factory_novel,
                     "memoryJobEntries": len(donors) * len(support),
                     "warning": "Role information is descriptive and finite-sample biased; duplicate and related individuals are not independent samples"}


class ContextReplay(BorrowReplay):
    def __init__(self, catalog, mode, views):
        super().__init__(catalog, mode, views)
        self.scopes, self.support, self.counts, self.outcomes = [], [], {}, []

    def event(self, event):
        super().event(event)
        if event["kind"] == "model":
            self.support, self.factory_support, scope = model_scope(self.generation, self.population, self.donors, self.catalog)
            self.scopes.append(scope)

    def mix(self, event):
        subset = self.subsets[event["subset"]]
        source = event["donorSlot"]
        donor = self.donors[-1 - source] if source < 0 else self.population[source]
        novel = any(donor["resources"][j] not in self.support[j] for j in subset)
        factory_novel = any(self.catalog[donor["resources"][j]][0] not in self.factory_support[j] for j in subset)
        root = len(subset) == len(self.support)
        key = ("memory" if source < 0 else "live", "root" if root else "partial", novel, factory_novel)
        super().mix(event)
        count = self.counts.setdefault(key, Counter())
        count["attempts"] += 1
        count["accepted"] += event["accepted"]
        count["archiveFreshAtEvaluation"] += event["archiveFresh"]
        count["fallbacks"] += event["fallback"]
        self.outcomes.append((key, tuple(event["objectives"])))

    def summary(self):
        final = set(map(tuple, self.archive))
        for key, objectives in self.outcomes:
            self.counts[key]["terminalObjectiveHitsIncludingDuplicates"] += objectives in final
        return {"modelScopes": self.scopes,
                "steps": [{"source": key[0], "subset": key[1], "donorTupleNovelToLiveSnapshot": key[2],
                           "donorFactoryNovelToLearnedMarginal": key[3], **value}
                          for key, value in sorted(self.counts.items())],
                "paidFEReconstructed": self.paid, "paidSHA256": self.digest.hexdigest()}


def audit(folder, mode):
    catalog, = rows(folder / "catalog.jsonl")
    receipt, = rows(folder / "receipt.jsonl")
    with (folder / "borrowed-views.jsonl").open(encoding="utf-8") as views:
        replay = ContextReplay(catalog["tuples"], mode, views)
        with (folder / "events.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                replay.event(json.loads(line))
        assert not views.read().strip()
    assert replay.paid == receipt["successfulFE"]
    assert replay.digest.hexdigest() == receipt["paidSHA256"]
    assert set(map(tuple, replay.archive)) == set(map(tuple, receipt["internalArchive"]))
    return replay.summary()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()
    fixtures = []
    for stem in ("20_8_5_1", "100_2_3_1"):
        for mode in ("NONE", "GRAFT"):
            result = audit(root / stem / ("ENGINEERING-" + mode) / "audit", mode)
            fixtures.append({"stem": stem, "mode": mode, **result})
            print(stem, mode, result["modelScopes"])
    result = {"status": "complete", "newSearchFE": 0, "newDecoderCalls": 0,
              "fixtures": fixtures,
              "scope": "Existing two-generation engineering fixtures only; different initialization and teacher source from the scientific arms",
              "interpretation": "FMW tuple support and learned factory marginals are different: current PaDependencyModel uses factory and priorities, not machine/worker entropy. Neither role information nor novelty proves erroneous dependencies or causal performance",
              "revision": "v1 ambiguous ModelSupport/NovelToGenerationModel labels described full FMW live-state support, not the actual factory marginal. Retained v1 numbers are not false, but those names must not be used to infer unseen learned categories. v2 separates both scopes without new FE",
              "nextPaidMechanismAuthorizedByThisDiagnosis": False, "goalAchieved": False}
    write_once(root / "donor-model-context-diagnosis-v2.json", result)


if __name__ == "__main__":
    main()
