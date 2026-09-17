# V6-M3D PROTOCOL — SET-VALUED 3D PASSIVE APL ELECTRICAL TRANSFER OPERATOR

**STATUS: FROZEN BEFORE ANY M3D NUMERICAL OPERATOR OUTPUT AND WHILE AMIN A1/B1/A4/B4 REMAIN NUMERICALLY BLIND.**

## Purpose
Construct the first V6 3D morphology-resolved **electrical-state** operator without fitting an optical observation model or a spatial length constant.

M3D asks only whether immutable MaleCNS APL morphology plus the already-frozen broad passive-property envelope yields a numerically well-defined and anatomically local DC electrical transfer structure.

It does not predict GCaMP, GABA release or KC inhibition.

## Fixed morphology/source
M3A2 must be PASS.

Use exactly:
- MaleCNS v1.0 APL bodies 10540 and 10977;
- D0 SWC hashes:
  - 10540: `22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f`
  - 10977: `34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf`
- the pre-V6 unique-largest-connected-component rule from `fly_mnq/v5_m4b_calibrate_kappa.py`, Git blob `b973c50c775e97fe0fe1564994e58570ed900bc7`;
- official MaleCNS syn-partners SHA256 `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07`;
- frozen KC count 4064 and raw APL↔KC row count 406552.

Coordinates/radii use the already-fixed MaleCNS scale 8 nm per source unit.

## Frozen passive envelope
The M3A literature hull remains:
- `Ra in [0.40,4.00] Ω·m`
- `Rm in [0.20,2.64] Ω·m²`

No point inside this rectangle may be selected from Prisco, Amin, Lin, V5 residuals or future market behavior.

For DC transfer, capacitance is absent from the equilibrium equations.

### Exact dimensionality reduction
For an edge with physical length L and endpoint radii r_i,r_j, assume radius changes linearly along the edge.

Axial resistance:
`Rax_ij = Ra * L / (π r_i r_j)`

so the axial conductance is:
`gax_ij = (1/Ra) * π r_i r_j / L`.

For each SWC edge, lateral frustum membrane area is:
`Aij = π (r_i+r_j) sqrt(L² + (r_i-r_j)²)`.

Assign half of Aij to each endpoint. No end-cap or soma membrane is invented.

Node leak:
`gm_i = A_i / Rm`.

Therefore the DC system can be written:
`[(1/Ra) L0 + (1/Rm) D_A] V = I`
or
`[L0 + q D_A] V = Ra I`
where
`q = Ra/Rm`.

Any **source-normalized transfer ratio** cancels the common factor Ra and depends only on q. Thus the full frozen 2D passive rectangle is represented by the exact interval:
- `q_min = 0.40/2.64 = 0.151515151515... 1/m`
- `q_max = 4.00/0.20 = 20.0 1/m`.

This reduction is algebraic, not fitted.

## Frozen q evaluation grid
For numerical qualification, use exactly 33 log-spaced q values including both endpoints:
`q_k = exp(linspace(log(q_min),log(q_max),33))`.

Do not adapt/refine the grid after outputs.

The grid is a deterministic robustness diagnostic, not a claim of exhaustive continuous optimization.

## Anatomical source and readout ensembles
Use only source-defined MaleCNS `primary_post` and the pre-existing semantic mapping:
- CA(*) → CALYX
- aL(*) → ALPHA
- a'L(*) → ALPHA_PRIME
- bL(*) → BETA
- b'L(*) → BETA_PRIME
- gL(*) → GAMMA
- PED(*) → PEDUNCLE
- everything else → OTHER.

Primary M3D compartments are:
`CALYX, ALPHA, ALPHA_PRIME, BETA, BETA_PRIME, GAMMA`.

PEDUNCLE and OTHER are reported but cannot rescue primary results.

### Unit KC→APL source
For a source compartment r:
- use every raw KC→APL synapse whose `primary_post` maps to r;
- map its APL postsynaptic xyz to the nearest node among all SWC nodes and require main-component label exactly as M3A2;
- distribute total injected current 1.0 A-equivalent dimensionlessly across main-component nodes proportional to raw source-site multiplicity.
The 1.0 absolute value is arbitrary but cancels after normalization and therefore is not a biological current claim.

### APL→KC electrical readout
For target compartment s:
- use every raw APL→KC synapse whose `primary_post` maps to s;
- map APL presynaptic xyz to its nearest main-component node;
- read the arithmetic mean node voltage over **raw output sites** (site multiplicity preserved).

For each source r and q, define:
`T[r,s,q] = mean_output_voltage(s) / mean_output_voltage(r)`.

Thus `T[r,r,q]=1` by construction when source readout is finite/positive.

No optical fluorescence or release nonlinearity is assumed.

## PN→APL calyx diagnostic
As a secondary architecture diagnostic only, reconstruct the already-qualified M0 ALPN→APL calyx sites and inject unit current proportional to those raw PN→APL site multiplicities. Read the same six APL→KC output compartments and normalize to CALYX.

This diagnostic cannot alter primary PASS/FAIL.

## Numerical integrity
For every APL and q:
- all edge lengths/radii/areas finite and positive;
- `L0 + q D_A` is symmetric positive definite up to solver numerical tolerance;
- all source/readout voltages finite;
- all raw mapped sites retain M3A2 main-component coverage 1.0;
- source normalization denominator finite and >0;
- `T[r,r]` agrees with 1 within 1e-10;
- no negative passive transfer ratio below -1e-12.

## Predeclared locality diagnostic
Without any fitted threshold, define **strict local dominance** for a primary source r at q:
`T[r,s,q] < 1` for every other primary target s != r.

Report for each APL/source:
- whether strict local dominance holds at all 33 q values;
- the worst nonlocal ratio `max_{q,s!=r} T[r,s,q]`;
- which target/q produces that maximum.

Formal primary locality classification:
- all six sources × both APLs satisfy strict local dominance at all 33 frozen q values:
  `PASS_M3D_PASSIVE_OPERATOR_AND_GRID_LOCAL_DOMINANCE`
- numerical/source integrity passes but any source violates strict local dominance:
  `PASS_M3D_PASSIVE_OPERATOR_LOCAL_DOMINANCE_NOT_ROBUST`
- source/numerical integrity fails:
  `FAIL_M3D_PASSIVE_OPERATOR_INTEGRITY`.

The second classification is not a failed source; it means morphology+passive uncertainty alone does not robustly guarantee compartment-local dominance.

## Guardrails
Forbidden:
- Amin fitted length constant;
- old V5 D2 lambda=50 µm;
- any fitted Ra/Rm point;
- an optical voltage→GCaMP map;
- release gain or KC-inhibition gain;
- per-region gain;
- changing source/readout ROI membership after outputs;
- using Prisco M2B residuals, Amin values, known V5 lobe residuals or MNQ/market outcomes.

## Consequence
A PASS constructs a qualified electrical operator only. It does not authorize Amin A1/B1 or A4/B4 unblinding unless a compatible observation bridge is independently established.

Market firewall remains CLOSED.
