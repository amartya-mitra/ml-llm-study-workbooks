#!/usr/bin/env python3
"""Chapter 6 worked example: reading a synthetic pretraining-run log.

EVERY number this script reads in is EITHER a SYNTHETIC/ILLUSTRATIVE
LOG VALUE (the SYNTHETIC_* constants and the per-step TRAIN_LOSS_OVERRIDES
/ GRAD_NORM_OVERRIDES / STEP_TIME_OVERRIDES dicts below) or a quantity
DERIVED from those by this script. This worked example is NOT a real
disclosed training run from any model -- it is a deliberately
constructed, clearly-labeled synthetic log, built to have exactly two
visible behavior changes so the chapter can walk through diagnosing
each one. The chapter prose repeats this "synthetic, not real" framing
explicitly wherever the numbers below are quoted, per this project's
sourcing discipline (AGENTS.md).

This script is the source of truth for every number quoted in
chapters/06-reading-real-pretraining-runs.qmd's worked example, and for
figures/source/fig_run_diagnosis_pipeline.py, which reads this script's
own JSON output rather than re-deriving or duplicating any number.

Two kinds of quantity appear below, labeled by key prefix / JSON section:
    - "observed_*" or fields inside "per_step_log": values the synthetic
      log itself reports -- step, train_loss, grad_norm, learning_rate,
      step_time_seconds (every step), and eval_loss (checkpoint steps
      only). These are exactly what a real training dashboard would log;
      nothing about them is computed.
    - "derived" quantities (everything in "derived_metrics" and
      "diagnosis"): computed BY THIS SCRIPT from the observed log using
      formulas declared in each function's docstring. A derived quantity
      is never itself logged -- it is always recomputed from logged
      fields, exactly as a learner reading a real run's dashboard would
      have to do.

Sourced formula reused from elsewhere in this workbook (not re-derived
here, per this chapter's own boundary note):
    - Training FLOPs per step is estimated as 6 * N * tokens, the same
      C ~= 6ND approximation Chapter 3 establishes and cites to
      [@src-50] (Kaplan et al.) and [@src-51] (Hoffmann et al.,
      Chinchilla). N (TOY_PARAM_COUNT below) is a declared toy parameter
      count, not a real model's size.
    - "Nominal peak FLOPs" and "achieved vs. nominal" are the same
      distinction Chapter 5 introduces (citing [@src-10]'s own measured
      caution that "H100s and B200s can usually only achieve around
      80-85% of the claimed peak FLOPs"); TOY_DECLARED_NOMINAL_PEAK_FLOPS_PER_DEVICE
      below is a deliberately round, declared assumption for this toy
      cluster -- it does not name or claim to match any specific real
      accelerator's datasheet figure.

Run: python3 workbooks/05-llm-training/data/worked-examples/pretraining_run_telemetry.py
Output: pretraining_run_telemetry.json (beside this script)
"""
import json
import os


class InvalidRunConfig(ValueError):
    pass


# ---------------------------------------------------------------------
# SYNTHETIC / ILLUSTRATIVE LOG -- not a real disclosed training run.
# ---------------------------------------------------------------------
NUM_STEPS = 30
SYNTHETIC_GLOBAL_BATCH_SIZE_SEQUENCES = 256
SYNTHETIC_SEQ_LEN_TOKENS = 4096
SYNTHETIC_DEVICE_COUNT = 32
SYNTHETIC_GRADIENT_ACCUMULATION_STEPS = 1  # declared explicitly: 1 optimizer
# step == 1 logged step == one forward/backward over the full global batch;
# no micro-step/optimizer-step ambiguity in this log (Chapter 4 already
# covers what changes when gradient accumulation or pipeline microbatches
# make "a step" ambiguous -- not re-derived here).
CHECKPOINT_STEPS = (10, 20, 30)

# Toy, declared, illustrative -- NOT a real model's parameter count or any
# vendor's accelerator spec.
TOY_PARAM_COUNT = 2_000_000_000
TOY_DECLARED_NOMINAL_PEAK_FLOPS_PER_DEVICE = 400e12  # 400 TFLOP/s, a round
# illustrative number for this toy cluster, not attributed to any named
# real accelerator.

BASELINE_STEP_TIME_SECONDS = 1.800
PEAK_LR = 3.0e-4
MIN_LR = 1.0e-4

# Event A: a loss + grad-norm spike at step 18. Step time stays at
# baseline during this event -- it is NOT a throughput event.
LOSS_SPIKE_STEP = 18
LOSS_SPIKE_VALUE = 4.350
GRAD_NORM_SPIKE_VALUE = 3.950

# Event B: a SUSTAINED global throughput drop across steps 24-27. Loss
# and grad-norm stay at their (unspiked) baseline trend throughout --
# it is NOT an optimization event.
THROUGHPUT_DROP_STEPS = (24, 25, 26, 27)
THROUGHPUT_DROP_STEP_TIME_SECONDS = 2.880

EVAL_GENERALIZATION_GAP = 0.15  # declared, illustrative constant offset

ANOMALY_RELATIVE_THRESHOLD = 0.20  # 20% relative deviation from trailing history
TRAILING_WINDOW_SIZE = 4  # previous steps only, current step excluded


def validate_run_config():
    if SYNTHETIC_GLOBAL_BATCH_SIZE_SEQUENCES <= 0 or SYNTHETIC_SEQ_LEN_TOKENS <= 0:
        raise InvalidRunConfig("global batch size and sequence length must be positive")
    if SYNTHETIC_DEVICE_COUNT <= 0:
        raise InvalidRunConfig("device_count must be positive")
    if SYNTHETIC_GRADIENT_ACCUMULATION_STEPS <= 0:
        raise InvalidRunConfig("gradient_accumulation_steps must be positive")
    if not (0.0 < ANOMALY_RELATIVE_THRESHOLD < 1.0):
        raise InvalidRunConfig("anomaly relative threshold must be in (0, 1)")
    if TRAILING_WINDOW_SIZE <= 0:
        raise InvalidRunConfig("trailing window size must be positive")
    for s in CHECKPOINT_STEPS:
        if not (1 <= s <= NUM_STEPS):
            raise InvalidRunConfig(f"checkpoint step {s} is outside the logged run [1, {NUM_STEPS}]")


def baseline_loss(step):
    """A smoothly decreasing illustrative training-loss curve -- not a
    claim about any real model's loss trajectory."""
    return 3.60 - 0.022 * step


def baseline_grad_norm(step):
    return 1.20 - 0.010 * step


def learning_rate(step):
    """Linear decay from PEAK_LR to MIN_LR over the logged run -- a
    deliberately simple, smooth schedule with NO anomaly at either
    event, so the log itself rules out "a scheduled LR change" as the
    cause of either event."""
    if NUM_STEPS <= 1:
        raise InvalidRunConfig("learning rate schedule requires NUM_STEPS > 1")
    return PEAK_LR - (PEAK_LR - MIN_LR) * (step - 1) / (NUM_STEPS - 1)


def observed_step_time_seconds(step):
    if step in THROUGHPUT_DROP_STEPS:
        return THROUGHPUT_DROP_STEP_TIME_SECONDS
    return BASELINE_STEP_TIME_SECONDS


def observed_train_loss(step):
    if step == LOSS_SPIKE_STEP:
        return LOSS_SPIKE_VALUE
    return baseline_loss(step)


def observed_grad_norm(step):
    if step == LOSS_SPIKE_STEP:
        return GRAD_NORM_SPIKE_VALUE
    return baseline_grad_norm(step)


def tokens_per_step():
    """Declared log-convention relation: tokens per optimizer step =
    global_batch_size (sequences) x seq_len (tokens/sequence) x
    gradient_accumulation_steps. gradient_accumulation_steps=1 here, so
    it is omitted from the product but stated explicitly for the
    general relation."""
    return (
        SYNTHETIC_GLOBAL_BATCH_SIZE_SEQUENCES
        * SYNTHETIC_SEQ_LEN_TOKENS
        * SYNTHETIC_GRADIENT_ACCUMULATION_STEPS
    )


def consumed_tokens(step, tps):
    """tokens consumed through and including `step` = step * tokens_per_step.
    This is the tokens = steps x global_batch_size x seq_len relation
    this chapter declares precisely."""
    return step * tps


def consumed_sequences(step):
    return step * SYNTHETIC_GLOBAL_BATCH_SIZE_SEQUENCES


def global_throughput_tokens_per_s(tps, step_time_s):
    if step_time_s <= 0:
        raise InvalidRunConfig("step_time_seconds must be positive")
    return tps / step_time_s


def per_device_throughput_tokens_per_s(global_tp, device_count):
    if device_count <= 0:
        raise InvalidRunConfig("device_count must be positive")
    return global_tp / device_count


def estimated_training_flops_per_step(param_count, tps):
    """C ~= 6*N*D per step, D = tokens_per_step -- Chapter 3's own
    scaling-law FLOPs approximation [@src-50;@src-51], reused here, not
    re-derived."""
    return 6 * param_count * tps


def achieved_flops_per_second(flops_per_step, step_time_s):
    if step_time_s <= 0:
        raise InvalidRunConfig("step_time_seconds must be positive")
    return flops_per_step / step_time_s


def nominal_peak_flops_per_second_cluster(device_count, peak_per_device):
    return device_count * peak_per_device


def achieved_fraction_of_nominal(achieved, nominal):
    if nominal <= 0:
        raise InvalidRunConfig("nominal_peak_flops_per_second_cluster must be positive")
    return achieved / nominal


def trailing_window_average(values_by_step, step, window=TRAILING_WINDOW_SIZE):
    """Mean of the metric over the up-to-`window` steps STRICTLY BEFORE
    `step` (never including the current step). Returns None if no prior
    steps exist (step 1). This is deliberately "history-only": it
    represents both (a) the baseline an anomaly check compares the
    current reading against, and (b) what a rolling-average dashboard
    metric computed just before this step would have shown."""
    prior_steps = [s for s in range(max(1, step - window), step) if s in values_by_step]
    if not prior_steps:
        return None
    return sum(values_by_step[s] for s in prior_steps) / len(prior_steps)


def relative_deviation(current, trailing_avg):
    if trailing_avg is None:
        return None
    if trailing_avg == 0:
        raise InvalidRunConfig("trailing average is zero; relative deviation undefined")
    return (current - trailing_avg) / trailing_avg


def main():
    validate_run_config()

    tps = tokens_per_step()
    flops_per_step = estimated_training_flops_per_step(TOY_PARAM_COUNT, tps)
    nominal_cluster_flops = nominal_peak_flops_per_second_cluster(
        SYNTHETIC_DEVICE_COUNT, TOY_DECLARED_NOMINAL_PEAK_FLOPS_PER_DEVICE,
    )

    loss_by_step = {}
    step_time_by_step = {}
    per_step_log = []
    for step in range(1, NUM_STEPS + 1):
        loss = observed_train_loss(step)
        grad_norm = observed_grad_norm(step)
        lr = learning_rate(step)
        step_time_s = observed_step_time_seconds(step)
        loss_by_step[step] = loss
        step_time_by_step[step] = step_time_s

        global_tp = global_throughput_tokens_per_s(tps, step_time_s)
        per_device_tp = per_device_throughput_tokens_per_s(global_tp, SYNTHETIC_DEVICE_COUNT)
        achieved_flops = achieved_flops_per_second(flops_per_step, step_time_s)
        achieved_fraction = achieved_fraction_of_nominal(achieved_flops, nominal_cluster_flops)

        trailing_loss_avg = trailing_window_average(loss_by_step, step)
        trailing_step_time_avg = trailing_window_average(step_time_by_step, step)
        loss_rel_dev = relative_deviation(loss, trailing_loss_avg)
        step_time_rel_dev = relative_deviation(step_time_s, trailing_step_time_avg)

        loss_anomaly = (loss_rel_dev is not None) and (abs(loss_rel_dev) > ANOMALY_RELATIVE_THRESHOLD)
        # Throughput anomaly is one-directional: only flag SLOWER than
        # trailing history (a step being faster is not a problem to flag).
        throughput_anomaly = (step_time_rel_dev is not None) and (step_time_rel_dev > ANOMALY_RELATIVE_THRESHOLD)

        entry = {
            "step": step,
            "observed": {
                "train_loss": loss,
                "grad_norm": grad_norm,
                "learning_rate": lr,
                "step_time_seconds": step_time_s,
                "eval_loss": (baseline_loss(step) + EVAL_GENERALIZATION_GAP) if step in CHECKPOINT_STEPS else None,
            },
            "derived": {
                "consumed_tokens": consumed_tokens(step, tps),
                "consumed_sequences": consumed_sequences(step),
                "global_throughput_tokens_per_s": global_tp,
                "per_device_throughput_tokens_per_s": per_device_tp,
                "achieved_flops_per_second": achieved_flops,
                "achieved_fraction_of_nominal": achieved_fraction,
                "trailing_window_avg_loss": trailing_loss_avg,
                "trailing_window_avg_step_time_seconds": trailing_step_time_avg,
                "loss_relative_deviation": loss_rel_dev,
                "step_time_relative_deviation": step_time_rel_dev,
                "loss_anomaly_flagged": loss_anomaly,
                "throughput_anomaly_flagged": throughput_anomaly,
            },
        }
        per_step_log.append(entry)

    detected_loss_anomaly_steps = [e["step"] for e in per_step_log if e["derived"]["loss_anomaly_flagged"]]
    detected_throughput_anomaly_steps = [e["step"] for e in per_step_log if e["derived"]["throughput_anomaly_flagged"]]

    by_step = {e["step"]: e for e in per_step_log}

    # ---- invalid-configuration checks (must raise) ----
    checks = {}
    try:
        trailing_window_average({1: 1.0}, 1)
        checks["trailing_average_at_step_one_is_none"] = trailing_window_average({1: 1.0}, 1) is None
    except InvalidRunConfig:
        checks["trailing_average_at_step_one_is_none"] = False

    try:
        global_throughput_tokens_per_s(100, 0)
        checks["invalid_zero_step_time_raised"] = False
    except InvalidRunConfig:
        checks["invalid_zero_step_time_raised"] = True

    try:
        per_device_throughput_tokens_per_s(100.0, 0)
        checks["invalid_zero_device_count_raised"] = False
    except InvalidRunConfig:
        checks["invalid_zero_device_count_raised"] = True

    try:
        achieved_fraction_of_nominal(1.0, 0)
        checks["invalid_zero_nominal_flops_raised"] = False
    except InvalidRunConfig:
        checks["invalid_zero_nominal_flops_raised"] = True

    try:
        relative_deviation(1.0, 0)
        checks["invalid_zero_trailing_average_raised"] = False
    except InvalidRunConfig:
        checks["invalid_zero_trailing_average_raised"] = True

    checks["detected_loss_anomaly_matches_declared_event"] = (detected_loss_anomaly_steps == [LOSS_SPIKE_STEP])
    checks["step27_not_flagged_despite_being_above_baseline"] = (
        27 in THROUGHPUT_DROP_STEPS and 27 not in detected_throughput_anomaly_steps
    )
    checks["achieved_fraction_never_exceeds_one"] = all(
        0.0 < e["derived"]["achieved_fraction_of_nominal"] < 1.0 for e in per_step_log
    )
    checks["achieved_fraction_drops_during_throughput_event"] = (
        by_step[25]["derived"]["achieved_fraction_of_nominal"] < by_step[20]["derived"]["achieved_fraction_of_nominal"]
    )

    # Within-run comparability controls: this chapter's own worked
    # example compares each step to its own recent trailing history, not
    # to a different run -- so the controls that matter are that the
    # configuration driving tokens_per_step and device_count did not
    # itself change inside the trailing window. All True here because
    # nothing about the declared configuration changes mid-run; see the
    # chapter prose for what it would mean if one of these were False.
    comparability_controls = {
        "device_count_unchanged_in_window": True,
        "global_batch_size_unchanged_in_window": True,
        "seq_len_unchanged_in_window": True,
        "gradient_accumulation_unchanged_in_window": True,
    }

    diagnoses = {
        "loss_spike_event": {
            "step": LOSS_SPIKE_STEP,
            "observed_signals": ["train_loss spike", "grad_norm spike", "step_time_seconds stays at baseline"],
            "competing_diagnoses": [
                {
                    "name": "optimization_instability",
                    "description": (
                        "A transient optimizer/gradient-dynamics issue (e.g. the current "
                        "learning rate interacting badly with a locally sharp region of the "
                        "loss landscape) produces a broad-based gradient-norm spike across "
                        "most parameter groups, with loss rising as a direct consequence."
                    ),
                },
                {
                    "name": "data_quality_problem",
                    "description": (
                        "An anomalous or corrupted batch/shard entering training at this step "
                        "(e.g. duplicated, truncated, or mixed-up tokens) produces an "
                        "unusually hard or malformed training example, raising loss and "
                        "producing a large gradient largely concentrated in a small subset of "
                        "parameter groups, unrelated to the optimizer's own dynamics."
                    ),
                },
            ],
            "distinguishing_measurement_not_logged": "per-parameter-group (or per-layer) gradient-norm breakdown",
        },
        "throughput_drop_event": {
            "steps": list(THROUGHPUT_DROP_STEPS),
            "observed_signals": ["step_time_seconds elevated", "train_loss and grad_norm stay at baseline trend"],
            "competing_diagnoses": [
                {
                    "name": "communication_bottleneck",
                    "description": (
                        "A collective-communication regression (e.g. increased all-reduce or "
                        "all-gather time) slows every device roughly equally, so the whole "
                        "step's wall-clock time rises uniformly across the cluster."
                    ),
                },
                {
                    "name": "straggler_device",
                    "description": (
                        "One slow device (e.g. thermal throttling, a flaky network interface) "
                        "paces the entire synchronous step, since a collective operation waits "
                        "for its slowest participant -- every other device sits idle, not "
                        "uniformly slow."
                    ),
                },
            ],
            "distinguishing_measurement_not_logged": "per-device (per-rank) step-time or utilization breakdown",
        },
    }

    result = {
        "synthetic_run_config": {
            "num_steps": NUM_STEPS,
            "global_batch_size_sequences": SYNTHETIC_GLOBAL_BATCH_SIZE_SEQUENCES,
            "seq_len_tokens": SYNTHETIC_SEQ_LEN_TOKENS,
            "device_count": SYNTHETIC_DEVICE_COUNT,
            "gradient_accumulation_steps": SYNTHETIC_GRADIENT_ACCUMULATION_STEPS,
            "checkpoint_steps": list(CHECKPOINT_STEPS),
            "toy_param_count": TOY_PARAM_COUNT,
            "toy_declared_nominal_peak_flops_per_device": TOY_DECLARED_NOMINAL_PEAK_FLOPS_PER_DEVICE,
            "anomaly_relative_threshold": ANOMALY_RELATIVE_THRESHOLD,
            "trailing_window_size": TRAILING_WINDOW_SIZE,
        },
        "tokens_per_step": tps,
        "estimated_training_flops_per_step": flops_per_step,
        "nominal_peak_flops_per_second_cluster": nominal_cluster_flops,
        "per_step_log": per_step_log,
        "detected_loss_anomaly_steps": detected_loss_anomaly_steps,
        "detected_throughput_anomaly_steps": detected_throughput_anomaly_steps,
        "comparability_controls": comparability_controls,
        "diagnoses": diagnoses,
        "invalid_configuration_checks": checks,
    }

    out_path = os.path.join(os.path.dirname(__file__), "pretraining_run_telemetry.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
