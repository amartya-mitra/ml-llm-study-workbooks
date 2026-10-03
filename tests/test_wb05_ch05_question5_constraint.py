"""Regression test for workbook 05 Chapter 5's Question 5 (synthesis/
design question in chapters/05-training-memory-and-communication.qmd
and its Answer Key entry).

An earlier version of this question asked for the minimum DP degree
under a 10 GiB-per-device memory budget, computing per-device
model-state memory as 16N/DP alone -- ignoring that even tensor-
parallel (TP) partitioning ALSO shards model-state memory. Once that
is accounted for, per-device memory is 16N/(DP x TP); since DP x TP is
fixed by the (here, 24-device) world size, this quantity is INVARIANT
across every valid factorization (3x8, 4x6, 6x4, 8x3, 12x2, 24x1, ...),
so a memory budget alone cannot select a unique (DP, TP) split. The
old question's "DP=3, TP=8" conclusion does not survive this
correction and is no longer the chapter's answer.

This test verifies the NEW question's premise: per-device model-state
memory under combined ZeRO-3 DP sharding and even TP partitioning is
invariant across every factorization of DP x TP = WORLD_SIZE, and that
every such factorization satisfies the stated 10 GiB budget by the
same margin -- i.e. the budget genuinely cannot distinguish between
them, which is why the chapter now asks for an ADDITIONAL constraint
instead of a unique numeric split.
"""
import unittest

N = 2_000_000_000
BYTES_PER_GIB = 2 ** 30
MODEL_STATE_TOTAL_BYTES = 16 * N
MEMORY_BUDGET_GIB = 10.0
WORLD_SIZE = 24


def divisor_pairs(n):
    """All (dp, tp) pairs with dp * tp == n and both >= 1."""
    return [(d, n // d) for d in range(1, n + 1) if n % d == 0]


def per_device_model_state_gib(dp, tp):
    return (MODEL_STATE_TOTAL_BYTES / (dp * tp)) / BYTES_PER_GIB


def fits_budget(dp, tp):
    return per_device_model_state_gib(dp, tp) <= MEMORY_BUDGET_GIB


class TestQuestion5MemoryBudgetAloneCannotSelectASplit(unittest.TestCase):
    def test_every_factorization_of_world_size_gives_identical_per_device_memory(self):
        pairs = divisor_pairs(WORLD_SIZE)
        values = {round(per_device_model_state_gib(dp, tp), 9) for dp, tp in pairs}
        self.assertEqual(
            len(values), 1,
            msg=f"expected one invariant value across all factorizations, got {values}",
        )

    def test_invariant_value_equals_16n_over_world_size(self):
        expected = (MODEL_STATE_TOTAL_BYTES / WORLD_SIZE) / BYTES_PER_GIB
        for dp, tp in divisor_pairs(WORLD_SIZE):
            self.assertAlmostEqual(per_device_model_state_gib(dp, tp), expected, places=9)

    def test_every_factorization_satisfies_the_stated_budget(self):
        for dp, tp in divisor_pairs(WORLD_SIZE):
            self.assertTrue(
                fits_budget(dp, tp),
                msg=f"(dp={dp}, tp={tp}) unexpectedly violates the {MEMORY_BUDGET_GIB} GiB budget",
            )

    def test_named_example_splits_are_all_equally_valid(self):
        # The specific splits the chapter prose and answer key name.
        named = [(3, 8), (4, 6), (6, 4), (8, 3), (12, 2), (24, 1)]
        values = {round(per_device_model_state_gib(dp, tp), 9) for dp, tp in named}
        self.assertEqual(len(values), 1)
        for dp, tp in named:
            self.assertEqual(dp * tp, WORLD_SIZE)
            self.assertTrue(fits_budget(dp, tp))

    def test_old_dp_only_framing_is_not_what_the_budget_implies(self):
        # The OLD (incorrect) framing used 16N/DP alone, ignoring TP's
        # own sharding contribution. That formula is NOT invariant
        # across factorizations with the same DP*TP -- demonstrating
        # why it gave a spuriously unique answer. We confirm the old
        # per-DP-only formula actually DOES vary with DP, which is
        # precisely the flaw: it was answering a different, simpler
        # question (no TP sharding at all) than the one actually posed
        # (TP participates in sharding too).
        old_formula_values = {
            round((MODEL_STATE_TOTAL_BYTES / dp) / BYTES_PER_GIB, 6)
            for dp, _tp in divisor_pairs(WORLD_SIZE)
        }
        self.assertGreater(
            len(old_formula_values), 1,
            msg="the old DP-only formula should vary across DP values -- that variation is exactly why it (wrongly) looked like it could select a unique split",
        )


if __name__ == "__main__":
    unittest.main()
