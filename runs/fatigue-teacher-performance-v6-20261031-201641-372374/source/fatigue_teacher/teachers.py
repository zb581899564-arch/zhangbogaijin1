"""Paid independent elite donors; never copy donor physical states."""
from dataclasses import dataclass, asdict
import numpy as np
from research.fatigue_mechanism.instances import parent_genome
from research.fatigue_mechanism.model import Genome
from research.fatigue_mechanism.decoder import decode
from .protocol import PROTOCOL


@dataclass(frozen=True)
class Teacher:
    bank_index: int
    genome: Genome
    objectives: tuple
    value: float


def fixed_factory_genome(instance, receiver, seed):
    rng, attrs = np.random.default_rng(seed), receiver.by_job()
    js = tuple(map(int, rng.permutation(instance.jobs)))
    new = {j: (f, int(rng.integers(len(instance.speeds[f][0]))),
                  int(rng.integers(len(instance.efficiencies[f][0])))) for j, (f, _, _) in attrs.items()}
    return Genome.from_job_attributes(js, new)


def bank_genomes(instance, receiver, seed, regime):
    result = []
    for i in range(PROTOCOL["bank_size"]):
        draw = seed + 1000033*i
        genome = fixed_factory_genome(instance, receiver, draw) if regime == "fixed_FA" else parent_genome(instance, draw)
        result.append(genome)
    return tuple(result)


def build_bank(instance, params, receiver, effective, seed, regime):
    bank = []
    for i, genome in enumerate(bank_genomes(instance, receiver, seed, regime)):
        result = decode(instance, genome, params, retain_trace=False)
        bank.append(Teacher(i, genome, tuple(map(float, result.objectives)), float(result.objectives @ effective)))
    teachers = tuple(sorted(bank, key=lambda t: (t.value, t.bank_index))[:PROTOCOL["teacher_count"]])
    return teachers, tuple(bank)


def restore_bank(values):
    return tuple(Teacher(v["bank_index"], Genome(**v["genome"]), tuple(v["objectives"]), v["value"]) for v in values)


def bank_record(bank):
    return [asdict(t) for t in bank]
