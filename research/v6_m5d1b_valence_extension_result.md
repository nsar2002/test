# V6-M5D1B formal result

Classification: PASS_M5D1B_VALENCE_EXTENSION_FROZEN

## Provenance

- Protocol: `research/v6_m5d1b_valence_extension_protocol.md`, SHA256 `6499ce037b98643c8110e59677e569d799ecca2c13e0f0abd246a4b2f5b3fdd3`. It was frozen in the protocol-only commit `d823e04bc67285cbccc027786925b576ad85c757` before any text of S5/S6 was read.
- Amendment: `research/v6_m5d1b_valence_extension_protocol_amendment_20260926.md`, commit `33b0cfd`. It was written after reading S5/S6. Provisions 1–2 withhold or clarify. Provision 3 (genotype scope) is a disclosed clarification that preserves intact-animal signs.
- Table: `research/v6_m5d1b_valence_extension_table.json`, commit `d1b6bf7`.
- GitHub Actions run 36252688728; job 108433557128; head SHA 77dfd711da55bf9dcf423a766fb9cd20ab2cfa42.
- Artifact ID 10909702599; artifact digest sha256:e796f9f9a0b434dacc8bc4bcd238a2221f0a3e45f491532cad16a355b61b3d5a.
- Result commit 496471dcc4ebd62a7ad126e7fdf81fb299b9279a.
- Result JSON SHA256 4ab95b21738fbeb61dbcebe4e647644c02b9d281c01d29ec4f78bb4a3cd38bad, byte-identical to the independent local execution.

All criteria A–G held, with 0 failure records:
- A: S1–S6 and all M5D1 anchors matched;
- B: completeness and M5D1 label parity;
- C: evidence, context and alias quotes are verbatim;
- D: the per-source bridge was recomputed exactly;
- E: no outcome data;
- F: the S5 inventory is empty and the S6 inventory has 22 names, 15 used;
- G: every merged label equals the frozen merge rule.

## What the two new sources contributed

- **S5 (Rubin, Aso et al. 2024, eLife 90523): nothing admissible.** S5 names MBONs only by hemibrain type number (for example MBON21, MBON33). The inherited M5D1 bridge matches compartment-style names only, so no S5 name bridges. This is a limitation of the frozen bridge, not evidence of "no effect".
- **S6 (Aso et al. 2019, eLife 49257)**, using wild-type statements under amendment provision 3:
  - AVERSIVE confirmed for PPL101 (PPL1-γ1pedc), PPL106 (PPL1-α3) and PPL103 (PPL1-γ2α′1), the last now from a single-type line;
  - APPETITIVE confirmed for PAM01/PAM02 (combined PAM-γ5 + PAM-β′2a).
  - TH-null and ectopic-NOS inversions are recorded as context only.
- **Correction:** S6 states that PPL1-α′2/α′2 (MB-V1) "cannot induce aversive memory by itself", and S3 confirms MB-V1 = PPL1-α′2α2 (line MB058B). PPL105 therefore moves from the M5D1 shared-line AVERSIVE to **UNRESOLVED**. This is the only merged change from M5D1.

## Merged signed labels (supersede M5D1 for later gates)

| Class | Label | Types |
|---|---|---|
| DAN | APPETITIVE | PAM01, PAM02 (shared line), PAM11 |
| DAN | AVERSIVE | PPL101, PPL103, PPL104 (shared line), PPL106 |
| MBON | ATTRACTIVE | MBON11, MBON12 |
| MBON | REPULSIVE | MBON05, MBON06 (shared line) |

Unsigned: DAN 4 UNRESOLVED (PAM07, PAM08, PAM10, PPL105) and 10 UNTESTED; MBON 8 UNRESOLVED and 26 UNTESTED.

## Structural finding (unchanged)

Compartments with both a signed teaching DAN and a signed plastic single-compartment MBON: **none**. The MVP still cannot close a valence-consistent teaching → plasticity → signed-readout loop.

## Rule weaknesses found (for future protocols; not changed retroactively)

1. The frozen fallback lets a name that already primary-matched one record also fallback-match another. Example: the S6 typo `PPL1-γ1ped` matches both PPL101 and PPL102. Here it was harmless, because PPL102 has no admissible result.
2. The frozen fallback maps slash-combination names to a combined-compartment type. Example: `PAM-γ5/PAM-β'2a` fell back to PAM15, a different cell type. Here it was harmless, because it is recorded as UNTESTED with an explanation.
3. The bridge has no type-number route, so hemibrain-numbered sources such as S5 cannot contribute.

## Next authorized directions (each needs its own frozen protocol; still no market)

1. **M5D1C: a hemibrain type-number bridge for S5.** Match a source `MBONnn` to MaleCNS type `MBONnn` exactly, cross-checked against a compartment statement in the same source. This could supply activation valence for newer single-compartment MBONs (for example in y2, y5, a'3 and B'2), where signed DANs already exist.
2. **A synapse-level compartment resolver** for multi-compartment MBONs (MBON11, MBON12). This requires synapse-location/ROI data under its own firewall.

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED.
