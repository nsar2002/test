# V6-M3F2A PROTOCOL — OFFICIAL MALECNS NEUROPIL-ROI SOURCE MAPPING AUDIT

**STATUS: FROZEN BEFORE READING fullbrain-roi-v4 LABEL METADATA OR SAMPLING APL NODES.**

## Purpose
Determine whether the official MaleCNS brain neuropil volume can directly provide deterministic anatomical C/H/V membership for APL skeleton nodes, without nearest-synapse interpolation.

M3F0 remains a permanent NO_ROBUST result under its frozen nearest-raw-synapse Voronoi support definition. M3F2A does not change or rescue M3F0; it audits a distinct independently released anatomical source representation.

No electrical transfer criterion is part of M3F2A.

## Authoritative sources
MaleCNS official release:
- neuropil segmentation: `precomputed://gs://flyem-male-cns/rois/fullbrain-roi-v4`;
- described by the official MaleCNS release as a brain neuropil compartment segmentation initialized from JRC2018M ROIs and manually refined;
- release resolution documented as 256 nm isotropic.

APL skeletons remain exact M3A2 sources:
- 10540 SWC SHA256 `22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f`;
- 10977 SWC SHA256 `34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf`;
- historical unique-largest-component rule remains unchanged.

## Frozen metadata audit
Before sampling:
1. acquire and hash the official precomputed `info` metadata;
2. resolve the source-provided segment-properties/name mapping, if exposed by the volume metadata;
3. require exact voxel resolution to be available;
4. require a deterministic mapping from label ID to source-defined neuropil name.

If source label names cannot be resolved from official metadata without manually inventing a mapping:
`BLOCKED_M3F2A_ROI_LABEL_METADATA`.

## Coordinate mapping
SWC coordinates are in MaleCNS EM coordinates with 8 nm/source-unit scale.

Node physical position in nm is:
`p_nm = 8 * p_swc`.

ROI voxel lookup must use the volume's own precomputed scale metadata (resolution and voxel_offset), preferably through CloudVolume/TensorStore rather than hand-assuming zero offset.

No affine registration, nearest ROI search, dilation, erosion, gap filling or distance cutoff is allowed.

## Frozen anatomical grouping
Only source label names that unambiguously match these mushroom-body compartments are eligible:

### C
- calyx / CA source-defined neuropil labels.

### V
- alpha lobe / alpha-prime lobe source-defined neuropil labels.

### H
- beta lobe / beta-prime lobe / gamma lobe source-defined neuropil labels.

The mapping from exact source label strings to C/V/H must be emitted before any electrical operator is loaded.

PEDUNCLE, OTHER, background/unlabeled and any non-MB label remain OUTSIDE.

No source label may be reassigned based on M3F0 violations or future Amin agreement.

## Main-component node audit
For each APL:
- sample every M3A2 main-component node exactly at its physical coordinate;
- report counts by exact source neuropil label;
- report aggregate C/V/H/OUTSIDE counts and fractions;
- require at least 100 labeled main-component nodes in each C, V and H aggregate;
- report any failed/out-of-bounds lookup.

Do not discard OUTSIDE nodes; report them transparently.

## Synapse consistency diagnostic
Using exact official MaleCNS APL↔KC raw sites:
- sample each raw APL postsynaptic/presynaptic site in the ROI volume;
- compare source volume label with the already-source-defined `primary_post` semantic region C/V/H where applicable;
- report exact agreement/confusion counts.

This is diagnostic only; no post-hoc threshold is introduced.

## Classification
`PASS_M3F2A_OFFICIAL_ROI_SOURCE_MAPPING`
only if:
- official metadata and label names resolve deterministically;
- both SWC sources pass identity/main-component checks;
- node lookup is deterministic and in-bounds;
- each APL has >=100 nodes in C, V and H.

Otherwise classify BLOCKED/FAIL by the failed source-integrity condition.

## Guardrails
Forbidden:
- Amin A1/B1/A4/B4 response values;
- selecting nodes using M3F0 transfer violations;
- nearest-synapse ROI assignment;
- morphology dilation or manual mask editing;
- q/Ra/Rm selection;
- electrical transfer PASS/FAIL;
- market/MNQ/reward/PnL/strategy output.

A PASS only establishes an independent source-defined stimulation-support representation. A separately frozen M3F2B would be required before any electrical eligibility calculation.

Market firewall remains CLOSED.
