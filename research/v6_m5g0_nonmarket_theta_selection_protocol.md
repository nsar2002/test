# V6-M5G0 — NON-MARKET θ SELECTION FROM THE FROZEN M5F0 SYNTHETIC DIAGNOSTICS

**STATUS: FROZEN WHILE THE M5F0 FORMAL RUNS WERE IN PROGRESS, BEFORE ANY M5F0 GRID DIAGNOSTIC EXISTED.** The only M5F0 numbers seen are from a 60-bar smoke run. Those are statistically meaningless (n = 30) and cover only θ_ref, not the grid.

## Purpose

The learner has five parameters, θ = (η₋, η₊, λ_K, λ_D, G_MAX). None has been selected; M5C, M5D0 and M5F0 were each qualified over all 72 grid points. The project memory requires θ to be identified **without market data** before MNQ opens.

This gate fixes one θ* by a deterministic rule applied to the frozen M5F0 synthetic diagnostics. No new simulation is run and no market datum is used.

## Why a maximin over synthetic worlds

M5F0 established that the frozen M5C rule potentiates the code that follows each teaching event. In markets that code can carry the just-realized outcome, which creates a built-in bias, most likely toward reversal. In M5F0's AR(φ) worlds a biased learner learns the correct sign in one regime (reversal, φ < 0) and the wrong sign in the other (momentum, φ > 0).

A θ that learns the correct sign in **both** regimes, and also learns a planted contemporaneous rule in both encoder arms, is the least biased and most generally able learner available. The rewired arm is included so that θ is not tuned to favour the connectome arm in the later connectome-versus-rewired comparison.

## Frozen rule

**Input.** `research/results/v6_m5f0_teaching_result.json`, the formal CI record. Its classification must be `PASS_M5F0_TEACHING_SEMANTICS_QUALIFIED`. Its SHA256 is recorded by this gate.

For each of the 72 grid points θ, the rule reads four out-of-sample correlations from `diagnostics.grid`:
- `PLANTED:connectome`
- `PLANTED:rewired`
- `AR(+0.3):connectome`
- `AR(-0.3):connectome`

It then computes the **worst case** `m(θ) = min of the four ρ_os`.

**Selection.**
- **θ\*** is the grid point with the largest m(θ).
- **Ties:** if several points reach the maximum exactly, the first in M5C `GRID` product order is chosen. That order is η₋, η₊, λ_K, λ_D, G_MAX, each in listed order.
- `AR(+0.0)` is **not** used. In an i.i.d. world ρ_os ≈ 0 for any learner, so it carries no selection information.

## Frozen classification

- **`PASS_M5G0_THETA_SELECTED`**: M5F0 is a PASS and m(θ\*) > **0.0691**. Every one of the four worlds then learns the correct sign at the M5F0 one-sided p < 0.001 bound.
- **`FAIL_M5G0_NO_THETA_LEARNS_ALL_WORLDS`**: M5F0 is a PASS and m(θ\*) ≤ 0.0691. No grid point learns both regimes and both arms. θ\* is still reported but is **not** authorized for MNQ.
- **`BLOCKED_M5G0_PREREQUISITE`**: M5F0 is not a PASS, or its result is missing or malformed.

## Diagnostics (never criteria)

- the sorted list of the 10 best points by m(θ), with their four ρ_os;
- the marginal effect of each parameter: mean m(θ) per level;
- the fraction of grid points with ρ_os(AR(+0.3)) < 0, i.e. the wrong sign in the momentum world.

## Consequence

On PASS, θ\* becomes the frozen learner parameter for the MNQ walk-forward protocol, in both arms. On FAIL, no θ is authorized, and the MNQ protocol must either pre-register an in-training selection rule or record the learner as unable to learn both regimes.

## Firewalls

- No market, reward or PnL data is used.
- Only synthetic M5F0 outputs are read.
- MNQ stays CLOSED.
