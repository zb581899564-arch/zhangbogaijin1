"""Paid teacher setup, receiver-only caches, and one true child per decision."""
from dataclasses import dataclass, asdict
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.statistics import select_minima
from research.fatigue_reuse.chain import timed
from .teachers import build_bank, bank_record
from .candidates import make_pool
from . import scoring
from .protocol import PROTOCOL


@dataclass
class Receiver:
    genome: object
    trace: object
    version: int = 0
    cache: object = None
    epoch: object = None


def decide(instance, params, state, teachers, weights, scales, identity, seeds,
           rng, step, epochs, phases, started, deadline):
    method, regime = identity["method"], identity["regime"]
    pool_seed = seeds["pool"] + 1000003*step
    pool, metadata = timed(phases, "generation", make_pool, instance, state.genome, teachers,
                           pool_seed, identity["block_size"], regime)
    if method not in ("direct", "random") and state.cache is None:
        state.cache = timed(phases, "cache_build", scoring.build, instance, params, state.genome,
                            state.trace, method, regime, weights, scales, state.version)
        state.epoch = {"epoch": len(epochs), "version": state.version, "uses": 0,
                       "on_time_uses": 0, "closed_reason": None}
        if hasattr(state.cache, "work"):
            state.epoch["incremental_work"] = state.cache.work
        epochs.append(state.epoch)
    scores, partials, stage0_ns = timed(phases, "scoring", scoring.scores, instance, params,
        state.genome, state.trace, pool, teachers, state.cache, method, regime, state.version)
    if state.epoch is not None:
        state.epoch["uses"] += 1
    support = np.arange(len(pool)) if scores is None else select_minima(scores)
    chosen = int(support[int(rng.integers(len(support)))])
    candidate = pool[chosen]
    child = timed(phases, "child_decode", decode, instance, candidate.genome, params,
                  method not in ("direct", "random"))
    effective = np.asarray(weights)/scales
    before, after = float(state.trace.objectives @ effective), float(child.objectives @ effective)
    completed = perf_counter_ns()-started
    on_time = deadline is None or completed <= deadline
    accepted = bool(on_time and before-after > 1e-10)
    if state.epoch is not None and on_time:
        state.epoch["on_time_uses"] += 1
    row = {"step": step, "parent_version": state.version, "pool_seed": pool_seed,
        "pool_metadata": metadata, "chosen_index": chosen, "kind": candidate.kind, "origins": candidate.origins,
        "factory_changes": len(candidate.factory_moves), "attribute_changes": len(candidate.attribute_changes),
        "chosen_genome": asdict(candidate.genome), "child_objectives": child.objectives.tolist(),
        "before_value": before, "child_value": after, "accepted": accepted, "on_time": bool(on_time),
        "evaluation_completed_ns": completed, "scores": None if scores is None else scores.tolist(),
        "score_support": support.tolist(), "stage0_ns": stage0_ns, "partial_calls": partials,
        "cache_epoch": None if state.epoch is None else state.epoch["epoch"]}
    if accepted:
        if state.epoch is not None:
            state.epoch["closed_reason"] = "accepted"
        state.genome, state.trace, state.version = candidate.genome, child, state.version+1
        state.cache, state.epoch = None, None
    return row


def run(instance, params, initial, weights, identity, seeds, protocol=PROTOCOL):
    started = perf_counter_ns()
    phases, rows, epochs = {}, [], []
    method = identity["method"]
    rng = np.random.default_rng(seeds["choice"])
    parent = timed(phases, "initial_decode", decode, instance, initial, params, method not in ("direct", "random"))
    scales = parent.objectives.copy()
    effective = np.asarray(weights)/scales
    teachers, bank = timed(phases, "teacher_bank", build_bank, instance, params, initial,
                            effective, seeds["bank"], identity["regime"])
    bank_values, initial_genome = bank_record(bank), asdict(initial)
    state = Receiver(initial, parent)
    deadline = int(protocol["time_budget_seconds"]*1e9) if identity["mode"] == "time" else None
    decisions = 1 if identity["mode"] == "snapshot" else protocol["decisions"]
    while (len(rows) < decisions if deadline is None else perf_counter_ns()-started < deadline):
        rows.append(decide(instance, params, state, teachers, weights, scales, identity, seeds,
                           rng, len(rows), epochs, phases, started, deadline))
    if state.epoch is not None:
        state.epoch["closed_reason"] = "terminal_right_censored"
    final_genome, final_values = asdict(state.genome), state.trace.objectives.tolist()
    finished = perf_counter_ns()-started
    result = {**identity, "initial_genome": initial_genome, "final_genome": final_genome,
        "initial_objectives": scales.tolist(), "final_objectives": final_values,
        "gain": float(parent.objectives @ effective)-float(state.trace.objectives @ effective),
        "elapsed_ns": finished, "deadline_ns": deadline, "overrun_ns": max(0, finished-deadline) if deadline is not None else 0,
        "attempted_decisions": len(rows), "on_time_decisions": sum(r["on_time"] for r in rows),
        "accepted": state.version, "teacher_bank": bank_values, "teacher_indices": [t.bank_index for t in teachers],
        "teacher_values": [t.value for t in teachers], "seeds": seeds,
        "full_decodes": 1+len(bank)+len(rows), "teacher_full_decodes": len(bank),
        "partial_calls": sum(r["partial_calls"] for r in rows), "stage0_ns": sum(r["stage0_ns"] for r in rows),
        "phases_ns": phases, "bookkeeping_ns": finished-sum(phases.values()), "cache_builds": len(epochs)}
    return result, rows, epochs
