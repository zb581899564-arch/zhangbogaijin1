"""Explicit v6 design; no unused budget/count fields inherited from old trials."""
import json
from research.fatigue_mechanism.protocol import PROTOCOL as V1


PROTOCOL = {
    "version": "fatigue-teacher-v6",
    "scope": "standalone receiver-conditioned structure selection, not a population optimizer",
    "instance_rule": "one eligible instance per (N,F), sorted cells; choose stage index cell_index modulo eligible-stage-count; no v5 outcomes used",
    "parent_seeds": [8089, 16193, 32503, 65011, 130027],
    "setup_seed_base": 314159,
    "profile_seed_base": 271828,
    "profile": {"name": "strong_fast_recovery", "beta": .7, "alpha_per_base": .45, "mu_per_base": .8},
    "targets": {"TEC": [0., 1., 0.], "balanced": [1/3, 1/3, 1/3]},
    "regimes": ["fixed_FA", "transfer_FA"],
    "block_sizes": [2, 6],
    "bank_size": 8,
    "teacher_count": 2,
    "bank_seed_base": 20261121,
    "pool_seed_base": 20261122,
    "choice_seed_base": 20261123,
    "validation_seeds": [23, 53],
    "validation_cases": 288,
    "methods": ["direct", "cheap", "time", "fatigue", "random"],
    "decisions": 24,
    "time_budget_seconds": .5,
    "teacher_source": "top2 of8 paid independent legal genomes, ranked on teacher's own objectives under fixed initial receiver scales; isolated elite donors, not actual PSO pbest/gbest",
    "fixed_teacher_FA": "bank randomizes JS/MA/WA but shares initial receiver's per-job FA; transfer bank has independent legal FA",
    "candidate_pool": "same block of2/6 jobs; each teacher proposes relative order and order+complete job-owned tuples; reject illegal/unchanged; deduplicate by exact per-factory (job,machine,worker) sequences, dropping neutral cross-factory global interleavings, retain all origins",
    "empty_pool": "explicit receiver-noop singleton; still perform one full child evaluation; preserve case and count, never resample for favorable validity or quality",
    "direct": "best teacher's OWN normalized scalar objective, uniform across unique legal seq/joint variants; no receiver-state score",
    "cheap": "old-state local defects with time-only adjoint, no artificial16-defect cutoff for block edits; max_affected=N, all scans/defects paid",
    "time": "exact stage0 plus time-only downstream boundary; incremental for fixed_FA, full stage0 for transfer_FA",
    "fatigue": "same exact stage0, downstream full-fatigue boundary; same implementation/fallback as time",
    "transfer_boundary_limit": "FA-changing candidates still use old downstream factory/routes in the boundary linearization; explicitly an extrapolation stratum, not an exact or newly differentiated later topology",
    "normalization": "initial receiver objective vector fixed throughout a chain for bank ranking, predictions and acceptance",
    "acceptance": "strict true scalar improvement >1e-10; recompute physical fatigue in recipient for ALL methods",
    "FE": "one initial +8 paid teacher-bank full evaluations +one selected full per attempt; snapshot10, fixed24 gives33; equal-time FE naturally differs and is reported",
    "same_pool": "snapshot tests share identical receiver/bank/block/genotypes; sequential chains share seeds and pool rule, not identical pools after their parents diverge",
    "bank_lifetime": "bank paid and built once within each run's clock, then frozen; no future offspring truth or all-candidate oracle in selection",
    "deadline": "nonpreemptive setup/decisions; selected full decode must finish by deadline to accept; setup can consume budget; actual overrun included in gain/sec",
    "online_clock": "RNG, initial and8 bank decodes, ranking, generation/legality/dedup, all cache/prefix/adjoint work, selection, selected full decode, acceptance/invalidation and in-memory step logging",
    "offline": "common data loading and JSON I/O, final QA/pool regeneration, post-selection snapshot truth are separate counts and wall time, never feedback",
    "snapshot": "all13 instances x5 seeds x2 regimes x2 block sizes x2 targets,5 methods once each; after choices fixed, complete every candidate as offline truth and measure realized and uniform-tie expected gain",
    "chains": "same260 instance/seed/regime/block contexts, strong-fast TEC, 24 decisions and0.5 seconds, all5 methods",
    "expected_snapshot_cases": 520,
    "expected_snapshot_runs": 2600,
    "expected_chain_runs": 2600,
    "expected_total_runs": 5200,
    "primary": {"regime": "fixed_FA", "block_size": 2, "target": "TEC",
                "comparisons": [["time", "direct"], ["time", "cheap"], ["fatigue", "direct"], ["fatigue", "cheap"]],
                "family": "12 tests:4 contrasts x(snapshot realized gain, fixed24 gain, time0.5 gain), one joint Holm family; other cells/tie expectation exploratory"},
    "statistics": {"bootstrap": 10000, "sign_flips": "exact enumeration of all2^13 instance signs", "seed": 20261124,
                   "unit": "13 instance clusters; first average5 seeds within each instance for sign flip and W/T/L; hierarchical instance->seed bootstrap95 unadjusted effect intervals"},
    "run_order": "case target/mode order and method order deterministic rotating, one process/thread, no tuning after outcomes",
    "no_tuning": True,
}


def all_instances(project):
    eligible = json.loads((project / "docs/chapter4_instance_eligibility.json").read_text(encoding="utf-8"))["eligible"]
    return list(V1["instances"]) + sorted(set(eligible)-set(V1["instances"]))


def selected_instances(project):
    groups = {}
    for name in all_instances(project):
        n, f, k, _ = map(int, name.removesuffix(".txt").split("_"))
        groups.setdefault((n, f), []).append((k, name))
    return [sorted(groups[key])[i % len(groups[key])][1] for i, key in enumerate(sorted(groups))]
