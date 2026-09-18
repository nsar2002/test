# V6-M3F4 PROTOCOL — PUBLISHED-LOCATION APL DIRECT-STIMULATION ELIGIBILITY

**STATUS: FROZEN BEFORE M3F4 ELECTRICAL OUTPUT AND BEFORE ANY AMIN A1/B1 RESPONSE VALUE IS OPENED.**

## Why this is a new model version
M3F2B is permanently `NO_ROBUST` for the deliberately stronger proposition that **any** node anywhere inside an entire official horizontal or vertical neuropil could serve as the local ATP source.

The published Amin et al. 2020 experiment is more specific and was known independently of M3F2B electrical output:
- the ATP/GABA pipette was positioned at the **tip of the vertical lobe**;
- for horizontal-lobe stimulation it was positioned **close to the junction point in the horizontal lobe**;
- the experimental backbone was discretized at fixed **20 µm** spacing.

M3F4 is therefore a final, source-semantics refinement of stimulation support, not a selection based on M3F2B violating node IDs or margins.

No M3F2B violating node ID, q, margin or readout may enter M3F4 source construction.

## Hard prerequisite
M3F2A must be `PASS_M3F2A_OFFICIAL_ROI_SOURCE_MAPPING`.

M3F2B's failure does not alter source geometry; it only proves whole-lobe arbitrary-source robustness is too strong.

## Frozen morphology/operator
Use exactly M3A2/M3D:
- APL10540 and APL10977 historical main components;
- exact M3D DC passive discretization;
- exact 33-point q grid over `Ra/Rm=[0.15151515151515155,20]` 1/m;
- no q/Ra/Rm restriction.

## Exact official labels
Use only exact direct `fullbrain-roi-v4` labels already qualified by M3F2A, side-specific:
- C: `CA(side)`
- vertical sublobes: `aL(side)`, `a'L(side)`
- horizontal sublobes: `bL(side)`, `b'L(side)`, `gL(side)`.

APL10540 uses right-side labels; APL10977 left-side labels.

Background/outside or other neuropils cannot enter source support.

## Tree-geodesic landmarks
All distances below are physical cable geodesic distances on the qualified main-component SWC, using the already-fixed 8 nm/source-unit geometry.

No Euclidean shortcut, nearest synapse, electrical response, or Amin response is used.

### Vertical-tip landmarks
For each vertical sublobe separately (`aL`, `a'L`):
1. compute each node's tree-geodesic distance to the nearest official-H node (union of `bL,b'L,gL`);
2. within that exact vertical sublabel, find the maximum of that distance;
3. every exactly tied maximizer is a vertical-tip landmark.

The B-source support is the union, across `aL` and `a'L`, of nodes carrying the same exact vertical sublabel whose tree-geodesic distance to any corresponding tip landmark is **<=20 µm**.

This 20-µm scale is fixed from the published backbone segment spacing, not from model output.

### Horizontal-junction landmarks
For each horizontal sublobe separately (`bL`, `b'L`, `gL`):
1. compute each node's tree-geodesic distance to the nearest official-V node (union of `aL,a'L`);
2. within that exact horizontal sublabel, find the minimum of that distance;
3. every exactly tied minimizer is a horizontal-junction landmark.

The A-source support is the union, across `bL,b'L,gL`, of nodes carrying the same exact horizontal sublabel whose tree-geodesic distance to any corresponding junction landmark is **<=20 µm**.

No component may be dropped after inspection. Every expected exact sublabel must contribute >=1 landmark and >=1 support node or the gate is source-BLOCKED.

## Readout
Use the same frozen raw APL→KC output-site multiplicity weights as M3F2B:
- C = CALYX
- V = ALPHA + ALPHA_PRIME
- H = BETA + BETA_PRIME + GAMMA.

At each frozen q solve:
`[L0+q D_A] phi_G = w_G`, G∈{C,V,H}.

## Frozen pointwise support criterion
For every horizontal-junction support node, both APLs and all 33 q:
- `phi_H > phi_C`
- `phi_H > phi_V`.

For every vertical-tip support node:
- `phi_V > phi_C`
- `phi_V > phi_H`.

No margin threshold.

A complete pointwise PASS guarantees the ordinal prediction for every nonnegative stimulation distribution wholly supported inside the preregistered published-location neighborhood.

## Classification
All pointwise inequalities pass:
`PASS_M3F4_PUBLISHED_LOCATION_HV_ORDINAL_ELIGIBILITY`.

Any inequality fails:
`NO_ROBUST_M3F4_PUBLISHED_LOCATION_HV_ORDINAL_PREDICTION`.

Missing expected source label/landmark/support:
`BLOCKED_M3F4_PUBLISHED_LOCATION_SOURCE_MAPPING`.

Report only support/landmark counts and worst electrical diagnostics. Do not alter support after output.

## Final-source-model rule
M3F4 is the **final** source-support refinement allowed for Amin A1/B1 under this passive operator.

If M3F4 fails:
- no further tip width, percentile, erosion, dilation, q restriction, node trimming or stimulation-distribution variant may be tried on A1/B1;
- A1/B1 remains blind for this architecture;
- any redesigned architecture requires a new independent holdout.

## Guardrails
Forbidden:
- M3F2B violating node IDs/margins in source construction;
- Amin A1/B1/A4/B4 response values;
- Amin fitted passive length;
- red-dye response amplitudes to tune support;
- q/Ra/Rm selection;
- optical mapping;
- market/MNQ/reward/PnL/strategy output.

Market firewall remains CLOSED.
