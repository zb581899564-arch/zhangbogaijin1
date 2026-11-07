"""Replay the singleton adapter, independent pass archives and public paid union."""
from collections import defaultdict
import hashlib
import json

from audit_core import (ParetoLedger, check_flags, check_population, json_lines, raw_bytes,
                        raw_hash, read_json, require, same_front, state_raw)
from audit_selection import member_identity, verify_selection
from audit_workspace import Workspace


def signed64(value):
    value &= (1 << 64) - 1
    return value - (1 << 64) if value >= (1 << 63) else value


def same_members(actual, expected, label):
    require([member_identity(p) for p in actual] == [member_identity(p) for p in expected],
            label + " ancestry, order, quotas or working raw state differs")


class Replay:
    def __init__(self, folder, catalog, source):
        self.folder, self.catalog, self.source = folder, catalog, source
        self.receipt = read_json(folder / "receipt.json")
        self.mode = self.receipt["mode"]
        require(self.mode in ("RAW_ROLE", "POST_ROLE", "POST_PARETO"), "Unknown probe mode")
        self.B = 100 * (2 * catalog["jobs"] - 1) - 20 * (catalog["factories"] - 1)
        self.public = ParetoLedger(source["A0"])
        self.imported = defaultdict(set)
        for member in source["parents"] + source["children"]:
            self.imported[raw_hash(member["raw"])].add(max(1, member["sourcePaidByFE"]))
            require(not self.public.offer(member["raw"]["objectives"])["fresh"],
                    "Already-paid imported point is missing from POST_GLOBAL A0")
        imports = read_json(folder / "imports.json")
        same_members(imports["parents"], source["parents"], "Imported parents")
        same_members(imports["children"], source["children"], "Imported children")
        same_front(imports["A0"], source["A0"], "Imported A0")
        same_front(imports["initialPublicArchive"], self.public.points, "Initial public archive")
        self.paid, self.prefixes, self.outputs = {}, {}, {}
        self.digest = hashlib.sha256()
        self.proposal_digest, self.proposal_prefixes = hashlib.sha256(), {}
        self.prefix_fees = {1, 2, self.B, 2 * self.B, 3 * self.B - 1, 3 * self.B}
        self.prefix_fees.update(map(int, self.receipt["paidPrefixes"]))
        self.current = self.last_workspace = self.private = self.last_detail = None
        self.active = False
        self.sequence = self.state_count = self.views = self.local = self.programs = self.completed = 0
        self.prepared_passes = 0
        self.pass_records, self.model_results, self.pass_checks = [], [], []
        self.selected = self.selection_checks = None
        self.expected_seeds = self.check_seeds()

    def check_seeds(self):
        seed = self.source["metadata"]["seed"] ^ 0x6C8E9CF5
        require(self.receipt["sourceSeed"] == self.source["metadata"]["seed"] and
                self.receipt["seed"] == seed, "Input source seed or probe seed changed")
        plan = dict(polish=seed, rawFirst=seed, rawSecond=signed64(seed ^ 0x9E3779B97F4A7C15),
                    final=seed ^ 0x51D0A7E3)
        require(self.receipt["seedPlan"]["probeSeedXor"] == 0x6C8E9CF5 and
                all(self.receipt["seedPlan"][key] == value for key, value in plan.items()),
                "Frozen seed plan changed")
        return dict(P_POLISH=plan["polish"], C_POLISH=plan["polish"], RAW_1=plan["rawFirst"],
                    RAW_2=plan["rawSecond"], FINAL=plan["final"])

    def expected_members(self, phase):
        if phase == "P_POLISH":
            return self.source["parents"]
        if phase == "C_POLISH":
            return self.source["children"]
        if phase == "RAW_2":
            return self.outputs["RAW_1"]
        if phase == "FINAL" and self.mode == "RAW_ROLE":
            return self.outputs["RAW_2"]
        require(self.selected is not None, "Local pass began before required survivor selection")
        return self.selected

    def pass_start(self, event):
        require(not self.active, "Overlapping native passes")
        phases = ["RAW_1", "RAW_2", "FINAL"] if self.mode == "RAW_ROLE" else ["P_POLISH", "C_POLISH", "FINAL"]
        index = len(self.pass_records)
        require(index < 3 and event["phase"] == phases[index] and event["pass"] == index + 1,
                "Native pass phase/order differs")
        require(event["beforeFE"] == len(self.paid) == index * self.B and
                event["expectedFE"] == self.B and event["seed"] == self.expected_seeds[event["phase"]],
                "Pass budget boundary or seed differs")
        expected = self.expected_members(event["phase"])
        same_members(event["beforePopulation"], expected, "Pass input")
        check_population(event["beforePopulation"])
        independent = event["phase"] in ("P_POLISH", "C_POLISH")
        require(event["archiveBasis"] == ("A0_INDEPENDENT" if independent else "CURRENT_PUBLIC"),
                "Wrong private acceptance archive basis")
        initial = self.source["A0"] if independent else self.public.points.tolist()
        self.private = ParetoLedger(initial)
        same_front(event["internalArchive"], self.private.points, "Pass initial private archive")
        same_front(event["publicArchive"], self.public.points, "Pass initial public archive")
        self.current = Workspace(self, event)
        self.active = True

    def paid_event(self, event):
        require(self.active and self.current.pending is not None and event["fe"] == len(self.paid) + 1,
                "Paid event outside a pending native proposal or wrong FE")
        require(event["phase"] == self.current.start_event["phase"], "Paid event phase differs")
        private_flags = self.private.offer(event["objectives"])
        public_flags = self.public.offer(event["objectives"])
        check_flags(event, private_flags, "Native private paid flags")
        self.paid[event["fe"]] = dict(event, privateFlags=private_flags, publicFlags=public_flags)

    def paid_detail(self, event):
        fee = event["fe"]
        require(fee == len(self.paid) and (self.last_detail is None or fee == self.last_detail["fe"] + 1),
                "Missing, duplicate or unordered paid detail")
        require(event["phase"] == self.current.start_event["phase"], "Paid detail phase differs")
        paid = self.paid[fee]
        require(event["raw"]["objectives"] == paid["objectives"] and
                raw_hash(event["raw"]) == event["rawHash"] == paid["rawHash"], "Paid detail raw hash differs")
        for name in ("privateFlags", "publicFlags"):
            check_flags(event[name], paid[name], name)
        basis = "NATIVE_PUBLIC" if self.receipt["nativeObserver"] else "PRIVATE_PASS"
        require(event["acceptanceArchive"] == paid["acceptanceArchive"] == basis,
                "Observer acceptance-archive marker differs")
        if self.receipt["nativeObserver"]:
            require(self.mode == "RAW_ROLE" and paid["privateFlags"] == paid["publicFlags"],
                    "Native RAW observer bridge flags differ")
        self.digest.update(raw_bytes(event["raw"], fee))
        if fee in self.prefix_fees:
            self.prefixes[str(fee)] = self.digest.hexdigest()
        self.last_detail = event

    def selection(self, event):
        require(self.selected is None and not self.active and event["mode"] == self.mode,
                "Duplicate, misplaced or mislabeled selection")
        before = self.mode == "RAW_ROLE"
        require(len(self.paid) == (0 if before else 2 * self.B), "Selection occurred at wrong FE")
        parents = self.source["parents"] if before else self.outputs["P_POLISH"]
        children = self.source["children"] if before else self.outputs["C_POLISH"]
        policy = "FULL_ALL" if self.mode == "POST_PARETO" else "FULL_ROLE"
        self.selected, self.selection_checks = verify_selection(dict(event, policy=policy), parents, children, policy)
        same_members(event["afterPopulation"], self.selected, "Selected working population")
        saved = read_json(self.folder / "selection.json")
        require(saved["mode"] == self.mode and saved["policy"]["mode"] == policy and
                saved["groups"] == event["groups"], "Selection artifact differs from timeline")
        same_members(saved["afterPopulation"], self.selected, "Saved selection")
        same_members(read_json(self.folder / "selected.json"), self.selected, "Selected artifact")

    def pass_finish(self, event):
        workspace = self.current
        require(self.active and event["pass"] == workspace.passno and
                event["phase"] == workspace.start_event["phase"], "Pass finish identity differs")
        delta = len(self.paid) - workspace.start_event["beforeFE"]
        require(event["beforeFE"] == workspace.start_event["beforeFE"] and
                event["afterFE"] == len(self.paid) and event["successful"] == delta == workspace.local and
                event["expectedFE"] == self.B and event["seed"] == workspace.start_event["seed"],
                "Pass fee accounting differs")
        require(event["attempted"] == event["successful"] + event["failed"] and
                event["complete"] is workspace.complete, "Pass completion or failed fee differs")
        require(not event["complete"] or (delta == self.B and event["error"] is None),
                "Complete pass has wrong budget/error")
        output = workspace.output_members()
        same_members(event["afterPopulation"], output, "Reconstructed post-pass population")
        for slot, row in enumerate(event["afterPopulation"][:len(workspace.population)]):
            state = workspace.states[workspace.population[slot]]
            require(row["stateId"] == state["id"] and row["paidFE"] == state["paidFE"] and
                    row["resources"] == state["resources"] and row["keys"] == state["keys"] and
                    row["workingView"] == state_raw(state, self.catalog["tuples"]),
                    "Pass retained internal genes or neutral working view differs")
        same_front(event["internalArchive"], self.private.points, "Final private pass archive")
        same_front(event["publicArchive"], self.public.points, "Final public pass archive")
        if workspace.population:
            self.last_workspace = workspace
        self.check_native(event["native"])
        self.outputs[event["phase"]] = output
        self.pass_records.append({k: v for k, v in event.items() if k != "sequence"})
        self.model_results.extend(workspace.models)
        self.pass_checks.append(dict(phase=event["phase"], successful=delta, complete=workspace.complete,
                                     retainedPendingProposal=workspace.pending is not None,
                                     publicArchiveSize=len(self.public.points), privateArchiveSize=len(self.private.points)))
        self.active = False

    def check_native(self, native):
        require(native["enabled"] and native["detailedEvidence"] and
                native["passesStarted"] == self.prepared_passes and
                native["completePasses"] == self.completed and native["completePrograms"] == self.programs and
                native["localEvaluations"] == self.local and native["preparedViews"] == native["validatedViews"] == self.views,
                "Native cumulative diagnostics differ")
        if self.last_workspace is None:
            require(native["workspace"] is None, "Unexpected unprepared workspace")
        else:
            self.last_workspace.check_workspace(native["workspace"])

    def run(self):
        own = {"passStart": self.pass_start, "paid": self.paid_event, "paidDetail": self.paid_detail,
               "selection": self.selection, "passFinish": self.pass_finish}
        native = {"view": "view", "model": "model", "ready": "ready", "program": "start",
                  "proposal": "proposal", "step": "step", "programEnd": "end", "passEnd": "pass_end"}
        for event in json_lines(self.folder / "events.jsonl"):
            self.sequence += 1
            require(event["sequence"] == self.sequence, "Evidence sequence is incomplete")
            kind = event["kind"]
            if kind in own:
                own[kind](event)
            else:
                require(kind in native and self.active and event["pass"] == self.current.passno and
                        event["phase"] == self.current.start_event["phase"], "Unknown or misplaced native event")
                getattr(self.current, native[kind])(event)
                if kind == "proposal":
                    self.record_proposal()
        require(not self.active, "Unfinished pass lacks partial receipt")
        return self

    def record_proposal(self):
        fields = ("pass", "slot", "step", "subset", "donorSlot", "parentId", "donorId", "fallback", "resources", "keys")
        record = {key: self.current.pending[key] for key in fields}
        self.proposal_digest.update(json.dumps(record, sort_keys=True, separators=(",", ":")).encode())
        fee = len(self.paid) + 1
        if fee in self.prefix_fees:
            self.proposal_prefixes[str(fee)] = self.proposal_digest.hexdigest()
