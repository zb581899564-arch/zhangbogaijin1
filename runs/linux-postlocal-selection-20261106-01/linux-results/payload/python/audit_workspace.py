"""Native view/model/FOS/mixing/live-donor/role-acceptance reconstruction."""
from collections import Counter, defaultdict

from audit_core import (FAMILY_COUNTS, OBJECTIVE_ROLE, ROLES, check_raw, physical,
                        raw_hash, require, state_raw)
from audit_models import check_model


class Workspace:
    def __init__(self, owner, event):
        self.owner, self.catalog, self.start_event = owner, owner.catalog, event
        self.passno, self.members = event["pass"], event["beforePopulation"]
        self.population, self.families, self.sources = [], [], []
        self.states, self.masks, self.models = {}, defaultdict(list), []
        self.model_domains, self.visited = set(), set()
        self.program = self.pending = None
        self.local = self.programs = 0
        self.complete = self.ready_seen = False

    def birth(self, event, **extra):
        self.owner.state_count += 1
        require(event["id"] == self.owner.state_count, "Native state IDs are not a complete sequence")
        value = dict(event, **extra)
        self.states[event["id"]] = value
        return value

    def view(self, event):
        slot = event["slot"]
        require(event["pass"] == self.passno and slot == len(self.population), "View pass/slot differs")
        member = self.members[slot]
        require(event["family"] == member["family"] and event["source"] == member["raw"],
                "View source or family differs from input member")
        require(event["objectives"] == member["raw"]["objectives"], "View changed objectives")
        source_hash, fee = raw_hash(event["source"]), event["paidFE"]
        if fee < 0:
            require(source_hash in self.owner.imported and -fee in self.owner.imported[source_hash],
                    "Negative source fee does not match an imported already-paid source")
        else:
            require(0 < fee <= len(self.owner.paid) and self.owner.paid[fee]["rawHash"] == source_hash,
                    "View reads unpaid, future or differently encoded state")
        require(len(event["resources"]) == len(event["keys"]) == self.catalog["jobs"], "View size differs")
        require(all(type(r) is int and 0 <= r < len(self.catalog["tuples"]) for r in event["resources"]),
                "View resource is outside catalog")
        require(all(0 < key < 1 for key in event["keys"]), "Neutral view keys must be inside (0,1)")
        encoded = state_raw(event, self.catalog["tuples"])
        check_raw(encoded, self.catalog["jobs"], self.catalog["factories"])
        require(physical(encoded, self.catalog["factories"]) == physical(event["source"], self.catalog["factories"]),
                "Neutral view changed the physical per-factory schedule")
        self.birth(event, pointRaw=event["source"])
        self.population.append(event["id"])
        self.families.append(event["family"])
        self.sources.append(event)
        self.owner.views += 1

    def model(self, event):
        require(event["pass"] == self.passno and len(self.population) == 100, "Model before full view preparation")
        family = event["family"]
        require(event["slots"] == [i for i, value in enumerate(self.families) if value == family],
                "Model learned from a different cohort")
        domain = family, event["factory"]
        require(domain not in self.model_domains, "Model domain recorded twice")
        self.model_domains.add(domain)
        population = {i: self.states[state_id] for i, state_id in enumerate(self.population)}
        self.models.append(check_model(event, population, self.catalog))
        self.masks[family].extend(event["subsets"])

    def ready(self, event):
        require(not self.ready_seen and event["families"] == self.families and
                Counter(self.families) == FAMILY_COUNTS, "Ready population/domain quotas differ")
        expected = {(-1, -1)} | {(f, factory) for f in range(4) for factory in range(self.catalog["factories"])}
        require(self.model_domains == expected, "Missing native model domain")
        for family in FAMILY_COUNTS:
            require(len(self.masks[family]) == 2 * self.catalog["jobs"] -
                    (1 if family < 0 else self.catalog["factories"]), "Incomplete FOS")
        self.ready_seen = True

    def start(self, event):
        slot = event["slot"]
        require(self.ready_seen and self.program is None and slot not in self.visited and
                slot == len(self.visited), "Program order, uniqueness or ready state differs")
        require(event["family"] == self.families[slot] and
                sorted(event["order"]) == list(range(len(self.masks[event["family"]]))),
                "Program family or complete FOS permutation differs")
        require(event["inputFee"] == self.sources[slot]["paidFE"] and
                event["receiverRaw"] == self.sources[slot]["source"], "Receiver identity changed")
        role = self.members[slot]["role"]
        require(event["preference"] == role and event["physicalGroup"] == ROLES.index(role) + 1,
                "Native four-role local acceptance preference changed")
        self.program = dict(event, nextStep=0)
        self.visited.add(slot)

    def proposal(self, event):
        program = self.program
        require(program is not None and self.pending is None, "Proposal without one active program")
        require(event["slot"] == program["slot"] and event["step"] == program["nextStep"] and
                event["subset"] == program["order"][event["step"]], "Proposal schedule differs")
        donor_slot = event["donorSlot"]
        require(0 <= donor_slot < 100 and donor_slot != event["slot"] and
                self.families[donor_slot] == program["family"], "Invalid donor domain")
        parent = self.states[self.population[event["slot"]]]
        donor = self.states[self.population[donor_slot]]
        require((event["parentId"], event["donorId"]) == (parent["id"], donor["id"]),
                "Proposal does not use current live receiver/donor states")
        require(all(point["paidFE"] <= len(self.owner.paid) for point in (parent, donor)),
                "Proposal uses a future state")
        resources, keys = list(parent["resources"]), list(parent["keys"])
        mask = self.masks[program["family"]][event["subset"]]
        for job in mask:
            resources[job], keys[job] = donor["resources"][job], donor["keys"][job]
        tuples = self.catalog["tuples"]
        missing = len({tuples[r][0] for r in resources}) != self.catalog["factories"]
        require(event["fallback"] is missing, "Empty-factory fallback flag differs")
        if missing:
            resources, keys = list(parent["resources"]), list(parent["keys"])
        if program["family"] >= 0:
            require(not missing and all(tuples[a][0] == tuples[b][0] for a, b in
                                        zip(resources, parent["resources"])), "Fixed family allocation changed")
            require(len({tuples[parent["resources"][j]][0] for j in mask}) == 1, "Fixed FOS crossed factory")
        self.pending = dict(event, resources=resources, keys=keys, beforePaid=len(self.owner.paid))

    def step(self, event):
        pending = self.pending
        require(pending is not None, "Accepted/rejected step has no pending proposal")
        for key in ("pass", "slot", "step", "subset", "donorSlot", "parentId", "donorId", "fallback"):
            require(event[key] == pending[key], "Paid step proposal identity differs: " + key)
        fee = event["paidFE"]
        require(fee == len(self.owner.paid) == pending["beforePaid"] + 1, "Proposal has other than one successful FE")
        value = self.birth(event, resources=pending["resources"], keys=pending["keys"])
        raw = state_raw(value, self.catalog["tuples"])
        require(raw_hash(raw) == self.owner.paid[fee]["rawHash"], "Paid genotype is not the causal mask mixture")
        require(raw == self.owner.last_detail["raw"], "Paid full vectors differ from reconstructed child")
        value["pointRaw"] = raw
        old = self.states[event["parentId"]]["objectives"]
        target = OBJECTIVE_ROLE.get(self.program["preference"])
        accepted = ((all(a <= b for a, b in zip(event["objectives"], old)) or
                     not self.owner.paid[fee]["dominated"]) if target is None else
                    event["objectives"][target] < old[target])
        require(event["accepted"] is accepted, "Role acceptance differs from private pre-insertion flags")
        if accepted:
            self.population[event["slot"]] = event["id"]
        self.program["nextStep"] += 1
        self.local += 1
        self.owner.local += 1
        self.pending = None

    def end(self, event):
        require(self.program is not None and self.pending is None and
                event["slot"] == self.program["slot"] and
                self.program["nextStep"] == len(self.program["order"]), "Incomplete programEnd")
        self.snapshot(event["result"], self.states[self.population[event["slot"]]])
        self.program = None
        self.programs += 1
        self.owner.programs += 1

    def pass_end(self, event):
        require(self.programs == len(self.visited) == 100 and self.program is None, "Incomplete passEnd")
        self.check_workspace(event["workspace"])
        self.complete = True
        self.owner.completed += 1

    @staticmethod
    def snapshot(actual, expected):
        require(all(actual[key] == expected[key] for key in ("id", "paidFE", "objectives")),
                "Native state snapshot differs")

    def check_workspace(self, actual):
        require(actual["families"] == self.families and len(actual["population"]) == len(self.population),
                "Native workspace membership differs")
        for row, state_id in zip(actual["population"], self.population):
            self.snapshot(row, self.states[state_id])
        require(actual["programs"] == self.programs, "Workspace completed-program counter differs")
        if self.pending is None:
            require(actual["pending"] is None, "Unexpected retained pending proposal")
        else:
            for key in ("pass", "slot", "step", "subset", "donorSlot", "parentId", "donorId", "fallback"):
                require(actual["pending"][key] == self.pending[key], "Pending proposal snapshot differs")

    def output_members(self):
        output = []
        for slot, member in enumerate(self.members):
            if slot < len(self.population):
                point = self.states[self.population[slot]]
                output.append(dict(member, raw=point["pointRaw"]))
            else:
                output.append(dict(member))
        return output
