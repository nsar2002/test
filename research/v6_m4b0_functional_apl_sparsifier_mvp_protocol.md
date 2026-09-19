> **WITHDRAWN BEFORE EXECUTION / SUPERSEDED.** This draft was never executed. It is superseded by canonical V6-M4B0 per-hemisphere functional APL protocol commit `21e3c82bc091731f0ed733b01734adce3a74b905` and formal PASS result commit `2c03026d01c93619dcf206e8af1660ac08350f32`. The global 4064-KC competition pool below MUST NOT be executed or treated as canonical. It is retained only for audit history.\n\n# V6-M4B0 — FUNCTIONAL APL SPARSIFIER MVP — PUBLIC EXECUTION MIRROR

Canonical private frozen protocol commit: `eb00869cc6bf4413a1c2c9542ed6b43e1a74af4b`.

This public mirror exists only for source-only execution/provenance.

## Frozen scientific scope

M3F4 passive whole-neuron transfer and M4A1 SK active rescue are closed. M4B0 tests a lower-fidelity, parameter-free MVP abstraction: exact MaleCNS/Seki PN→KC expansion is retained, while APL is represented only as a deterministic KC competition/sparsification controller. This does not claim that real APL is binary, globally uniform, or lacks local/lobe dynamics.

No M3F4 residual, M4A1 residual, Amin response value, MNQ datum, reward, PnL or trading result may affect this gate.

## Frozen M4A parity

Reconstruct frozen V5-M4A exactly.

Required:
- Seki XLSX SHA256 `333aa890ab52ac5d39f0a9bc51520ee00244bc750da7f34c65070ba5fd0c2d3d`;
- N_KC=4064;
- 31/31 Seki glomeruli resolve;
- final PN count=157;
- selected PN→KC edges=12886;
- frozen s=`0.247265221878225`;
- APL-OFF coding at s equals `0.2000057897174618` within one quantum `1/(4064*17)`.

Parity failure -> `BLOCKED_M4B0_M4A_PARITY`.

## Frozen operator

For each of 17 odors:
- `q_off=max(s*base_drive-1,0)`;
- `z_off=1[q_off>0]`;
- K=`floor(0.10*N_KC+0.5)` = 406 when N_KC=4064;
- if positive q_off count <=K, retain all positives;
- otherwise retain exactly K largest q_off;
- exact ties break by ascending MaleCNS KC bodyId;
- `z_on` is binary retained=1, else 0;
- inhibition cannot activate an OFF-inactive KC;
- no fitted gain/kappa/lambda/Ra/Rm/conductance/current/per-lobe/per-odor parameter exists.

## Frozen PASS criteria

A. ON-active subset of OFF-active for all odors.
B. ON count equals min(K, OFF-positive count) for every odor.
C. Exact rank/tie rule correct.
D. mean ON active fraction lies in [0.095,0.105].
E. all 17 ON odor patterns are distinct.
F. Across all 136 unordered odor pairs, float64 Pearson correlation of 4064-dimensional binary KC vectors must be finite; arithmetic mean ON correlation must be strictly lower than OFF.
G. Reverse KC row order, recompute from bodyId-aware rule, restore by bodyId: every ON bit must reproduce exactly.

Diagnostics only: per-odor counts, correlation distribution, Jaccard overlaps, participation-ratio/effective-rank summaries.

PASS -> `PASS_M4B0_FUNCTIONAL_APL_SPARSIFIER_MVP_ELIGIBLE`.
Valid M4A parity but any A-G fail -> `FAIL_M4B0_FUNCTIONAL_APL_SPARSIFIER_MVP`.

PASS authorizes M5 KC/DAN/MBON learning-architecture work under this explicit MVP abstraction only. It does not reopen Amin/M4V0 or authorize MNQ reward/trading.
