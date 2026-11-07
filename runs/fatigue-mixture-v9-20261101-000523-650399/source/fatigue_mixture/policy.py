"""Truth-independent fixed 50/50 choices; candidates use a separate RNG."""
import numpy as np
from research.fatigue_exchange.operators import pool


def family(method, step, branch_seed):
    if method in ("plain", "swap_rebind"):
        return method
    if method == "mix_iid":
        pick = int(np.random.default_rng(branch_seed+1000003*step).integers(2))
    elif method == "mix_alternate":
        pick = (int(np.random.default_rng(branch_seed).integers(2))+step) % 2
    else:
        raise ValueError(method)
    return ("plain", "swap_rebind")[pick]


def candidate(state, method, step, seeds):
    selected = family(method, step, seeds["branch"])
    proposal_seed = seeds["proposal"]+1000003*step
    return selected, proposal_seed, pool(state, selected, proposal_seed, 1)[0].state
