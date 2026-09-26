# V6-M5C — DOPAMINE-GATED KC→MBON PLASTICITY CHRONOLOGY — SYNTHETIC/NO-MARKET QUALIFICATION

**STATUS: FROZEN BEFORE M5C IMPLEMENTATION AND BEFORE ANY M5C OUTPUT.**

## Freeze record

This protocol is committed alone, before any M5C code, on branch `claude/hello-8eabhu` of the public executor `nsar2002/test`. Unlike M5B0–M5B3B there is no canonical private `nsar2002/test15` commit for M5C: the authoring session had read-only access to test15. The public protocol-only commit is therefore the freeze of record. Mirroring this file byte-identically into test15 later is allowed. Changing it after M5C code exists requires a separate, dated amendment file; this file must never be edited in place.

## Authorization

V6-M5B3B result `PASS_M5B3B_COMPARTMENT_GATING_MVP_QUALIFIED` (canonical private protocol commit `9fc5b987d0c897dc9b3285b33c955cf003def9bd`) authorizes M5C "to freeze and unit-test a dopamine-gated KC→MBON plasticity chronology on this eligible edge set using synthetic/non-market event streams". It does not authorize market reward.

V6-M5A0 (FLY_MNQ_PROJECT_MEMORY) requires timing/order, bidirectional depression/potentiation, weight bounds and causal delay to be frozen before reward opens. M5C freezes their functional form and qualifies it with causal unit tests. M5C does **not** select any numerical value for them.

## Independent biological basis (qualitative only)

- Hige, Aso, Modi, Rubin & Turner 2015, *Neuron* 88(5):985–998, "Heterosynaptic Plasticity Underlies Aversive Olfactory Learning in Drosophila". Pairing an odor with activation of specific DANs induces odor-specific depression of KC→MBON transmission. Induction depends strictly on the temporal order of the two stimuli.
- Handler, Graham, Cohn, Morantte, Siliciano, Zeng, Li & Ruta 2019, *Cell* 178(1):60–75.e19, doi:10.1016/j.cell.2019.05.040. Forward pairing (odor/KC before dopamine) depresses KC→MBON signaling, with DopR1 required. Backward pairing (dopamine before odor/KC) potentiates it, with DopR2 required.
- Aso & Rubin 2016, *eLife* 5:e16135, doi:10.7554/eLife.16135. DAN cell types/compartments differ in training requirements, decay dynamics, storage capacity and flexibility. This is why the shared rule below is an explicit MVP simplification.

These citations were checked against bibliographic search records. The publisher full texts were not opened in the authoring environment because publisher domains were blocked by its egress policy. No numerical value (time constant, rate, amplitude or bound) is taken from these papers. They support only the qualitative order→sign rule, the coincidence requirement and compartment locality.

## Frozen prerequisites (parity anchors)

Pinned MaleCNS v1.0 minconf-0.5 sources (same URLs as M5B3B):
- annotations SHA256 `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`
- connectome weights SHA256 `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1`

Frozen inputs (file SHA256):
- `fly_mnq/v6_m5b3b_compartment_gating_mvp.py` `0a8d6c3fb61e7659fb885433dc0a93998dfa3b1b05397d8310274eb9fe14914b`
- `fly_mnq/v6_m4b0_functional_apl_sparsifier.py` `5927c88dbcbee6ae291d7d2c2dc70893e2c3c3f48ba1a28cb7c79eb1a328bac5`
- `research/results/v6_m5b2_exact_learner_topology_result.json` `9f05cd3f87759299396133c9c7aeda9e55bebaf4b60d9887573b17a47075b733`
- `research/results/v6_m5b3a_compartment_label_schema_result.json` `dbf3844742d551910f642b05207c3d5b6d155a5fe9a9c89297aa9282bc439f58`
- `research/results/v6_m5b3b_compartment_gating_mvp_result.json` `1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2`

M5C re-executes the frozen M5B3B script unchanged against the pinned sources and requires:
- M5B3B result JSON SHA256 `1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2`;
- M5B3B gate-population JSON SHA256 `8ca690aacb7ebde862f4a37279549206011857eed3d6b6d49ecc146fdfa979ca`;
- eligible-edge content digest `b2567b0107378c25297f3571397be7bdf470ce04daed9cf846bd6c5d1062b637`.

The digest is SHA256 over, in the order body_pre, body_post, raw_weight, compartment, gate_dan_count, of `name + NUL + dtype.str + NUL + repr(shape) + NUL` followed by the C-contiguous array bytes. The recorded npz file SHA256 `cc347569347e3332ead93eeb94411641d542818953cc6a5e9db8565b9711cf01` is reported as a diagnostic only, because zlib output bytes may differ across environments without any content change. A local re-execution before this freeze reproduced all three file hashes exactly.

Frozen structure that must be reproduced:
- KC = 4064 (somaSide L 2019 / R 2045), DAN = 340, MBON = 97, by exact official class;
- exact KC→MBON aggregate edges = 61,210; plastic-eligible = 26,532; nonplastic = 34,678;
- fast-MB DAN bodies = 328 (PAM01–PAM15, PPL101–PPL106); non-fast DAN bodies = 12;
- 16 gate compartments; 12 compartments carry eligible edges: B'1, B'2, B1, a'1, a'2, a'3, a1, a2, a3, y2, y4, y5.

Any source, hash, count or structure mismatch → `BLOCKED_M5C_PREREQUISITE_PARITY`.

## Frozen state

- Every exact KC→MBON aggregate edge e=(k, m) carries a dimensionless gain `g_e`, initialized to `g_e = 1` (anatomical baseline). A later effective weight would be `raw_weight_e × g_e`. M5C defines no MBON readout.
- A plastic edge is an M5B3B-eligible edge with its single compartment `c(e)`. Nonplastic edges (multi-compartment MBON input, MBON22 calyx input) keep `g_e = 1` exactly, forever.
- The frozen M5B3B gate population is `G_c` for compartment c. A DAN mapped to several compartments belongs to each of them.

## Inputs per discrete step t = 0 … T−1

- `z(t) ∈ {0,1}^4064`: KC events, keyed by KC bodyId.
- `a(t) ∈ {0,1}^340`: events for all exact DAN bodies, keyed by DAN bodyId. Only the 328 fast-MB DAN bodies map to any gate. Activity of the other 12 must have no effect.
- Steps are abstract event steps. No physical time unit is claimed.
- No reward, valence, price, return, PnL, MBON output, label or future input exists anywhere in the interface.

## Frozen chronology (per step t, in this order)

1. Compartment dopamine: `D_c(t) = n_c(t) / |G_c|`, where `n_c(t)` is the integer count of active DAN bodies in `G_c`. This gives D ∈ [0,1], is valence-agnostic, and has no dependence on compartment size.
2. KC eligibility trace, including the current step: `x_k(t) = λ_K · x_k(t−1) + z_k(t)`, with `x_k(−1) = 0`.
3. Plastic-edge update for e = (k, m) with compartment c:
   `Δg_e(t) = −η₋ · x_k(t) · D_c(t) + η₊ · y_c(t−1) · z_k(t)`
   `g_e(t) = min(max(g_e(t−1) + Δg_e(t), 0), G_MAX)`
4. Dopamine trace, strictly past for potentiation: `y_c(t) = λ_D · y_c(t−1) + D_c(t)`, with `y_c(−1) = 0`, updated after step 3.
5. Nonplastic edges are untouched.

Implied pairing kernel for one KC event and one full-gate dopamine event (D=1), starting from baseline, before clipping:
- dopamine Δ ≥ 0 steps after the KC event (forward or coincident): `Δg = −η₋ · λ_K^Δ` (depression);
- KC event Δ ≥ 1 steps after the dopamine event (backward): `Δg = +η₊ · λ_D^(Δ−1)` (potentiation);
- with `0^0 = 1`. Same-step coincidence is classified as forward (depression). This discretization convention is frozen here.

Read-before-write rule for later gates: any readout at step t must use `g(t−1)`.

## Parameters: form frozen, values NOT selected

θ = (η₋, η₊, λ_K, λ_D, G_MAX), with structural constraints η₋ > 0, η₊ > 0, 0 ≤ λ_K < 1, 0 ≤ λ_D < 1 and G_MAX > 1. G_MAX > 1 makes backward-pairing potentiation from baseline representable. No per-compartment, per-DAN-type, per-hemisphere or per-KC parameter exists.

M5C selects no value. Every criterion must hold at **every** point of the frozen test grid:
- η₋ ∈ {0.05, 0.5}
- η₊ ∈ {0.05, 0.5}
- λ_K ∈ {0.0, 0.5, 0.9}
- λ_D ∈ {0.0, 0.5, 0.9}
- G_MAX ∈ {1.5, 2.0}

That is 72 points. Production values must be frozen by a later protocol before reward opens, from independent sources or explicit non-market criteria, and never from MNQ, market, reward or PnL outcomes.

## Frozen synthetic streams

- RNG: NumPy PCG64, seed `20260926`.
- KC events for integration streams come from the frozen M4B0 `sparsify` function, imported unchanged from the pinned file, applied to standard-normal synthetic scores. This gives exactly 202 (L) / 205 (R) active KCs per step.
- DAN events for random streams are independent Bernoulli(0.05) per DAN body per step, over all 340 DAN bodies.
- Random-stream length T = 64.

## Frozen criteria

PASS requires every criterion at every grid point.

A. **Prerequisite parity**: all anchors and counts above are exact.

B. **Pairing kernel exactness**: for each of the 12 eligible compartments c and each Δ ∈ {−3,…,+3}, run a stream with T = 7 in which all 4064 KCs fire once at step 3 and every DAN in `G_c` (and no other DAN) fires once at step 3+Δ. Starting from baseline, the final gain of every eligible edge of c must equal, within absolute tolerance 1e-12:
   - `1 − η₋ · λ_K^Δ` for Δ ≥ 0;
   - `1 + η₊ · λ_D^(|Δ|−1)` for Δ < 0.

C. **Order→sign rule**: in the B scenarios, forward or coincident pairing (Δ ≥ 0) never increases g and gives a strict decrease whenever `λ_K^Δ > 0`. Backward pairing (Δ < 0) never decreases g and gives a strict increase whenever `λ_D^(|Δ|−1) > 0`. Pairings outside the trace window (zero factor) give exactly zero change.

D. **Coincidence requirement and KC specificity**:
   - D1: a KC-only stream (sparsifier KC events, all DAN silent) leaves every g bitwise equal to 1;
   - D2: a DAN-only stream (random DAN events, all KC silent) leaves every g bitwise equal to 1;
   - D3: one step with a sparsifier KC pattern S and all 328 fast DANs active changes exactly the eligible edges whose KC is in S, and no other edge.

E. **Compartment locality**: for each of the 328 fast DAN bodies alone, fired coincidently with all KCs, the set of changed edges equals exactly the eligible edges of that DAN's mapped compartments. Each of the 12 non-fast DAN bodies alone changes nothing.

F. **Nonplastic invariance**: all 34,678 nonplastic edges stay exactly 1.0 in every stream, including when their MBON's compartments receive dopamine.

G. **Bounds and saturation**: in every stream, `0 ≤ g ≤ G_MAX` at every step. Both saturation streams have T = 2048 and 32 pairings spaced 64 steps apart, starting from baseline:
   - depression: all 4064 KCs and all 328 fast DANs fire together at steps 64j (j = 0…31). Every eligible edge must end at exactly 0;
   - potentiation: all 328 fast DANs fire at steps 64j and all 4064 KCs fire at steps 64j+1 (j = 0…31). Every eligible edge must end at exactly G_MAX;
   - neither bound is ever exceeded, and nonplastic edges stay at 1.

   Why 64-step spacing: under the chronology, carry-over from earlier pairings contributes at most `0.5 · 0.9^63 / (1 − 0.9^64) < 7e-4` per pairing anywhere in the grid. The minimum drive per pairing is 0.05, so both saturations are guaranteed within 21 pairings at every grid point. Adjacent pairings are deliberately not used, because overlapping forward and backward terms can reverse the net sign.

H. **Causality (no look-ahead)**: for a random stream and cut points τ ∈ {8, 16, 32, 48}, replacing all inputs after τ with independent random inputs leaves g(0…τ) bitwise identical.

I. **Determinism**: two executions of the same stream are bitwise identical, including the canonical SHA256 of the gain trajectory.

J. **Permutation equivariance**: a joint random permutation of KC order, DAN order and edge order gives, after restoring by (KC bodyId, MBON bodyId), bitwise identical gains.

K. **Valence-agnostic shared rule**: the B kernel is identical across all 12 compartments, PAM- and PPL1-gated alike. θ has exactly 5 scalars.

L. **M4B0 integration**: in sparsifier-driven random streams (seed above), every step has exactly 202 L / 205 R active KCs, and criterion F, the G bounds and criterion H hold. Zeroing the 12 non-fast DAN channels leaves the gains bitwise unchanged.

M. **Interface firewall**: the plasticity routine's signature accepts only (structure, θ, KC events, DAN events). No reward, market, label, MBON-output or future argument exists. The M5C script declares an explicit input manifest and reads only the pinned sources, the frozen scripts/result JSONs and the outputs of the unchanged M5B3B re-execution.

All gains, traces and dopamine values are float64.

Diagnostics only (no criterion): the kernel table at one reference grid point, the fraction of eligible edges changed and the gain summaries per compartment in the integration streams, and the runtime.

## Formal classification

- `PASS_M5C_DOPAMINE_GATED_KC_MBON_CHRONOLOGY_QUALIFIED`: A–M all true at all 72 grid points.
- `FAIL_M5C_PLASTICITY_CHRONOLOGY`: A true, and any of B–M false at any grid point. The failing criteria and grid points are listed; thresholds are never moved.
- `BLOCKED_M5C_PREREQUISITE_PARITY`: A false.

## Consequence of PASS

PASS qualifies this chronology as the no-market KC→MBON plasticity operator for the MVP learner. It authorizes a later M5D protocol to freeze, still without market data:
- MBON population readout under the read-before-write rule;
- DAN teaching semantics, including any valence assignment from independent sources;
- a non-market procedure for identifying θ.

PASS does NOT select η₋, η₊, λ_K, λ_D or G_MAX. It does NOT authorize MNQ reward, PnL, strategy selection, trading or prop-firm evaluation.

## Declared limitations (not tested, carried forward)

1. **Hemisphere pooling**: M5B3B gate populations are not side-resolved. M5B2 reports cross-soma-side KC→MBON edges (L→R 6,408; R→L 6,356). A dopamine event in compartment c therefore gates the eligible edges of c in both mushroom bodies. Side-resolved gating needs DAN terminal-side evidence (ROI or synapse location), which requires its own source gate; synapse coordinates remain unopened.
2. **Shared rule across compartments**: Aso & Rubin 2016 report compartment/DAN-type-specific dynamics. Per-compartment parameters are not identified and are not introduced.
3. **Abstract time**: no mapping from steps to seconds; biological pairing windows are not calibrated.
4. **Aggregate edges**: plasticity acts per KC→MBON body pair, not per synapse.
5. **Synthetic DAN activity**: binary synthetic events only. No DAN dynamics, no MBON→DAN feedback, no valence.

## Firewalls

- MNQ, reward, PnL, strategy, trading and prop-firm evaluation CLOSED.
- Learning-rate, trace-decay and bound magnitudes are not selected.
- Reward valence/sign not assigned to DAN types.
- Synapse coordinates unopened.
- Multi-compartment KC→MBON edges nonplastic.
- Amin numeric values unopened.
- M4V0 numeric values unopened.
