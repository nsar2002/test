# V6-M5B3C — SYNAPSE-LEVEL KC→MBON COMPARTMENT RESOLVER

**STATUS: FROZEN BEFORE ANY RECORD-BATCH BYTE OF EITHER SYNAPSE FILE WAS READ.** So far, only the footers, schema messages and dictionary batches of the two synapse files have been read (V6-M5B3C0, V6-M5B3C1).

## Authorization and purpose

M5B3B made an aggregate KC→MBON edge plastic only when the MBON has dendritic input in exactly one canonical compartment. It froze input to multi-compartment MBONs "until a separately validated synapse-level compartment resolver exists". V6-M5D1C found that every signed MBON facing a signed teaching DAN is multi-compartment: MBON11, MBON12, MBON21, MBON29 and MBON33.

V6-M5B3C1 (run 36293331100) established two facts:
- the MB lobe-compartment label of a synapse point is the syn-points column `subprimary`;
- it is not present in syn-partners.

M5B3C builds and validates that resolver. It then derives compartment-specific plastic sub-edges for multi-compartment MBONs.

## Pinned sources

Synapse files come from the public bucket `flyem-male-cns`, `v1.0/connectome-data/flat-connectome/`. Each must match the M5B3C0/M5B3C1 records and the bucket's `md5Hash` on every value below:

| File | Bytes | Generation | ETag = MD5 (hex) | Record batches | Footer bytes |
|---|---|---|---|---|---|
| syn-partners-male-cns-v1.0-minconf-0.5.feather | 6,777,179,098 | 1780494942562468 | 58efcf712f8c4d4de5f2ad51e97def76 | 4,759 | 116,632 |
| syn-points-male-cns-v1.0-minconf-0.5.feather | 13,061,489,098 | 1780494991007477 | c69d08758de07582035cc8843574493a | 5,455 | 140,760 |

The SHA256 of each full file is computed over every byte and recorded. It becomes the pin for later gates.

Other pinned inputs (SHA256):
- body annotations: `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`;
- connectome weights (minconf 0.5): `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1`;
- `fly_mnq/v6_m5b3b_compartment_gating_mvp.py`: `0a8d6c3fb61e7659fb885433dc0a93998dfa3b1b05397d8310274eb9fe14914b`;
- M5B3B result JSON: `1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2`;
- M5B3C0 result JSON: `4c0f237cf8d270ec6abaebf3926e750e75c8079bda7c1a4da8f6138af7c12c7e`;
- M5B3C1 result JSON: `4a3d73dac3fd87ed266a8e8003f1f345cf1b06aa0f5e5960d35f8be3e38b21b5`, which supplies the vocabularies;
- `fly_mnq/v6_m5b3c1_roi_vocabulary_probe.py`: `6a88359ea4b0b90f2e615d48cfd21a51b7f188a24c34d51d7cdd0ee6c0419557`, which supplies the read-only footer flatbuffer parser.

## Frozen read method

Each synapse file is read **once, strictly sequentially**:
1. Every connection is an HTTP request with `Range: bytes=<offset>-`. It must return status 206 with the exact `Content-Range`, the pinned ETag and the pinned `x-goog-generation`.
2. A transport error resumes at the current offset. At most 8 reconnections are allowed per file.
3. Any response that fails these conditions is a pin error and is never retried.
4. SHA256 and MD5 are computed over all bytes in order.

The Arrow IPC stream embedded after the 8-byte file magic is parsed for **exactly** the pinned number of record batches. Parsing is projected to the fields below with pyarrow 17.0.0 `IpcReadOptions(included_fields=…)`:
- **partners:** `x_post, y_post, z_post, body_pre, body_post, conf_pre, conf_post, primary_post`;
- **points:** `x, y, z, kind, body, compartment, primary, subprimary`.

In every record batch, each dictionary of a parsed dictionary field must equal the M5B3C1-recorded vocabulary.

The bytes after the last parsed batch are captured from the same stream. The footer is parsed with the frozen M5B3C1 reader. Three conditions must hold:
- the footer lists exactly the pinned number of record-batch blocks;
- its last block ends exactly where the parser stopped;
- the only bytes in between are an end-of-stream marker: none, `00000000`, or `ffffffff00000000`.

## Frozen row selection

**KC set:** annotation `class == "Kenyon_Cell"` (4,064). **MBON set:** `class == "MBON"` (97).

- **Partners:** keep rows with `body_pre` ∈ KC and `body_post` ∈ MBON.
- **Points:** keep rows with `kind == "PostSyn"` and `body` ∈ MBON.

Kept rows must contain no nulls in the parsed fields.

## Frozen join

Each kept partner row is joined to PostSyn points by exact equality of (`body_post`, `x_post`, `y_post`, `z_post`) with (`body`, `x`, `y`, `z`).

- Points sharing (body, x, y, z) form one group.
- A partner row is **consistent** iff it matches a group and all points of that group carry the same `subprimary` and the same `primary`.
- A consistent row takes that group's labels.

## Frozen label mapping

A consistent row's `subprimary` label maps to an M5B3B lobe compartment **only** if it is one of the 30 reference labels `a1(L)` … `g5(R)`. The mapping is:
- the prefix `g` becomes `y`, and `b` becomes `B`;
- alpha and primes are unchanged;
- the side tag is removed but recorded.

Every other label is **unresolved**. That includes `<unspecified>`, `gL-unspecified(L/R)` and all non-MB labels, as well as every inconsistent or unmatched row. The peduncle is never mapped to `pedc`, the generic-`ped` conflation that M5B3B refused.

## Frozen criteria

- **A. Prerequisites exact**
  - The protocol and all pinned inputs match their SHA256.
  - The synthetic self-test passes.
  - Identity counts hold: KC 4,064; MBON 97; 61,210 KC→MBON weight edges.
  - The M5B3B MBON map is reproduced exactly from the annotations: 55 single-compartment, 40 multi-compartment, 2 outside the map.
- **B. Source integrity:** for both files:
  - the byte count and MD5 equal the pin;
  - the pinned number of record batches is parsed;
  - there are 0 dictionary mismatches and 0 nulls in kept rows;
  - the tail check passes.
- **C. Aggregate parity:**
  - For every KC→MBON pair, the number of kept partner rows equals the pinned `weight`: the same 61,210 pairs, the same values, no duplicate weight pairs, and the total synapse count equals the weight sum.
  - The single-compartment plastic edge set reproduces the M5B3B eligible set exactly: edge count and weight per compartment.
- **D. Join complete and consistent:**
  - every kept partner row matches;
  - every match is consistent;
  - the joined point's `primary` equals the row's `primary_post` for every row, compared as label strings.
- **E1. Pooled semantics:** over all KC-input synapses of the 55 single-compartment MBON bodies, the fraction whose resolved compartment equals the body's M5B3B compartment is **≥ 0.80**.
- **E2. Per-body semantics:** for each of the 55 single-compartment bodies, the unique most frequent resolved compartment among its KC-input synapses equals its M5B3B compartment. A tie counts as failure.
- **F.** No market, valence or θ quantity enters any criterion.

Classification:
- **`BLOCKED_M5B3C_SOURCE`** if A or B fails, if any read or parse error occurs, or if an execution error prevents C–E from being evaluated. The error is recorded.
- **`PASS_M5B3C_COMPARTMENT_RESOLVER_VALIDATED`** if C, D, E1 and E2 all hold.
- **`FAIL_M5B3C_RESOLVER_VALIDATION`** otherwise. The failing criteria are listed.

**Why the E1 threshold is 0.80.** It is a gross-failure detector, not a tuned value; no synapse label has been seen. A wrong column, a wrong label mapping or a mis-join would give agreement near chance across 15 compartments. The pre-freeze synthetic mutants (label shuffle, γ4/γ5 code swap) fail both E1 and E2. The margin below 1.0 allows for ROI-boundary effects and the `gL-unspecified` region. The smallest single-compartment body has 35 KC synapses (MBON34, from the already open weights), so a per-body plurality is meaningful.

## Frozen learner-edge rule

This rule is applied after the criteria and is used downstream only on PASS.

- **Single-compartment MBON:** the whole aggregate edge stays plastic in its M5B3B compartment. This is M5B3B unchanged.
- **Multi-compartment MBON:** a synapse joins the plastic sub-edge (KC, MBON, c) iff all of the following hold:
  - its resolved compartment c is one of the MBON's M5B3B-named lobe compartments;
  - c is gated by at least one fast DAN in the M5B3B gate population.

  Every other synapse joins the nonplastic remainder, with reason `offmap`, `ungated` or `unresolved`.
- **MBON outside the fast lobe map (MBON22):** nonplastic, reason `outside`.

Sub-edge weights are synapse counts. By criterion C, plastic plus nonplastic weight equals each aggregate edge weight.

## Outputs

- **Committed:** `research/results/v6_m5b3c_resolver_result.json` and `research/results/v6_m5b3c_learner_edges.npz`. The npz carries the plastic `(pre, post, comp, weight)` and nonplastic `(pre, post, reason, weight)` arrays. Its array content digest is recorded in the JSON, because zip bytes are not guaranteed identical across machines.
- **Artifact only:**
  - the per-synapse table `v6_m5b3c_kc_mbon_synapses.npz`, whose digest is recorded;
  - `v6_m5b3c_transport_log.json`, holding reconnections and timings. These are machine-dependent and kept out of the result JSON.

## Diagnostics (never criteria)

- the confidence ranges of the kept partner rows;
- the neuronal-part (`compartment` column) distribution of joined post points;
- agreement between the label side and the KC soma side;
- for each multi-compartment body: in-map counts per named compartment, off-map counts, unresolved counts and their top `primary_post` labels;
- plastic weight per compartment, split into unchanged single-compartment edges and resolved sub-edges;
- newly plastic compartments;
- nonplastic weight by reason;
- the signed-loop table. It pairs M5D1C-signed MBON types holding plastic weight in a compartment with the M5D1C-signed DAN types gating that compartment, and flags consistency with the valence-balance model (aversive DAN with attractive MBON, appetitive DAN with repulsive MBON);
- local versus GitHub Actions byte parity of the result JSON.

## Declared limitations

- **ROI boundaries are official annotations, not ground truth.** Synapses near compartment borders can carry a neighbouring label.
- **Gating stays hemisphere-pooled**, as in M5B3B. The side tag is recorded only.
- **The whole-edge rule is kept for single-compartment MBONs**, for continuity with M5B3B, M5C and M5D0. Their off-compartment fraction is reported, not removed.
- **The `pedc` part of MBON11 stays nonplastic** because it cannot be resolved.

## Firewalls

- MNQ, reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED.
- θ is not selected.
- Valence is diagnostic only.
- Amin and M4V0 numeric values remain unopened.
- Only the listed fields of the two synapse files are parsed. All their bytes are hashed.
