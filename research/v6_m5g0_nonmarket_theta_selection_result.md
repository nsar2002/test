# V6-M5G0 — RESULT: BLOCKED_M5G0_PREREQUISITE

**Classification.** `BLOCKED_M5G0_PREREQUISITE`. The frozen rule requires the formal M5F0 record to be `PASS_M5F0_TEACHING_SEMANTICS_QUALIFIED`. It is `FAIL_M5F0_TEACHING_SEMANTICS` (criterion G), so no θ is selected.

## Provenance

| Item | Value |
|---|---|
| Protocol | `research/v6_m5g0_nonmarket_theta_selection_protocol.md`, SHA256 `efe42171…`, frozen in 2c7dcc8 before any M5F0 grid result existed |
| Implementation | a29bca5, `fly_mnq/v6_m5g0_theta_selection.py` SHA256 `68f7ede3…` |
| Workflow | 7c53c91 |
| Formal record | CI run 36380046236, bot commit 69f1ce0. `research/results/v6_m5g0_theta_selection_result.json` SHA256 `1e9ba976…` |
| Input | M5F0 record SHA256 `9e1d8ec7…` |
| Local run | Byte-identical (`1e9ba976…`) |

## Negative controls (code path, non-formal data)

The selector's code path was tested on non-formal inputs before the formal run:
- On a 60-bar M5F0 smoke record, relabelled as a PASS, it gives PASS.
- Each of the following gives BLOCKED: M5F0 not a PASS, a missing world, a short world, swapped grid order, and a NaN ρ.
- Every ρ set to exactly 0.0691 gives FAIL.
- A planted two-way tie resolves to the first point in M5C product order.

## Descriptive only (not a selection)

Read from the formal M5F0 grid: only 4 of 72 points exceed 0.0691 in both AR(±0.3) worlds. This is recorded for context only. The frozen rule does not run without an M5F0 PASS.

## Consequence

θ stays at the M5C-declared reference point θ_ref (η₋ = η₊ = 0.05, λ_K = λ_D = 0.5, G_MAX = 2.0). That point was declared before any data.
