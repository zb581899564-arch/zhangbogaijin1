"""Same v2 candidate stream, avoiding construction of unselected genomes."""
import numpy as np
from research.fatigue_mechanism.model import Genome
from research.fatigue_topology.trials import Trial


def local_pool(instance, parent, seed, count=16):
    rng, attrs, descriptors = np.random.default_rng(seed), parent.by_job(), []
    for job in parent.js:
        f, m, w = attrs[job]
        for kind, limit, current in (("one_machine", len(instance.speeds[f][0]), m),
                                      ("one_worker", len(instance.efficiencies[f][0]), w)):
            alternatives = [i for i in range(limit) if i != current]
            if alternatives:
                descriptors.append((kind, job, int(rng.choice(alternatives))))
    for f in range(instance.factories):
        sequence = [j for j in parent.js if attrs[j][0] == f]
        descriptors.extend(("adjacent_order", a, b) for a, b in zip(sequence, sequence[1:]))
    rng.shuffle(descriptors)
    if len(descriptors) < count:
        raise ValueError("too few distinct legal candidates")
    result = []
    for kind, job, other in descriptors[:count]:
        js, changed = list(parent.js), dict(attrs)
        if kind == "adjacent_order":
            i, j = js.index(job), js.index(other)
            js[i], js[j] = js[j], js[i]
            jobs = (job, other)
        else:
            f, m, w = attrs[job]
            changed[job] = (f, other, w) if kind == "one_machine" else (f, m, other)
            jobs = (job,)
        result.append(Trial("legal_local", kind, Genome.from_job_attributes(js, changed), jobs))
    return tuple(result)
