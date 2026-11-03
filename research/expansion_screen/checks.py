"""Synthetic protocol checks only: no decoder, scheduler or performance search.

Run from the project root: python -m research.expansion_screen.checks
"""

import copy
import json
from pathlib import Path
import unittest

from .decision import evaluate_followup, evaluate_screen

CONFIG = json.loads((Path(__file__).parents[1] / "dynamic_benchmark" / "expansion_screen_v1.json")
                    .read_text(encoding="utf-8"))


def matrix(values=None):
    """Every synthetic cell exists; small metrics stand in for offline HV."""
    values = {**{"BASELINE": 100.0, "TAIL": 101.0, "SYNC": 100.0, "SHARE": 104.0,
                 "VALUE_SHARE": 108.0, "NSGA2_4V": 103.0, "SPEA2_4V": 102.0,
                 "MOEAD_4V": 101.0, "NSGA2_VNS_4V": 100.0}, **(values or {})}
    return [{"instance": item["stem"], "seed": seed, "variant": label,
             "hv": {reference: values[label] for reference in ("1.25", "1.5", "2.0")},
             "igdplus": 1.0, "hv_half": values[label], "hv_fe15000": values[label]}
            for item in CONFIG["instances"] for seed in CONFIG["algorithm_seeds"] for label in CONFIG["variants"]]


def change(records, variant, value, instances=None, seeds=None, references=None, field="hv"):
    for record in records:
        if record["variant"] != variant or instances is not None and record["instance"] not in instances:
            continue
        if seeds is not None and record["seed"] not in seeds:
            continue
        if field == "hv":
            for reference in references or ("1.25", "1.5", "2.0"):
                record["hv"][reference] = value
        else:
            record[field] = value


def yellow_with_fe_question():
    records = matrix({"NSGA2_4V": 106.0})
    change(records, "SHARE", 110.0, field="hv_fe15000")
    change(records, "NSGA2_4V", 100.0, field="hv_fe15000")
    return records


def followup_matrix(initial_result, candidate_hv=105.0, external_hv=104.0):
    plan = initial_result["followup"]
    values = {plan["selected_candidate"]: candidate_hv, "BASELINE": 100.0,
              plan["locked_external"]: external_hv}
    return [{"instance": item["stem"], "seed": seed, "variant": label,
             "hv": {reference: values[label] for reference in ("1.25", "1.5", "2.0")},
             "igdplus": 1.0, "hv_half": None, "hv_fe15000": None}
            for item in CONFIG["instances"] for seed in CONFIG["followup"]["seeds"] for label in plan["variants"]]


class DecisionChecks(unittest.TestCase):
    def initial(self, records=None):
        return evaluate_screen(matrix() if records is None else records, CONFIG)

    def test_complete_green_and_json_serializable_without_input_mutation(self):
        records = matrix()
        before = copy.deepcopy(records)
        result = self.initial(records)
        self.assertEqual(result["status"], "GREEN")
        self.assertEqual(result["ready_for_step6"], ["SHARE", "VALUE_SHARE"])
        self.assertEqual(result["external_selection"]["selected"], "NSGA2_4V")
        self.assertEqual(records, before)
        self.assertIsNone(result["followup"]["selected_candidate"])
        json.dumps(result, allow_nan=False)

    def test_clear_red_overrides_unmet_green(self):
        result = self.initial(matrix({"SHARE": 80.0}))
        share = result["candidates"]["SHARE"]
        self.assertEqual(share["color"], "RED")
        self.assertIn("large_losses_to_strongest_external", share["triggered_red_conditions"])
        self.assertIsNone(result["followup"]["selected_candidate"])

    def test_one_instance_cannot_carry_mean(self):
        records = matrix({"SHARE": 99.0, "TAIL": 99.0, "SYNC": 97.0, "NSGA2_4V": 99.0})
        change(records, "SHARE", 180.0, instances=[CONFIG["instances"][0]["stem"]])
        share = self.initial(records)["candidates"]["SHARE"]
        baseline = share["comparisons"]["BASELINE"]
        self.assertGreater(baseline["mean_effect_percent"], 2)
        self.assertLess(baseline["mean_after_removing_best_instance_percent"], 0)
        self.assertEqual(baseline["practical_wins"], 1)
        self.assertEqual(share["color"], "YELLOW")

    def test_seed_outlier_cannot_create_practical_wins(self):
        records = matrix({"SHARE": 99.0, "TAIL": 99.0, "SYNC": 97.0, "NSGA2_4V": 99.0})
        change(records, "SHARE", 130.0, seeds=[CONFIG["algorithm_seeds"][0]])
        share = self.initial(records)["candidates"]["SHARE"]
        self.assertGreater(share["comparisons"]["BASELINE"]["mean_effect_percent"], 2)
        self.assertEqual(share["comparisons"]["BASELINE"]["practical_wins"], 0)
        self.assertEqual(share["color"], "YELLOW")

    def test_matched_parent_failure_blocks_followup_even_with_fe_gain(self):
        records = yellow_with_fe_question()
        change(records, "SYNC", 104.0)
        result = self.initial(records)
        eligibility = result["followup"]["eligibility"]["SHARE"]
        self.assertTrue(eligibility["FE15000"]["gate"]["pass"])
        self.assertFalse(eligibility["conditions"]["conditions"]["matched_parent_initial_green"]["pass"])
        self.assertIsNone(result["followup"]["selected_candidate"])

    def test_tail_control_failure_blocks_followup(self):
        records = yellow_with_fe_question()
        change(records, "TAIL", 106.0)
        result = self.initial(records)
        self.assertFalse(result["followup"]["eligibility"]["SHARE"]["eligible"])
        self.assertIsNone(result["followup"]["selected_candidate"])

    def test_sensitivity_flip_is_yellow_and_does_not_reselect_external(self):
        records = matrix()
        change(records, "SHARE", 99.5, references=["1.25"])
        change(records, "MOEAD_4V", 500.0, references=["1.25"])
        result = self.initial(records)
        share = result["candidates"]["SHARE"]
        self.assertEqual(share["color"], "YELLOW")
        self.assertEqual(share["sensitivity"]["1.25"]["strongest_external"]["comparator"], "NSGA2_4V")
        self.assertFalse(share["green_conditions"]["sensitivity_1.25"]["pass"])

    def test_zero_denominator_is_unresolved_and_never_green(self):
        records = matrix()
        change(records, "BASELINE", 0.0, instances=[CONFIG["instances"][0]["stem"]])
        result = self.initial(records)
        self.assertIsNone(result["external_selection"]["selected"])
        share = result["candidates"]["SHARE"]
        self.assertEqual(share["color"], "YELLOW")
        self.assertIsNone(share["comparisons"]["BASELINE"]["mean_effect_percent"])
        self.assertFalse(share["green_conditions"]["versus_BASELINE"]["pass"])
        json.dumps(result, allow_nan=False)

    def test_systematic_igd_worsening_is_yellow_and_both_zero_is_zero(self):
        records = matrix()
        change(records, "SHARE", 1.2, field="igdplus")
        share = self.initial(records)["candidates"]["SHARE"]
        self.assertEqual(share["color"], "YELLOW")
        self.assertGreater(share["igdplus"]["BASELINE"]["median_symmetric_worsening_percent"], 5)
        for record in records:
            record["igdplus"] = 0.0
        share = self.initial(records)["candidates"]["SHARE"]
        self.assertEqual(share["igdplus"]["BASELINE"]["median_symmetric_worsening_percent"], 0)

    def test_incomplete_duplicate_unknown_seed_and_validity(self):
        records = matrix()
        self.assertEqual(self.initial(records[:-1])["status"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(self.initial(records + [records[0]])["status"], "INVALID")
        changed = copy.deepcopy(records)
        changed[0]["seed"] = 1
        self.assertEqual(self.initial(changed)["status"], "INVALID")
        changed[0]["seed"] = CONFIG["algorithm_seeds"][0]
        changed[0]["hv"]["1.5"] = float("nan")
        self.assertEqual(self.initial(changed)["status"], "INVALID")
        self.assertEqual(evaluate_screen(records, CONFIG, valid=False)["status"], "INVALID")

    def test_Cstar_is_global_method_not_instance_oracle(self):
        records = matrix({"NSGA2_4V": 100.0, "SPEA2_4V": 102.0})
        first = CONFIG["instances"][0]["stem"]
        change(records, "NSGA2_4V", 200.0, instances=[first])
        result = self.initial(records)
        self.assertEqual(result["external_selection"]["selected"], "NSGA2_4V")
        rows = result["candidates"]["SHARE"]["comparisons"]["strongest_external"]["instances"]
        self.assertEqual([row["comparator_mean_hv"] for row in rows], [200.0] + [100.0] * 5)
        self.assertEqual(len(result["external_selection"]["scores"]), 4)

    def test_Cstar_tie_uses_median_then_label_order(self):
        records = matrix({"NSGA2_4V": 102.0, "SPEA2_4V": 102.0, "MOEAD_4V": 102.0})
        result = self.initial(records)
        self.assertEqual(result["external_selection"]["selected"], "MOEAD_4V")
        first = CONFIG["instances"][0]["stem"]
        change(records, "MOEAD_4V", 97.0)
        change(records, "MOEAD_4V", 127.0, instances=[first])
        change(records, "NSGA2_4V", 101.0)
        result = self.initial(records)
        self.assertEqual(result["external_selection"]["selected"], "SPEA2_4V")

    def test_FE_followup_needs_four_all_seed_instance_pairs(self):
        records = yellow_with_fe_question()
        censored_instances = [item["stem"] for item in CONFIG["instances"][:3]]
        change(records, "SHARE", None, instances=censored_instances,
               seeds=[CONFIG["algorithm_seeds"][0]], field="hv_fe15000")
        result = self.initial(records)
        self.assertEqual(result["followup"]["eligibility"]["SHARE"]["FE15000"]["comparison"]["complete_pair_instances"], 3)
        self.assertIsNone(result["followup"]["selected_candidate"])
        change(records, "SHARE", 110.0, instances=[censored_instances[0]], field="hv_fe15000")
        self.assertEqual(self.initial(records)["followup"]["selected_candidate"], "SHARE")

    def test_late_catchup_can_qualify_without_FE_coverage(self):
        records = yellow_with_fe_question()
        change(records, "SHARE", None, field="hv_fe15000")
        change(records, "SHARE", 100.0, field="hv_half")
        result = self.initial(records)
        self.assertTrue(result["followup"]["eligibility"]["SHARE"]["late_catchup"]["gate"]["pass"])
        self.assertEqual(result["followup"]["selected_candidate"], "SHARE")

    def test_single_priority_never_switches_to_secondary_when_primary_yellow(self):
        records = yellow_with_fe_question()
        change(records, "VALUE_SHARE", 108.0)
        change(records, "VALUE_SHARE", 99.5, references=["1.25"])
        result = self.initial(records)
        self.assertEqual(result["candidates"]["VALUE_SHARE"]["color"], "YELLOW")
        self.assertEqual(result["followup"]["selected_candidate"], "SHARE")
        change(records, "SHARE", None, field="hv_fe15000")
        change(records, "VALUE_SHARE", 120.0, field="hv_fe15000")
        result = self.initial(records)
        self.assertTrue(result["followup"]["eligibility"]["VALUE_SHARE"]["eligible"])
        self.assertIsNone(result["followup"]["selected_candidate"])

    def test_secondary_only_when_primary_green(self):
        records = matrix()
        change(records, "VALUE_SHARE", 99.5, references=["1.25"])
        result = self.initial(records)
        self.assertEqual(result["candidates"]["SHARE"]["color"], "GREEN")
        self.assertEqual(result["followup"]["selected_candidate"], "VALUE_SHARE")

    def test_followup_new_seeds_only_locks_external_and_ends_allowance(self):
        initial = self.initial(yellow_with_fe_question())
        records = followup_matrix(initial)
        result = evaluate_followup(records, CONFIG, initial)
        self.assertEqual(result["status"], "LIMITED_CONTINUE")
        self.assertEqual(result["ready_for_step6"], ["SHARE"])
        self.assertFalse(result["initial_seeds_used"])
        self.assertEqual(result["locked_external"], initial["external_selection"]["selected"])
        self.assertEqual(result["analysis_seeds"], CONFIG["followup"]["seeds"])
        self.assertFalse(result["further_followup_allowed"])
        self.assertEqual(evaluate_followup(records, CONFIG, result)["status"], "INVALID")
        self.assertEqual(evaluate_followup(records + matrix(), CONFIG, initial)["status"], "INVALID")
        self.assertEqual(evaluate_followup(records[:-1], CONFIG, initial)["status"], "INSUFFICIENT_EVIDENCE")
        json.dumps(result, allow_nan=False)

    def test_followup_requires_two_of_three_directions_and_no_second_chance(self):
        initial = self.initial(yellow_with_fe_question())
        records = followup_matrix(initial, candidate_hv=99.0, external_hv=99.0)
        change(records, "SHARE", 125.0, seeds=[CONFIG["followup"]["seeds"][0]])
        result = evaluate_followup(records, CONFIG, initial)
        baseline = result["candidates"]["SHARE"]["comparisons"]["BASELINE"]
        self.assertGreater(baseline["mean_effect_percent"], 2)
        self.assertEqual(baseline["practical_wins"], 0)
        self.assertEqual(result["status"], "PAUSE")
        self.assertEqual(result["ready_for_step6"], [])
        self.assertFalse(result["further_followup_allowed"])

    def test_followup_rejects_changed_model_instances_references_and_consumed_plan(self):
        initial = self.initial(yellow_with_fe_question())
        records = followup_matrix(initial)
        for section in ("model", "instances", "metrics"):
            changed = copy.deepcopy(CONFIG)
            if section == "model":
                changed[section]["standby"] = 2.0
            elif section == "instances":
                changed[section][0]["stem"] = "replacement"
            else:
                changed[section]["primary_reference"] = [1.25, 1.25, 1.25]
            self.assertEqual(evaluate_followup(records, changed, initial)["status"], "INVALID")
        consumed = copy.deepcopy(initial)
        consumed["followup"]["campaigns_used"] = 1
        self.assertEqual(evaluate_followup(records, CONFIG, consumed)["status"], "INVALID")

    def test_exact_boundary_and_unrounded_threshold(self):
        records = matrix({"SHARE": 104.0, "NSGA2_4V": 100.0})
        change(records, "SHARE", 101.0)
        result = self.initial(records)
        metric = result["candidates"]["SHARE"]["comparisons"]["BASELINE"]
        self.assertEqual(metric["practical_wins"], 6)
        change(records, "SHARE", 100.9999999)
        result = self.initial(records)
        self.assertEqual(result["candidates"]["SHARE"]["comparisons"]["BASELINE"]["practical_wins"], 0)

    def test_exact_negative_one_and_symmetric_igd_five_boundaries(self):
        records = matrix({"BASELINE": 95.0, "TAIL": 100.0, "SYNC": 97.0, "SHARE": 99.0,
                          "NSGA2_4V": 100.0, "SPEA2_4V": 98.0, "MOEAD_4V": 97.0,
                          "NSGA2_VNS_4V": 96.0})
        for record in records:
            record["igdplus"] = 41.0 if record["variant"] == "SHARE" else 39.0
        share = self.initial(records)["candidates"]["SHARE"]
        self.assertEqual(share["color"], "GREEN")
        self.assertEqual(share["comparisons"]["strongest_external"]["median_effect_percent"], -1)
        self.assertEqual(share["igdplus"]["BASELINE"]["median_symmetric_worsening_percent"], 5)
        self.assertEqual(share["igdplus"]["BASELINE"]["instances_symmetric_worsening_greater_than5_percent"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
