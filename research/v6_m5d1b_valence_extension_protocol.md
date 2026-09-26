# V6-M5D1B — VALENCE EVIDENCE EXTENSION — TWO ADDITIONAL PINNED SOURCES

**STATUS: FROZEN BEFORE ANY TEXT OF S5 OR S6 WAS READ.** Only the article titles, first authors and years were read to identify the sources.

## Freeze record

This protocol is committed alone, before the extension table or any verifier code, on branch `claude/hello-8eabhu` of `nsar2002/test`. The public protocol-only commit is the freeze of record. Changes require a separate, dated amendment file.

## Authorization and purpose

V6-M5D1 PASS (run 36252059568; result JSON SHA256 `996070bbd217195dac39600eaa90fa5a44d3ce3902aa2ded12b2eab161c8679d`) recorded that no eligible compartment has both a signed teaching DAN and a signed plastic MBON. It named "Extend valence evidence" as the next authorized direction.

M5D1B adds two pinned independent sources and merges their findings with the frozen M5D1 table under a frozen, conservative merge rule. New evidence can fill gaps but can never override a recorded conflict. No model, reward, market or PnL outcome exists or is used.

## Pinned sources

Same repository and commit as M5D1 (`elifesciences/elife-article-xml` @ `d146492a0d8efed2fc3bb377ef9b22dde455936b`, `articles/<file>`):
- **S5** `elife-90523-v1.xml`, SHA256 `876ef708f2269ae5c7ea9743d65e4fcffb5e8efb0d69936f7715fe468e5b1f31`. Rubin, Aso et al. 2024, eLife, "New genetic tools for mushroom body output neurons in Drosophila". Additional MBON activation-valence evidence source.
- **S6** `elife-49257-v3.xml`, SHA256 `f1166b0c679009497f5c52b38cb12cfe1646375e33183c87e7376a5fa3131496`. Aso et al. 2019, eLife, "Nitric oxide acts as a cotransmitter in a subset of dopaminergic neurons to diversify memory dynamics". Additional DAN teaching-valence evidence source.

S1–S4 and the frozen M5D1 artifacts are inherited unchanged:
- M5D1 table `research/v6_m5d1_valence_source_table.json`, SHA256 `72804479baeea2c2c81f11d6344ca3b6616b7e0f2d1a60da9030fc47ae5fee42`;
- M5D1 result SHA256 `996070bb…`;
- M5D1 verifier SHA256 `e220fc4e16affa742c96b7b3857b93e6f98004f4b42bddbbb0213c3167e87a3a`;
- M5D1 amendment SHA256 `e86079975e3ec08db2a231cffc1414bfcf415dd14deec406ab787f0340e79e5a`.

## Inherited rules

Everything in the frozen M5D1 protocol and its 2026-09-26 amendment applies to S5 (MBON records) and S6 (DAN records) exactly as it applied to S2 and S1:
- label vocabularies;
- the forward-pairing timing rule;
- shared-line and line-level conflict handling;
- the exact nomenclature bridge (primary instance-token match; fallback only for a unique non-empty compartment set);
- text normalization;
- verbatim, name-bearing evidence quotes;
- context quotes;
- whitespace names;
- nomenclature-only mentions;
- the frozen name scan and inventory.

The normalization, bridge and scan functions are imported unchanged from the pinned M5D1 verifier file.

## New findings

For every one of the 21 DAN and 38 MBON records, the extension table records a `new_finding`:
- DAN records: the S6 finding;
- MBON records: the S5 finding.

Each finding has `label`, `source_names`, `bridge_rule`, `shared_line`, `evidence`, `context_quotes`, `note` and `conflict` (true only when the label is `UNRESOLVED` because of a contradiction or line-level conflict, i.e. amendment provision 2).

## Frozen merge rule

For each record, the M5D1 finding is classified first:
- signed (`APPETITIVE`/`AVERSIVE`/`ATTRACTIVE`/`REPULSIVE`);
- `NO_SIGNIFICANT_*`;
- conflict: `UNRESOLVED` whose M5D1 note cites amendment provision 2;
- gap: any other `UNRESOLVED`;
- `UNTESTED`.

The new finding is classified the same way, using its `conflict` field.

The merged label is decided in this order:
1. If either finding is a conflict → `UNRESOLVED`.
2. If the signed findings contain both signs of the same axis → `UNRESOLVED`.
3. If exactly one sign appears among the findings, and no finding is `NO_SIGNIFICANT_*` → that sign.
4. If a sign appears together with a `NO_SIGNIFICANT_*` finding → `UNRESOLVED`.
5. If there is no sign and at least one `NO_SIGNIFICANT_*` → `NO_SIGNIFICANT_*`.
6. Otherwise, if either finding is a gap → `UNRESOLVED`; else `UNTESTED`.

## Output table (authored after this freeze)

`research/v6_m5d1b_valence_extension_table.json` contains:
- `dan_records` and `mbon_records`: for each (type, token), `m5d1_label`, `new_finding` and `merged_label`;
- `inventory_s5` (MBON names found in S5 by the frozen scan) and `inventory_s6` (DAN names found in S6), with dispositions.

## Frozen verification criteria

A. **Source parity**: S1–S6 SHA256 from the pinned commit URLs, the pinned MaleCNS annotations, and all M5D1 anchors above.

B. **Completeness**:
   - exactly the 21 DAN and 38 MBON records;
   - each `m5d1_label` equals the label in the frozen M5D1 table;
   - every label is from its vocabulary.

C. **Evidence integrity** of new findings: under the inherited rules, with S6 for DAN and S5 for MBON. `conflict: true` requires label `UNRESOLVED`.

D. **Bridge integrity** of new findings: recomputed from the pinned instance tokens and M5B3B sets, using the names of the new source.

E. **No outcome contamination**: as in M5D1.

F. **Inventory completeness**: the frozen scan applied to S5 (MBON) and S6 (DAN), with the same used/unused and bridging requirements as M5D1.

G. **Merge correctness**: the verifier recomputes every `merged_label` from the frozen merge rule. Each must match.

Diagnostics only:
- merged label counts;
- per-compartment coverage, i.e. whether each eligible compartment now has both a signed gate-DAN label and a signed single-compartment MBON label;
- agreement with the valence-balance model (aversive-DAN compartments → attractive MBONs; appetitive → repulsive), reported and never enforced.

## Formal classification

- `PASS_M5D1B_VALENCE_EXTENSION_FROZEN`: A–G all true.
- `FAIL_M5D1B_VALENCE_EXTENSION_INTEGRITY`: A true, and any of B–G false.
- `BLOCKED_M5D1B_SOURCE_PARITY`: A false.

Coverage is reported, not required.

## Consequence of PASS

The merged labels supersede the M5D1 labels as the only admissible teaching and readout signs for later V6 gates. Unsigned merged labels carry no sign.

PASS does not define the reward→DAN or MBON→action mapping, select θ, or open MNQ, reward, PnL, strategy, trading or prop-firm evaluation.

## Firewalls

- MNQ/reward/PnL/trading CLOSED.
- θ not selected.
- Synapse coordinates unopened.
- Amin and M4V0 numeric values unopened.
- The PAM/PPL1 cluster approximation is not a source.
