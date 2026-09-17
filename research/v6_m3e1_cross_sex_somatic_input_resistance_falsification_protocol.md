# V6-M3E1 PROTOCOL — CROSS-SEX SOMATIC INPUT-RESISTANCE GROSS FALSIFICATION

**STATUS: FROZEN BEFORE ANY M3E1 MALECNS INPUT-RESISTANCE MODEL OUTPUT.**

## Purpose
Test whether the currently frozen male-MaleCNS 3D passive morphology model is at least **grossly compatible** with independently measured adult APL somatic input resistance.

This is a falsification-only gate. It must not identify or narrow Ra/Rm.

## Preconditions
Required:
- M3A2 PASS — historical unique-largest-component morphology qualified.
- M3D qualified passive electrical operator.
- M3E0 PASS — source-defined MaleCNS soma locations map to the qualified main components.

## Experimental source
Official Chen et al. 2026 adult APL whole-cell source already frozen in V5-D4:
- Zenodo record 18644411, `Ephys_sparse coding.zip`
- full archive SHA256 `bc723b55aa0655452a828bec71e42da5e037a800a970823e3997b00c1bfe631f`
- workbook `APL_NS_SD_RS_final.xlsx`
- workbook SHA256 `419644f8806d4189b032cdcc578320904c3c666770fae680ef126c4d511349b7`
- exact D4 inclusion: 20 rows with `State==NS`.

### Unit correction locked before model output
The workbook column is labelled `Rin (Gohm @ -50pA)` but displays values such as 125.2086 for dV=-6.26043 mV at -50 pA. Physical conversion is:
`6.26043 mV / 50 pA = 0.1252086 GΩ = 125.2086 MΩ`.

The preserved D4 transcript already normalized the workbook values accordingly.

Frozen official-workbook NS summary in GΩ:
- n = 20
- min = `0.0809216`
- q25 = `0.1148641`
- median = `0.1264146`
- q75 = `0.13307865`
- max = `0.1987428`

Primary empirical **gross compatibility interval** is the complete observed min-max:
`R_exp = [0.0809216, 0.1987428] GΩ`.

This wide interval is deliberate because MaleCNS is male whereas the whole-cell recordings are from mated female flies.

D4 raw re-extraction is diagnostic only:
`[0.07712698129507203, 0.1958723097581131] GΩ`.
It cannot change the primary interval.

## MaleCNS model
Use exactly the M3D passive network:
- exact MaleCNS v1.0 SWC hashes;
- historical unique-largest component;
- 8 nm/source-unit scale;
- linear-taper axial resistance
  `Rax_ij = Ra L / (π r_i r_j)`;
- lateral-frustum membrane area split equally between endpoints;
- no end caps;
- no invented soma sphere/area;
- node membrane leak resistance `Rm/A_i`.

Use source-defined soma mapping from M3E0:
- APL10540: official somaLocation maps to SWC node 12;
- APL10977: official somaLocation maps to SWC node 10.

Implementation must independently reconstruct these mappings from the exact annotation/SWC sources and require parity with M3E0.

For one ampere injected at the mapped soma node:
`Rin_model = V_soma / 1 A`.

Report in GΩ.

## Frozen passive rectangle
Unchanged from M3A/M3D:
- `Ra ∈ [0.40, 4.00] Ω·m`
- `Rm ∈ [0.20, 2.64] Ω·m²`.

No point may be selected from the experimental result or from the already-known M3D ALPHA_PRIME crossing.

## Exact envelope extrema
The DC model is a passive resistor network connected to ground through positive membrane resistors.

For fixed morphology:
- every axial resistor scales positively with Ra;
- every membrane resistor scales positively with Rm.

By Rayleigh monotonicity of effective resistance in a passive resistor network, somatic input resistance is nondecreasing when any constituent resistance increases.

Therefore the continuous rectangle extrema are exactly:
- `Rmin = Rin(Ra_min,Rm_min)`;
- `Rmax = Rin(Ra_max,Rm_max)`.

All four corners must still be evaluated as an implementation check, and the expected monotone ordering must hold.

No finite search grid defines the primary bounds.

## Frozen PASS/FAIL
For each APL define the continuous model interval:
`M_apl = [Rmin_apl,Rmax_apl]`.

The experimental band is:
`E = [0.0809216,0.1987428] GΩ`.

Overlap:
`overlap(M,E) = max(M_low,E_low) <= min(M_high,E_high)`.

### PASS
`PASS_M3E1_GROSS_INPUT_RESISTANCE_COMPATIBILITY`
only if BOTH APL10540 and APL10977 model intervals overlap E.

### FAIL
`FAIL_M3E1_CURRENT_PASSIVE_MORPHOLOGY_GROSSLY_INCOMPATIBLE`
if either APL interval is disjoint from E.

## Critical interpretation
A PASS does **not**:
- identify Ra or Rm;
- shrink the passive rectangle;
- authorize using only overlapping parameter pairs;
- repair M3D's APL10540 ALPHA_PRIME locality edge;
- establish male=female passive morphology;
- identify voltage→calcium/release;
- authorize Amin unblinding.

A FAIL does not reject connectome topology. It falsifies the **current passive morphology instantiation as a quantitative somatic-resistance model** unless an independently justified missing element is added in a new preregistered architecture (for example source-supported soma membrane geometry or cross-sex morphology correction). Such an element may not be tuned to the target.

## Guardrails
Forbidden:
- selecting/truncating Ra/Rm from overlap;
- using the M3D q≈0.3 locality crossing to choose a bound;
- adding soma area after seeing M3E1 output;
- using Amin fitted spatial length or Amin response values;
- fitting an electrophysiological target;
- MNQ/reward/PnL/strategy/prop-firm inspection.

Amin A1/B1/A4/B4 remains numerically BLIND. Market firewall remains CLOSED.
