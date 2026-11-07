"""Small numerical checks for the newly exposed coverage/reporting contract."""
import unittest

import numpy as np

from .tri_indicators import bidirectional_coverage, directional_description


class TriIndicatorChecks(unittest.TestCase):
    def test_identical_front_is_covered_in_both_directions(self):
        result = bidirectional_coverage([[1, 2, 3]], [[1, 2, 3]])
        self.assertEqual((result["C_A_B"], result["C_B_A"]), (1, 1))
        self.assertEqual(result["sharedObjectiveVectors"], 1)

    def test_dominator_and_incomparable_fronts(self):
        better = bidirectional_coverage([[1, 1, 1]], [[2, 2, 2]])
        self.assertEqual((better["C_A_B"], better["C_B_A"]), (1, 0))
        neither = bidirectional_coverage([[1, 3, 1]], [[3, 1, 1]])
        self.assertEqual((neither["C_A_B"], neither["C_B_A"]), (0, 0))

    def test_duplicate_vectors_do_not_reweight_target_set(self):
        result = bidirectional_coverage([[1, 2, 1]], [[2, 2, 1], [2, 2, 1], [0, 4, 1]])
        self.assertEqual((result["coveredB"], result["totalB"], result["C_A_B"]), (1, 2, .5))

    def test_invalid_front_is_not_silently_compared(self):
        for front in ([], [[1, 2]], [[1, np.nan, 3]], [[1, np.inf, 3]]):
            with self.subTest(front=front), self.assertRaises(ValueError):
                bidirectional_coverage(front, [[1, 2, 3]])

    def test_vectorized_coverage_matches_scalar_weak_dominance(self):
        rng = np.random.default_rng(20261105)
        for _ in range(32):
            a = np.unique(rng.integers(0, 5, (9, 3)), axis=0)
            b = np.unique(rng.integers(0, 5, (7, 3)), axis=0)
            expected = sum(any(all(x <= y for x, y in zip(p, q)) for p in a) for q in b)
            result = bidirectional_coverage(a, b)
            self.assertEqual(result["coveredB"], expected)
            self.assertEqual(result["C_A_B"], expected / len(b))

    def test_directional_conflicts_are_visible(self):
        self.assertEqual(directional_description(1, 2, .8, .2)["label"], "MIXED_DIRECTIONS")
        self.assertEqual(directional_description(1, -2, .8, .2)["label"], "ALIGNED_TOWARD_A")
        neutral_c = directional_description(1, -2, 0, 0)
        self.assertTrue(neutral_c["coverageUninformative"])


if __name__ == "__main__":
    unittest.main()
