"""Regression test for workbook 05 Chapter 5's Question 5 (synthesis/
design question in chapters/05-training-memory-and-communication.qmd
and its Answer Key entry).

Unlike Chapter 4's Question 5 (which forced a unique (tp, dp, ...)
tuple from two simultaneous exact-equality constraints), this question
poses a different kind of systems problem: a continuous memory-budget
INEQUALITY (how many devices are needed so that 16N/DP does not
exceed a stated per-device budget) combined with a discrete
divisibility requirement (DP must divide a fixed 24-device world
size). This test brute-forces every divisor of 24 and confirms that
exactly one is the minimum value satisfying both constraints, and
that it is the value the chapter and Answer Key both state.
"""
import unittest

N = 2_000_000_000
BYTES_PER_GIB = 2 ** 30
MODEL_STATE_TOTAL_BYTES = 16 * N
MEMORY_BUDGET_GIB = 10.0
WORLD_SIZE = 24


def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


def fits_budget(dp):
    per_device_gib = (MODEL_STATE_TOTAL_BYTES / dp) / BYTES_PER_GIB
    return per_device_gib <= MEMORY_BUDGET_GIB


class TestQuestion5MemoryBudgetConstraintIsUnambiguous(unittest.TestCase):
    def test_minimum_continuous_dp_is_between_2_and_3(self):
        gib_total = MODEL_STATE_TOTAL_BYTES / BYTES_PER_GIB
        min_continuous_dp = gib_total / MEMORY_BUDGET_GIB
        self.assertGreater(min_continuous_dp, 2.0)
        self.assertLess(min_continuous_dp, 3.0)

    def test_dp_equals_2_does_not_fit_the_budget(self):
        self.assertFalse(fits_budget(2))

    def test_dp_equals_3_fits_the_budget(self):
        self.assertTrue(fits_budget(3))

    def test_exactly_one_minimal_divisor_of_24_satisfies_both_constraints(self):
        valid_divisors = [d for d in divisors(WORLD_SIZE) if fits_budget(d)]
        self.assertEqual(min(valid_divisors), 3)
        # Confirm no SMALLER divisor of 24 also satisfies the budget
        # (i.e. the minimum is forced, not merely one of several).
        smaller_divisors = [d for d in divisors(WORLD_SIZE) if d < 3]
        self.assertTrue(all(not fits_budget(d) for d in smaller_divisors))

    def test_resulting_tp_degree_is_8(self):
        dp = 3
        tp = WORLD_SIZE // dp
        self.assertEqual(WORLD_SIZE % dp, 0)
        self.assertEqual(tp, 8)
        self.assertEqual(dp * tp, WORLD_SIZE)

    def test_a_larger_divisor_than_necessary_is_not_the_answer(self):
        # Sanity check against the "common trap" in the Answer Key:
        # 4 and 6 are also valid divisors that fit the budget, but
        # they are not the MINIMUM, so they are not the stated answer.
        self.assertTrue(fits_budget(4))
        self.assertTrue(fits_budget(6))
        self.assertGreater(4, 3)
        self.assertGreater(6, 3)


if __name__ == "__main__":
    unittest.main()
