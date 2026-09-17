# V6-M3A2 PROTOCOL — PRE-EXISTING MAIN-COMPONENT MORPHOLOGY AUDIT

**STATUS: FROZEN BEFORE M3A2 EXECUTION AND BEFORE ANY AMIN RESPONSE UNBLINDING.**

## Purpose
Resolve the official SWC representation issue exposed by M3A without inventing a new morphology rule.

M3A2 does **not** relax M3A after seeing a desired model outcome. It reuses the exact deterministic component-selection rule already present in the canonical V5 geometry operator before V6 existed.

## Historical rule authority
Canonical prior implementation:
- `nsar2002/test15`
- branch `fly-mnq-v5-m6a-20260916`
- file `fly_mnq/v5_m4b_calibrate_kappa.py`
- Git blob SHA `b973c50c775e97fe0fe1564994e58570ed900bc7`

The relevant algorithm is frozen as:
1. build an undirected graph from SWC parent-child links when the parent ID exists in the same SWC;
2. compute connected components;
3. calculate node count for every component;
4. require a **unique** component with maximum node count;
5. define that component as the main component;
6. remap only parent links internal to that component;
7. require exactly one root after remapping;
8. traverse from that root and require all main-component nodes to be reached.

No other component-ranking metric is allowed.

## Source identity
Official MaleCNS v1.0 APL SWCs:
- APL 10540 expected D0 SHA256: `22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f`
- APL 10977 expected D0 SHA256: `34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf`

Current files must be byte-identical to those D0 hashes. Any mismatch => source FAIL.

## Required morphology audit
For each APL:
- parse all valid non-comment SWC rows;
- require unique node IDs;
- require finite x/y/z and strictly positive radius;
- construct the graph exactly as above;
- report:
  - total node count,
  - number of components,
  - every component's node count,
  - all raw roots,
  - unique-largest component ID and node count,
  - node fraction retained,
  - discarded component node counts,
  - main-component root ID,
  - main-component edge count,
  - total/main/discarded cable length in source units and micrometres using the already-fixed 8 nm/source-unit scale;
- require unique-largest component;
- require exactly one main-component root;
- require traversal covers all main-component nodes;
- require no cycle/incomplete traversal.

No minimum retained-node fraction is introduced after seeing M3A. The historical algorithm itself determines admissibility.

## Raw-site coverage parity
M3A2 must also re-establish the historical structural invariant that relevant APL synapse sites belong to the selected main component.

Use official MaleCNS source-defined synapse geometry only. For every APL↔KC raw synapse site used by the canonical APL physiology operator:
1. find its nearest node among **all** SWC nodes;
2. inspect that node's connected-component label;
3. require every relevant site to have the selected main-component label.

Formal requirement:
`main_component_raw_site_coverage == 1.0` for both APLs.

No distance threshold or manual reassignment is allowed. If exact public-source reconstruction of the D0 APL↔KC site universe is unavailable, classification is BLOCKED rather than silently omitting this criterion.

## PASS
`PASS_M3A2_PREEXISTING_MAIN_COMPONENT_MORPHOLOGY` only if both APLs satisfy:
- exact D0 SWC SHA256 parity;
- unique largest component;
- one root inside selected main component;
- complete valid traversal;
- finite/positive geometry;
- 100% relevant raw-site main-component coverage.

## FAIL/BLOCKED
- hash mismatch => `FAIL_M3A2_SOURCE_IDENTITY`
- largest component not unique => `FAIL_M3A2_MAIN_COMPONENT_NOT_UNIQUE`
- selected component not a valid rooted tree => `FAIL_M3A2_MAIN_COMPONENT_NOT_TREE`
- any relevant raw site outside selected component => `FAIL_M3A2_RAW_SITE_COVERAGE`
- official source geometry required for coverage cannot be reconstructed deterministically => `BLOCKED_M3A2_RAW_SITE_SOURCE`

No rule may be modified after execution.

## Guardrails
Forbidden:
- choosing root 1 because M3A exposed it;
- manually deleting/reconnecting fragments;
- selecting by cable length, spatial position, Amin agreement, Prisco fit, V5 residuals, or future MNQ performance;
- fitting any morphology attenuation constant here;
- using Amin A4/B4 response numbers;
- opening MNQ/reward/PnL/strategy/prop-firm outputs.

A PASS only authorizes a later morphology/operator gate. It does not authorize Amin unblinding or market evaluation.
