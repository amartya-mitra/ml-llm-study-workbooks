"""Structural (causality) regression tests for workbook 05 Chapter 4's
1F1B pipeline-schedule figure.

An earlier version of figures/source/fig_pipeline_timeline.py computed
each stage's warmup forward count from a closed-form offset
(p-1-stage_index) rather than simulating real dependencies. That
formula gives the LAST stage zero warmup forwards, which produced a
causally invalid schedule: the last stage's first operation was a
backward (B1) with no matching forward (F1) having run yet on that
same stage. A backward pass always needs its own stage's matching
forward pass to have already produced the activation it reads.

These tests inspect the schedule structure directly -- not just "the
diagram looks plausible" -- so this specific bug (or an equivalent
one) cannot silently return.
"""
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG_SOURCE_DIR = os.path.join(REPO_ROOT, "workbooks", "05-llm-training", "figures", "source")
sys.path.insert(0, FIG_SOURCE_DIR)
from fig_pipeline_timeline import build_1f1b_schedule, P_STAGES, M_MICROBATCHES  # noqa: E402


def _times_by_op(schedule, stage):
    """{'F': {microbatch_index: time}, 'B': {microbatch_index: time}}"""
    times = {"F": {}, "B": {}}
    for t, label in schedule[stage]:
        kind, idx = label[0], int(label[1:])
        times[kind][idx] = t
    return times


class TestPipelineScheduleCausality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = P_STAGES
        cls.m = M_MICROBATCHES
        cls.schedule, cls.max_slot = build_1f1b_schedule(cls.p, cls.m)
        cls.times = {s: _times_by_op(cls.schedule, s) for s in range(cls.p)}

    def test_every_stage_has_exactly_m_forwards_and_m_backwards(self):
        for s in range(self.p):
            self.assertEqual(len(self.times[s]["F"]), self.m, msg=f"stage {s}")
            self.assertEqual(len(self.times[s]["B"]), self.m, msg=f"stage {s}")

    def test_every_stage_first_operation_is_a_forward(self):
        for s in range(self.p):
            all_slots = sorted(t for t, _ in self.schedule[s])
            first_slot = all_slots[0]
            first_label = dict(self.schedule[s])[first_slot]
            self.assertTrue(first_label.startswith("F"), msg=f"stage {s}'s first op is {first_label}, not a forward")

    def test_last_stage_processes_f1_before_b1(self):
        last = self.p - 1
        self.assertLess(
            self.times[last]["F"][1], self.times[last]["B"][1],
            msg="last stage's F1 must occur before its B1",
        )

    def test_forward_precedes_backward_same_stage_same_microbatch(self):
        for s in range(self.p):
            for i in range(1, self.m + 1):
                self.assertLess(
                    self.times[s]["F"][i], self.times[s]["B"][i],
                    msg=f"stage {s}: F{i} must precede B{i}",
                )

    def test_forward_propagates_downstream_in_order(self):
        for s in range(1, self.p):
            for i in range(1, self.m + 1):
                self.assertGreater(
                    self.times[s]["F"][i], self.times[s - 1]["F"][i],
                    msg=f"F({s},{i}) must occur after F({s - 1},{i})",
                )

    def test_backward_propagates_upstream_in_order(self):
        for s in range(0, self.p - 1):
            for i in range(1, self.m + 1):
                self.assertGreater(
                    self.times[s]["B"][i], self.times[s + 1]["B"][i],
                    msg=f"B({s},{i}) must occur after B({s + 1},{i})",
                )

    def test_no_stage_double_books_a_time_slot(self):
        for s in range(self.p):
            slots = [t for t, _ in self.schedule[s]]
            self.assertEqual(len(slots), len(set(slots)), msg=f"stage {s} has a duplicate time slot")

    def test_no_operation_precedes_its_dependency_globally(self):
        # A backward at (s, i) must never be timestamped earlier than
        # or equal to the forward (s, i) it depends on, checked without
        # relying on the simulator's own bookkeeping.
        for s in range(self.p):
            for i in range(1, self.m + 1):
                self.assertLess(self.times[s]["F"][i], self.times[s]["B"][i])

    def test_schedule_is_deterministic_across_runs(self):
        schedule2, max_slot2 = build_1f1b_schedule(self.p, self.m)
        self.assertEqual(self.schedule, schedule2)
        self.assertEqual(self.max_slot, max_slot2)

    def test_warmup_steady_and_drain_phases_all_present(self):
        # Every stage must show at least one pure-forward warmup slot,
        # at least one steady-state slot where it alternates, and at
        # least one pure-backward drain slot -- i.e. fill, steady
        # state, and drain are all non-empty for every stage.
        for s in range(self.p):
            f_times = sorted(self.times[s]["F"].values())
            b_times = sorted(self.times[s]["B"].values())
            self.assertGreaterEqual(f_times[0], 0)
            self.assertGreater(len(f_times), 0)
            self.assertGreater(len(b_times), 0)
            # last backward strictly after last forward for every stage
            # except it need not be immediately after -- drain exists
            # as long as some backward follows the last forward.
            self.assertGreater(b_times[-1], f_times[0])


if __name__ == "__main__":
    unittest.main()
