# V6-M5F0 — DAN TEACHING SEMANTICS, COMPARTMENT-VALENCE READOUT AND NO-MARKET CAUSAL LEARNING TESTS

**STATUS: FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY M5F0 OUTPUT.** No market data exists in this gate. All tasks are synthetic.

## Authorization

The project memory lists what must be frozen before MNQ reward opens. Status of each item:
- **Frozen:** the exact subset (M5B1, M5B2); the sensory-to-KC encoding (M5E0 PASS, run 36361200150); the plasticity chronology (M5C PASS); the MBON readout (M5D0 PASS).
- **Frozen here:** **DAN teaching semantics** and **no-market causal unit tests**.

The learner structure is M5B3B. The resolver line is closed (M5B3D), so multi-compartment MBON input stays nonplastic.

## Pinned inputs (SHA256)

**Carried over:**
- The M5D0 prerequisite chain, unchanged:
  - `fly_mnq/v6_m5c_dopamine_gated_plasticity_chronology.py`: `57ba0542338588f1d0b27a24a9e91affd12209b32d8328726dd8b85503ad96a4`, together with every file in its `FROZEN_FILES`;
  - M5C result `77b9c79a70bfc589b43a53c61df253aa908dd9052a3e5a1032a3f1df7d455d5c`, whose classification must be the M5C PASS;
  - the M5B3B re-execution parity and the eligible-edge content digest;
  - the pinned annotations and weights.
- `fly_mnq/v6_m5d0_mbon_readout_conditioning.py`: `fa40e79552488c6d47fe653ffc086d1f33f321c39e71d79c58bb25a19eac9f5c`. Its `raw_drive` and `make_readout_weights` are imported unchanged.
- M5D0 result `30063194b47253503b937ee9939e96dcfbfeb711001eccdad9d8000f2fa1b182`, whose classification must be the M5D0 PASS.

**New:**
- `fly_mnq/v6_m5e0_sensory_kc_encoder.py`: `35c3181380d9647a06a2fb0a47f6a1f924ee1f38531d90846090e20e82cf1a47`. Its `Encoder` is imported unchanged.
- `research/results/v6_m5e0_encoder_result.json`: `a778a02d5efef468b4860a020d3985fbfb664fb1ae8e3758cea941807c0a451f`. Its classification must be the M5E0 PASS.
- `research/results/v6_m5e0_wiring.npz`: `e31c8e0ed9636c629e7088a053064bd399324b73aac298d6698aab3f84ecd31b`. It holds the rewired arm, `k_rewired`.
- `research/results/v6_m5d1b_valence_extension_result.json`: `4ab95b21738fbeb61dbcebe4e647644c02b9d281c01d29ec4f78bb4a3cd38bad`. Its merged DAN label counts must be APPETITIVE 3 and AVERSIVE 4.
- `research/v6_m5d1c_type_number_bridge_result.md`: `364b5629ca4dcd85825b7118130c31d94c90fb9276047ae1542a644ff35ac201`. It is the record of the admissible signs.

## Frozen teaching semantics

**Outcome.** o(t) is a real number attached to bar t, the interval (t, t+1]. It becomes known only when bar t+1 begins.

**DAN event D(o).**

| Condition | Active DAN bodies |
|---|---|
| o > 0 | every body of the M5D1C **APPETITIVE** types PAM01, PAM02, PAM11 |
| o < 0 | every body of the **AVERSIVE** types PPL101, PPL103, PPL104, PPL106 |
| o = 0 | none |

All other DANs are always silent. Teaching is binary: only the sign of o is used.

**Schedule.** Each bar t becomes two consecutive steps of the frozen M5C chronology:

| Step | KC input | DAN input | Role |
|---|---|---|---|
| I(t), inference | z(t) | none | The readout for bar t is computed here from the gains after T(t−1): read before write. |
| T(t), teaching | z(t) (the state persists until its outcome) | D(o(t)) | Executed only once o(t) is known, after bar t and before I(t+1). |

z(t) is the M5E0 code of the features u(t), which are known at t.

**Declared consequence.** M5C's backward term (+η₊·y·z) potentiates the next code z(t+1) after every teaching event. In markets z(t+1) can carry information about o(t), so this is a contemporaneous-contamination risk. It is inherent in the frozen rule. This gate measures it (AR(1) diagnostics) and does not remove it.

## Frozen compartment-valence readout

**Taught compartments.** These are the M5B3B eligible compartments whose gate population contains a signed type:
- **APP = {y5, B'2, a1}**: PAM01 in y5, PAM02 in B'2, PAM11 in a1.
- **AV = {y2, a'1, a'3, a3}**: PPL103 in y2 and a'1, PPL104 in a'3, PPL106 in a3.

y1 (PPL101) has no eligible edge. The sets are recomputed at runtime and must equal these.

**MBON sets.** M_APP and M_AV are the single-compartment MBON bodies of APP and AV.

**Relative response.** For each MBON, `R_m(t) = r_m(g, z(t)) / r_m(1, z(t))`, using the M5D0 raw drive. MBONs with `r_m(1, z(t)) = 0` are excluded at step t.

**Score.**
```
s(t) = mean_{m∈M_AV} R_m(t) − mean_{m∈M_APP} R_m(t)
```
If either set has no valid MBON at t, then s(t) = 0; these steps are counted.

**Rationale.** In the valence-balance model (Aso et al. 2014b), MBONs of compartments taught by aversive DANs promote approach, and MBONs of compartments taught by appetitive DANs promote avoidance. Forward pairing depresses KC→MBON gain. So s(t) > 0 means the avoidance-promoting output is relatively depressed, and predicts a positive outcome. Only DAN signs are used; MBON signs stay unresolved.

## θ

The M5C 72-point grid is used; no value is selected. θ_ref is the M5C-declared reference point: η₋ = η₊ = 0.05, λ_K = λ_D = 0.5, G_MAX = 2.0.

## Frozen synthetic tasks

The generator is PCG64 with seed **20261001**. Draws are made in the order listed. Every task has T = 4,000 bars.

1. **PLANTED.**
   - Features: u(t) ∈ ℝ^20, i.i.d. N(0,1).
   - Outcome: o(t) = u₀(t) + 0.5·ε(t), with ε ~ N(0,1).
2. **SHUFFLED.**
   - The PLANTED features and evaluation outcomes are reused.
   - Teaching uses a fixed random permutation (the next draw) of the PLANTED outcomes.
3. **AR(φ)**, for φ ∈ {−0.3, 0.0, +0.3}.
   - Returns: r(0) ~ N(0,1), then r(t) = φ·r(t−1) + √(1−φ²)·ε(t).
   - Features: u₀(t) = r(t), the last completed bar. u₁…u₁₉ are i.i.d. N(0,1).
   - Outcome: o(t) = r(t+1). The sequence is generated for T+1 steps.

**Metric: ρ_os.** The Pearson correlation between s(t) and o(t) over the second half, t ∈ [2000, 4000). Learning continues throughout, and every s(t) is read before write.

## Frozen criteria (connectome arm)

- **A. Prerequisites.**
  - All pins match, and the M5B3B re-execution parity holds.
  - The structure counts equal M5C's `EXPECTED`.
  - M5E0 is a PASS.
  - The DAN sign counts are 3 and 4.
  - APP and AV equal the frozen sets.
- **B. Teaching semantics exact.**
  - For 1,000 random outcomes, including exact zeros, the DAN vector equals the frozen body sets bitwise.
  - D(0) is the zero vector.
- **C. Causality**, at θ_ref on PLANTED:
  - Perturbing features and outcomes of bars t ≥ 3,000 leaves s(t) for t < 3,000 bitwise unchanged.
  - Perturbing outcomes only, for bars t ≥ 3,000, also leaves s(3000) unchanged.
- **D. Determinism.** Two runs give bitwise identical s(t) and final gains.
- **E. Bounds.** At every grid point run, all gains stay within [0, G_MAX], and all R_m are finite and ≥ 0.
- **F. Learning**, at θ_ref: PLANTED ρ_os > **0.0691**. This is a one-sided z-test at p < 0.001 for n = 2,000, since 3.090/√2000 = 0.0691.
- **G. Teaching-specificity control**, at θ_ref: |SHUFFLED ρ_os| ≤ **0.0691**.
- **H. Interface firewall.**
  - The chronology is the unchanged M5C `run_chronology(structure, theta, kc_events, dan_events)`.
  - The teaching event for bar t is constructed only from o(t), at step T(t).
  - The readout function takes no outcome argument. This is checked by signature inspection.

Classification:
- **`PASS_M5F0_TEACHING_SEMANTICS_QUALIFIED`:** A–H all hold.
- **`FAIL_M5F0_TEACHING_SEMANTICS`:** A holds and any of B–H fails. Failures are listed; thresholds are never moved.
- **`BLOCKED_M5F0_PREREQUISITE_PARITY`:** A fails.

## Diagnostics (never criteria)

- PLANTED ρ_os at all 72 grid points, in both the connectome arm and the rewired arm (M5E0 `k_rewired`).
- AR(φ) ρ_os for φ = −0.3, 0 and +0.3, at θ_ref and at all 72 grid points, in the connectome arm. This characterizes the contamination bias: whether the learned sign follows φ.
- The final-gain distribution: the fraction of plastic edges at 0, at G_MAX, and within 1 ± 0.01.
- The count of steps with s = 0.

## Declared limitations

- **Teaching is binary.** The magnitude of the outcome is not used.
- **Only the 3 appetitive and 4 aversive signed DAN types teach.** PPL101 has no eligible edge.
- **Plastic outputs are few.** The MBONs in APP and AV are few: MBON27 (γ5, whose synapse-level compartment is uncertain), MBON03/04/26 (β′2) and MBON07 (α1) on the appetitive side; MBON32/34/35/25-like (γ2), MBON15/31 (α′1), MBON16/17/28 (α′3) and MBON14 (α3) on the aversive side.
- **The contamination bias of backward potentiation is intrinsic to M5C** and is only measured here.
- **Time is abstract:** two chronology steps per bar.

## Firewalls

- MNQ, reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED. Only synthetic tasks are used.
- θ is not selected.
- Amin and M4V0 numeric values remain unopened.
- The MNQ_extdata Drive folder stays unopened.
