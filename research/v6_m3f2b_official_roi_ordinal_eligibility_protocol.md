# V6-M3F2B PROTOCOL — OFFICIAL-ROI DIRECT-APL ELECTRICAL ELIGIBILITY

**STATUS: FROZEN BEFORE M3F2A RESULT AND BEFORE ANY M3F2B ELECTRICAL OUTPUT.**

## Purpose
Test whether direct APL stimulation restricted by the independent official MaleCNS neuropil segmentation yields a robust horizontal/vertical local electrical ordering across the complete frozen passive uncertainty set.

M3F0 remains permanently NO_ROBUST under nearest-synapse Voronoi support. M3F2B is a new source representation, not a relaxation of M3F0.

## Hard prerequisite
Execute only if M3F2A returns:
`PASS_M3F2A_OFFICIAL_ROI_SOURCE_MAPPING`.

Otherwise M3F2B is BLOCKED and no Amin response is opened.

## Frozen morphology/operator
Use exactly M3D/M3A2:
- APL10540 and APL10977 historical main components;
- exact M3D DC passive discretization;
- exact 33-point q grid spanning `Ra/Rm=[0.15151515151515155,20] 1/m`;
- no q truncation or passive-parameter fit.

## Official stimulation support
Use exact M3F2A direct volume labels, with the already frozen source-name semantics:
- C = calyx/CA labels;
- V = alpha + alpha-prime lobe labels;
- H = beta + beta-prime + gamma lobe labels.

Primary H source set = every main-component SWC node whose exact official ROI voxel label maps H.
Primary V source set = every main-component SWC node whose exact official ROI voxel label maps V.

Nodes labeled C, OUTSIDE/background or other neuropils are not stimulation-source candidates for the corresponding H/V intervention.

No nearest-synapse assignment, dilation, erosion, geodesic expansion, source-site selection, boundary trimming or manual removal is permitted.

## Readout
Use exact raw APL→KC output-site multiplicity readout weights:
- C = CALYX;
- V = ALPHA + ALPHA_PRIME;
- H = BETA + BETA_PRIME + GAMMA.

Each group's raw output weights sum to 1.

At each frozen q solve the adjoint:
`[L0+qD_A] phi_G = w_G`, G∈{C,V,H}.

## Frozen worst-case pointwise criterion
For every official-H source node j, every q and both APLs:
- `phi_H[j] > phi_C[j]`
- `phi_H[j] > phi_V[j]`.

For every official-V source node:
- `phi_V[j] > phi_C[j]`
- `phi_V[j] > phi_H[j]`.

No margin threshold.

Because the passive system is linear, a full pointwise PASS guarantees the same ordering for every nonnegative stimulation distribution supported entirely inside the corresponding official ROI set.

## Classification
`PASS_M3F2B_OFFICIAL_ROI_HV_ORDINAL_ELIGIBILITY`
only if all H and V pointwise inequalities pass for both APLs and all 33 q values.

Otherwise:
`NO_ROBUST_M3F2B_OFFICIAL_ROI_HV_ORDINAL_PREDICTION`.

The gate must report:
- official H/V source-node counts;
- violating node/q count;
- worst local-minus-best-distant margin, q, source node ID and distant group;
- q-specific minimum margin.

No node may be removed after inspection.

## Guardrails
Forbidden:
- Amin A1/B1/A4/B4 response values;
- selecting official labels based on electrical results;
- q/Ra/Rm restriction;
- source-node trimming;
- optical mapping;
- Amin fitted length;
- market/MNQ/reward/PnL/strategy outputs.

A PASS only freezes an ordinal model prediction for a separately preregistered A1/B1 validation. It is not an optical magnitude validation.

Market firewall remains CLOSED.
