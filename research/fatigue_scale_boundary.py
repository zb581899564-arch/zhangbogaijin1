"""Posthoc-only support-boundary audit, no decoder or new search calls."""
import os
for name in ("OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[name]="1"
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter_ns
import shutil
from research.fatigue_scale.records import read, save
from research.fatigue_scale.state import State, replay
from research.fatigue_scale.operators import segments, indexed_move


def certificate():
    state=State(((0,),(1,),(2,)),((0,0),)*3)
    dims=((2,2),)*3
    endings=set()
    for first in range(3):
        size=sum(row[1] for row in segments(state,first,dims)[1])
        for rank in range(size):
            middle=indexed_move(state,first,dims,rank)[0]
            for second in range(3):
                if first==second:continue
                for next_rank in range(sum(r[1] for r in segments(middle,second,dims)[1])):
                    endings.add(indexed_move(middle,second,dims,next_rank)[0])
    swapped=replay(state,{"family":"swap_rebind","jobs":[0,1],"resources":[(0,0),(0,0)]})
    assert swapped not in endings and len(endings)==27
    return {"parent":state,"atomic_swap":swapped,"N2_unique_endpoints":len(endings),
        "all_N2_FA_unchanged":all(s.queues==state.queues for s in endings),"atomic_swap_outside_N2":True}


def inspect(row):
    initial=State.from_record(row["initial_state"])
    factory={j:f for f,q in enumerate(initial.queues) for j in q}
    counts=list(initial.counts())
    metrics=Counter(initial_two_singletons=int(sum(c==1 for c in counts)>=2), runs=1)
    for step in row["steps"]:
        edit=step["edit"]
        if step["family"]=="swap_rebind":
            a,b=edit["jobs"]
            fa,fb=factory[a],factory[b]
            assert fa!=fb
            both=counts[fa]==counts[fb]==1
            metrics["atomic_singleton_attempts"]+=both
            metrics["swap_attempts"]+=1
            if step["accepted"]:
                metrics["atomic_singleton_accepted"]+=both
                factory[a],factory[b]=fb,fa
        else:
            metrics["plain_components"]+=2
            metrics["empty_N1_components"]+=sum(m is None for m in edit["moves"])
            if step["accepted"]:
                for move in edit["moves"]:
                    if move is None:continue
                    job,new_factory=move[:2]
                    counts[factory[job]]-=1
                    counts[new_factory]+=1
                    factory[job]=new_factory
    final=State.from_record(row["final_state"])
    assert tuple(counts)==final.counts()
    assert factory=={j:f for f,q in enumerate(final.queues) for j in q}
    return metrics


def run(output):
    started=perf_counter_ns()
    groups=defaultdict(Counter)
    for row in read(output,"search"):
        key=(row["model"],row["target"],row["mode"],row["seconds"],row["method"])
        groups[key].update(inspect(row))
    rows=[dict(zip(("model","target","mode","seconds","method"),key))|dict(values) for key,values in groups.items()]
    result={"posthoc":True,"new_decoder_calls":0,"counterexample":certificate(),"groups":rows,
        "wall_ns":perf_counter_ns()-started,"interpretation":"v9 subset only in audited tiny domain; counts do not imply novelty or causal gain"}
    target=output/"posthoc_source"
    target.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__),target/Path(__file__).name)
    save(output/"boundary_review.json",result)
    print(f"BOUNDARY_REVIEW {output/'boundary_review.json'}",flush=True)


if __name__=="__main__":
    import sys
    run(Path(sys.argv[1]))
