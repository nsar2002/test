# V6-M4V0 — INDEPENDENT dSK MECHANISM VALIDATION SOURCE RESERVED

**STATUS: RESERVED BEFORE ANY CHEN 2026 RAW ABF MEMBER PAYLOAD IS OPENED.**

## Purpose
M3F4 closed the final passive APL source-support route. M4A0 qualified Chen 2026 raw electrophysiology as an architecture/calibration source, but Chen is not a pristine validation source.

Before any Chen raw trace is opened, this protocol reserves an independent Drosophila SK electrophysiology source so a later active-channel model cannot be validated only against the same Chen dataset used to motivate or calibrate it.

## Reserved independent source
Abou Tayoun AN, Li X, Chu B, Hardie RC, Juusola M, Dolph PJ.
**The Drosophila SK channel (dSK) contributes to photoreceptor performance by mediating sensitivity control at the first visual network.**
Journal of Neuroscience 31(39):13897–13910 (2011).
DOI: `10.1523/JNEUROSCI.3134-11.2011`
PMID: `21957252`
PMCID: `PMC3758547`

This paper is outside the previously fixed adult-APL electrical/optical source corpus recorded in the canonical project memory and has not been used to select V6 passive parameters, M3F4 source supports, or Chen electrophysiology subsets.

## What is already burned / known
The source's high-level published mechanism is not blind and cannot count as holdout evidence:
- Drosophila has a dSK channel;
- the paper reports a slow Ca2+-activated K+ current in photoreceptors;
- dSK perturbation affects that current.

Those qualitative statements are mechanism prior only.

No numerical Figure 2 current values, digitized traces, quantitative kinetics, or fitted channel parameters from this source may be opened or used during M4A1.

## Reserved holdout material
The untouched quantitative holdout is the independent whole-cell dSK current experiment in **Figure 2**, especially the source-reported peak-current comparison in Figure 2D and its corresponding Figure 2C electrophysiology protocol.

Numerical plot values remain reserved. No digitization is authorized now.

## Role and limitation
This is a **mechanism-level** independent validation source. It can later falsify a proposed Drosophila SK current law or parameterization if the proposed law makes a source-translatable quantitative prediction.

It is deliberately **not** treated as APL-specific validation:
- photoreceptor channel magnitude/distribution cannot be transferred quantitatively into APL;
- photoreceptor-specific current amplitude cannot tune APL SK conductance;
- photoreceptor morphology/localization cannot set APL spatial SK placement.

Therefore a PASS against M4V0 would be necessary support for an explicit dSK mechanism but never sufficient for an APL production model. A separate downstream APL/circuit holdout is still required before any production-readiness claim.

## Future unblinding rule
M4V0 numerical values may be opened only after:
1. the Chen-derived active mechanism form is frozen;
2. the exact model-to-Figure-2 observable mapping is frozen;
3. no M4V0 numerical value has been used for parameter selection.

If no defensible source-translatable prediction exists, M4V0 is classified NOT_APPLICABLE rather than retrofitted.

## Firewalls
Forbidden before the later M4V0 validation protocol:
- digitizing Figure 2 numerical values;
- using photoreceptor values to tune APL parameters;
- changing M3F4 source support/q/Ra/Rm;
- opening Amin A1/B1/A4/B4;
- MNQ/reward/PnL/strategy/prop-firm evaluation.

Chen raw ABF payload remains unopened at the instant this reservation is frozen.
