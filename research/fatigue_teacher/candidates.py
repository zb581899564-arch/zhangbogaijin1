"""Truth-independent teacher block inheritance with auditable legality/dedup."""
from dataclasses import dataclass, replace
import numpy as np
from research.fatigue_mechanism.model import Genome
from research.fatigue_mechanism.decoder import _validate_genome


@dataclass(frozen=True)
class Candidate:
    pool: str
    kind: str
    genome: Genome
    jobs: tuple
    origins: tuple
    factory_moves: tuple = ()
    attribute_changes: tuple = ()


def physical_signature(instance, genome):
    factories = [[] for _ in range(instance.factories)]
    for j, f, m, w in zip(genome.js, genome.fa, genome.ma, genome.wa):
        factories[f].append((j, m, w))
    return tuple(tuple(values) for values in factories)


def inherit(receiver, teacher, block, joint):
    selected, attrs = set(block), receiver.by_job()
    positions = [i for i, j in enumerate(receiver.js) if j in selected]
    sequence = [j for j in teacher.genome.js if j in selected]
    js = list(receiver.js)
    for position, job in zip(positions, sequence):
        js[position] = job
    if joint:
        donor = teacher.genome.by_job()
        for job in block:
            attrs[job] = donor[job]
    return Genome.from_job_attributes(js, attrs)


def make_pool(instance, receiver, teachers, seed, size, regime):
    if regime not in ("fixed_FA", "transfer_FA"):
        raise ValueError("unknown teacher transfer regime")
    rng = np.random.default_rng(seed)
    block = tuple(map(int, rng.choice(instance.jobs, size=size, replace=False)))
    original, receiver_attrs = physical_signature(instance, receiver), receiver.by_job()
    proposals, values = {}, {"attempted": 0, "illegal": 0, "unchanged": 0, "duplicates": 0,
                             "block": list(block), "fallback_noop": False}
    for teacher in teachers:
        for joint in (False, True):
            values["attempted"] += 1
            genome = inherit(receiver, teacher, block, joint)
            try:
                _validate_genome(instance, genome)
            except ValueError:
                values["illegal"] += 1
                continue
            child_attrs = genome.by_job()
            if regime == "fixed_FA" and any(receiver_attrs[j][0] != child_attrs[j][0] for j in block):
                raise AssertionError("fixed_FA teacher bank violated contract")
            signature = physical_signature(instance, genome)
            if signature == original:
                values["unchanged"] += 1
                continue
            origin = (teacher.bank_index, "joint" if joint else "sequence")
            if signature in proposals:
                values["duplicates"] += 1
                old = proposals[signature]
                proposals[signature] = replace(old, origins=(*old.origins, origin))
            else:
                moved = tuple(j for j in block if receiver_attrs[j][0] != child_attrs[j][0])
                changed = tuple(j for j in block if receiver_attrs[j] != child_attrs[j])
                proposals[signature] = Candidate("teacher", "joint" if joint else "sequence", genome, block,
                                                 (origin,), moved, changed)
    pool = tuple(proposals.values())
    if not pool:
        values["fallback_noop"] = True
        pool = (Candidate("teacher", "noop", receiver, block, ()),)
    values["unique_candidates"] = len(pool)
    return pool, values
