"""Linux-only mathematical acceptance entry; does not read scientific runs."""
import platform


def run_checks():
    if platform.system() != "Linux":
        raise RuntimeError("Numerical checks are authorized only on Linux; no local execution")
    from .check_attainment import (check_conditional_quartile_sections, check_empty_and_three_seed_attainment,
                                  check_exact_attainment)
    from .check_indicators import (check_coverage_and_reference, check_hv_and_distances,
                                  check_normalization_and_extremes, check_paired_effects)
    from .check_stages import check_chronological_telescope, check_stage_validation
    from .eaf_difference import check_eaf_difference

    checks = [check_hv_and_distances, check_coverage_and_reference,
              check_normalization_and_extremes, check_paired_effects,
              check_exact_attainment, check_empty_and_three_seed_attainment,
              check_conditional_quartile_sections, check_chronological_telescope,
              check_stage_validation, check_eaf_difference]
    passed = []
    for check in checks:
        check()
        passed.append(check.__name__)
    return {"status": "PASS", "platform": platform.system(), "checks": passed,
            "kind": "mathematical_fixtures_only", "search_evaluations": 0,
            "scheduling_model_calls": 0, "scientific_performance_claim": False}
