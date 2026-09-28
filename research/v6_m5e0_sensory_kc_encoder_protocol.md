# V6-M5E0 — DETERMINISTIC SENSORY-TO-KC ENCODER AND WIRING CONTROL (NO MARKET)

**STATUS: FROZEN BEFORE THE ENCODER WAS IMPLEMENTED OR RUN.**

The connectome inputs (pinned annotations and weights) are already open. The only statistics seen are the ALPN→KC counts listed under "Identity anchors". No encoder output, code statistic or market value has been seen.

## Authorization

The project memory's next-direction block states that "M5 may advance only behind the M4 gate". It lists what must be frozen before MNQ reward opens: the exact KC/DAN/MBON subset, a deterministic sensory-to-KC encoding, DAN teaching semantics, the KC→MBON plasticity chronology and eligibility, the MBON readout, and no-market causal unit tests. Their status:
- **Frozen:** the M4 gate (M4B0 PASS), the subset (M5B1, M5B2), the chronology (M5C PASS) and the readout (M5D0 PASS).
- **This gate:** the **deterministic sensory-to-KC encoding**, plus the wiring control that will make "does the connectome add information?" testable.

The M5B3C/M5B3D resolver line is closed. The learner uses the M5B3B structure.

## Scientific role

Market features enter the fly model the way odours do. Each feature drives projection-neuron (PN) channels; PNs drive Kenyon cells (KCs) through the MaleCNS PN→KC connectome; the frozen M4B0 APL sparsifier keeps the top 10 % of KCs per hemisphere.

The **degree-preserving PN→KC rewiring control** keeps every quantity except the connectome's specific wiring. A later MNQ protocol can therefore attribute any performance difference to the wiring structure itself.

## Pinned inputs (SHA256)

- body annotations: `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`;
- connectome weights (minconf 0.5): `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1`;
- `fly_mnq/v6_m4b0_functional_apl_sparsifier.py`: `5927c88dbcbee6ae291d7d2c2dc70893e2c3c3f48ba1a28cb7c79eb1a328bac5`. Its `sparsify` is imported unchanged: top k = round(0.10·n) per hemisphere (202 L / 205 R), ties broken by ascending bodyId.

## Identity anchors

These counts were seen during design and are frozen as parity anchors:
- **KC:** `class == "Kenyon_Cell"`: 4,064 (2,019 L / 2,045 R).
- **PN layer:** `class == "ALPN"` bodies with at least one synapse onto a KC in the pinned weights: **314 bodies**, **88 types**, **22,586 PN→KC edges**, **390,928 synapses**.
- **W** is the PN×KC integer synapse-count matrix of those edges.

## Frozen encoder

1. **Channel ranking.** The 88 PN types are ranked by total PN→KC synapses (descending), with ties broken by type name (ascending, Python string order). Rank r = 0…87.
2. **Feature interface.** At each step the encoder takes a finite vector `u(t) ∈ ℝ^F`, with 1 ≤ F ≤ 44. The features must already be causally standardized; standardization belongs to the later MNQ protocol, not to this gate. F outside 1…44, or a non-finite value, is an error.
3. **ON/OFF channels.** Feature j (0-based) drives two channels:
   - **ON:** the type of rank 2j, with activity `clip(u_j, 0, 3)`;
   - **OFF:** the type of rank 2j+1, with activity `clip(−u_j, 0, 3)`.

   Every PN body of a driven type carries its channel's activity. PNs of unassigned types carry 0. The saturation at 3 standardized units is fixed a priori: it bounds any single channel so that one extreme feature cannot monopolize the KC code, mirroring PN response saturation.
4. **Exact drive.** Activities are quantized as `a_q = round(a · 2^20)` (int64, round-half-even). The KC drive is `s_k = Σ_p W[p,k] · a_q[p]` in int64 arithmetic. It is exact, so it is identical for any summation order or machine. The bound is the maximum KC total PN input (253 synapses, seen pre-freeze) × 3 × 2^20 = 7.96 × 10^8, well below 2^53.
5. **Sparsification.** `z(t) = sparsify(kc_ids, kc_sides, s(t))`, using the frozen M4B0 function on float64(s), which is exact. KCs are ordered by ascending bodyId.

The encoder is memoryless: z(t) depends only on u(t).

## Frozen wiring control

- **Method.** Degree-preserving bipartite double-edge swaps on the 22,586 PN→KC edges (Maslov–Sneppen), using a PCG64 generator with seed **20260929**.
  - Each step draws two edges uniformly, (p1, k1, w1) and (p2, k2, w2), and proposes (p1, k2, w1) and (p2, k1, w2).
  - The proposal is rejected if p1 = p2, if k1 = k2, or if (p1, k2) or (p2, k1) already exists.
  - Each edge's synapse count travels with its PN.
  - **10 × 22,586 = 225,860 swap attempts.**
- **Preserved exactly:** every PN's out-degree and out-weight multiset, and every KC's in-degree (claw count).
- **Destroyed:** which KCs a given PN (glomerulus) contacts, and therefore any glomerulus-specific convergence structure.

## Frozen criteria

- **A. Prerequisite parity.**
  - Every pinned hash matches.
  - All identity anchors are exact.
  - Every KC side is L or R.
- **B. Exact arithmetic.** On the synthetic test streams, the int64 drive equals an independent float64 dense computation `a_q @ W` bitwise.
- **C. Exact sparsity.** Every code has exactly 202 active left KCs and 205 active right KCs.
- **D. Memorylessness.** Changing u at any other step never changes z(t).
- **E. Channel map.** The ranking is deterministic. F = 44 maps 88 distinct types. F = 0, F = 45 and a non-finite input each raise an error.
- **F. Wiring control.**
  - Degrees and PN out-weight multisets are preserved exactly.
  - No duplicate edges are created.
  - The fraction of original edges retained is **≤ 1.25 × R0**. R0 = Σ_{(p,k)∈E} d_p·d_k / E² is the first-order configuration-model expectation for a fully mixed graph with the same degrees. It is computed in the run from the original degree sequences.
  - Two generations with the frozen seed are bitwise identical.

  **Pre-freeze note.** A draft used a fixed bound of 0.05. Before this freeze, R0 was computed from the degree sequences alone (PN out-degree up to 489, KC in-degree up to 39), giving **R0 ≈ 0.0468**. A perfectly mixed control would therefore sit at that bound by chance. The relative bound replaced it before any shuffle was run.
- **G. Determinism.** Two complete runs produce identical content digests for W, the shuffled W and every synthetic code.

**Synthetic test streams.** The generator is PCG64 with seed 20260930 and T = 2,000 steps. The streams are:
1. i.i.d. N(0,1) with F = 20;
2. an equicorrelated N(0,1) stream with ρ = 0.8 and F = 20;
3. F = 44 i.i.d.;
4. an all-zero input with F = 20;
5. single-feature impulses: u = +3·e_j and −3·e_j for every j < 20.

Classification:
- **`PASS_M5E0_SENSORY_KC_ENCODER_QUALIFIED`:** A–G all hold.
- **`FAIL_M5E0_SENSORY_KC_ENCODER`:** A holds and any of B–G fails. Failures are listed.
- **`BLOCKED_M5E0_PREREQUISITE_PARITY`:** A fails.

## Diagnostics (never criteria)

- the channel table: type, bodies, edges, synapses, KCs reached;
- the number of KCs with positive drive per stream, and the fraction of steps where a zero-drive KC enters the top-k code (bodyId-tie regime). The all-zero input is expected to fall wholly in this regime;
- mean pairwise KC-code overlap against input correlation (stream 1 against stream 2): decorrelation;
- KC-class composition (γ, αβ, α′β′, other) of active codes;
- PN-type × KC-class contact preference: a chi-square statistic for the original and the shuffled W;
- code overlap between original and shuffled W on the same inputs.

## Declared limitations

- **Feature-to-glomerulus assignment is by rank, not by meaning.** It is arbitrary but frozen, and shared by the connectome and control arms.
- **Only ALPN input is used.** KCs without ALPN input (mostly visual γd and αβp) can enter a code only in the zero-drive tie regime.
- **Channel strengths differ by PN type,** as in the fly. This is shared by both arms.
- **No PN dynamics,** adaptation, or lateral inhibition in the antennal lobe.

## Firewalls

- MNQ, reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED. No market data is read.
- θ is not selected.
- Amin and M4V0 numeric values remain unopened.
