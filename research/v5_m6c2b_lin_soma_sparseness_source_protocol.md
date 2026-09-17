# V5-M6C2B SOURCE-ONLY PROTOCOL — LIN SOMA POPULATION-SPARSENESS PERTURBATION

Frozen before reading numerical Figure-5c bar heights/error bars and before any M6C2B model comparison.

## Scientific purpose
V5-M6C1 is alpha-consistent but leaves one shared positive APL loop scale kappa underidentified. The Bergmann-2026 raw Dataset-S1 route (M6C2) is currently SOURCE_EXECUTOR_BLOCKED before any numerical workbook cell was opened. M6C2B is an independent fallback observable from Lin et al. 2014 that measures KC SOMA population sparseness under acute APL synaptic blockade. It may constrain kappa only if the source-only digitization qualifies under the rules below.

M6C2B must remain blind to: M6C1 numerical kappa scan/model outputs except the fact that kappa remains underidentified; M6B3 held-out alpha-prime/beta/beta-prime/gamma transfer values; all full-network simulator outputs; MNQ chronology/reward/PnL/strategy/prop-firm outcomes.

## Fixed external source
Primary article: Lin AC et al. 2014, "Sparse, Decorrelated Odor Coding in the Mushroom Body Enhances Learned Odor Discrimination", Nature Neuroscience 17:559-568, DOI 10.1038/nn.3660, PMCID PMC4000970.
Primary numerical source for this gate: Figure 5c in the author/publisher article PDF or the corresponding original PMC/Nature figure image, whichever is byte-accessible first. Exact source bytes must be SHA256-locked before digitization.

Figure-5 source semantics fixed before numerical reading:
- KC SOMATA/activity maps, not mushroom-body lobes.
- Population sparseness is the graded response statistic used by the paper, not binary active-cell fraction.
- APL>shi^ts1 unlabeled hemispheres are the temperature/control condition.
- APL>shi^ts1 labeled hemispheres are the acute APL-output-blockade condition at restrictive temperature.
- Figure 5 uses a seven-odor panel. M6C2B does NOT require one-to-one odor matching because the primary experimental observable is the WITHIN-PANEL change in population sparseness under APL blockade, temperature-corrected by the unlabeled control. No individual odor from the four non-Seki-overlap odors may be separately compared to the model.
- The exact Seki-panel overlaps identified before model comparison are ethyl acetate, ethyl butyrate and isoamyl acetate (= Seki isopentyl acetate); this fact is recorded for provenance only and is not used to cherry-pick Figure-5 values.

## Primary experimental observable fixed before values
Let S_U22 and S_U32 be the plotted mean population sparseness for APL>shi^ts1 UNLABELED control hemispheres at 22C and 32C. Let S_L22 and S_L32 be the corresponding plotted means for APL>shi^ts1 LABELED hemispheres.

Define the temperature-corrected APL-blockade effect on soma population sparseness as the difference-of-differences:

    DeltaS_exp = (S_L32 - S_L22) - (S_U32 - S_U22)

Expected direction from the qualitative source text is DeltaS_exp < 0 because acute APL blockade decreases population sparseness after correcting for temperature effects. Direction is a qualification check, not a tunable target.

For model comparison it is convenient to use the positive blockade magnitude:

    M_exp = -DeltaS_exp

No ratio transform is allowed for the primary gate because sparseness is bounded and a ratio can be unstable or misleading near zero.

## Digitization protocol fixed before values
1. Use only Figure 5c.
2. Hash-lock the exact source PDF/image before extracting pixels.
3. Calibrate the y-axis from at least three labeled y-ticks. Fit a linear pixel-y to sparseness-value map. If residual calibration error exceeds the equivalent of 0.01 sparseness units, source digitization fails.
4. Identify the four means solely by x-axis/genotype/temperature labels: APL>shi^ts1 unlabeled 22C, unlabeled 32C, labeled 22C, labeled 32C. Do not use bar height to identify groups.
5. Mean value = center of the plotted mean marker or mean bar endpoint according to the source graphic. The graphical rule must be applied identically to all four means.
6. SEM value = distance from mean marker/bar endpoint to the terminal point of its error bar along the y-axis. Significance brackets/stars are excluded.
7. Perform two independent pixel passes after resetting the crop/origin. Each of the four mean estimates must agree within 2 source pixels between passes; y-tick calibration must be identical up to rounding. Otherwise FAIL_DIGITIZATION_REPRODUCIBILITY.
8. Final digitized mean/SEM for each group is the arithmetic average of the two pass estimates after conversion to y-axis units.
9. Record pixel coordinates, y-axis calibration, source dimensions, crop coordinates, and both passes in a machine-readable JSON artifact.

## Conservative experimental uncertainty fixed before values
The primary uncertainty interval must not pretend that hemisphere-level points are independent flies when the source reports some flies contribute two hemispheres.

Therefore use a conservative SEM envelope rather than a hemisphere bootstrap:
- For each of the four means define an approximate 95% marginal interval mean +/- 1.96*SEM.
- Construct the WORST-CASE difference-of-differences interval by endpoint propagation:

    DeltaS_low  = (L32_low  - L22_high) - (U32_high - U22_low)
    DeltaS_high = (L32_high - L22_low)  - (U32_low  - U22_high)

- Convert to positive blockade magnitude interval:

    M_low  = max(0, -DeltaS_high)
    M_high = max(0, -DeltaS_low)

This intentionally ignores any beneficial pairing covariance and is conservative. No interval shrinking, clipping other than the physical M>=0 lower bound, post-hoc SEM replacement, or favorable covariance assumption is allowed.

## Qualification gates
The source-only constraint is QUALIFIED only if all are true:
1. exact Figure 5c source provenance is recorded and hashed;
2. four group labels are unambiguous;
3. y-axis has >=3 usable labeled ticks and linear calibration residual <=0.01 sparseness units;
4. two-pass mean locations agree within 2 pixels for all four means;
5. all four means lie within the displayed sparseness axis bounds and all SEMs are finite/nonnegative;
6. DeltaS_exp < 0 and M_exp > 0;
7. conservative interval has finite endpoints and M_high > M_low;
8. source/caption confirms KC soma population sparseness and acute APL shi^ts1 perturbation semantics.

If any gate fails, classify NONQUALIFYING_SOURCE_CONSTRAINT and do not use Figure 5c to constrain kappa.

## Model-side observable (definition frozen before experimental values)
A later, separate M6C2B model protocol may be written only if this source stage QUALIFIES.

The model must remain exactly the accepted M6C1 raw-synapse-site architecture with frozen s=0.247265221878225, lambda=50 um, M6B3 recurrent local-release equations, one shared positive kappa, and no per-lobe gains.

Use the GLOBAL KC soma/spike state z for this source because Figure 5c is a KC-soma observable. For each of all 17 frozen Seki odors, compute the same population-sparseness functional used by Lin on the nonnegative graded z responses. Average sparseness over all 17 odors separately for APL ON at kappa and APL OFF at kappa=0, producing S_model_on(kappa) and S_model_off.

Define:

    M_model(kappa) = S_model_on(kappa) - S_model_off

Expected M_model >=0. The experimental difference-of-differences removes temperature/control drift, so compare M_model directly to [M_low, M_high]. The model functional/formula must be implemented from the paper's published population-sparseness equation before any kappa result is inspected.

## Identifiability consequence
If the source stage QUALIFIES, the later model gate may intersect:
- frozen global coding interval [9.5%,10.5%];
- frozen Lin alpha-lobe interval from M5/M6C1;
- new Lin Figure-5c soma-sparseness interval [M_low,M_high].

Only if the combined admissible positive-kappa interval is nonempty and has multiplicative width <=1.10 may a diagnostic kappa candidate be defined. The still-blinded alpha-prime/beta/beta-prime/gamma transfer values may be opened only AFTER this primary identifiability gate passes. No thresholds/intervals may change after Figure-5c values are seen.

MNQ/reward/PnL/strategy/prop-firm evaluation remains CLOSED.
