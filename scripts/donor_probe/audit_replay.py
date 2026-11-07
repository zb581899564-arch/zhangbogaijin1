"""Independent exact Pareto ledger and live-state replay of every paid proposal."""
from collections import Counter, defaultdict
import hashlib
import math
import struct
import numpy as np

from analysis_common import json_lines, read_json, require, state
from audit_genome import JavaRandom, proposal_seed, verify_mix


OBJECTIVE_ROLE = {"MAKESPAN": 0, "ENERGY": 1, "WORKER_COST": 2}


def sorted_points(points):
    array = np.asarray(points, dtype=float)
    require(array.ndim == 2 and array.shape[1] == 3 and np.isfinite(array).all(), "Invalid objective matrix")
    return sorted(map(tuple, array))


class ParetoLedger:
    def __init__(self, initial):
        self.points = np.empty((0, 3))
        for row in initial:
            self.offer(row)
        require(sorted_points(self.points) == sorted_points(initial), "A0 is not a unique exact ND archive")

    def offer(self, raw):
        child = np.asarray(raw, dtype=float)
        require(child.shape == (3,) and np.isfinite(child).all(), "Nonfinite child objectives")
        weak = np.all(self.points <= child, axis=1)
        identical = np.all(self.points == child, axis=1)
        dominated, equal = bool(np.any(weak & ~identical)), bool(np.any(identical))
        admitted = not dominated and not equal
        if admitted:
            remove = np.all(child <= self.points, axis=1) & np.any(child != self.points, axis=1)
            self.points = np.vstack((self.points[~remove], child))
        return dict(dominated=dominated, equal=equal, admitted=admitted)


def update_paid_digest(digest, step):
    digest.update(struct.pack(">q", step["fe"]))
    for name in ("JS", "FA", "MA", "WA"):
        values = step[name]
        digest.update(struct.pack(">i", len(values)))
        digest.update(struct.pack(">" + "i" * len(values), *values))
    digest.update(struct.pack(">ddd", *step["objectives"]))


def validate_models(models, before, jobs, factories):
    require(set(models) == {str(r["family"]) for r in before}, "Wrong model families")
    for family, masks in models.items():
        require(len(masks) == 2 * jobs - (1 if int(family) < 0 else factories), "Incomplete family FOS")
        for mask in masks:
            require(bool(mask) and all(type(j) is int and 0 <= j < jobs for j in mask)
                    and len(mask) == len(set(mask)), "Invalid job-index subset mask")
    expected = sum(len(models[str(r["family"])]) for r in before)
    require(expected == 100 * (2 * jobs - 1) - 20 * (factories - 1), "Wrong complete-pass FE")
    return expected


def receipt_check(receipt, source_seed, arm, expected):
    require(receipt["mode"] == arm and receipt["sourceSeed"] == source_seed
            and receipt["seed"] == source_seed ^ 0x51D0A7E3, "Wrong receipt mode or seed")
    require(receipt["attempted"] == receipt["successful"] == receipt["expectedFE"] == expected
            and receipt["failed"] == 0, "Partial/failed/nonmatching pass cannot enter science")
    require(receipt.get("error") is None, "Receipt preserved a search error")
    seconds = receipt["searchSeconds"]
    require(math.isfinite(seconds) and seconds > 0, "Invalid measured search duration")


def donor_pool(before, views, slot, arm):
    family = before[slot]["family"]
    live = [("R", r["slot"]) for r in before if r["family"] == family and r["slot"] != slot]
    external = [(v["source"], v["id"]) for v in views if v["family"] == family
                and (arm == "UNION" or arm in ("G", "S") and arm in v["source"])]
    return live + external


def validate_step_schedule(row, before, models, slots, observed_subsets):
    slot, step, subset = row["slot"], row["step"], row["subset"]
    require(0 <= slot < 100 and row["family"] == before[slot]["family"]
            and row["role"] == before[slot]["role"], "Receiver identity changed")
    masks = models[str(row["family"])]
    require(step == slots[slot] and 0 <= subset < len(masks), "Step/subset sequence differs")
    require(row["mask"] == masks[subset] and subset not in observed_subsets[slot], "FOS mask not visited exactly once")
    require(all(slots[s] == len(models[str(before[s]["family"])]) for s in range(slot)), "Receiver slot order changed")
    slots[slot] += 1
    observed_subsets[slot].add(subset)


def choose_causal_donor(row, pool, states, views, paid_at, probe_seed, capture_after):
    require(row["poolSize"] == len(pool), "Pool size differs from independently reconstructed pool")
    draw_seed = proposal_seed(probe_seed, row["slot"], row["step"])
    require(row["proposalSeed"] == draw_seed, "Proposal seed is not the frozen Java64 formula")
    draw = JavaRandom(draw_seed).next_int(len(pool))
    require(row["draw"] == draw, "Donor draw differs from independent Java nextInt")
    donor_type, donor_id = pool[draw]
    require((row["donorType"], row["donorId"]) == (donor_type, donor_id), "Selected donor differs from pool/draw")
    if donor_type == "R":
        require(row["donorPaidByFE"] == paid_at[donor_id], "R donor is stale or reads a future state")
        require(paid_at[donor_id] == -1 or paid_at[donor_id] < row["fe"], "R source FE is not yet available")
        return states[donor_id]
    donor = views[donor_id]
    require(row["donorPaidByFE"] == donor["paidByFE"] <= capture_after, "External source is not already paid")
    return donor


def replay(folder, captured, before, models, views, catalog, jobs, factories, source_seed, arm):
    expected = validate_models(models, before, jobs, factories)
    receipt = read_json(folder / "receipt.json")
    receipt_check(receipt, source_seed, arm, expected)
    ledger = ParetoLedger(captured["background"])
    states, paid_at = [state(r) for r in before], [-1] * 100
    pools = [donor_pool(before, views, slot, arm) for slot in range(100)]
    slots, subsets = [0] * 100, [set() for _ in range(100)]
    digest, schedule = hashlib.sha256(), hashlib.sha256()
    flags_count, total = Counter(), 0
    source_domain = defaultdict(lambda: dict(proposals=0, accepted=0, admitted=0, equal=0, dominated=0, fallback=0))
    for domain in ("free80", "fixed20"):
        for source in ("R", "G", "S", "GS"):
            source_domain[f"{domain}/{source}"]
    for total, row in enumerate(json_lines(folder / "steps.jsonl"), 1):
        require(row["fe"] == total, "Successful FE is not a complete 1..expected sequence")
        validate_step_schedule(row, before, models, slots, subsets)
        parent = states[row["slot"]]
        require(row["parentObjectives"] == parent["objectives"], "Parent objectives disagree with current working state")
        donor = choose_causal_donor(row, pools[row["slot"]], states, views, paid_at,
                                   receipt["seed"], captured["receipt"]["afterGlobalFE"])
        verify_mix(parent, donor, row, catalog, factories)
        flags = ledger.offer(row["objectives"])
        require(all(type(row[k]) is bool and row[k] == value for k, value in flags.items()), "Pre-insert archive flags disagree")
        accepted = (all(a <= b for a, b in zip(row["objectives"], parent["objectives"])) or not flags["dominated"]
                    if row["role"] == "CENTER" else
                    row["objectives"][OBJECTIVE_ROLE[row["role"]]] < parent["objectives"][OBJECTIVE_ROLE[row["role"]]])
        require(type(row["accepted"]) is bool and row["accepted"] == accepted, "Role acceptance disagrees")
        if accepted:
            states[row["slot"]], paid_at[row["slot"]] = state(row), total
        flags_count.update(k for k, value in dict(flags, accepted=accepted).items() if value)
        domain = "free80" if row["family"] < 0 else "fixed20"
        counted = source_domain[f'{domain}/{row["donorType"]}']
        counted["proposals"] += 1
        for name, value in dict(flags, accepted=accepted, fallback=row["fallback"]).items():
            counted[name] += int(value)
        update_paid_digest(digest, row)
        schedule.update(struct.pack(">iiiiq", row["slot"], row["step"], row["subset"], row["family"], row["proposalSeed"]))
    require(total == expected and all(slots[s] == len(models[str(before[s]["family"])]) for s in range(100)),
            "Incomplete receiver program or complete pass")
    require([state(r) for r in read_json(folder / "after.json")] == states, "after.json differs from accepted live-state reconstruction")
    require(sorted_points(read_json(folder / "front.json")) == sorted_points(ledger.points), "Final ND archive differs exactly")
    require(digest.hexdigest() == receipt["paidSHA256"], "Paid stream digest differs from reconstructed big-endian bytes")
    return dict(arm=arm, sourceSeed=source_seed, expectedFE=expected, successfulFE=total,
                finalArchiveSize=len(ledger.points), flags=dict(flags_count),
                paidSHA256=digest.hexdigest(), scheduleSHA256=schedule.hexdigest(),
                byReceiverDomainAndSource=dict(source_domain),
                completeCausalReplay=True, poolAndDrawIndependentlyReconstructed=True,
                physicalObjectivesIndependentlyDecoded=False)
