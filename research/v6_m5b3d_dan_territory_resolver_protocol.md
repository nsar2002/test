# V6-M5B3D — DAN-TERRITORY KC→MBON COMPARTMENT RESOLVER (POST-FAIL REDESIGN)

**STATUS: FROZEN BEFORE ANY FAST-DAN→KC SYNAPSE ROW WAS SELECTED, COUNTED OR INSPECTED.**

## Why this gate exists — declared post-FAIL redesign

V6-M5B3C (run 36294693074) recorded **FAIL_M5B3C_RESOLVER_VALIDATION**:
- It resolved compartments from the official MaleCNS sub-compartment ROI label `subprimary`.
- Pooled agreement with the M5B3B compartment of the 55 single-compartment MBONs was 0.7655, below 0.80.
- In 7 of 55 bodies, the most frequent compartment was not the named one.
- Sources, join and aggregate parity held exactly.
- Post-hoc diagnostics (`fly_mnq/v6_m5b3c_posthoc_kc_class.py`) showed the cause is the ROI boundaries: 6.1 % of resolved synapses carried a label from a lobe system their presynaptic KC cannot innervate.

This gate is a **redesign made after seeing that FAIL**. The following was seen before this freeze:
- the M5B3C per-synapse ROI labels and their per-body summaries;
- the KC-class cross-tabulation.

The following was not seen, selected, counted or inspected: any fast-DAN→KC synapse row. The redesign uses two principles that do not depend on ROI annotation:

1. **An MB compartment is the territory of its dopaminergic input.** Compartments are defined by the tiling of DAN axon terminals and MBON dendrites (Aso et al. 2014, *eLife* 3:e04577; Li et al. 2020, *eLife* 9:e62576). A KC→MBON synapse is assigned to the compartment of the nearest release site where a fast DAN contacts a KC.
2. **KC axons are confined to their lobe system:** γ KCs to the γ lobe, αβ KCs to the α/β lobes, α′β′ KCs to the α′/β′ lobes. Candidate release sites are therefore restricted to the synapse's own KC class and hemisphere.

**The validation criteria are unchanged from M5B3C.** E1 ≥ 0.80 and E2 per-body plurality are applied to the same 55 bodies. No threshold was moved.

## Pinned sources

Only `syn-partners-male-cns-v1.0-minconf-0.5.feather` is read. It is streamed in full, sequentially, and must match each of the following:
- 6,777,179,098 bytes;
- generation 1780494942562468;
- ETag and MD5 `58efcf712f8c4d4de5f2ad51e97def76`;
- **full-file SHA256 `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07`** (the M5B3C pin);
- 4,759 record batches;
- a 116,632-byte footer.

`syn-points` is not read.

Other pinned inputs (SHA256):
- body annotations: `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`;
- connectome weights: `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1`;
- `fly_mnq/v6_m5b3c_synapse_compartment_resolver.py`: `7fc15e98a33f8f1f70a2a382aa7f6bd873b4c6462643849b0b3b66c61b5a4779`. It supplies the frozen streaming, parity, validation and edge-building functions, which are reused unchanged;
- M5B3C result JSON: `91e65addba9f6a080267aee1559a887ca11c0f5d869744fa572a0403bbd10d59`;
- `fly_mnq/v6_m5b3b_compartment_gating_mvp.py`: `0a8d6c3fb61e7659fb885433dc0a93998dfa3b1b05397d8310274eb9fe14914b`;
- M5B3B result JSON: `1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2`;
- M5B3C0 result: `4c0f237cf8d270ec6abaebf3926e750e75c8079bda7c1a4da8f6138af7c12c7e`;
- M5B3C1 result: `4a3d73dac3fd87ed266a8e8003f1f345cf1b06aa0f5e5960d35f8be3e38b21b5`;
- M5B3C1 module: `6a88359ea4b0b90f2e615d48cfd21a51b7f188a24c34d51d7cdd0ee6c0419557`.

## Frozen read method

The read method is identical to M5B3C and uses the pinned M5B3C functions:
- **Stream:** a sequential stream in which every connection must return 206 with the exact `Content-Range`, the pinned ETag and the pinned generation. At most 8 reconnections are allowed.
- **Hashes:** SHA256 and MD5 are computed over all bytes.
- **Parsing:** exactly 4,759 record batches are parsed, projected to `x_pre, y_pre, z_pre, x_post, y_post, z_post, body_pre, body_post, primary_post`.
- **Dictionaries:** every batch's `primary_post` dictionary must equal the M5B3C1 vocabulary.
- **Tail check:** the tail is verified against the footer.

## Frozen row selection and identities

Identity sets come from the annotations:
- **KC:** `class == "Kenyon_Cell"` (4,064).
- **MBON:** `class == "MBON"` (97).
- **Fast DAN:** `class == "DAN"` with type in the M5B3B `DAN_MAP` (PAM01–15, PPL101–106; 328 bodies).

Rows kept:
- **KC→MBON:** `body_pre` ∈ KC and `body_post` ∈ MBON.
- **Fast-DAN→KC:** `body_pre` ∈ fast DAN and `body_post` ∈ KC.

**KC class** comes from the annotation type prefix: `KCg` → γ, `KCab` → αβ, `KCa'b'` → α′β′. Any other type is unknown. **KC side** is the annotation `somaSide`.

## Frozen territory definition

**Lobe systems:**
- γ: `y1…y5`;
- αβ: `a1 a2 a3 B1 B2`;
- α′β′: `a'1 a'2 a'3 B'1 B'2`.

For each fast-DAN type t and system S, `comp(t, S)` is the unique lobe compartment of S among the M5B3B `DAN_MAP[t]` compartments, if one exists. Uniqueness is checked at runtime. `pedc` is not a lobe compartment.

**Candidate release sites for (S, side):** the distinct presynaptic locations (`x_pre, y_pre, z_pre`) of fast-DAN→KC rows that meet all three conditions:
- the postsynaptic KC has class S;
- the postsynaptic KC has that side;
- `comp(DAN type, S)` exists.

Each site carries the label `comp(DAN type, S)`.

**Assignment.** A KC→MBON synapse is located at its presynaptic KC T-bar (`x_pre, y_pre, z_pre`). It receives the label of the exactly nearest candidate site of its KC's (class, side). The procedure:
- Distance is Euclidean in voxel coordinates, which are 8 nm isotropic per the dataset viewer descriptor.
- The 16 nearest candidates are retrieved with a `scipy 1.14.1` `cKDTree`.
- Squared distances are then recomputed exactly in int64.
- If the candidates at the minimal distance carry more than one compartment, or the tie may extend beyond 16 candidates, the synapse is **unresolved**.
- A synapse whose KC class is unknown is **unresolved**.

## Frozen criteria

- **A. Prerequisites exact:**
  - the synthetic self-test passes (M5B3C machinery plus the territory cases);
  - the protocol and all pinned inputs match;
  - identities hold: KC 4,064; MBON 97; fast DAN 328; 61,210 KC→MBON weight edges;
  - the M5B3B MBON map is reproduced (55 single, 40 multi, 2 outside);
  - every KC has side L or R.
- **B. Source integrity:**
  - bytes, SHA256 and MD5 equal the pin;
  - 4,759 batches are parsed;
  - there are 0 dictionary mismatches and 0 nulls in kept rows;
  - the tail check passes.
- **C. Aggregate parity:**
  - the KC→MBON synapse counts per pair equal the 61,210 pinned weights exactly;
  - the M5B3B single-compartment eligible set is reproduced exactly.
- **D. Territory coverage:** each of the 15 lobe compartments has at least one candidate release site on each side (30 cells).
- **E1. Pooled semantics:** over all KC-input synapses of the 55 single-compartment MBON bodies, the fraction assigned their M5B3B compartment is **≥ 0.80**. Unresolved synapses count as misses.
- **E2. Per-body semantics:** for each of the 55 bodies, the unique most frequent assigned compartment equals its M5B3B compartment. A tie counts as failure.
- **F.** No market, valence or θ quantity enters any criterion.

Classification:
- **`BLOCKED_M5B3D_SOURCE`** if A or B fails, if any read or parse error occurs, or if an execution error prevents C–E from being evaluated. The error is recorded.
- **`PASS_M5B3D_DAN_TERRITORY_RESOLVER_VALIDATED`** if C, D, E1 and E2 all hold.
- **`FAIL_M5B3D_RESOLVER_VALIDATION`** otherwise. The failing criteria are listed.

## Frozen learner-edge rule

The rule is identical to M5B3C and uses the pinned `build_learner_edges`. It is used downstream only on PASS.

- **Single-compartment MBON:** the whole aggregate edge stays plastic in its M5B3B compartment.
- **Multi-compartment MBON:** a synapse joins the plastic sub-edge (KC, MBON, c) iff c is one of the MBON's M5B3B-named lobe compartments and is gated by at least one fast DAN. Otherwise it joins the nonplastic remainder, with reason `offmap`, `ungated` or `unresolved`.
- **MBON22:** nonplastic, reason `outside`.

## Outputs

- **Committed:**
  - `research/results/v6_m5b3d_resolver_result.json`;
  - `research/results/v6_m5b3d_learner_edges.npz`, with its content digest recorded in the JSON.
- **Artifact only:**
  - the per-synapse table `v6_m5b3d_kc_mbon_synapses.npz`, holding the KC T-bar location, the assigned code and the nearest-site distance;
  - the transport log, which is machine-dependent.

## Diagnostics (never criteria)

- resolved and unresolved counts (unknown KC class, ties);
- percentiles of the nearest-site distance and of the pre–post distance (nm);
- the number of fast-DAN→KC rows and the candidate sites per (class, side);
- a **type-shuffle control**: pooled agreement when the candidate labels are permuted within each (class, side), with PCG64 seed 20260928, on the same neighbour sets;
- pooled agreement among resolved synapses only;
- for each of the 55 bodies, the territory plurality next to the M5B3C ROI plurality;
- for each multi-compartment body: in-map, off-map and unresolved counts;
- plastic weight per compartment, split into unchanged single-compartment edges and resolved sub-edges;
- newly plastic compartments;
- nonplastic weight by reason;
- the signed-loop table, with the same definition as M5B3C;
- local versus GitHub Actions byte parity.

## Declared limitations

- **The nearest release site stands in for dopamine reach.** It is not a diffusion model.
- **The `pedc` territory of PPL101 is merged into γ1 for γ-KC synapses**, because `comp(PPL101, γ) = y1`. This adds PPL102 to the gate of such synapses. αβ-KC synapses can never be assigned `pedc`.
- **The validation bodies are the same 55 used in M5B3C,** and M5B3C's per-body outcomes are known. The criteria were not changed; the method was changed on anatomical principles.
- **Gating stays hemisphere-pooled** (M5B3B).
- **The whole-edge rule for single-compartment MBONs is kept.**

## Firewalls

- MNQ, reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED.
- θ is not selected.
- Valence is diagnostic only.
- Amin and M4V0 numeric values remain unopened.
- The user's MNQ_extdata Drive folder stays unopened.
