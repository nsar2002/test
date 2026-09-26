# V6-M5D0 — MBON POPULATION READOUT AND LEARNER-LEVEL SYNTHETIC CONDITIONING — NO-MARKET QUALIFICATION

**STATUS: FROZEN BEFORE M5D0 IMPLEMENTATION AND BEFORE ANY M5D0 OUTPUT.**

## Freeze record

This protocol is committed alone, before any M5D0 code, on branch `claude/hello-8eabhu` of `nsar2002/test`. As with M5C, there is no canonical private `nsar2002/test15` commit, and the public protocol-only commit is the freeze of record. Changes after M5D0 code exists require a separate, dated amendment file.

## Authorization

V6-M5C result `PASS_M5C_DOPAMINE_GATED_KC_MBON_CHRONOLOGY_QUALIFIED` (run 36249100776; result JSON SHA256 `77b9c79a70bfc589b43a53c61df253aa908dd9052a3e5a1032a3f1df7d455d5c`) authorizes a later M5D protocol to freeze, still without market data, "MBON population readout under the read-before-write rule". M5D0 freezes that readout. It then qualifies the complete no-market learner on synthetic conditioning paradigms:

M4B0 sparsifier → M5C plasticity → MBON readout

M5D0 assigns no valence, no action mapping and no parameter value.

## What this gate can and cannot show

The conditioning outcomes tested below follow analytically from the frozen M5C rule plus the readout definition. M5D0 is therefore an **integration and implementation qualification**: it verifies that the full pipeline reproduces these predictions exactly on the real MaleCNS structure. It is not an independent biological validation.

The qualitative paradigms mirror canonical experiments:
- forward pairing depresses the paired-odor response (Hige et al. 2015, *Neuron* 88:985–998);
- backward pairing potentiates it, and associations can be rewritten by reversing pairing order (Handler et al. 2019, *Cell* 178:60–75).

## Frozen prerequisites

Everything frozen by M5C is inherited unchanged: pinned sources, M5B3B re-execution parity, the eligible-edge content digest, and the structure counts.

Additional frozen files (SHA256):
- `research/v6_m5c_dopamine_gated_plasticity_chronology_protocol.md` `4590ab29cfba6fe9a559003286c94146cb96082bbe2f6c6d864437c5ce26eee6`
- `fly_mnq/v6_m5c_dopamine_gated_plasticity_chronology.py` `57ba0542338588f1d0b27a24a9e91affd12209b32d8328726dd8b85503ad96a4`
- `research/results/v6_m5c_plasticity_chronology_result.json` `77b9c79a70bfc589b43a53c61df253aa908dd9052a3e5a1032a3f1df7d455d5c`, whose classification must be the M5C PASS.

The M5C chronology (`run_chronology`) and structure builder are imported unchanged from the pinned M5C file. The M4B0 `sparsify` function is imported unchanged from its pinned file.

MBON structure that must be reproduced from M5B3B: 97 MBON bodies, of which 55 are single-compartment, 40 multi-compartment and 2 outside the fast lobe map. Every eligible compartment has at least one single-compartment MBON.

Any mismatch → `BLOCKED_M5D0_PREREQUISITE_PARITY`.

## Frozen readout definition

For MBON body m, let E_m be its exact KC→MBON aggregate edges (all 61,210 edges, plastic and nonplastic, grouped by postsynaptic body). Let `w_e` be the raw aggregate synapse count as float64, and `g_e` the M5C gain.
- Raw drive: `r_m(g, z) = Σ_{e∈E_m} w_e · g_e · z_{k(e)}`
- Normalized drive: `ρ_m(g, z) = r_m(g, z) / W_m`, with `W_m = Σ_{e∈E_m} w_e`
- The population readout is the vector ρ over all 97 MBON bodies, keyed by bodyId.
- Read-before-write: within a stream, the readout at step t is `ρ(g(t−1), z(t))`, computed before the step-t plasticity update.
- There is no valence, sign, threshold, nonlinearity, MBON dynamics, MBON→MBON or MBON→DAN feedback, and no action mapping.

## Frozen synthetic paradigms

- RNG: NumPy PCG64, seed `20260927`.
- For each eligible compartment c, in the order B'1, B'2, B1, a'1, a'2, a'3, a1, a2, a3, y2, y4, y5, draw a (2 × 4064) standard-normal score block and apply the frozen M4B0 `sparsify`. This gives the odor patterns A_c and B_c.
- The dopamine event for c fires every DAN body in the frozen gate population G_c and no other DAN. Trial spacing is L = 32 steps; each block has N = 8 trials.
- **FWD**: A_c and dopamine together at steps 32j, for j = 0…7. T = 256.
- **BWD**: dopamine at 32j and A_c at 32j+1, for j = 0…7. T = 256.
- **REV**: the FWD block (steps 32j, j<8), then a BWD block (dopamine at 256+32j, A_c at 256+32j+1, j<8). T = 512. The gain state after step 255 is retained.
- B_c is never presented during training. It is only read out at test.
- Test responses are pure functions of a gain state: `R_m(X) = r_m(g, z_X) / r_m(1, z_X)` for X ∈ {A_c, B_c}, where `r_m(1, z_X) > 0`.

Why L = 32 is enough: under the M5C chronology, carry-over between trials is at most `0.5 · 0.9^31 / (1 − 0.9^32) ≈ 0.0198` per trial anywhere in the grid. The minimum per-trial drive is 0.05, so each FWD trial strictly depresses and each BWD trial strictly potentiates the A_c edges at every grid point until a bound is reached.

Tested MBONs T_A(c): single-compartment MBONs of c with `r_m(1, z_A) > 0`.

Shared-DAN set: `C(c) = {c' : G_c' ∩ G_c ≠ ∅}`, from the frozen M5B3B gate populations.

## Parameters

The same 72-point θ grid as M5C (η₋, η₊ ∈ {0.05, 0.5}; λ_K, λ_D ∈ {0.0, 0.5, 0.9}; G_MAX ∈ {1.5, 2.0}). No value is selected. Every criterion must hold at every grid point.

## Frozen criteria

A. **Prerequisite parity**: all anchors, the M5C PASS and the MBON structure above.

B. **Readout exactness and bounds**:
   - Exactness is θ-independent and is evaluated once. Take 16 random states from the same seed stream, drawn after the odor patterns: g uniform on [0, 2.0] for plastic edges, g = 1 for nonplastic edges, and z from `sparsify` on standard-normal scores. There, `ρ` computed by (i) `np.bincount` over edges must equal (ii) sorted-segment `np.add.reduceat` within relative difference 1e-12.
   - Bounds are evaluated at every grid point: every readout computed anywhere in M5D0 must satisfy `0 ≤ ρ ≤ G_MAX`.

C. **Read-before-write**: in every FWD stream, the streaming readout at step 0 equals `ρ(1, z_A)` bitwise. At step 32 it equals `ρ(g(31), z_A)` bitwise, and differs from `ρ(g(32), z_A)` for at least one MBON in T_A(c).

D. **Forward depression**: T_A(c) is non-empty for every eligible c, and after FWD `R_m(A) < 1` for every m in T_A(c).

E. **Backward potentiation**: after BWD, `R_m(A) > 1` for every m in T_A(c).

F. **Reversal**: in REV, `R_m(A)` at the end is strictly greater than `R_m(A)` after step 255, for every m in T_A(c).

G. **Overlap-only odor specificity**, in each of FWD, BWD and REV:
   - all plastic edges from A_c KCs in compartment c carry one identical gain `a_c` (bitwise);
   - every single-compartment MBON m of c with `r_m(1, z_B) > 0` satisfies `|(R_m(B) − 1) − ω_m · (a_c − 1)| ≤ 1e-10`, with `ω_m = Σ_{e∈E_m, k(e)∈A_c∩B_c} w_e / Σ_{e∈E_m, k(e)∈B_c} w_e`.

H. **Compartment locality at readout**: in all three paradigms, `r_m(g, z_X) == r_m(1, z_X)` bitwise for X ∈ {A_c, B_c} for:
   - every single-compartment MBON of an eligible compartment not in C(c);
   - every multi-compartment MBON;
   - every outside-map MBON.

I. **Determinism**: re-running FWD for c gives bitwise identical final gains and test readouts.

J. **Permutation equivariance**: a joint permutation of KC, DAN and edge order gives, after keying by MBON bodyId, bitwise identical FWD test readouts. The permutations are drawn from the same PCG64 stream after the random states of B.

K. **Interface firewall**:
   - the readout function signature is exactly (structure, weights, gains, kc_event);
   - the streaming learner signature is exactly (structure, weights, theta, kc_events, dan_events);
   - no reward, valence, market, label or future argument exists;
   - the script reads only the M5C input manifest plus the M5C files listed above.

Diagnostics only (no criterion), at the reference point η₋ = η₊ = 0.05, λ_K = λ_D = 0.5, G_MAX = 2.0:
- per-compartment tested-MBON counts by somaSide;
- R(A) and R(B) summaries per paradigm;
- the A/B KC overlap sizes;
- the naive population readout summary.

## Formal classification

- `PASS_M5D0_MBON_READOUT_CONDITIONING_QUALIFIED`: A–K all true at all 72 grid points.
- `FAIL_M5D0_MBON_READOUT_CONDITIONING`: A true, and any of B–K false. Failures are listed; thresholds are never moved.
- `BLOCKED_M5D0_PREREQUISITE_PARITY`: A false.

## Consequence of PASS

The readout ρ above becomes the frozen MBON population readout for later V6 gates. PASS authorizes M5D1, a DAN/MBON valence source gate that uses independent literature only. It must explicitly handle documented exceptions to the approximation that PAM DANs are appetitive and PPL1 DANs aversive.

PASS does NOT select θ, assign valence, define actions, or authorize MNQ reward, PnL, strategy selection, trading or prop-firm evaluation.

## Declared limitations (carried forward)

1. Gating remains hemisphere-pooled (from M5B3B), so conditioning compartment c changes both left and right MBONs of c.
2. The readout is a linear static drive. There are no MBON dynamics, no nonlinearity, and no MBON→MBON or MBON→DAN feedback.
3. All M5C limitations still apply: one shared rule across compartments, abstract time, aggregate-edge plasticity, synthetic binary DAN activity.

## Firewalls

- MNQ, reward, PnL, strategy, trading and prop-firm evaluation CLOSED.
- θ values not selected; valence not assigned.
- Synapse coordinates unopened.
- Amin and M4V0 numeric values unopened.
