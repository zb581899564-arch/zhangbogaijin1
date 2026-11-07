"""Genome-only audit of local job-set compatibility across different complete FA assignments."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, rows, write_once

BASIS=ROOT/"runs/guide-feedback-gate-20261105-001255-379798"
STEMS=("20_8_5_1","100_2_3_1")
SEED=9850003


def assignment(solution):
    return tuple(f for _,f in sorted(zip(solution["JS"],solution["FA"])))


def modules(solution,factories):
    for factory in range(factories):
        positions=[p for p,f in enumerate(solution["FA"]) if f==factory]
        jobs=tuple(solution["JS"][p] for p in positions)
        yield ((factory,tuple(sorted(jobs))),
               (jobs,tuple(solution["MA"][p] for p in positions),tuple(solution["WA"][p] for p in positions)))


def analyze(path,factories):
    solutions=rows(path);library=defaultdict(list)
    for index,s in enumerate(solutions):
        fa=assignment(s)
        for key,encoding in modules(s,factories):library[key].append((index,fa,encoding))
    details=[];cross_keys=0
    for records in library.values():
        if len({r[1] for r in records})>1:cross_keys+=1
    for i,s in enumerate(solutions):
        fa=assignment(s);factory_counts=[]
        for key,parent in modules(s,factories):
            same={r[2] for r in library[key] if r[1]==fa}
            cross={r[2] for r in library[key] if r[1]!=fa}
            novel=cross-same
            factory_counts.append({"factory":key[0],"sameWholeFAEncodings":len(same),
                                   "crossWholeFAEncodings":len(cross),"newCompatibleEncodings":len(novel)})
        details.append({"receiverIndex":i,"factories":factory_counts,
                        "hasAdditionalCompatibleModule":any(x["newCompatibleEncodings"]>0 for x in factory_counts)})
    covered=sum(x["hasAdditionalCompatibleModule"] for x in details)
    return {"paidReceiverCount":len(solutions),"distinctWholeFA":len({assignment(s) for s in solutions}),
            "factoryJobSetKeys":len(library),"keysPresentInDifferentWholeFAs":cross_keys,
            "receiversWithAdditionalModule":covered,"receiverFraction":covered/len(solutions),
            "receivers":details}


def main():
    root=ROOT/"runs"/datetime.now().strftime("local-context-overlap-%Y%m%d-%H%M%S-%f");root.mkdir()
    write_once(root/"protocol.json",{"sources":{s:str(BASIS/s/str(SEED)/"GEN/solutions.jsonl") for s in STEMS},
        "scope":"Zero search FE, zero decoder calls. Structural availability only; final paid ND archives selected in advance, not all paid observations.",
        "question":"Does matching each factory's own job set expose distinct complete local encodings unavailable under matching the entire FA?",
        "control":"Both libraries use identical paid parent archives and unrestricted retained records; only whole-FA versus local-job-set matching differs. "
                  "This is not a replay of the current cap8 protected-family pool and not a measured improvement over its actual chooser.",
        "gate":"At least20% of paid receivers on each instance have a distinct local encoding from another whole FA absent among same-whole-FA sources. "
               "A pass authorizes offline objective/decode diagnostics only, never a selector or whole-budget run.",
        "limits":"No role producer metadata, objective gain, fatigue specificity, novelty, timing advantage or whole-run benefit can be inferred from counts."})
    shutil.copy2(Path(__file__),root/"source.py")
    result={s:analyze(BASIS/s/str(SEED)/"GEN/solutions.jsonl",int(s.split("_")[2])) for s in STEMS}
    passed=all(r["receiverFraction"]>=.2 for r in result.values())
    write_once(root/"results.json",result)
    write_once(root/"status.json",{"status":"COMPLETE","searchFE":0,"decoderCalls":0,"worthOfflineObjectiveAudit":passed})
    print("CONTEXT_OVERLAP_ROOT",root)
    print({s:{k:v for k,v in r.items() if k!="receivers"} for s,r in result.items()})
    print("WORTH_OFFLINE_OBJECTIVE_AUDIT",passed)


if __name__=="__main__":main()
