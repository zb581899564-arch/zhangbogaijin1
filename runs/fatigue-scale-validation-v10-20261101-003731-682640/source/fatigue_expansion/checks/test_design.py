from collections import Counter
from pathlib import Path
import unittest
import numpy as np
from ..protocol import PROTOCOL, instances, cells, chain_protocol
from ..statistics import contrast, holm


class DesignChecks(unittest.TestCase):
    def test_complete_schedule_and_distinct_seed_scope(self):
        project = Path(__file__).resolve().parents[3]
        names = instances(project)
        self.assertEqual(len(names), 36)
        self.assertEqual(len(set(names)), 36)
        self.assertEqual(len(names)*len(PROTOCOL["parent_seeds"])*(len(cells())*5+2), 2916)
        self.assertEqual(sorted({int(n.split("_")[0]) for n in names}), [20, 50, 100, 150, 200])
        self.assertTrue(set(PROTOCOL["parent_seeds"]).isdisjoint(PROTOCOL["validation"]["seeds"]))
        self.assertEqual(chain_protocol(2.)["time_budget_seconds"], 2.)
        self.assertEqual(PROTOCOL["time_budget_seconds"], .25)

    def test_paired_inference_uses_instances_and_all_seeds(self):
        rows = [{"instance": name, "parent_seed": seed, "method": method, "gain": value}
                for name in ("a", "b") for seed in PROTOCOL["parent_seeds"]
                for method, value in (("cut_time", .2), ("random", .1))]
        result = contrast(rows, "cut_time", "random")
        self.assertEqual(result["instance_clusters"], 2)
        self.assertEqual(result["paired_parents"], 6)
        self.assertEqual(result["instance_wins"], 2)
        np.testing.assert_allclose(result["bootstrap_95_interval"], [.1, .1])
        self.assertTrue(.24 < result["one_sided_instance_signflip_p"] < .26)
        with self.assertRaises(AssertionError):
            contrast(rows[:-1], "cut_time", "random")

    def test_holm_is_familywise_monotone_and_requires_positive_interval(self):
        rows = [{"one_sided_instance_signflip_p": p, "bootstrap_95_interval": ci}
                for p, ci in ((.001, [.1, .2]), (.02, [.1, .2]), (.03, [-.1, .2]), (.9, [-.1, .2]))]
        holm(rows)
        np.testing.assert_allclose([r["holm_adjusted_p"] for r in rows], [.004, .06, .06, .9])
        self.assertEqual([r["primary_direction_supported"] for r in rows], [True, False, False, False])


if __name__ == "__main__":
    unittest.main()
