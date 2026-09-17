# V6-M3E0 PROTOCOL — APL SOMA-LOCATION / CROSS-SEX SOURCE-BRIDGE AUDIT

**STATUS: FROZEN BEFORE READING THE APL 10540/10977 somaLocation VALUES.**

## Purpose
Determine whether official MaleCNS v1.0 annotations contain a source-defined soma location for both APL neurons that can be mapped deterministically to the already-qualified M3A2 main-component skeleton.

This gate only establishes geometry/schema eligibility for a later input-resistance falsification test. It does NOT calibrate Ra/Rm.

## Source identity
Use:
- official MaleCNS v1.0 body annotations SHA256 `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`;
- official APL SWC hashes frozen in M3A2;
- body IDs 10540 and 10977.

## Frozen criteria
For each APL:
1. exactly one annotation row exists for the body ID;
2. `somaLocation` is present and parses to one finite xyz coordinate;
3. `flywireType` is non-empty, providing the source-defined female-connectome type match field used by MaleCNS;
4. map somaLocation to the nearest node among the complete SWC;
5. that nearest node must belong to the historical M3A2 unique-largest main component;
6. report nearest-node distance in source units and micrometres, but **do not introduce an after-the-fact distance threshold**;
7. report somaSide/rootSide/type/class/flywireType/mancType when present, without using these fields to select a different skeleton component.

## Classification
All criteria for both APLs:
`PASS_M3E0_SOURCE_DEFINED_APL_SOMA_MAPPING`.

Otherwise:
`FAIL_M3E0_APL_SOMA_MAPPING_SOURCE`.

## Cross-sex interpretation fixed in advance
The 2026 adult APL whole-cell recordings used mated female flies, while MaleCNS v1.0 is male.

Therefore even an M3E0 PASS does not authorize using the female input-resistance distribution to select a favorable male-MaleCNS Ra/Rm point.

A future gate may use the female electrophysiology only as **falsification/compatibility evidence over the complete frozen male morphology uncertainty set** unless an independent source establishes a quantitatively transferable female↔male APL passive morphology mapping.

The existence of a non-empty `flywireType` is evidence of source-defined cell-type correspondence, not proof of identical biophysical geometry across sexes.

## Guardrails
No:
- Amin response values;
- Prisco M2B parameter points;
- V5 residual-driven parameter selection;
- electrophysiology input-resistance values;
- Ra/Rm fit;
- market/MNQ data.

Market firewall remains CLOSED.
