# V6-M5D1C formal result

Classification: PASS_M5D1C_TYPE_NUMBER_BRIDGE_FROZEN

## Provenance

- Protocol: `research/v6_m5d1c_type_number_bridge_protocol.md`, SHA256 `ca531a8ec50192f8252c2a7a980a6c5c69108f5daf89cdb6946f39c83eaa1b06`, frozen in the protocol-only commit `ff25ecee094507b2cd58782ae196d041ba01002d` before any S5 statement was read.
- Table: `research/v6_m5d1c_type_number_bridge_table.json`, commit `42589ef`.
- GitHub Actions run 36253035242; job 108434520710; head SHA 4bfc3e4a99565ee462c1e5570c6abfd14665d390.
- Artifact ID 10909038024; artifact digest sha256:fef6f48d7435ac19aa171ee9052debbc66f63fd31b9e044ee8f96ac182ee700c.
- Result commit 214b341c801193a2dfd1d192846bb123dafadcc1.
- Result JSON SHA256 a259e77c5fa9db5d6486cd26b21d4fe2184b3d3a7648e8f6b2c88e13f8c47244, byte-identical to the independent local execution.

All criteria A–G held, with 0 failure records.

## Bridge

- 22 distinct type numbers were found in S5.
- 20 were confirmed by the automated S4/S5 nomenclature cross-check, which requires `MBONnn (<compartments>)` to normalize exactly to the MaleCNS instance token.
- MBON23 and MBON28 were not confirmed, so they are not bridged.

## New signed MBON labels (S5, Rubin, Aso et al. 2024)

| Type | Label | S5 statement |
|---|---|---|
| MBON21 (γ4γ5) | REPULSIVE | "When CsChrimson is expressed in MBON21 or MBON29, flies avoid illuminated quadrants of the arena." |
| MBON29 (γ4γ5) | REPULSIVE | same statement |
| MBON33 (γ2γ3) | ATTRACTIVE | "…activation in a line for MBON33 promoted attraction to the illuminated quadrants, although this effect was observed only at the first test period." |

The MBON33 caveat is recorded with the label. In the same paper, used as memory unconditioned stimuli, MBON21 and MBON29 induced aversive memory and MBON33 induced appetitive memory (context only).

## Current admissible signs (supersede M5D1B)

| Class | Label | Types |
|---|---|---|
| DAN | APPETITIVE | PAM01, PAM02, PAM11 |
| DAN | AVERSIVE | PPL101, PPL103, PPL104, PPL106 |
| MBON | ATTRACTIVE | MBON11, MBON12, MBON33 |
| MBON | REPULSIVE | MBON05, MBON06, MBON21, MBON29 |

## Structural finding (sharpened)

Compartments with both a signed teaching DAN and a signed **plastic** (single-compartment) MBON: still **none**.

Every signed MBON that would face a signed DAN is multi-compartment, and therefore nonplastic under the M5B3B rule. In every such case the signs match the canonical valence-balance model (Aso et al. 2014b):

| MBON | Compartments | MBON label | Signed DAN | DAN label | Model prediction |
|---|---|---|---|---|---|
| MBON11 | γ1, pedc | ATTRACTIVE | PPL101 | AVERSIVE | aversive DAN depresses an approach MBON ✔ |
| MBON12 | γ2, α′1 | ATTRACTIVE | PPL103 | AVERSIVE | ✔ |
| MBON33 | γ2, γ3 | ATTRACTIVE | PPL103 (γ2) | AVERSIVE | ✔ |
| MBON21 | γ4, γ5 | REPULSIVE | PAM01 (γ5) | APPETITIVE | appetitive DAN depresses an avoidance MBON ✔ |
| MBON29 | γ4, γ5 | REPULSIVE | PAM01 (γ5) | APPETITIVE | ✔ |

The DAN and MBON labels come from different papers and experiments. That they agree with the model in all five cases is an independent consistency result, reported as a diagnostic and never used as a criterion.

**Conclusion:** the remaining blocker for a closed, valence-consistent learning loop is the M5B3B rule that freezes KC input to multi-compartment MBONs. Valence evidence is no longer the limiting factor.

## Declared limitation

The verifiers check that quotes are verbatim, name-bearing, bridged and merged correctly. They cannot check that a label's sign matches the meaning of a genuine quote. Sign semantics are audited through the recorded quotes, as declared for M5D1, M5D1B and M5D1C.

## Next authorized direction

**M5B3C: a compartment resolver for multi-compartment MBON KC input.** M5B3B said multi-compartment input stays frozen "until a separately validated synapse-level compartment resolver exists". The resolver requires opening synapse-location/ROI data under its own frozen source firewall. It is the single gate that would close the loop for MBON11, MBON12, MBON21, MBON29 and MBON33.

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED.
