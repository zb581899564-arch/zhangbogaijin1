"""Reconstruct immediate cross-role state reads from already validated engineering logs."""
from collections import Counter, defaultdict
import json

from run_long_budget_bridge import read, rows
from pa_population_replay import Replay
from pa_population_state_checks import physical
from research.semantic_repair.evidence import digest

ROLES = ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST")


def caller(fe, jobs):
    if fe < 1:
        raise ValueError("Unpaid state")
    if fe <= 100:
        return "INITIAL"
    slot = ((fe - 101) // (2 * jobs - 1)) % 100
    return ROLES[0] if slot < 15 else ROLES[1] if slot < 70 else ROLES[2] if slot < 85 else ROLES[3]


def exposure(endpoint, jobs):
    """Exact per-role proposal exposure, including partial slots and generations."""
    sets = 2 * jobs - 1
    cycles, tail = divmod(max(0, endpoint - 100), 100 * sets)
    fees = Counter(INITIAL=min(100, endpoint))
    for slot in range(100):
        role = caller(101 + slot * sets, jobs)
        fees[role] += cycles * sets + max(0, min(sets, tail - slot * sets))
    assert sum(fees.values()) == endpoint
    return dict(fees)


class FlowReplay(Replay):
    def __init__(self, catalog):
        super().__init__(catalog)
        self.flows = defaultdict(Counter)
        self.first = {}
        self.fee_callers = Counter()
        self.checked_callers = 0

    def paid_event(self, event):
        super().paid_event(event)
        birth_role = caller(event["paidFE"], len(event["resources"]))
        if event["kind"] == "step":
            assert event["role"] == birth_role
            self.checked_callers += 1
        self.fee_callers[birth_role] += 1
        if event["archiveFresh"]:
            key = tuple(event["objectives"])
            assert key not in self.first
            self.first[key] = {"caller": birth_role, "bornFE": event["paidFE"],
                               "acceptedInternally": event.get("accepted")}

    def mix(self, event):
        parent = self.population[event["slot"]]
        donor = self.population[event["donorSlot"]]
        subset = self.subsets[event["subset"]]
        super().mix(event)
        row = self.flows[donor["role"], event["role"]]
        row["reads"] += 1
        row["accepted"] += event["accepted"]
        changed = physical(event, self.catalog) != physical(parent, self.catalog)
        row["physicalChanged"] += changed
        row["physicalChangedAccepted"] += changed and event["accepted"]
        row["freshChangedDonorReads"] += event["donorChangedThisGeneration"]
        row["freshChangedDonorAcceptedPhysicalChange"] += bool(
            event["donorChangedThisGeneration"] and changed and event["accepted"])
        row["freshArchivePoint"] += event["archiveFresh"]
        row["freshArchivePointRejectedInternally"] += event["archiveFresh"] and not event["accepted"]
        if len(subset) == len(event["resources"]):
            # A root move exactly copies an already evaluated donor; archive
            # admission cannot be new, although the receiver can still accept it.
            assert event["hash"] == donor["hash"] and not event["archiveFresh"]
            row["rootReads"] += 1
            row["rootAccepted"] += event["accepted"]


def engineering_flow(root, stem, identities):
    folder = root / stem / "main/audit"
    for name in ("events.jsonl", "catalog.jsonl", "receipt.jsonl", "independent-replay.json"):
        path = folder / name
        identities[str(path)] = digest(path)
    catalog, = rows(folder / "catalog.jsonl")
    receipt, = rows(folder / "receipt.jsonl")
    assert read(folder / "independent-replay.json")["allPaidStatesAndAcceptanceReconstructed"]
    replay = FlowReplay(catalog["tuples"])
    with (folder / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                replay.event(json.loads(line))
    assert receipt["status"] == "COMPLETE" and receipt["failedFE"] == 0
    assert replay.paid == receipt["successfulFE"] == receipt["attemptedFE"]
    assert replay.digest.hexdigest() == receipt["paidSHA256"]
    assert replay.accepted == receipt["accepted"] and replay.changed_reads == receipt["changedCurrentGenerationDonorReads"]
    assert dict(replay.fee_callers) == exposure(replay.paid, len(replay.population[0]["resources"]))
    terminal = {tuple(point) for point in receipt["internalArchive"]}
    assert terminal == set(map(tuple, replay.archive))
    callers = Counter(replay.first[obj]["caller"] for obj in terminal)
    rejected = Counter(replay.first[obj]["caller"] for obj in terminal
                       if replay.first[obj]["acceptedInternally"] is False)
    flows = [{"donorRole": donor, "receiverRole": receiver, **dict(counts)}
             for (donor, receiver), counts in sorted(replay.flows.items())]
    cross = Counter()
    for row in flows:
        if row["donorRole"] != row["receiverRole"]:
            cross.update({key: value for key, value in row.items() if isinstance(value, int)})
    return {"stem": stem, "source": str(folder), "engineeringFixtureNotPerformanceSample": True,
        "observedPaidFE": replay.paid, "checkedCallerFormulaSteps": replay.checked_callers,
        "proposalExposure": dict(replay.fee_callers), "flows": flows, "crossRoleTotals": dict(cross),
        "terminalPointsByFirstCaller": dict(callers), "terminalFirstCallerRejectedInternally": dict(rejected),
        "rootNewArchivePointCount": 0, "causalRoleBenefitProved": False}
