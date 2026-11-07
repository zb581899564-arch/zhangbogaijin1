"""Independent current-state and borrowed-state mixing reconstruction, no search calls."""
import json

from run_long_budget_bridge import rows,write_once
from pa_population_replay import Replay
from pa_population_state_checks import identity,paid_bytes,physical,snapshot


class BorrowReplay(Replay):
    def __init__(self,catalog,mode,views):
        super().__init__(catalog)
        self.mode,self.views,self.original,self.donors=mode,views,None,[]
        self.external=0;self.initial_support=[];self.unseen=0

    def event(self,event):
        super().event(event)
        if event["kind"]=="initial":
            if len(self.population)==1:self.initial_support=[set() for _ in event["resources"]]
            for j,r in enumerate(event["resources"]):self.initial_support[j].add(r)
        elif event["kind"]=="model":
            if self.original is None:
                initial=json.loads(next(self.views));assert initial["generation"]==-1
                self.original=initial["points"];assert len(self.original)==100
            current=json.loads(next(self.views));assert current["generation"]==self.generation
            self.donors=current["points"];assert len(self.donors)==100
            for i,(before,after) in enumerate(zip(self.original,self.donors)):
                assert before["id"]==after["id"]==-1-i and 1<=after["paidFE"]<=50000
                assert after["hash"]==identity(after) and before["hash"]==identity(before)
                assert after["resources"]==before["resources"] and after["objectives"]==before["objectives"]
                assert physical(after,self.catalog)==physical(before,self.catalog)

    def mix(self,event):
        assert self.phase=="MIXING" and event["generation"]==self.generation
        slot,source=event["slot"],event["donorSlot"]
        if slot!=self.current_slot:
            assert slot==self.current_slot+1 and event["step"]==0
            self.current_slot=slot;self.used_subsets.clear()
        assert event["step"]==len(self.used_subsets) and event["subset"] not in self.used_subsets
        self.used_subsets.add(event["subset"]);subset=self.subsets[event["subset"]]
        parent=self.population[slot]
        if source<0:
            assert self.mode=="GRAFT" and 0<=-1-source<len(self.donors)
            donor=self.donors[-1-source];self.external+=1
        else:
            assert source!=slot and 0<=source<100
            donor=self.population[source]
        assert event["parentId"]==parent["id"] and event["parentHash"]==parent["hash"]
        assert event["donorId"]==donor["id"] and event["donorHash"]==donor["hash"]
        resources,keys=parent["resources"].copy(),parent["keys"].copy()
        for job in subset:resources[job],keys[job]=donor["resources"][job],donor["keys"][job]
        missing=len({self.catalog[r][0] for r in resources})!=max(t[0] for t in self.catalog)+1
        assert event["fallback"]==missing
        if missing:resources,keys=parent["resources"],parent["keys"];assert event["objectives"]==parent["objectives"]
        if len(subset)==len(resources):assert event["objectives"]==donor["objectives"]
        event["resources"],event["keys"]=resources,keys
        self.birth(event);self.paid_event(event)
        target={"MAKESPAN":0,"ENERGY":1,"WORKER_COST":2}.get(event["role"])
        accept=(all(a<=b for a,b in zip(event["objectives"],parent["objectives"])) or not event["archiveDominated"]) if target is None else event["objectives"][target]<parent["objectives"][target]
        assert event["accepted"]==accept
        fresh,changed=donor["id"] in self.accepted_ids,donor["id"] in self.changed_ids
        assert event["donorAcceptedThisGeneration"]==fresh and event["donorChangedThisGeneration"]==changed
        self.fresh_reads+=fresh;self.changed_reads+=changed
        if accept:
            self.population[slot]=event;self.accepted_ids.add(event["id"]);self.accepted+=1
            if event["hash"]!=parent["hash"]:self.changed_ids.add(event["id"])
        self.unseen+=any(r not in self.initial_support[j] for j,r in enumerate(resources))
        self.fallbacks+=missing;self.unchanged+=event["hash"]==parent["hash"];self.fees["mixing"]+=1


def audit(folder,mode):
    catalog,=rows(folder/"catalog.jsonl");receipt,=rows(folder/"receipt.jsonl")
    with (folder/"borrowed-views.jsonl").open(encoding="utf-8") as views:
        replay=BorrowReplay(catalog["tuples"],mode,views)
        with (folder/"events.jsonl").open(encoding="utf-8") as events:
            for line in events:replay.event(json.loads(line))
        assert not views.read().strip()
    assert replay.paid==receipt["successfulFE"]==receipt["attemptedFE"]==receipt["paidFullTimelineQA"]==receipt["decoder"]["dynamic.evaluations"]
    assert receipt["failedFE"]==0 and receipt["paidSHA256"]==replay.digest.hexdigest()
    assert receipt["accepted"]==replay.accepted and receipt["borrow"]["borrow.externalReads"]==replay.external
    for saved,actual in zip(receipt["lastPopulation"],replay.population):snapshot(saved,actual)
    assert set(map(tuple,receipt["internalArchive"]))==set(map(tuple,replay.archive))
    assert {tuple(p["objectives"]) for p in receipt["lastValidFront"]}==set(map(tuple,replay.archive))
    result={"allPaidGenomesBorrowedViewsAndAcceptanceReconstructed":True,"successfulFE":replay.paid,
        "paidSHA256":receipt["paidSHA256"],"externalReads":replay.external,"pointsWithInitialUnseenTuple":replay.unseen,
        "sourceBornFENeverExceeds50000":True,"newSearchFE":0,"decoderCalls":0}
    write_once(folder/"independent-borrowed-replay.json",result);return result
