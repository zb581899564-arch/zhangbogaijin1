"""Zero-FE support audit of atomic tuples versus same-factory machine/worker products."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from collections import defaultdict
from datetime import datetime
from itertools import product
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock, hypervolume, igd_plus, nondominated
from run_pa_allele_domain_audit import by_job
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage
from research.semantic_repair.evidence import digest

SOURCE = ROOT / "runs/pa-base-qualification-20261105-180835-751659"
ENGINE = ROOT / "runs/pa-population-engineering-20261105-164116-698339"


def tracked_rows(path, identities):
    identities[str(path)] = digest(path)
    return rows(path)


def support(initial, legal):
    jobs = len(initial[0]["JS"])
    atomic = [set() for _ in range(jobs)]
    for point in initial:
        for job, value in enumerate(by_job(point)):
            assert value in legal
            atomic[job].add(value)
    factories = {f for f, _, _ in legal}
    for f in factories:
        machines = {m for ff, m, _ in legal if ff == f}
        workers = {w for ff, _, w in legal if ff == f}
        assert {(f, m, w) for m, w in product(machines, workers)} == {t for t in legal if t[0] == f}
    factorized, job_rows = [], []
    for job, observed in enumerate(atomic):
        by_factory = defaultdict(set)
        for f, m, w in observed: by_factory[f].add((m, w))
        expanded = {(f, m, w) for f, pairs in by_factory.items()
                    for m in {m for m, _ in pairs} for w in {w for _, w in pairs}}
        assert observed <= expanded <= legal
        factorized.append(expanded)
        job_rows.append({"job": job, "factoryFraction": len(by_factory) / len(factories),
            "atomicFraction": len(observed) / len(legal), "factorizedFraction": len(expanded) / len(legal),
            "atomicTuples": sorted(observed), "newTuplesFromConditionalProduct": sorted(expanded - observed),
            "remainingMissingMarginals": sorted(legal - expanded)})
    return atomic, factorized, job_rows


def normalized(points, norm):
    return (np.asarray(points, dtype=float).reshape(-1, 3) - norm["lower"]) / norm["scale"]


def objective_potential(base, subset, control, reference, norm):
    front = nondominated(np.vstack([base, subset]))
    a = normalized(front, norm)
    return {"frontSize": len(front), "HV": {str(r): hypervolume(a, (r,) * 3) for r in (1.25, 1.5, 2.)},
        "IGDplus": igd_plus(a, reference), "coverageAgainstFullControl": bidirectional_coverage(front, control),
        "isSearchResult": False}


def context(spec, seed, arms, identities):
    stem, norm = spec["stem"], spec["normalization"]
    folder = SOURCE / stem / str(seed)
    initial = tracked_rows(folder / "FE500K-PA_JOINT/initial-population.jsonl", identities)
    assert len(initial) == 100
    catalog, = tracked_rows(ENGINE / stem / "main/audit/catalog.jsonl", identities)
    legal = set(map(tuple, catalog["tuples"]))
    atomic, factorized, job_rows = support(initial, legal)
    endpoints = {}
    reference_points = []
    for reference_seed in (13910003, 13910037):
        for arm in arms:
            points = [r for r in tracked_rows(SOURCE / stem / str(reference_seed) / ("FE500K-" + arm) / "checkpoint-solutions.jsonl", identities)
                      if r["checkpointKind"] == "FE" and r["checkpoint"] == 500000]
            assert points
            if reference_seed == seed: endpoints[arm] = points
            reference_points.extend(r["objectives"] for r in points)
    reference = nondominated(normalized(reference_points, norm))
    base = np.asarray([r["objectives"] for r in endpoints["PA_JOINT"]])
    base_hv = hypervolume(normalized(base, norm), (1.5,) * 3)
    observations = []
    for arm, points in endpoints.items():
        vectors = [by_job(p) for p in points]
        atom_mask = [all(t in atomic[j] for j, t in enumerate(v)) for v in vectors]
        factor_mask = [all(t in factorized[j] for j, t in enumerate(v)) for v in vectors]
        if arm.startswith("PA_"): assert all(atom_mask)
        raw = np.asarray([p["objectives"] for p in points])
        atom_subset = raw[np.asarray(atom_mask)]
        factor_subset = raw[np.asarray(factor_mask)]
        atom_potential = objective_potential(base, atom_subset, raw, reference, norm)
        factor_potential = objective_potential(base, factor_subset, raw, reference, norm)
        all_potential = objective_potential(base, raw, raw, reference, norm)
        observations.append({"arm": arm, "terminalPoints": len(points),
            "insideAtomicCount": sum(atom_mask), "insideConditionalProductCount": sum(factor_mask),
            "outsideAtomicFraction": 1 - sum(atom_mask) / len(points),
            "insideConditionalProductFraction": sum(factor_mask) / len(points),
            "atomicSupportedKnownPointUnion": atom_potential,
            "conditionalSupportedKnownPointUnion": factor_potential, "fullKnownPointUnion": all_potential,
            "conditionalOnlyUnionHVOverOwnPct": 100 * (factor_potential["HV"]["1.5"] - atom_potential["HV"]["1.5"]) / base_hv,
            "fullKnownUnionHVOverOwnPct": 100 * (all_potential["HV"]["1.5"] - base_hv) / base_hv,
            "completeGenotypeReachabilityOrCausalGainProved": False})
    return {"stem": stem, "seed": seed, "jobs": len(atomic), "factories": len({f for f, _, _ in legal}),
        "legalResourceTuples": len(legal), "jobSupport": job_rows,
        "meanAtomicFraction": float(np.mean([r["atomicFraction"] for r in job_rows])),
        "meanConditionalProductFraction": float(np.mean([r["factorizedFraction"] for r in job_rows])),
        "meanFactoryFraction": float(np.mean([r["factoryFraction"] for r in job_rows])), "observations": observations}


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-conditional-domain-audit-%Y%m%d-%H%M%S-%f")
        root.mkdir(); identities = {}
        print("PA_CONDITIONAL_DOMAIN_ROOT", root, flush=True)
        write_once(root / "protocol.json", {"source": str(SOURCE), "sampling": "All6arms x2registered instances x2seeds at500k, no selected good points",
            "question": "Which resource support is lost by atomic FMW copying, and how much can be represented by already-seen conditional machine/worker marginals?",
            "domain": "Per-job union over observed factories of M_seen(job,f) x W_seen(job,f), verified against legal catalog",
            "metrics": "HV/IGD+/bidirectional C on unions of known paid points for support diagnosis only; original scales and common6arm x2seed empirical reference",
            "limits": "Not generated/evaluated new schedules, not algorithm results, not complete genome reachability or performance causality, and no automatic new operator",
            "newSearchFE": 0, "decoderCalls": 0, "defaultMainlineChanged": False})
        shutil.copy2(Path(__file__), root / Path(__file__).name)
        try:
            identities[str(SOURCE / "protocol.json")] = digest(SOURCE / "protocol.json")
            plan = read(SOURCE / "protocol.json")
            results = [context(spec, seed, plan["arms"], identities) for spec in plan["instances"] for seed in plan["seeds"]]
            assert all(digest(Path(p)) == sha for p, sha in identities.items())
            write_once(root / "input-identities.json", identities)
            write_once(root / "analysis.json", {"contexts": results, "newSearchFE": 0, "decoderCalls": 0,
                "consumedInputsUnchanged": True, "newAlgorithmImplemented": False, "causalPerformanceGainProved": False, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), "newSearchFE": 0, "decoderCalls": 0})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "newSearchFE": 0, "decoderCalls": 0, "goalAchieved": False})
        print("PA_CONDITIONAL_DOMAIN_COMPLETE", [(r["stem"], r["seed"], r["meanAtomicFraction"], r["meanConditionalProductFraction"]) for r in results], flush=True)


if __name__ == "__main__":
    main()
