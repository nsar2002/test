# V6-M3F0 PROTOCOL — ROBUST DIRECT-APL STIMULATION ORDINAL ELIGIBILITY

**STATUS: FROZEN BEFORE ANY AMIN A1/B1 RESPONSE VALUE IS OPENED.**

## Purpose
Determine whether the already-qualified 3D passive APL operator makes a **scale-free, intervention-location-robust ordinal prediction** for direct local APL stimulation in the horizontal and vertical mushroom-body lobes.

This gate uses only MaleCNS morphology/connectome geometry and the full frozen passive uncertainty set. It does not read Amin Figure-7 response values.

If the electrical ordering is robust enough, a later M3F1 gate may unblind only Amin A1/B1 and test direction/order. Amin A4/B4 remains the reserved primary KC-inhibition holdout.

## Published experimental semantics fixed before unblinding
Amin et al. 2020 Figure 7 column 1 (A1/B1/C1) reports APL GCaMP6f response to direct local ATP/P2X2 activation of APL.

Rows:
- A1 = horizontal-lobe stimulation;
- B1 = vertical-lobe stimulation;
- C1 = calyx stimulation.

A1/B1 each have published n=10 neurons (6 flies).

The source normalizes responses to the highest responding segment/data point. M3F0 therefore makes **only an ordinal local-vs-distant prediction**; it does not predict fluorescence magnitude.

Calyx stimulation is not part of primary M3F0 because the paper documents a P2X2/ATP calyx confound in related experiments; C may be reported only as secondary anatomy.

## Frozen source identities
Use exact M3D/M3A2 sources:
- MaleCNS v1.0 syn-partners SHA256 `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07`;
- brain.npz SHA256 `cc9bd1ecd00bd703a6fa648bc6ad145c93c7c1ee53debdcc9ce0d1f4305e6aca`;
- APL10540 SWC SHA256 `22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f`;
- APL10977 SWC SHA256 `34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf`.

Historical unique-largest-component rule from M3A2 remains mandatory.

## Frozen region aggregation
Use the pre-existing semantic mapping:
- C = CALYX;
- V = ALPHA ∪ ALPHA_PRIME;
- H = BETA ∪ BETA_PRIME ∪ GAMMA.

No region may be added, removed or reassigned after output.

## Source-defined morphology partition
For each APL, construct labeled APL anchor sites from **all raw APL↔KC synapse sites** in C/H/V:
- KC→APL row: use APL postsynaptic xyz and row `primary_post`;
- APL→KC row: use APL presynaptic xyz and row `primary_post`.

Map semantic ROI to C/H/V using the frozen aggregation above.

Every main-component SWC node is assigned to the label of its nearest C/H/V anchor site in Euclidean MaleCNS source coordinates.

No distance threshold is allowed.

Report:
- C/H/V node counts;
- nearest-anchor distance distribution/max;
- any exact nearest-distance tie across different labels.

If any exact cross-label nearest tie occurs, those nodes are classified AMBIGUOUS and primary robust eligibility fails rather than choosing a favorable tie-break.

## Frozen electrical operator
Use exact M3D steady passive discretization and exact 33-point log q-grid:
`q=Ra/Rm ∈ [0.15151515151515155,20] 1/m`.

Because only normalized/source-order transfer is tested, absolute Ra cancels as in M3D.

## Frozen readouts
For each APL, build three normalized raw-site readout weight vectors from APL→KC output sites:
- w_C = raw output-site multiplicity in CALYX;
- w_V = raw output-site multiplicity in ALPHA/ALPHA_PRIME;
- w_H = raw output-site multiplicity in BETA/BETA_PRIME/GAMMA.

Weights within each group sum to 1.

For each q and group G in {C,V,H}, solve the adjoint:
`[L0 + q D_A] phi_G = w_G`.

By symmetry, `phi_G[j]` is the mean group-G electrical readout caused by a unit source at node j, up to a common positive scale.

## Primary worst-case ordinal condition
For **every non-ambiguous source node** assigned H, every q, and each APL:
- `phi_H[j] > phi_C[j]`
- `phi_H[j] > phi_V[j]`.

For **every non-ambiguous source node** assigned V:
- `phi_V[j] > phi_C[j]`
- `phi_V[j] > phi_H[j]`.

This pointwise condition is deliberately stronger than needed. If it passes, every nonnegative direct-stimulation source distribution supported entirely within the corresponding H or V partition also preserves local dominance by linearity.

No margin threshold is introduced. Strict inequality is the complete rule.

## Classification
`PASS_M3F0_HV_DIRECT_STIM_ORDINAL_PREDICTION_ELIGIBLE`
only if:
- source/hash/main-component integrity passes;
- no ambiguous cross-label nearest-anchor node exists;
- both APLs satisfy all H and V pointwise inequalities at all 33 q values.

Otherwise:
`NO_ROBUST_M3F0_HV_DIRECT_STIM_ORDINAL_PREDICTION`.

A non-pass does not falsify local APL biology; it means MaleCNS + the broad passive uncertainty + source-location uncertainty are insufficient for a preregistered A1/B1 ordinal prediction.

## Guardrails
Forbidden:
- Amin A1/B1/A4/B4 response numbers;
- Amin fitted spatial length;
- selecting only one APL;
- restricting q using M3D/M3E1 outcomes;
- selecting a source node after seeing transfer;
- fitting an optical mapping;
- market/MNQ/reward/PnL/strategy output.

## Consequence of PASS
Freeze deterministic model prediction:
- horizontal ATP: H response rank > C and V;
- vertical ATP: V response rank > C and H.

Only then may M3F1 open A1/B1 response values for a direction-only test. A4/B4 remains blind.

Market firewall remains CLOSED.
