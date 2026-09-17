# V6-M3E1 PROTOCOL — CROSS-SEX SOMATIC INPUT-RESISTANCE FALSIFICATION

**STATUS: FROZEN BEFORE ANY MALECNS PASSIVE-MODEL INPUT-RESISTANCE OUTPUT IS COMPUTED.**

## Purpose
Use the already-burned adult APL whole-cell physiology as a conservative **falsification-only** check on the complete frozen MaleCNS passive-property envelope.

This gate MUST NOT identify, rank, select, shrink or reweight Ra/Rm. Its only scientific question is whether the full pre-existing male-MaleCNS passive uncertainty set is grossly incompatible with the adult female APL somatic input-resistance scale.

## Important blindness status
The physiology source is not a holdout:
- it was already used in V5-D4/D8/D9;
- the source workbook was reopened during M3E1 planning before this protocol was frozen.

Therefore no threshold may be learned from its values. The rule below is purely set-theoretic and fixed before the male passive-model resistance output is computed.

## Frozen physiology source
Workbook: `APL_NS_SD_RS_final.xlsx`
Drive file ID: `1loieGuh2rh7LdwduhhONJif_EbYaB5cy`
Prior D4 staged workbook SHA256: `419644f8806d4189b032cdcc578320904c3c666770fae680ef126c4d511349b7`.

Use exactly first-sheet rows with `State == "NS"`.
Frozen expected count: **20 cells**.

Primary measured quantity is recomputed from the source `dV (mV @ -50pA)` field:
`R_obs_ohm = abs(dV_mV)*1e-3 / (50e-12)`.

Do NOT trust the workbook header text `Rin (Gohm @ -50pA)` as a unit declaration. The numeric Rin column is retained only as a parity diagnostic:
`Rin_column_numeric ≈ R_obs_ohm / 1e6`,
i.e. the stored numeric values behave as MΩ.

No cell may be omitted.

## Frozen morphology/electrical model
Prerequisites:
- M3A2 PASS;
- M3D qualified passive electrical operator;
- M3E0 PASS source-defined soma mapping.

Use exact MaleCNS v1.0 APL main-component skeletons and exact M3E0 soma nodes:
- APL10540: node 12;
- APL10977: node 10.

Passive cable discretization is exactly M3D:
- linear-taper edge axial resistance,
- lateral-frustum membrane area split half to each endpoint,
- no invented end-cap or soma membrane,
- no fitted length constant.

Frozen passive rectangle:
- `Ra ∈ [0.40, 4.00] Ω·m`
- `Rm ∈ [0.20, 2.64] Ω·m²`.

## Exact input resistance
For each APL and passive pair:
`A = (1/Ra)L0 + (1/Rm)D_A`.

Inject exactly 1 A mathematical test current at the frozen soma node and solve:
`A V = e_soma`.

Then:
`Rin_model = V_soma / 1 A` in Ω.

The 1 A is only a linear-system probe and is not a biological current.

## Exact passive-envelope extrema
Somatic driving-point resistance in this passive resistor/leak network is monotone non-decreasing when any axial or membrane resistance is increased (Rayleigh monotonicity).

Therefore the complete rectangular uncertainty set has exact extrema at:
- minimum: `Ra=0.40, Rm=0.20`;
- maximum: `Ra=4.00, Rm=2.64`.

Also compute the four corners for diagnostic transparency. No adaptive grid or optimizer is required for the formal range.

## Frozen empirical set
Let:
- `Robs_min = min(all 20 NS R_obs)`
- `Robs_max = max(all 20 NS R_obs)`.

Median, quartiles and individual values are diagnostics only and cannot alter classification.

## Frozen falsification rule
For each MaleCNS APL independently, define its complete model interval:
`M_apl = [Rmodel_min, Rmodel_max]`.

Define the burned female empirical hull:
`E = [Robs_min, Robs_max]`.

### PASS / not falsified
`PASS_M3E1_CROSS_SEX_RIN_NOT_FALSIFIED`
only if **both** APL10540 and APL10977 model intervals have non-empty intersection with E.

### FAIL
`FAIL_M3E1_CROSS_SEX_RIN_INCOMPATIBLE`
if either APL's complete frozen passive interval has empty intersection with E.

This rule is intentionally conservative because physiology is female and geometry is male.

## Critical non-calibration rule
Even on PASS:
- do not intersect the Ra/Rm rectangle with the female resistance values;
- do not compute a posterior;
- do not choose q;
- do not use the empirical median to select a point;
- do not use the known M3D ALPHA_PRIME locality crossing to prefer a subset;
- do not claim cross-sex passive equivalence.

The original full Ra/Rm rectangle remains intact unless a future independent same-sex or quantitatively transferable source is preregistered.

## Guardrails
No Amin A1/B1/A4/B4 values.
No optical bridge.
No Prisco M2B rescue.
No region gain.
No market/MNQ/reward/PnL/strategy output.

Market firewall remains CLOSED.
