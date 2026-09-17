# V6-M3F0B PROTOCOL — FEMALE FLYWIRE v783 ZENODO SWC REPRESENTATION AUDIT

**STATUS: FROZEN BEFORE READING THE PARQUET SCHEMA OR ANY APL ROW FROM THE ZENODO SKELETON FILE.**

## Purpose
Test the single independently published alternative female FlyWire v783 skeleton representation after M3F0 showed that the fast public precomputed skeletons contain thousands of zero-radius vertices and therefore fail the preregistered passive-cable geometry requirement.

This gate is representation/source validation only. It cannot inspect electrophysiology or passive-model agreement.

## Identity is already immutable
Reuse exactly the two APL root IDs selected prospectively in M3F0 from the pinned systematic annotation table:
- left: `720575940624547622`
- right: `720575940613583001`.

No other root ID may be substituted.

## Canonical alternative skeleton source
Schlegel et al., Nature 2024 supplemental dataset:
- Zenodo record/version: `10.5281/zenodo.10877326`, v2;
- exact file: `sk_lod1_783_healed_ds2.parquet`;
- source-published MD5: `a4c104776f33ec539ef859064c4de3df`;
- direct source URL:
  `https://zenodo.org/records/10877326/files/sk_lod1_783_healed_ds2.parquet?download=1`.

The publisher describes this file as SWC-format skeletons for all FlyWire neurons, generated from LOD1 meshes and 2× downsampled, with coordinates in nanometres; all root IDs refer to FlyWire release 783.

The complete source file must be downloaded and the published MD5 verified before any APL extraction. Also record SHA256 of the exact downloaded bytes.

## Frozen schema qualification
Before extracting values, inspect only Parquet metadata/schema.

Required deterministic navis/SWC semantics:
- a neuron/root-ID column recognized as `neuron` or `fragment_id`;
- node identifier: `node_id` or neurarrow `sample_id`;
- finite spatial fields `x,y,z`;
- `radius`;
- a tree-parent field `parent_id`, OR an equivalent publisher/navis schema that deterministically reconstructs parent relations without morphology fitting.

If the exact APL rows cannot be selected by the immutable root IDs or SWC parent relations cannot be recovered deterministically:
`BLOCKED_M3F0B_ZENODO_SWC_SCHEMA`.

No column may be chosen because it yields better electrophysiology agreement.

## Frozen extraction
Read only rows belonging to the two immutable APL root IDs using Parquet filtering on the source identity column.

For each APL require:
1. at least 100 nodes;
2. exactly one row per node ID;
3. finite x/y/z;
4. finite and **strictly positive radius for every node**;
5. exactly one tree root after parent reconstruction;
6. every non-root parent exists within the same neuron;
7. no self-parent;
8. no cycle;
9. one connected component;
10. `edges = nodes-1`;
11. all parent-child edge lengths finite and >0.

Report:
- node/edge counts;
- root ID;
- radius min/median/max in nm;
- coordinate ranges;
- total cable length in µm;
- any duplicate/missing-parent/cycle/component diagnostics.

## Soma correspondence
Use the already-pinned M3F0 source soma coordinates:
- left root 720575940624547622:
  `[333408,188960,148040] nm`;
- right root 720575940613583001:
  `[717664,204160,120560] nm`.

Map each to the nearest Zenodo skeleton node. Report nearest distance and radius. No new distance threshold.

## Cross-representation diagnostics
After both representations are independently qualified/failed, report only descriptive parity:
- Zenodo vs fast-precomputed node count;
- total cable length ratio;
- soma nearest-node distance;
- radius summary.

Do not force byte/node identity because the Zenodo skeletons are explicitly LOD1-derived and 2× downsampled.

## PASS / FAIL
PASS:
`PASS_M3F0B_FEMALE_ZENODO_SWC_CABLE_GEOMETRY`
only if the complete source hash passes and BOTH immutable APL skeletons satisfy all frozen SWC/radius/tree criteria.

FAIL:
`FAIL_M3F0B_FEMALE_ZENODO_SWC_CABLE_GEOMETRY`
if the schema is interpretable but either APL has nonpositive/nonfinite radii or invalid tree geometry.

BLOCKED:
`BLOCKED_M3F0B_ZENODO_SWC_SCHEMA`
if deterministic identity/SWC extraction is not possible.

## Guardrails
No:
- radius imputation/interpolation/epsilon;
- mesh reskeletonization;
- morphology scale fit;
- alternate FlyWire root;
- hemisphere substitution/mirroring;
- input-resistance value;
- Ra/Rm selection;
- Amin/Prisco outcome;
- MNQ/reward/PnL/strategy result.

## Consequence
Only a PASS authorizes a same-sex female morphology × female Chen electrophysiology passive gate.

Amin A1/B1/A4/B4 remains numerically BLIND. Market firewall remains CLOSED.
