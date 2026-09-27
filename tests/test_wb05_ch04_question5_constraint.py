"""Regression test for workbook 05 Chapter 4's Question 5 (interview/
design question in chapters/04-distributed-parallelism.qmd and its
Answer Key entry in solutions/04-distributed-parallelism-solutions.qmd).

An earlier version of this question stated only "tp <= 8" (an upper
bound) and "the data-parallel group must be large" (unquantified),
then presented tp=8, dp=8 as if it "maximized" the data-parallel
group -- but under those loose constraints, tp=1, dp=64 also satisfies
tp<=8 and gives a STRICTLY LARGER data-parallel group, so the proposed
answer did not actually follow from the stated constraints.

The question was corrected to state two precise, separately justified
requirements: tp must equal exactly 8 (a per-layer weight/activation
memory requirement, not merely an upper bound), and dp must be at
least 8 (an optimizer-state/gradient memory requirement). This test
brute-forces every (tp, dp, pp, cp, ep) factorization of 64 and
confirms that exactly one satisfies both requirements, and that it is
the combination the chapter and its Answer Key both state.
"""
import unittest
from itertools import product


WORLD_SIZE = 64
REQUIRED_TP = 8
MIN_DP = 8


def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


def enumerate_valid_configs(world_size, required_tp, min_dp):
    """Every (tp, dp, pp, cp, ep) of positive integers whose product is
    world_size, restricted to tp == required_tp and dp >= min_dp."""
    valid = []
    ds = divisors(world_size)
    for tp, dp, pp, cp, ep in product(ds, repeat=5):
        if tp * dp * pp * cp * ep != world_size:
            continue
        if tp != required_tp:
            continue
        if dp < min_dp:
            continue
        valid.append((tp, dp, pp, cp, ep))
    return valid


class TestQuestion5ConstraintIsUnambiguous(unittest.TestCase):
    def test_exactly_one_configuration_satisfies_both_stated_requirements(self):
        valid = enumerate_valid_configs(WORLD_SIZE, REQUIRED_TP, MIN_DP)
        self.assertEqual(
            valid, [(8, 8, 1, 1, 1)],
            msg=f"expected exactly one valid (tp,dp,pp,cp,ep) tuple, got {valid}",
        )

    def test_stated_answer_key_combination_is_valid(self):
        tp, dp, pp, cp, ep = 8, 8, 1, 1, 1
        self.assertEqual(tp * dp * pp * cp * ep, WORLD_SIZE)
        self.assertEqual(tp, REQUIRED_TP)
        self.assertGreaterEqual(dp, MIN_DP)

    def test_tp1_dp64_is_rejected_once_tp_is_required_to_equal_8(self):
        # This is exactly the counterexample that made the ORIGINAL
        # (tp<=8, dp "large") phrasing ill-posed: tp=1, dp=64 respects
        # tp<=8 and gives a larger DP group than tp=8, dp=8. Requiring
        # tp == 8 (not merely <= 8) is what excludes it.
        tp, dp, pp, cp, ep = 1, 64, 1, 1, 1
        self.assertEqual(tp * dp * pp * cp * ep, WORLD_SIZE)
        self.assertNotEqual(tp, REQUIRED_TP, msg="tp=1 must be rejected by the exact-tp=8 requirement")

    def test_previously_suggested_alternate_tp8_pp2_dp4_is_now_invalid(self):
        # An earlier version of the Answer Key allowed tp=8, pp=2,
        # dp=4 as an alternative valid answer. Under the revised,
        # precise dp>=8 requirement, dp=4 no longer qualifies.
        tp, dp, pp, cp, ep = 8, 4, 2, 1, 1
        self.assertEqual(tp * dp * pp * cp * ep, WORLD_SIZE)
        self.assertLess(dp, MIN_DP, msg="dp=4 must be rejected by the dp>=8 requirement")


if __name__ == "__main__":
    unittest.main()
