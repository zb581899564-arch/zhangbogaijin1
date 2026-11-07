"""Canonical physical states and the full strong single-job neighborhood."""
from dataclasses import dataclass
from itertools import permutations
import numpy as np
from research.fatigue_mechanism.model import Genome


@dataclass(frozen=True)
class State:
    queues: tuple
    resources: int

    def genome(self):
        js = tuple(j for queue in self.queues for j in queue)
        attrs = {j: (f, (self.resources >> (2*j)) & 1, (self.resources >> (2*j+1)) & 1)
                 for f, queue in enumerate(self.queues) for j in queue}
        return Genome.from_job_attributes(js, attrs)


def moves(state, job):
    source = next(f for f, queue in enumerate(state.queues) if job in queue)
    removed = tuple(tuple(j for j in queue if j != job) for queue in state.queues)
    keep = state.resources & ~(3 << (2*job))
    result = []
    for target in range(2):
        if target != source and not removed[source]:
            continue
        for position in range(len(removed[target])+1):
            queue = removed[target]
            changed = list(removed)
            changed[target] = (*queue[:position], job, *queue[position:])
            for resource in range(4):
                child = State(tuple(changed), keep | (resource << (2*job)))
                if child != state:
                    result.append(child)
    return tuple(result)


class Space:
    def __init__(self, jobs):
        self.jobs, self.resource_count = jobs, 4**jobs
        self.queues = tuple((order[:cut], order[cut:]) for order in permutations(range(jobs)) for cut in range(1, jobs))
        self.queue_index = {q: i for i, q in enumerate(self.queues)}
        self.size = len(self.queues)*self.resource_count

    def state(self, index):
        q, resources = divmod(int(index), self.resource_count)
        return State(self.queues[q], resources)

    def index(self, state):
        return self.queue_index[state.queues]*self.resource_count+state.resources


@dataclass
class Graph:
    space: Space
    pointer: np.ndarray
    destination: np.ndarray
    group: np.ndarray

    @property
    def source(self): return self.group // self.space.jobs

    @property
    def job(self): return self.group % self.space.jobs

    @property
    def row_pointer(self): return self.pointer[::self.space.jobs]

    def neighbors(self, index, job):
        group = int(index)*self.space.jobs+job
        return self.destination[self.pointer[group]:self.pointer[group+1]]


def build_graph(space):
    pointer, destination = [0], []
    for i in range(space.size):
        state = space.state(i)
        for job in range(space.jobs):
            ids = [space.index(child) for child in moves(state, job)]
            assert len(ids) == len(set(ids)) and ids
            destination.extend(ids)
            pointer.append(len(destination))
    pointer = np.asarray(pointer, dtype=np.int64)
    groups = np.repeat(np.arange(space.size*space.jobs, dtype=np.int32), np.diff(pointer))
    return Graph(space, pointer, np.asarray(destination, dtype=np.int32), groups)
