"""Genome-level availability and recorded action2 origins; no new search or decoder calls."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once

COHORT=ROOT/"runs/teacher-coupling-probe-20261105-011608-145831"
FRESH=ROOT/"runs/guide-feedback-probe-20261105-001115-004809"
ROLES=("MAKESPAN","CENTER","ENERGY","WORKER_COST")


def key(s):return tuple(tuple(s[k]) for k in ("JS","FA","MA","WA","objectives"))


def main():
    root=ROOT/"runs"/datetime.now().strftime("global-information-flow-%Y%m%d-%H%M%S-%f");root.mkdir()
    write_once(root/"protocol.json",{"scope":"Zero new FE/decodes, read-only source availability and first-paid-genome provenance.",
        "sources":[str(COHORT),str(FRESH)],"limitations":"Cohort FULL_ROLE and older fresh-feedback PAIR_ROLE_CROWD are different configurations. "
            "Availability and structural direction only; no cross-configuration efficacy comparison or gene-transfer/causal-credit claim."})
    shutil.copy2(Path(__file__),root/"source.py");availability=[];matrices=[]
    for stem in ("20_8_5_1","100_2_3_1"):
        for seed in (10060007,10060031):
            path=COHORT/stem/str(seed)/"ON";initial={key(s) for s in rows(path/"initial-population.jsonl")}
            data,=rows(path/"teacher-cohorts.jsonl")
            availability.append({"stem":stem,"seed":seed,"cohorts":[{"role":c["role"],"paidFE":c["paidFE"],
                "guideCount":len(c["guideLibrary"]),"allGuidesFromInitialization":all(key(g) in initial for g in c["guideLibrary"])} for c in data["cohorts"]]})
        for seed in (9760003,9760033):
            data,=rows(FRESH/stem/str(seed)/"BATCH/guides.jsonl")
            records=[r for r in data["selections"] if r["action"]==2 and r["firstPaidFE"]>100]
            counts=Counter((r["role"],r["originRole"]) for r in records)
            matrix={receiver:{source:counts[(receiver,source)] for source in ROLES} for receiver in ROLES}
            backward=sum(n for (target,source),n in counts.items() if ROLES.index(source)>ROLES.index(target))
            assert backward==0,"Unexpected future-role source in the first serial phase"
            matrices.append({"stem":stem,"seed":seed,"sourceMeaning":"First paid occurrence of identical four-vector genome", "action2NewGenomeOrigins":matrix,"laterRoleToEarlierRoleSelections":backward})
    all_initial=all(c["allGuidesFromInitialization"] for a in availability for c in a["cohorts"])
    result={"availability":availability,"serialFreshOriginMatrices":matrices,"allFrozenOriginalCohortArchivesInitialOnly":all_initial,
        "structuralFinding":"Original internal archives have no same-generation cross-role accepted updates; serial batch-refresh permits earlier-to-later feedback only. "
                            "A round-synchronous schedule with per-role persistent Q state would test reverse flow, not merely the freshness interval. Quality benefit remains untested.",
        "newSearchFE":0,"newDecoderCalls":0}
    write_once(root/"results.json",result);write_once(root/"status.json",{"status":"COMPLETE","sourceInitialOnlyVerified":all_initial,"searchFE":0,"decoderCalls":0})
    print("GLOBAL_FLOW_ROOT",root);print("INITIAL_ONLY",all_initial);print("FRESH_SERIAL_MATRICES",matrices)


if __name__=="__main__":main()
