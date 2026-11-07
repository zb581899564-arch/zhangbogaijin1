"""Independent representation and causal donor-state checks; no physical decoder."""
import math
from analysis_common import require


def by_job(row, field):
    result = [None] * len(row["JS"])
    require(sorted(row["JS"]) == list(range(len(result))), "JS is not a job permutation")
    require(len(row[field]) == len(result), f"Wrong {field} length")
    for job, value in zip(row["JS"], row[field]):
        result[job] = value
    return result


def physical(row, factories):
    return tuple(tuple((j, m, w) for j, f, m, w in zip(row["JS"], row["FA"], row["MA"], row["WA"])
                       if f == factory) for factory in range(factories))


def collect_catalog(rows):
    catalog = {}
    for row in rows:
        fa, ma, wa = (by_job(row, name) for name in ("FA", "MA", "WA"))
        require(len(row["resources"]) == len(fa), "Resource length differs from job count")
        for resource, f, m, w in zip(row["resources"], fa, ma, wa):
            value = (f, m, w)
            require(resource not in catalog or catalog[resource] == value, "Inconsistent resource tuple ID")
            catalog[resource] = value
    require(len(set(catalog.values())) == len(catalog), "Resource IDs alias one tuple")
    return catalog


def verify_encoding(row, catalog, factories):
    count = len(row["resources"])
    require(len(row["keys"]) == count and all(math.isfinite(k) and 0 <= k <= 1 for k in row["keys"]),
            "Keys must be finite by-job values in [0,1]")
    order = sorted(range(count), key=lambda job: (row["keys"][job], -job))
    require(row["JS"] == order, "JS disagrees with stored-key ordering and tie rule")
    tuples = [catalog[value] for value in row["resources"]]
    require(set(v[0] for v in tuples) == set(range(factories)), "Empty or unknown factory")
    for axis, name in enumerate(("FA", "MA", "WA")):
        require(row[name] == [tuples[j][axis] for j in order], f"{name} disagrees with resource IDs")


def verify_mix(parent, donor, step, catalog, factories):
    resources, keys = list(parent["resources"]), list(parent["keys"])
    for job in step["mask"]:
        resources[job], keys[job] = donor["resources"][job], donor["keys"][job]
    fallback = set(catalog[r][0] for r in resources) != set(range(factories))
    require(step["fallback"] is fallback, "Incorrect empty-factory fallback flag")
    if fallback:
        resources, keys = parent["resources"], parent["keys"]
    require(step["resources"] == resources and step["keys"] == keys,
            "Child is not the mask mixture of the current causal donor and receiver")
    verify_encoding(step, catalog, factories)
    if parent["family"] >= 0:
        require(by_job(step, "FA") == by_job(parent, "FA") == by_job(donor, "FA"),
                "Fixed-family per-job factory context changed")


class JavaRandom:
    """48-bit java.util.Random with Java signed rejection in nextInt(bound)."""
    def __init__(self, seed):
        self.seed = (seed ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def next_bits(self, bits):
        self.seed = (self.seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        return self.seed >> (48 - bits)

    def next_int(self, bound):
        require(0 < bound <= (1 << 31) - 1, "Invalid Java nextInt bound")
        if bound & (bound - 1) == 0:
            return (bound * self.next_bits(31)) >> 31
        while True:
            bits = self.next_bits(31)
            value = bits % bound
            if bits - value + bound - 1 < (1 << 31):
                return value


def proposal_seed(seed, slot, step):
    value = (seed ^ ((0x632BE59BD9B4E019 * (slot + 1)
                     + 0x9E3779B97F4A7C15 * (step + 1)) & ((1 << 64) - 1))) & ((1 << 64) - 1)
    return value - (1 << 64) if value >= (1 << 63) else value
