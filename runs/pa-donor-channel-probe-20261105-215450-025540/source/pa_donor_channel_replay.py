"""Independent bounded-memory reconstruction of work/history donors and original acceptance."""
from collections import Counter
import hashlib
import json

import numpy as np

from run_long_budget_bridge import rows, write_once
from pa_population_state_checks import identity, paid_bytes, physical, offer
from pa_role_policy_audit import acceptance_pair


class ChannelReplay:
    def __init__(self, catalog, mode):
        self.catalog, self.mode = catalog, mode
        self.working, self.previous, self.latest = [], [], []
        self.archive = np.empty((0, 3))
        self.paid = self.last_id = self.aliases = 0
        self.generation = self.reencoded = 0
        self.current_slot = -1
        self.visited = set()
        self.subsets = {}
        self.digest = hashlib.sha256()
        self.counts = Counter()

    def birth(self, state):
        assert state["id"] == self.last_id + 1
        self.last_id += 1
        assert state["hash"] == identity(state)

    def paid_state(self, state, event):
        self.birth(state)
        self.paid += 1
        assert state["paidFE"] == self.paid
        self.digest.update(paid_bytes(state, self.catalog, self.paid))
        self.archive = offer(self.archive, {**event, "objectives": state["objectives"]})

    def initial(self, event):
        state = event["state"]
        assert event["slot"] == len(self.working) and self.generation == 0
        self.paid_state(state, event)
        self.working.append(state); self.previous.append(state); self.latest.append("INITIAL")

    def reencode(self, event):
        slot, after, alias = event["slot"], event["after"], event["previous"]
        if slot == 0:
            assert event["generation"] == self.generation + 1
            self.generation += 1; self.reencoded = 0
            self.current_slot = -1; self.visited.clear(); self.subsets.clear()
        assert slot == self.reencoded and len(self.working) == 100
        self.reencoded += 1
        before, previous = self.working[slot], self.previous[slot]
        assert event["beforeId"] == before["id"] and event["beforePreviousId"] == previous["id"]
        self.birth(after)
        for original, new in ((before, after), (previous, alias)):
            assert new["resources"] == original["resources"] and new["objectives"] == original["objectives"]
            assert new["role"] == original["role"] and new["paidFE"] == original["paidFE"]
            assert physical(new, self.catalog) == physical(original, self.catalog)
        if previous["id"] == before["id"]:
            assert alias == after
        else:
            self.birth(alias); self.aliases += 1
        self.working[slot] = after; self.previous[slot] = alias

    def paid(self, event):
        slot, source = event["slot"], event["donorSlot"]
        assert event["generation"] == self.generation and self.reencoded == 100 and source != slot
        parent, live, previous = self.working[slot], self.working[source], self.previous[source]
        assert event["parentId"] == parent["id"] and event["liveId"] == live["id"] and event["previousId"] == previous["id"]
        category = self.latest[source]
        cross = live["role"] != parent["role"] and live["role"] != "CENTER"
        if cross and category != "INITIAL": self.counts["channel.eligible." + category] += 1
        revert = cross and (self.mode == "REVERT_BRIDGE" and category == "BRIDGE"
                            or self.mode == "REVERT_COMMON" and category == "COMMON")
        donor = previous if revert else live
        assert event["mode"] == self.mode and event["category"] == category
        assert event["reverted"] == revert and event["donorId"] == donor["id"]
        self.counts["channel.reads"] += 1
        if revert: self.counts["channel.reverted." + category] += 1
        self.check_subset(event, len(parent["resources"]))
        child = event["state"]
        assert child["role"] == parent["role"]
        child["resources"], child["keys"] = parent["resources"].copy(), parent["keys"].copy()
        for job in event["subset"]:
            child["resources"][job], child["keys"][job] = donor["resources"][job], donor["keys"][job]
        missing = len({self.catalog[r][0] for r in child["resources"]}) != max(t[0] for t in self.catalog) + 1
        assert event["fallback"] == missing
        if missing:
            child["resources"], child["keys"] = parent["resources"], parent["keys"]
            assert child["objectives"] == parent["objectives"]
        self.paid_state(child, event)
        own, center = acceptance_pair(parent["role"], parent["objectives"], child["objectives"], event["archiveDominated"])
        assert own == event["accepted"]
        if own:
            self.previous[slot] = parent
            self.latest[slot] = "BRIDGE" if parent["role"] != "CENTER" and not center else "COMMON"
            self.counts["channel.accepted." + self.latest[slot]] += 1
            self.working[slot] = child

    def check_subset(self, event, jobs):
        slot, subset_index, subset = event["slot"], event["subsetIndex"], event["subset"]
        if slot != self.current_slot:
            assert slot == self.current_slot + 1 and event["step"] == 0
            if slot > 0: assert len(self.visited) == 2 * jobs - 1
            self.current_slot = slot; self.visited.clear()
        assert event["step"] == len(self.visited) and subset_index not in self.visited
        assert subset and len(set(subset)) == len(subset) and all(0 <= j < jobs for j in subset)
        if subset_index in self.subsets: assert self.subsets[subset_index] == subset
        else: self.subsets[subset_index] = subset
        self.visited.add(subset_index)


def audit(folder, catalog_path, mode):
    catalog, = rows(catalog_path)
    receipt, = rows(folder / "run-receipt.jsonl")
    replay = ChannelReplay(catalog["tuples"], mode)
    with (folder / "channel-events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            {"initial": replay.initial, "reencode": replay.reencode, "paid": replay.paid}[event["kind"]](event)
    assert replay.paid == receipt["successful"] == receipt["attempted"] == receipt["decoder"]["dynamic.evaluations"]
    assert receipt["failed"] == 0 and receipt["paidSHA256"] == replay.digest.hexdigest()
    for key, count in replay.counts.items(): assert receipt["search"][key] == count
    assert receipt["search"].get("channel.shadowNeutralAliases", 0) == replay.aliases
    assert receipt["search"]["channel.mode"] == mode and receipt["search"]["channel.workingAcceptanceUnchanged"]
    point, = [r for r in rows(folder / "anytime.jsonl") if r["checkpointKind"] == "FE" and r["checkpoint"] == replay.paid and r["reached"]]
    assert set(map(tuple, point["front"])) == set(map(tuple, replay.archive))
    result = {"allPaidGenomesAndAcceptancesReconstructed": True, "successfulFE": replay.paid,
        "paidSHA256": replay.digest.hexdigest(), "additionalNeutralAliasesChecked": replay.aliases,
        "mode": mode, "channelCounts": dict(replay.counts), "newSearchFE": 0, "decoderCalls": 0}
    write_once(folder / "independent-channel-replay.json", result)
    return result
