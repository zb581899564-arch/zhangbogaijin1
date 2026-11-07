"""Deterministic phase-knee calibration and fixed ledger design; zero search evaluations."""
from fractions import Fraction
from itertools import groupby

import numpy as np

from reverse_ledger_analysis import archive_admissions
from run_dynamic_deep_roles import ledger
from run_dynamic_reverse_ledger_audit import ROOT, trial_folder
from run_long_budget_bridge import hypervolume, read


ANCHOR = ROOT / "runs/dynamic-reverse-ledger-20261103-231754-095093"
OLD = ROOT / "runs/dynamic-deep-roles-20261103-212007-121034"
ROLE_NAMES = ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST")
GROUP_SIZE = (15, 55, 15, 15)
ROUNDS = (8, 8, 7, 7)
GLOBAL_PER_CYCLE = 5000
CROSS_PER_VISIT = 2
CAP = 500000
FIRST_LOCAL = 100 + GLOBAL_PER_CYCLE


def phase_quarters(folder, norm, stage_start=FIRST_LOCAL):
    """Use first-cycle external HV, not accepted-only objective improvements."""
    history = archive_admissions(folder)
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    slots = [r for r in ledger(folder) if r[0] <= 100]
    result = {}
    for gid, part in groupby(slots, key=lambda r: r[1]):
        local = list(part)
        paid = sum(r[4] for r in local)
        cutoffs = [stage_start + paid * k // 4 for k in range(5)]
        hv = [float(hypervolume((np.asarray([p for t, p in history if t <= cut]) - lower) / scale,
                                (1.5,) * 3)) for cut in cutoffs]
        # Rate, rather than absolute gain, keeps the rule exact when integer quarter lengths differ.
        rates = [max(0.0, b - a) * 10000 / (j - i)
                 for a, b, i, j in zip(hv, hv[1:], cutoffs, cutoffs[1:])]
        knee = next((k for k in range(1, 4) if max(rates[:k]) > 1e-12
                     and max(rates[k:]) <= .25 * max(rates[:k])), 4)
        result[ROLE_NAMES[gid - 1]] = {"cutoffs": cutoffs, "hv": hv, "deltaHVPer10000FE": rates,
                                      "kneeQuarter": knee, "phaseFE": paid, "visits": GROUP_SIZE[gid - 1]}
        stage_start += paid
    assert list(result) == list(ROLE_NAMES)
    return result


def allocate(total, weights):
    """Largest remainder, with earlier physical slot first on exact ties."""
    exact = [Fraction(total) * w / sum(weights) for w in weights]
    out = [int(x) for x in exact]
    order = sorted(range(len(out)), key=lambda i: (out[i] - exact[i], i))
    for i in order[:total - sum(out)]:
        out[i] += 1
    assert sum(out) == total and min(out) > 0
    return out


def schedule(original, weights):
    factory_by_visit = {i: [] for i in range(1, 101)}
    group_by_visit = {}
    for visit, group, r, factory, _, _ in original:
        if visit > 100:
            break
        group_by_visit[visit] = group
        if r >= 0:
            factory_by_visit[visit].append(factory)
    assert all(len(v) == sum(ROUNDS) for v in factory_by_visit.values())
    count = len(ROUNDS)
    local, rest = divmod(CAP - 100 - count * GLOBAL_PER_CYCLE, count)
    assert rest == 0
    out, quotas, offset = [], [], 0
    for cycle, n_rounds in enumerate(ROUNDS):
        intra = allocate(local - 100 * CROSS_PER_VISIT, weights)
        quotas.append({name: {"inter": CROSS_PER_VISIT * size, "intra": budget}
                       for name, size, budget in zip(ROLE_NAMES, GROUP_SIZE, intra)})
        by_group = {g + 1: iter(allocate(b, [1] * GROUP_SIZE[g])) for g, b in enumerate(intra)}
        for position in range(1, 101):
            visit, group = 100 * cycle + position, group_by_visit[position]
            out.append((visit, group, -1, -1, CROSS_PER_VISIT, 0))
            slot_budget = allocate(next(by_group[group]), [1] * n_rounds)
            factories = factory_by_visit[position][offset:offset + n_rounds]
            out.extend((visit, group, r, f, b, 0) for r, (f, b) in enumerate(zip(factories, slot_budget)))
        offset += n_rounds
    assert sum(r[4] for r in out) + 100 + count * GLOBAL_PER_CYCLE == CAP
    return out, quotas


def design():
    norm = read(ANCHOR / "protocol.json")["normalization"]
    active = phase_quarters(trial_folder(ANCHOR, "SPECIAL"), norm)
    old = phase_quarters(OLD / "SPECIAL/trials/fatigue/SHARE_JOB_ALIGNED", norm)
    old_slots = ledger(trial_folder(ANCHOR, "U_RECORD"))
    ordinary_weights = list(map(Fraction, GROUP_SIZE))
    # Knee depth per visit; group size then converts to group total. Equal depth is the ordinary control.
    role_weights = [Fraction(r["phaseFE"] * r["kneeQuarter"], 4) for r in active.values()]
    plans = {"DEEP": old_slots}
    quotas = {}
    for key, weights in (("ROTATE", ordinary_weights), ("ROLE", role_weights)):
        plans[key], quotas[key] = schedule(old_slots, weights)
    assert [(v, g, r, f) for v, g, r, f, _, _ in plans["ROTATE"]] == [
        (v, g, r, f) for v, g, r, f, _, _ in plans["ROLE"]]
    assert [r[4] for r in plans["ROTATE"]] != [r[4] for r in plans["ROLE"]]
    return plans, {"calibrationL_U": active, "sensitivityL_S": old, "quotas": quotas,
                   "roleWeightByGroup": dict(zip(ROLE_NAMES, map(float, role_weights)))}
