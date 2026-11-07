"""Verify the intended paired construction noise and invariant controls in frozen probe outputs."""
import argparse
from collections import defaultdict
from pathlib import Path

from run_long_budget_bridge import read,rows,write_once


def key(value):
    return tuple(tuple(value[k]) for k in ("JS","FA","MA","WA","objectives"))


def verify(root,kind):
    checked=0
    for spec in read(root/"protocol.json")["instances"]:
        stem=spec["stem"];raw=rows(root/stem/"probe/kernel-raw.jsonl");groups=defaultdict(list)
        for r in raw:
            if kind=="teacher":
                c,p,_=r["caseId"].split("-");group=(c,p,r["rep"])
            else:group=(r["caseId"].split("-")[0],r["rep"])
            groups[group].append(r)
        if kind=="teacher":manifest=read(root/stem/"cases.json")["cohorts"]
        else:manifest=read(root/stem/"manifest.json")
        for group,records in groups.items():
            assert len({r["seed"] for r in records})==1,"Construction seeds differ within a paired parent/rep"
            for kernel in ("PAPER","JOB_ALIGNED","CLASSIC_GLOBAL","CLASSIC_PERSONAL"):
                choices=[r for r in records if r["kernel"]==kernel];expected={}
                for r in choices:
                    if kind=="teacher":
                        cohort=int(group[0][1:]);g=int(r["caseId"].split("-")[2][1:]);source=manifest[cohort]["sampledGuides"][g]
                    else:
                        parent=int(group[0][1:]);rule=r["caseId"].split("-")[1];source=manifest[parent]["chosenPersonal"][rule]
                    source_key=key(source);child_key=key(r["child"])
                    if source_key in expected:assert expected[source_key]==child_key,"Equal input teachers and noise produced unequal children"
                    expected[source_key]=child_key
                if kind=="teacher" and kernel=="CLASSIC_PERSONAL":
                    assert len({key(r["child"]) for r in choices})==1,"Personal-only control changed when only global guide changed"
                if kind=="personal" and kernel=="CLASSIC_GLOBAL":
                    assert len({key(r["child"]) for r in choices})==1,"Global-only control changed when only personal guide changed"
            checked+=1
    result={"status":"PASS","pairedParentRepGroups":checked,"sameConstructionSeeds":True,"equalTeacherInputReproducesEqualChildren":True,
            "invariantUnusedTeacherControl":True,"newDecoderCalls":0,"newSearchFE":0}
    write_once(root/"paired-input-verification.json",result);return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument("root",type=Path);parser.add_argument("kind",choices=("teacher","personal"));args=parser.parse_args()
    print(verify(args.root,args.kind))


if __name__=="__main__":main()
