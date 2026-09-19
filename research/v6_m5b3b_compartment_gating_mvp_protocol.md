# PUBLIC EXECUTION MIRROR

Canonical private frozen protocol commit: `9fc5b987d0c897dc9b3285b33c955cf003def9bd`.

# V6-M5B3B — PROSPECTIVE DAN/MBON COMPARTMENT-GATING MAP FOR THE LEARNING MVP

**STATUS: FROZEN BEFORE M5B3B EXECUTION.**

## Purpose

M5B3A established complete source identity labels for the 340 DANs and 97 MBONs. M5B3B converts established adult-mushroom-body nomenclature into a deterministic compartment map and defines the first unambiguous set of KC→MBON edges that may become plastic in the MVP.

The key conservative rule is prospective: **aggregate KC→MBON edges are plastic only when the target MBON has dendritic input in exactly one canonical learning compartment.** Multi-compartment MBON KC-input remains frozen until a separately validated synapse-level compartment resolver exists.

This avoids falsely allowing dopamine in one compartment to modify KC→MBON synapses located in another compartment.

## Independent biological basis

Li et al. 2020/2021, eLife 9:e62576:
- MBON dendrites and DAN terminals define 15 lobe compartments;
- dopamine/KC coincidence modifies KC→MBON synapses in the relevant compartment;
- adult MB nomenclature encodes compartment innervation in DAN/MBON names;
- PPL1 and PAM neurons provide localized lobe modulation.

Takemura et al. 2017, eLife 6:e26975:
- KC→MBON, KC→DAN and DAN→MBON connections are present;
- only a small minority of KC→MBON synapses have direct DAN synaptic contact, so direct triadic DAN contact is NOT required for a compartmental dopamine gate.

Scheffer et al. 2020, eLife 9:e57443 naming table:
- MB-associated DAN types are PAM01–PAM15 and PPL101–PPL106;
- PPL107/108 and PPL201–PPL204 are dopaminergic classes but are not part of that MB-associated DAN type block.

Virtual Fly Brain / FlyBase ontology is used only to resolve nomenclature details already encoded in the established type names, including:
- PPL101 = gamma1 + pedunculus-core innervation;
- PPL106 = alpha3;
- MBON input-vs-output arrow semantics.

No market result or M5B2 edge strength informed the map.

## Canonical learning-compartment vocabulary

Source-native ASCII labels:
- gamma: `y1,y2,y3,y4,y5`
- alpha: `a1,a2,a3`
- beta: `B1,B2`
- alpha-prime: `a'1,a'2,a'3`
- beta-prime: `B'1,B'2`
- distal pedunculus core: `pedc`

The 15 lobe compartments are the first 15 labels above. `pedc` is retained separately because published adult-MB anatomy treats it as an additional KC/MBON/DAN learning region.

Layer/subzone suffixes (a,m,p,d,s,c and combinations such as `a2sc`, `a2p3p`, `B'2mp`) do not create new top-level learning compartments.

## Frozen fast-MB DAN inclusion

Only these exact DAN types participate in the fast compartment gate:
- `PAM01` through `PAM15`
- `PPL101` through `PPL106`.

All other class==DAN bodies remain in the connectome but do not provide the fast KC→MBON learning gate in this MVP.

## Frozen DAN type → learning-compartment map

- PPL101 → {y1, pedc}
- PPL102 → {y1}
- PPL103 → {y2, a'1}
- PPL104 → {a'3}
- PPL105 → {a'2, a2}
- PPL106 → {a3}
- PAM01 → {y5}
- PAM02 → {B'2}
- PAM03 → {B2, B'2}
- PAM04 → {B2}
- PAM05 → {B'2}
- PAM06 → {B'2}
- PAM07 → {y4}
- PAM08 → {y4}
- PAM09 → {B1}
- PAM10 → {B1}
- PAM11 → {a1}
- PAM12 → {y3}
- PAM13 → {B'1}
- PAM14 → {B'1}
- PAM15 → {y5, B'2}

For PAM07 `y4<y1y2`, y4 is the DAN axonal/modulatory compartment; y1/y2 describe the opposite arbor side of the arrow and are not learning gates here.

For PAM09 `B1ped`, B1 is used for the canonical lobe gate. The generic `ped` suffix is not silently equated to `pedc`. Only PPL101 receives the explicit pedc mapping because the external ontology/published nomenclature identifies PPL101 as gamma1-pedc.

## Frozen MBON type/body → dendritic learning-compartment map

The region before `>` in an MBON name is the dendritic/input region. The following exact mappings are frozen from M5B3A source instances and published nomenclature:

- MBON01 → {y5, B'2}
- MBON02 → {B2, B'2}
- MBON03 → {B'2}
- MBON04 → {B'2}
- MBON05 → {y4}
- MBON06 → {B1}
- MBON07 → {a1}
- MBON09 → {y3, B'1}
- MBON10 → {B'1}
- MBON11 → {y1, pedc}
- MBON12 → {y2, a'1}
- MBON13 → {a'2}
- MBON14 → {a3}
- MBON15 → {a'1}
- MBON15-like → {a'1, a'2}
- MBON16 → {a'3}
- MBON17 → {a'3}
- MBON17-like → {a'2, a'3}
- MBON18 → {a2}
- MBON19 → {a2, a3}
- MBON20 → {y1, y2}
- MBON21 → {y4, y5}
- MBON22 → {}  [calyx; outside lobe/pedc fast learning map]
- MBON23 → {a2}
- MBON24 → {B2, y5}
- MBON25 → {y1, y2}
- MBON26 → {B'2}
- MBON27 → {y5}
- MBON28 → {a'3}
- MBON29 → {y4, y5}
- MBON30 → {y1, y2, y3}
- MBON31 → {a'1}
- MBON32 → {y2}
- MBON33 → {y2, y3}
- MBON34 → {y2}
- MBON35 → {y2}

### Body-specific MBON25-like rule

M5B3A showed MBON25-like source instances are not uniform:
- instance containing exactly `(y2)` → {y2}
- instance containing `(y1y2)` → {y1,y2}.

This body-specific source label controls the map; do not force a type-level union.

## Frozen MVP plastic-edge eligibility

A KC→MBON aggregate edge is **MVP-plastic-eligible** iff:
1. pre body is exact M5B1 KC;
2. post body is exact M5B1 MBON;
3. the MBON body maps to exactly one canonical compartment in the rule above;
4. at least one included fast-MB DAN body maps to that same compartment.

No direct DAN→that MBON edge is required.
No edge-weight threshold is applied.

For each eligible KC→MBON edge, record the complete set of same-compartment DAN body IDs as its *possible teaching-gate population*. This is an anatomical gating set only; it does not yet define reward sign, DAN activity, or update amplitude.

Multi-compartment MBON KC→MBON edges remain **present but frozen nonplastic**.
MBON22 calyx KC→MBON edges remain present but frozen nonplastic.

## Qualification

`PASS_M5B3B_COMPARTMENT_GATING_MVP_QUALIFIED` requires:

A. exact M5B3A/M5B2 prerequisite classifications;
B. every included PAM01–15/PPL101–106 body maps through its exact type;
C. every exact MBON body maps according to the frozen table/body-specific rule;
D. every single-compartment MBON body has at least one included DAN gate in the same compartment;
E. at least one eligible plastic KC→MBON edge exists in each of the three major lobe systems:
   - gamma;
   - alpha/beta;
   - alpha-prime/beta-prime;
F. all eligible edges are a strict subset of exact M5B2 KC→MBON edges;
G. no weight/performance/market criterion changes eligibility.

Otherwise classify `FAIL_M5B3B_COMPARTMENT_GATING_MVP` or `BLOCKED_M5B3B_SOURCE_PARITY`.

## Consequence of PASS

PASS authorizes M5C to freeze and unit-test a dopamine-gated KC→MBON plasticity chronology on this eligible edge set using synthetic/non-market event streams.

PASS does NOT authorize market reward yet.

## Firewalls

- MNQ/reward/PnL/trading CLOSED.
- learning-rate magnitude not selected.
- reward valence/sign not assigned to DAN types.
- synapse coordinates unopened.
- multi-compartment KC→MBON edges nonplastic.
- Amin numeric values unopened.
- M4V0 numeric values unopened.
