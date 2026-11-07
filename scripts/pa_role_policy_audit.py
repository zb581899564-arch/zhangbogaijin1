"""Offline acceptance-policy complements and immediate uses of specialist-only states."""
from collections import Counter, defaultdict
import json

from run_long_budget_bridge import rows
from pa_population_replay import Replay
from pa_population_state_checks import physical
from research.semantic_repair.evidence import digest

TARGETS = {"MAKESPAN": 0, "ENERGY": 1, "WORKER_COST": 2}


def acceptance_pair(role, parent, child, archive_dominated):
    center = all(a <= b for a, b in zip(child, parent)) or not archive_dominated
    own = center if role == "CENTER" else child[TARGETS[role]] < parent[TARGETS[role]]
    return own, center


def check_policy_fixtures():
    fixtures = (("MAKESPAN", [4, 8, 8], True, (True, False)),
                ("MAKESPAN", [6, 4, 4], False, (False, True)),
                ("MAKESPAN", [4, 4, 4], False, (True, True)),
                ("MAKESPAN", [6, 6, 6], True, (False, False)),
                ("ENERGY", [5, 5, 5], False, (False, True)))
    for role, child, dominated, expected in fixtures:
        assert acceptance_pair(role, [5, 5, 5], child, dominated) == expected


class PolicyReplay(Replay):
    def __init__(self, catalog):
        super().__init__(catalog)
        self.policies = defaultdict(Counter)
        self.specialist_only = {}
        self.resident_objectives, self.donor_objectives = set(), set()
        self.first = {}
        self.routes = defaultdict(Counter)
        self.route_admissions = []

    def paid_event(self, event):
        super().paid_event(event)
        if event["kind"] == "initial":
            self.resident_objectives.add(tuple(event["objectives"]))
        if event["archiveFresh"]:
            self.first[tuple(event["objectives"])] = {"role": event["role"],
                "bornFE": event["paidFE"], "accepted": event.get("accepted", True)}

    def event(self, event):
        if event["kind"] == "reencode":
            prior = self.specialist_only.get(event["beforeId"])
            if prior is not None:
                self.specialist_only[event["id"]] = prior
        super().event(event)

    def mix(self, event):
        parent = self.population[event["slot"]]
        donor = self.population[event["donorSlot"]]
        tag = self.specialist_only.get(donor["id"])
        self.donor_objectives.add(tuple(donor["objectives"]))
        super().mix(event)
        own, center = acceptance_pair(event["role"], parent["objectives"], event["objectives"], event["archiveDominated"])
        assert own == event["accepted"]
        if event["role"] != "CENTER":
            key = ("bothAccept" if own and center else "specialistOnlyAccept" if own
                   else "centerOnlyAccept" if center else "bothReject")
            self.policies[event["role"]][key] += 1
            if own and not center:
                self.specialist_only[event["id"]] = {"role": event["role"], "originFE": event["paidFE"]}
            self.policies[event["role"]]["freshArchivePointRejected"] += bool(event["archiveFresh"] and not own)
        if own:
            self.resident_objectives.add(tuple(event["objectives"]))
        if tag and tag["role"] != event["role"]:
            row = self.routes[tag["role"], event["role"]]
            row["reads"] += 1
            changed = physical(event, self.catalog) != physical(parent, self.catalog)
            row["physicalChanges"] += changed
            row["acceptedPhysicalChanges"] += changed and own
            row["freshArchivePoints"] += event["archiveFresh"]
            if changed and event["archiveFresh"]:
                self.route_admissions.append({"source": tag, "receiverRole": event["role"],
                    "bornFE": event["paidFE"], "objectives": event["objectives"], "accepted": own})


def audit_policies(source, stem, identities):
    folder = source / stem / "main/audit"
    for name in ("events.jsonl", "catalog.jsonl", "receipt.jsonl"):
        path = folder / name
        identities[str(path)] = digest(path)
    catalog, = rows(folder / "catalog.jsonl")
    receipt, = rows(folder / "receipt.jsonl")
    replay = PolicyReplay(catalog["tuples"])
    with (folder / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                replay.event(json.loads(line))
    assert replay.paid == receipt["successfulFE"] == receipt["attemptedFE"]
    assert replay.digest.hexdigest() == receipt["paidSHA256"] and receipt["failedFE"] == 0
    assert replay.accepted == receipt["accepted"]
    terminal = set(map(tuple, receipt["internalArchive"]))
    assert terminal == set(map(tuple, replay.archive))
    paths = [r for r in replay.route_admissions if tuple(r["objectives"]) in terminal]
    route_rows = [{"sourceRole": source_role, "receiverRole": receiver, **dict(counts)}
                  for (source_role, receiver), counts in sorted(replay.routes.items())]
    invisible = [replay.first[obj] for obj in sorted(terminal) if obj not in replay.resident_objectives]
    return {"stem": stem, "source": str(folder), "observedPaidFE": replay.paid,
        "policyComparisons": {role: dict(counts) for role, counts in replay.policies.items()},
        "immediateSpecialistOnlyRoutes": route_rows, "terminalRouteExamples": paths,
        "terminalPoints": len(terminal), "terminalObjectivesNeverResident": len(invisible),
        "terminalNeverResidentFirstCallers": dict(Counter(r["role"] for r in invisible)),
        "terminalObjectivesEverUsedAsDonor": len(terminal & replay.donor_objectives),
        "limits": "Direct observed state/genes use only. No transitive ancestry, counterfactual rollout, causal performance gain or new algorithm.",
        "newSearchFE": 0, "decoderCalls": 0}
