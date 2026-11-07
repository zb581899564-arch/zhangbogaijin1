"""Past-checkpoint donor pools, fixed-size sampling and explicit logical cost metadata."""
import random

from run_long_budget_bridge import rows, write_once
from research.semantic_repair.evidence import digest


def role(slot):
    return "MAKESPAN" if slot<15 else "CENTER" if slot<70 else "ENERGY" if slot<85 else "WORKER_COST"


def initial_records(folder):
    points=rows(folder/"initial-population.jsonl")
    assert len(points)==100 and [p["fe"] for p in points]==list(range(1,101))
    return [{**p,"bornFE":p["fe"]} for p in points]


def at(folder,fee):
    point,=[p for p in rows(folder/"anytime.jsonl") if p["checkpointKind"]=="FE" and p["checkpoint"]==fee and p["reached"]]
    assert point["fe"]==fee
    genes=[p for p in rows(folder/"checkpoint-solutions.jsonl") if p["checkpointKind"]=="FE" and p["checkpoint"]==fee]
    assert genes and {tuple(p["objectives"]) for p in genes}==set(map(tuple,point["front"]))
    assert all(1<=p["bornFE"]<=fee==p["checkpointFE"] for p in genes)
    return point,genes


def write_pool(path,points,seed,source,kind):
    rng=random.Random(seed ^ 0x4b6a31)
    indices=[rng.randrange(len(points)) for _ in range(100)]
    chosen=[points[i] for i in indices]
    with path.open("x",encoding="utf-8") as stream:
        for i,point in enumerate(chosen):
            assert 1<=point["bornFE"]<=50000
            fields=[str(i),role(i),str(point["bornFE"]),",".join(repr(x) for x in point["objectives"])]
            fields += [",".join(map(str,point[key])) for key in ("JS","FA","MA","WA")]
            stream.write("\t".join(fields)+"\n")
    write_once(path.with_suffix(".provenance.json"),{"source":str(source),"kind":kind,"sourceCheckpointFE":50000,
        "sampling":"100slots, uniform with replacement using independent frozenPythonRandom; no objective ranking",
        "candidatePoints":len(points),"selectedIndices":indices,"selectedBornFE":[p["bornFE"] for p in chosen],
        "teacherFileSHA256":digest(path),"importedRoleColumn":"Receiving slot preference, not source producer attribution"})
    return chosen


def write_initial(path,points):
    assert len(points)==100
    with path.open("x",encoding="utf-8") as stream:
        for i,p in enumerate(points):
            fields=[str(i),role(i),str(p["bornFE"]),",".join(repr(x) for x in p["objectives"])]
            fields += [",".join(map(str,p[key])) for key in ("JS","FA","MA","WA")]
            stream.write("\t".join(fields)+"\n")
