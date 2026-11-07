"""Canonical physical state with arbitrary factory resource dimensions."""
from dataclasses import dataclass
from research.fatigue_mechanism.model import Genome


@dataclass(frozen=True)
class State:
    queues: tuple
    resources: tuple

    @classmethod
    def from_record(cls, value):
        return cls(tuple(map(tuple, value["queues"])), tuple(map(tuple, value["resources"])))

    @classmethod
    def from_genome(cls, genome, factories):
        attrs = genome.by_job()
        queues = tuple(tuple(j for j in genome.js if attrs[j][0] == f) for f in range(factories))
        return cls(queues, tuple((attrs[j][1], attrs[j][2]) for j in range(len(genome.js))))

    def genome(self):
        attrs = {j: (f, *self.resources[j]) for f, q in enumerate(self.queues) for j in q}
        return Genome.from_job_attributes(tuple(j for q in self.queues for j in q), attrs)

    def counts(self):
        return tuple(map(len, self.queues))


def insert(state, job, factory, position, machine, worker):
    queues = [tuple(j for j in q if j != job) for q in state.queues]
    q = queues[factory]
    queues[factory] = (*q[:position], job, *q[position:])
    resources = list(state.resources)
    resources[job] = (machine, worker)
    return State(tuple(queues), tuple(resources))


def replay(state, descriptor):
    if descriptor["family"] == "plain":
        for move in descriptor["moves"]:
            if move is not None:
                state = insert(state, *move)
        return state
    a, b = descriptor["jobs"]
    queues = tuple(tuple(b if j == a else a if j == b else j for j in q) for q in state.queues)
    resources = list(state.resources)
    resources[a], resources[b] = map(tuple, descriptor["resources"])
    return State(queues, tuple(resources))
