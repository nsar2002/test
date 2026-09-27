# V6-M5B3C formal result

Classification: **FAIL_M5B3C_RESOLVER_VALIDATION**

Criteria A, B, C, D and F held. **E1 and E2 failed.** The thresholds were not moved.

## Provenance

- **Protocol:** `research/v6_m5b3c_synapse_compartment_resolver_protocol.md`, SHA256 `013fd988ecb063ee74d9b4487dc08dfdcf4270a2ad3b557ab1c53f58141c9cda`. Frozen in the protocol-only commit `0627505bbbbcda6a79abc13591b4aea978d739f8`, before any record-batch byte was read.
- **Implementation:** commit `dd47954f8b4f26db067f7194600e91162833c0ab`, module SHA256 `7fc15e98a33f8f1f70a2a382aa7f6bd873b4c6462643849b0b3b66c61b5a4779`.
- **GitHub Actions:**
  - run 36294693074, job 108551254010, head `ea650460fcc54e09b58987d9198d258ed509e5c4`;
  - artifact 10923861143, digest `sha256:37d7afde4d374bbf3683cd7fb1cd801f5788e568f86d55483dd65ada7572d209`;
  - result commit `0715f9593b22073798eb65f5b522da8bf8961aa4`.
- **Parity with the independent local execution:**
  - result JSON SHA256 `91e65addba9f6a080267aee1559a887ca11c0f5d869744fa572a0403bbd10d59`: byte-identical;
  - learner-edge npz and per-synapse npz: byte-identical;
  - learner-edge content digest `a3159ff6…c2cf01a`.

## What held

**Source integrity (B)**

| File | Bytes streamed | MD5 = bucket md5Hash | Record batches parsed | Rows | Full-file SHA256 (new pin) |
|---|---|---|---|---|---|
| syn-partners | 6,777,179,098 | yes | 4,759 / 4,759 | 311,833,243 | `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07` |
| syn-points | 13,061,489,098 | yes | 5,455 / 5,455 | 357,489,383 | `c16b1b63186c4d4f28939decea7444451f0f5f6f7ef1bb5dab5b2a7058f8f284` |

For both files:
- there were 0 dictionary mismatches and 0 nulls in kept rows;
- the footer-verified tail held: the last parsed batch ends exactly at the footer's last block, followed only by the 8-byte end-of-stream marker;
- the stream needed no reconnection.

**Aggregate parity (C):** exact.
- 463,640 KC→MBON synapse rows equal the sum of the 61,210 pinned weights, with the same pairs and the same counts.
- The M5B3B single-compartment eligible set is reproduced exactly, per compartment.

**Join (D):** complete and consistent.
- All 463,640 rows matched exactly one PostSyn point, out of 732,505 MBON PostSyn points.
- There were 0 duplicate point groups and 0 inconsistent rows.
- `primary` and `primary_post` disagreed on 0 rows.

## What failed

**E1.** The pooled agreement between the official `subprimary` compartment and the M5B3B compartment of the 55 single-compartment MBONs is **0.7655** (165,892 / 216,699). The threshold is 0.80.

**E2.** In 7 of 55 bodies, the most frequent resolved compartment differs from the body's M5B3B compartment:

| Body | Type | M5B3B | Plurality |
|---|---|---|---|
| 10816 | MBON31 (L) | a'1 | B'1 |
| 38853 | MBON15 (L) | a'1 | B'1 |
| 160320 | MBON25-like (L) | y2 | y1 |
| 515034 | MBON27 (R) | y5 | y4 |
| 519128 | MBON27 (L) | y5 | y4 |
| 558665 | MBON10 (R) | B'1 | y2 |
| 579919 | MBON10 (R) | B'1 | y3 |

## Post-hoc diagnostics (not criteria)

These were computed after the classification. They do not change it. They are recorded to direct the next step.

Source: `fly_mnq/v6_m5b3c_posthoc_kc_class.py` (SHA256 `7ff79e22…bb93`), run on the byte-identical per-synapse artifact (`ae61c997…`) and the pinned annotations. Output SHA256: `08c59e64…4ba78`.

1. **Hemisphere is right.** The label side equals the KC soma side for 413,113 of 413,215 resolved synapses (99.98 %).
2. **The ROI labels cross lobe systems.** KC axons are confined to their lobe system. Yet only **93.89 %** of resolved synapses carry a label from the lobe system of their KC:

   | KC class | labelled α/β | labelled α′/β′ | labelled γ |
   |---|---|---|---|
   | αβ | 100,382 | 3,631 | **6,905** |
   | α′β′ | 3,875 | 97,713 | **9,036** |
   | γ | 293 | 1,493 | 189,887 |

   The off-diagonal cells cannot be real anatomy. They are ROI-boundary errors.
3. **The MBONs are not the cause.** Only **2.92 %** of single-compartment MBON input comes from KCs of a different lobe system than the MBON's compartment. So, for example, the γ2/γ3 labels on MBON06-L (β1) input are mislabelled αβ-KC synapses, not dendrites extending into γ.
4. **Agreement among resolved synapses only is 0.8057.** Unresolved synapses count as misses in the frozen E1.
5. **Primary-level labels are coarse too.** Unresolved KC→MBON synapses carry primary labels such as `CRE`, a neighbouring neuropil outside the MB where KC axons do not run, as well as `CentralBrain-unspecified` and `PED`.
6. **MBON neuronal part of the post points:** dendrite 90.5 %, axon 8.3 %, other 1.2 %.

## Interpretation

At synapse resolution, the official MaleCNS sub-compartment ROIs are not precise enough to serve as the KC→MBON compartment resolver under the frozen validation.

The failure is attributable to the ROI boundaries (diagnostics 2, 3 and 5). It is not due to the sources, the join or the aggregation, which all held exactly.

## Consequences

- **The M5B3B freeze stays in force.** KC input to multi-compartment MBONs remains nonplastic.
- **No learner sub-edge from this gate is admissible.** The workflow committed `research/results/v6_m5b3c_learner_edges.npz` automatically; it is a record of a failed gate and must not be used downstream.
- **The diagnostic signed-loop table is not admissible structure.** It covers MBON11/PPL101 in γ1, MBON12/PPL103 in γ2 and α′1, MBON33/PPL103 in γ2, and MBON21 and MBON29/PAM01 in γ5.
- **The new full-file SHA256 pins are valid** for later gates.

## Next direction (proposal; requires its own frozen protocol)

A resolver based on the **functional definition of MB compartments**:
- a compartment is the territory of its dopaminergic input, so each KC→MBON synapse is assigned by the nearest fast-DAN release site (T-bar);
- the choice is restricted to DAN types innervating the lobe system of the synapse's presynaptic KC. This restriction is textbook KC anatomy, independent of ROI annotation.

The validation criteria stay exactly as frozen here: E1 ≥ 0.80 and E2 per-body plurality, on the same 55 bodies. The new protocol must declare that it was designed after this FAIL.

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED. θ is not selected.
