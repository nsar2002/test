# V6-M5D1 formal result

Classification: PASS_M5D1_VALENCE_SOURCE_TABLE_FROZEN

## Provenance

- Protocol: `research/v6_m5d1_valence_source_protocol.md`, SHA256 `e1f1bbd0be4bcee86c2be3d20b3796e4deb84c5f0cdfb04699d5403f81de3f90`, frozen in the protocol-only commit `f29b87c90bfc5c831fa505ee8cbf3b20d8ba55ce` before any pinned source text was read.
- Amendment: `research/v6_m5d1_valence_source_protocol_amendment_20260926.md`, commit `4c83399`. It only withholds signs.
- Table: `research/v6_m5d1_valence_source_table.json`, commit `b378cd1`.
- GitHub Actions run 36252059568; job 108431809424; head SHA 6cb9b42b3814a1fe3535370dbd2cf1538bbbd923.
- Artifact ID 10908958573; artifact digest sha256:bde6e08949e91abb9af049dd64842d31330854eacbc47f528c3f1244454f5177.
- Result commit 1ce3c0ec98e8b507e13540423d9968c8a75d4c59.
- Result JSON SHA256 996070bbd217195dac39600eaa90fa5a44d3ce3902aa2ded12b2eab161c8679d, byte-identical to the independent local execution. stdout SHA256 3328ac9e527b8919589208b7242514fbf80080b8d1d0b463177309ba1a9cb83c.

All criteria A–F held with 0 failure records:
- A: the four eLife XML sources matched their pinned SHA256 at elife-article-xml commit `d146492a`.
- B: 21 DAN and 38 MBON records.
- C: every quote is verbatim and name-bearing.
- D: the bridge was recomputed exactly.
- E: no outcome data.
- F: the inventory equals the frozen scan (60 names, 32 used).

## Signed labels (the only signs later gates may use)

DAN teaching valence (S1, Aso & Rubin 2016):

| Label | Type | Source name | Basis |
|---|---|---|---|
| APPETITIVE | PAM11 | PAM-α1 | single-type line |
| APPETITIVE | PAM01 | PAM-γ5 | shared line |
| APPETITIVE | PAM02 | PAM-β′2a | shared line |
| AVERSIVE | PPL101 | PPL1-γ1pedc | forward pairing |
| AVERSIVE | PPL106 | PPL1-α3 | single-type line |
| AVERSIVE | PPL103 | PPL1-γ2α′1 | shared line |
| AVERSIVE | PPL104 | PPL1-α′3 | shared line |
| AVERSIVE | PPL105 | PPL1-α′2α2 | shared line |

MBON activation valence (S2, Aso et al. 2014b):

| Label | Type | Source name | Basis |
|---|---|---|---|
| ATTRACTIVE | MBON11 | MBON-γ1pedc>α/β | named statement |
| ATTRACTIVE | MBON12 | MBON-γ2α′1 | named statement |
| REPULSIVE | MBON05 | MBON-γ4>γ1γ2 | named statement |
| REPULSIVE | MBON06 | MBON-β1>α | shared line |

Label counts:

| Class | Signed | UNRESOLVED | UNTESTED |
|---|---|---|---|
| DAN | 3 appetitive, 5 aversive | 3 (PAM07, PAM08, PAM10) | 10 |
| MBON | 2 attractive, 2 repulsive | 8 (M4/M6 group: MBON01, 03, 04; V2 group: MBON15–19) | 26 |

The UNRESOLVED labels come from amendment provisions 1 and 2. Examples: S2 states that MB011B gave a significant aversive effect "but not" MB210B or MB002B, which label the same M4/M6 types; and V2-cluster attraction reached significance only with the group driver MB052B.

## Structural finding (critical for the learner design)

The per-compartment coverage diagnostic shows that **no eligible compartment has both a signed teaching DAN label and a signed MBON label among its plastic (single-compartment) MBONs**:
- Both attractive MBONs (MBON11 γ1pedc>α/β, MBON12 γ2α′1) have multi-compartment dendrites. Under the frozen M5B3B rule their KC input is therefore nonplastic, although their compartments carry aversive DAN labels (PPL101, PPL103).
- The repulsive single-compartment MBONs (MBON05 in y4, MBON06 in B1) sit in compartments whose DAN types are UNRESOLVED or UNTESTED.
- Compartments with signed DANs (a1, y5, B'2, a'1, a'2, a'3, a2, a3, y2) have only UNRESOLVED or UNTESTED single-compartment MBONs.

Consequence: under the frozen definitions to date, the MVP learner cannot yet close a valence-consistent loop from a teaching signal, through KC→MBON plasticity, to a signed action readout. This is a real design result. It must not be bypassed with the PAM/PPL1 cluster approximation or with guessed labels.

## Claim boundary

The table records only what the pinned texts state in name-bearing statements. Many types were tested in these papers but their results appear only in figures, which this gate does not use. UNTESTED and UNRESOLVED therefore mean "no admissible textual sign", not "no effect".

## Guardrails

Remained closed: market, reward and PnL not loaded; no model outcome used; the cluster prior was not used as a source; Amin and M4V0 numeric values unopened.

## Next authorized directions (each needs its own frozen protocol, still no market)

1. **Extend valence evidence.** Pin additional independent sources (for example later MBON activation screens that cover newer MBON types, and DAN studies naming PAM-γ4, PAM-β1, PAM-γ3 and PAM-β′1) under the same quote-verified, exact-bridge rules.
2. **Synapse-level compartment resolver.** Allow multi-compartment MBONs such as MBON11 and MBON12 to receive compartment-specific plasticity. This requires opening synapse-location/ROI data under its own source firewall.

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED.
