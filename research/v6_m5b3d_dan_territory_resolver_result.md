# V6-M5B3D formal result

Classification: **FAIL_M5B3D_RESOLVER_VALIDATION**

Criteria A, B, C, D, E1 and F held. **E2 failed** for 3 of 55 bodies. The thresholds were not moved.

## Provenance

- **Protocol:** `research/v6_m5b3d_dan_territory_resolver_protocol.md`, SHA256 `a9bea6d68c51b971e9ac3d666a429c7165cadbf57849c7c02b1089577de8651e`. Frozen in the protocol-only commit `994a2b152b93188adeafa57196e726b9abd9628a`, before any fast-DAN→KC row was selected, counted or inspected.
- **Implementation:** commit `93d5cd8c8ef316343542963403ef4a3245b812f0`, module SHA256 `29f09962233fc243243d99cca204da3d93eb6d21cb2dc103632d573b7909a66f`. It reuses the pinned M5B3C machinery (`7fc15e98…`).
- **GitHub Actions:**
  - run 36360045958, job 108735282932, head `ee45270ff0e47d368e5e903093a32eff5f201c62`;
  - artifact 10944809404, digest `sha256:0b3fcdf3cc82e253b341542f8b658fb6616311ea20916bb7d2952c768252f92b`;
  - result commit `8dbd829ad5df0cd075de859c9989335034a6a311`.
- **Parity with the independent local execution:** the result JSON (SHA256 `3f8eb2c16fe7161215059cbb1ee7e4e3bbedc79869991a91b0a4dbc25d66cc8b`) and both npz files are byte-identical.

## What held

- **A. Prerequisites.**
  - The self-test passed: 9 cases, including M5B3C machinery and KD-tree assignment equal to brute force.
  - All pinned inputs matched.
  - Identities held: KC 4,064, MBON 97, fast DAN 328, 61,210 edges.
  - The M5B3B map was reproduced.
- **B. Source integrity.** syn-partners streamed in full with SHA256 `959d8ef4…` and MD5 equal to the pins; all 4,759 batches were parsed and the tail was verified.
- **C. Aggregate parity.** Exact: 463,640 synapses equal the 61,210 weights, and the M5B3B single-compartment set was reproduced.
- **D. Territory coverage.** All 30 (compartment, side) cells have candidate release sites. The 223,031 fast-DAN→KC rows give 74,527 distinct candidate sites.
- **E1. Pooled semantics.** Agreement is **0.8782** (190,296 / 216,699), at or above 0.80. With the ROI labels in M5B3C it was 0.7655.

## What failed

**E2.** In 3 of 55 single-compartment bodies, the most frequent territory compartment differs from the M5B3B compartment:

| Body | Type | M5B3B | Territory plurality | M5B3C ROI plurality |
|---|---|---|---|---|
| 515034 | MBON27 (R) | y5 | y4 (1,630 vs y5 1,393) | y4 |
| 519128 | MBON27 (L) | y5 | y4 (1,365 vs y5 811) | y4 |
| 160320 | MBON25-like (L) | y2 | y1 (238 vs y2 127) | y1 |

## Diagnostics (not criteria)

- **Type-shuffle control:** with candidate labels permuted within each (class, side), pooled agreement is **0.2645**. The territory signal is therefore not an artefact of site density.
- **Compared with M5B3C,** territory assignment fixes 4 of the 7 M5B3C plurality failures: MBON31-L, MBON15-L, and both MBON10-R bodies.
- **Unresolved synapses:** 3 with an unknown KC class and 3 with mixed-compartment ties, out of 463,640.
- **Pre–post distance** (KC T-bar to MBON PSD): median 149 nm, 99th percentile 333 nm.
- **Nearest-site distance:** median 852 nm, 90th percentile 1.59 µm, 99th percentile 75.7 µm. The long tail comes from KC→MBON synapses far from any lobe release site, including the calyx input of MBON22, which is nonplastic.
- **Post hoc: the three E2 bodies.** Two independent methods agree against the nomenclature on all three bodies: ROI labels (M5B3C) and DAN territory (M5B3D).
  - **MBON25-like 160320.** All of its KC input is γm, split γ1/γ2. Li et al. 2020 (eLife 9:e62576) describe MBON25 as "(γ1γ2)… receives input in the γ1 and γ2 compartments". So the γ2-only reading of this body's instance label is likely too narrow.
  - **MBON27.** Li et al. 2020 describe "MBON27 (γ5d)… receives about half its input inside the MB, from the γ5 compartment", with "80% visual effective input". In MaleCNS its KC input is dominated by γd (visual) KCs (2,829 of 3,205 synapses on body 515034). Its territory splits γ4/γ5: among γd synapses γ4 ≥ γ5, and among γm synapses γ5 > γ4. **This discrepancy is unresolved.** It may reflect MaleCNS anatomy or the γ4/γ5 territory boundary in the dorsal γ layer; the data here cannot decide.
- **Signed loops** hold under the territory assignment, with model-consistent signs. They are **not admissible** because the gate failed:

  | MBON | Compartment | Weight | DAN |
  |---|---|---|---|
  | MBON11 | γ1 | 27,196 | PPL101 |
  | MBON12 | γ2 | 11,539 | PPL103 |
  | MBON12 | α′1 | 9,358 | PPL103 |
  | MBON33 | γ2 | 1,055 | PPL103 |
  | MBON21 | γ5 | 1,876 | PAM01 |
  | MBON29 | γ5 | 2,169 | PAM01 |

## Decision on the resolver line

Two frozen resolvers failed E2. The second failed only on bodies where the nomenclature itself is in question. Further resolver iterations would rest on outcomes that are already known, which is a forking-paths risk, so **the resolver line is closed**:

- **The M5B3B freeze stays in force.** KC input to multi-compartment MBONs is nonplastic in the learner.
- **No M5B3C or M5B3D sub-edge is admissible.** `research/results/v6_m5b3d_learner_edges.npz` was committed automatically as a failed-gate record.
- **A limitation is added to M5B3B.** The nomenclature-based single-compartment assignment is uncertain at synapse level for MBON27 (both bodies) and MBON25-like 160320. Under M5B3B these bodies keep their whole-edge plasticity in γ5 and γ2.
- **A closed signed DAN–MBON valence loop is not available in the admissible structure.** Every signed MBON facing a signed DAN is multi-compartment (M5D1C).

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED. θ is not selected.
