# V6-M3F0 PROTOCOL — FEMALE FLYWIRE v783 APL MORPHOLOGY SOURCE / IDENTITY AUDIT

**STATUS: FROZEN BEFORE READING ANY APL ROW FROM THE PINNED FLYWIRE ANNOTATION TABLE AND BEFORE FETCHING ANY FEMALE APL SKELETON.**

## Purpose
Replace the male-MaleCNS/female-electrophysiology geometry mismatch with a source-defined **female adult fly brain** APL morphology, without choosing neurons or skeletons from passive/electrophysiology outcomes.

This gate is identity/source/structure only. It does not fit Ra/Rm, compare input resistance, open Amin values, or inspect market data.

## Canonical female connectome
Use FlyWire / FAFB public materialization `783`, the Female Adult Fly Brain release.

Systematic annotation source:
- repository: `flyconnectome/flywire_annotations`
- pinned Git commit: `8587524c1748ce5ef2080822a2fc890fc03bf597`
- file: `supplemental_files/Supplemental_file1_neuron_annotations.tsv`
- pinned Git blob SHA: `afea3e15a5671f5da0b9f7dd2e932d328c3b57a0`
- pinned file size from Git tree: `31,718,505` bytes.

The repository documentation states:
- `root_id` is the neuron ID in FlyWire release 783;
- `soma_x/y/z` are soma coordinates in 4×4×40 nm voxel space;
- `cell_type` is the systematic hierarchical type annotation;
- `side` is soma side for brain-intrinsic neurons;
- `dimorphism`, `matching_notes`, and `supertype` provide cross-sex/MaleCNS correspondence metadata.

No Codex community-label mixture is allowed for identity selection.

## Prospective APL selection rule
After source bytes are SHA256-locked, select **all and only** rows satisfying:
`cell_type == "APL"`
after exact whitespace trimming; comparison is case-sensitive.

Required qualification:
1. exactly two rows;
2. two distinct `root_id` values;
3. `side` yields exactly one left and one right neuron (accept canonical source spellings `left/right` or `L/R`, normalized only for comparison);
4. `soma_x,y,z` are all finite for both;
5. neither row has `status == "outlier_seg"`;
6. `cell_type` is exactly APL for both;
7. report but do not gate on `dimorphism`, `matching_notes`, `supertype`, `synonyms`, `top_nt`, `cell_class`, `super_class`.

If exact `cell_type=="APL"` does not produce the required bilateral pair, classification is:
`BLOCKED_M3F0_FEMALE_APL_IDENTITY_AMBIGUOUS`.
No fuzzy search, synonym expansion, community label, morphology similarity, MaleCNS match, or electrophysiology outcome may rescue it.

## Female skeleton source
For each prospectively selected root ID use the precomputed FlyWire v783 skeleton source exposed by `fafbseg`:
`https://flyem.mrc-lmb.cam.ac.uk/flyconnectome/flywire_skeletons_783/{root_id}`.

The `fafbseg` implementation for v783 supplies these as Neuroglancer precomputed skeletons with:
- identity transform;
- vertex attribute `radius` float32;
- units `1 nm`.

For every selected root ID:
1. download and SHA256-lock the exact raw precomputed skeleton bytes;
2. parse using a pinned open-source `navis/fafbseg` stack or an equivalent deterministic Neuroglancer-skeleton parser;
3. no reskeletonization from meshes is allowed;
4. no alternate root/version may be substituted after morphology output.

## Frozen skeleton structural audit
For each female APL:
- require >=100 nodes;
- node coordinates finite;
- radii finite and strictly positive;
- exactly one connected component after parsing;
- exactly one rooted tree / `edges = nodes-1`;
- no self-edge;
- no duplicate undirected edge;
- all nodes reachable from the root;
- all edge lengths finite and >0;
- report node count, root/node IDs as represented by parser, coordinate min/max in nm, radius min/median/max in nm, total cable length in µm.

If the public precomputed skeleton format is an unrooted tree but structurally connected with `edges=nodes-1`, a deterministic root may **not** be invented in M3F0. Report `root_semantics_unavailable` and classify structure as connected-tree qualified for DC cable use only. A later dynamic/root-dependent model would need a new root gate.

## Soma-to-skeleton correspondence
Convert annotation soma coordinates:
`[soma_x*4, soma_y*4, soma_z*40] nm`.

Map each source-defined soma coordinate to the nearest skeleton node and report:
- nearest-node distance in nm and µm;
- nearest-node radius;
- node identifier/index.

No post-hoc distance threshold is introduced in M3F0. Finite mapping is required.

## PASS
`PASS_M3F0_FEMALE_FLYWIRE_APL_MORPHOLOGY_SOURCE`
only if:
- exact pinned annotation source is acquired;
- prospective exact-type selection yields one left + one right APL;
- both exact v783 precomputed skeletons are acquired and hashed;
- both skeletons satisfy the connected-tree DC structure audit;
- source-defined soma coordinates map finitely to both skeletons.

## Guardrails
Forbidden:
- using M3D locality outcomes to select a female APL;
- selecting the female neuron closest to MaleCNS morphology;
- using input resistance to choose a skeleton or hemisphere;
- using Amin/Prisco response values;
- applying a morphology scaling factor;
- mirroring one hemisphere to replace the other;
- MNQ/reward/PnL/strategy/prop-firm inspection.

## Consequence
A PASS authorizes a separately preregistered **same-sex female morphology × female Chen electrophysiology** passive compatibility/identifiability gate.

It does not itself narrow Ra/Rm or identify an optical/release bridge.

Amin A1/B1/A4/B4 remains numerically BLIND. Market firewall remains CLOSED.
