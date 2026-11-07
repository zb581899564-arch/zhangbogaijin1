"""All36 existing reconstructed instances, unchanged setup/profile seed mapping."""
from dataclasses import replace
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from research.fatigue_expansion.protocol import instances
from .protocol import PROTOCOL
from .state import State


def load(project, index, name):
    instance = load_instance(project/"data/chapter4"/name, PROTOCOL["setup_seed_base"]+index)
    values = {p["name"]: fatigue_profile(instance, p, PROTOCOL["profile_seed_base"]+index)
              for p in PROTOCOL["profiles"]}
    fast = values["strong_fast_recovery"]
    values["beta0"] = replace(fast[0], beta=0.), {**fast[1], "beta": 0., "source": "same dynamic decoder, beta=0"}
    return instance, values


def initial(instance, seed):
    genome = parent_genome(instance, seed)
    return genome, State.from_genome(genome, instance.factories)


def cells():
    for model in PROTOCOL["models"]:
        for mode, seconds in (("FE", None), ("time", .5), ("time", 2.)):
            yield model, "TEC", mode, seconds, model == "strong_fast_recovery"
    yield "strong_fast_recovery", "balanced", "time", .5, False
