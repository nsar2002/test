# V6-M5F0 — RESULT: FAIL_M5F0_TEACHING_SEMANTICS (criterion G)

**Classification.** `FAIL_M5F0_TEACHING_SEMANTICS`. Criteria A–F and H hold. **G (shuffled-teaching control) fails.** Thresholds were not moved.

## Provenance

| Item | Value |
|---|---|
| Protocol | `research/v6_m5f0_dan_teaching_semantics_protocol.md`, SHA256 `771d730c…`, frozen in 6f2de87 before implementation |
| Implementation | e0958b7, `fly_mnq/v6_m5f0_dan_teaching_semantics.py` SHA256 `ca3a573c…` |
| Workflow | 7fa485f |
| Formal record | CI run **36364249451** (workflow_dispatch at a29bca5), bot commit 5acdf5a. `research/results/v6_m5f0_teaching_result.json` SHA256 `9e1d8ec7…` |
| First CI run | 36362161860 (push at 7fa485f). All gate steps succeeded, but the persist push was rejected as non-fast-forward. See the deviation below. |
| Artifact (first run) | 10946513181, zip SHA256 `2ad759d3…`. The container's proxy denies the artifact blob host, so it was not read. |
| Local run | Cloud container, not the user's PC. Result JSON SHA256 `f4e54411…`. |

**Parity.** The digests of s(t) and of the final gains (θ_ref, PLANTED) are **bitwise identical** between local and CI, and the classification and all criteria are identical. The JSONs differ only in ρ floats, by at most 6.7×10⁻¹⁶: last-ULP BLAS reduction noise, as in M5E0.

## Results at θ_ref

| Quantity | Value | Criterion |
|---|---|---|
| PLANTED ρ_os | **0.8218** | F: > 0.0691 — holds |
| SHUFFLED ρ_os | **−0.2561** | G: \|ρ\| ≤ 0.0691 — **fails** |
| AR(0.0) ρ_os | −0.0041 | diagnostic |
| AR(+0.3) ρ_os (momentum) | **−0.2740** (wrong sign) | diagnostic |
| AR(−0.3) ρ_os (reversal) | +0.2745 | diagnostic |
| Steps with s = 0 | 0 | diagnostic |
| Final plastic gains | 3.6% at 0, 0.5% at G_MAX, 44% within 1 ± 0.01 | diagnostic |

## Grid diagnostics (72 points)

- **PLANTED.** Connectome arm median 0.194, with 60 of 72 points above 0.0691. Rewired arm median 0.142, with 55 of 72. The connectome arm is higher than the rewired arm at 63 of 72 points (mean +0.023).
- **AR(0.0).** All 72 points lie within ±0.031, so no false learning appears in an i.i.d. world.
- **AR(±0.3).** 12 points have the correct sign in both regimes; only 4 are above 0.0691 in both.
- **The predicted reversal bias is confirmed.** It comes from M5C's backward potentiation of the code that follows each teaching event, and at θ_ref the learner learns the reversal regime and gets momentum wrong.

## Reading of the G failure

A learner taught with a *permuted* outcome sequence still correlates with the true outcome at |ρ| = 0.26. So the readout's correlation is **not specific to teaching**. In the reduced-scale control below it was +0.41, with the opposite sign.

**Hypothesis, not tested here:**
- ρ is scale-invariant.
- The KC code is dominated by the channel of the first feature, which the M5E0 ranking assigns to the strongest PN type. In PLANTED that feature is the planted predictor.
- Any random gain asymmetry between APP and AV compartments over those KCs then yields a readout aligned with ±u₀, i.e. a large |ρ| of random sign.

## Deliberate mutants (reduced scale; not formal)

Run at T = 400 with the grid reduced to θ_ref (`scratchpad dev_m5f0_mutants.py`).

- **Unmutated control:** already fails G (shuffled ρ +0.41). At this scale G cannot separate mutants.
- **Detected:**
  - *Teaching with the next outcome* flips F (planted ρ −0.79).
  - *An outcome argument added to the readout* is caught by H.
  - *Noise added to s* is caught by C and D.
  - *Gains pushed above G_MAX* are caught by E.
- **Not diagnosed:** three mutants (read-after-teach, valence swap, D(0) ≠ 0) crashed in the harness and were not run further.
- **Limitation of the frozen criterion C.**
  - The outcome-only perturbation catches a one-bar teaching lead only if the perturbed outcome at bar 3,000 changes sign, because teaching is binary. That is a probability of about 1/2.
  - The lead mutant was not caught by C in this run.
  - The formal implementation has no such lead: teaching for bar t uses o(t) at T(t), and s(t) is read at I(t) before it. But C alone would not prove that.

## Process deviation (mine, recorded)

I pushed 2c7dcc8 and a29bca5 while run 36362161860 was still executing. Its persist step therefore could not fast-forward. History was not rewritten. The unchanged workflow was re-dispatched with no pushes during the run.

From M5G0 on, workflows rebase only the bot's result commit onto the branch head before pushing.

## Consequences

- **M5G0 is BLOCKED.** Its frozen rule requires an M5F0 PASS, so θ is not selected.
- **θ_ref remains the only pre-declared θ.**
- **MNQ test design.** Teaching specificity must be tested directly on market data, by the same learner with shuffled teaching as a control arm.
