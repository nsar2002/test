# V5-M6C2 SOURCE-ONLY PROTOCOL — INDEPENDENT BERGMANN CALYX APL-BLOCKADE CONSTRAINT

Frozen before opening numerical values from Bergmann et al. 2026 Dataset S1 and before any M6C2 model comparison.

## Scientific purpose
M6C1 removed the previous alpha inconsistency but left one shared positive APL loop scale kappa underidentified: global coding plus the frozen Lin alpha interval admitted the full coding interval, whose multiplicative width exceeded 1.10. M6C2 may therefore seek one additional independent adult Drosophila observable. This source-only stage may not inspect M6C1 numerical kappa/model outputs, the still-blinded alpha-prime/beta/beta-prime/gamma transfer values, full-network simulator health, MNQ data, reward, PnL, strategy or prop-firm outcomes.

## External source fixed before values
Primary article: Bergmann GA et al., “Conflicting adaptations in an inhibitory feedback circuit”, The Journal of Physiology (2026), DOI 10.1113/JP290394, PMCID PMC13039246.
Primary data source: publisher/PMC Dataset S1, labelled TJP-604-3005-s002.xlsx / tjp70419-sup-0002-SuppMat.xlsx. The downloaded bytes must be SHA256-locked before parsing.
Qualitative source facts fixed before data extraction: Figure 5 measures KC GCaMP6f responses to 5 s 10^-2 isoamyl acetate before and after bath histamine; APL expresses Ort stochastically; no-Ort hemispheres are negative controls; measurements include the calyx; the no-dTRPA1 group is the unmanipulated-KC control population apart from the common temperature protocol.
Chemical bridge fixed before values: isoamyl acetate and isopentyl acetate are the same compound; M4A/Seki uses the label “isopentyl acetate”. No other odor synonym/substitution is allowed.

## Allowed data subset
Only Figure 5 / associated control data satisfying ALL of the following may contribute to the primary constraint:
1. KC imaging, calyx ROI only.
2. no-dTRPA1 condition only. KC>dTRPA1 adapted flies are excluded from calibration.
3. 10^-2 isoamyl acetate only.
4. paired before-histamine and after-histamine KC response measurements.
5. both APL>Ort-positive experimental hemispheres and no-Ort negative-control hemispheres, identified from source metadata.
6. Raw/source Dataset-S1 numerical data only. Digitising plotted points is forbidden if the source table cannot be unambiguously parsed.
7. Alpha, alpha-prime, beta, beta-prime and gamma response rows may be used only to verify that filtering has not accidentally selected the wrong source block; their numerical response values must not be reported or used in the source constraint.

## Required source schema / qualification
The dataset must permit deterministic identification of: condition (no-dTRPA1 versus KC>dTRPA1), Ort status (APL>Ort versus no-Ort), anatomical ROI, pre/post-histamine state, response value, and a pairing identifier at least at hemisphere level. A fly identifier is required for the primary uncertainty calculation because the published N indicates some flies contribute two hemispheres. If a usable fly identifier cannot be recovered without interpretation or manual relabelling, this source stage is FAIL_SOURCE_SCHEMA and M6C2 model comparison is not authorized.
All response values used must be finite numeric source values. Do not remove outliers, winsorize, threshold responses, change signs, normalize across flies, or choose exclusions from the observed response distribution.

## Fly-level reduction fixed before values
For each included fly and Ort-status group separately:
- collect every eligible calyx hemisphere belonging to that fly;
- compute the arithmetic mean BEFORE response across those hemispheres;
- compute the arithmetic mean AFTER response across the same eligible hemispheres.
This yields exactly one paired (before_f, after_f) record per fly. If a hemisphere lacks its paired before or after value, exclude that incomplete hemisphere before fly averaging and report it. Do not borrow measurements across hemispheres or flies.

## Primary external observable fixed before values
For Ort-positive no-dTRPA1 flies define
  R_Ort = mean_f(after_f) / mean_f(before_f).
For no-Ort no-dTRPA1 negative-control flies define
  R_noOrt = mean_f(after_f) / mean_f(before_f).
The independent APL-blockade observable is the double ratio
  D_calyx = R_Ort / R_noOrt.
This is intended to cancel first-order non-APL histamine/imaging effects measured in the stochastic no-Ort negative controls. It is the only Bergmann scalar permitted to constrain kappa in the next model gate.
Required finite-denominator qualification: both group-level mean-before values and R_noOrt must be strictly positive and finite. Otherwise FAIL_SOURCE_NUMERICS.

## Uncertainty interval fixed before values
Primary uncertainty is a stratified fly-level nonparametric bootstrap of D_calyx:
- independently resample Ort-positive flies with replacement within the Ort-positive group and no-Ort flies with replacement within the no-Ort group;
- preserve each sampled fly’s paired before_f/after_f values;
- 100,000 bootstrap replicates;
- NumPy PCG64 seed = 20260916;
- compute D_calyx for every replicate using the exact group-mean-ratio and double-ratio equations above;
- primary interval = percentile [2.5%, 97.5%] of finite valid bootstrap replicates.
If more than 0.1% of bootstrap replicates are invalid because a required denominator is nonpositive/nonfinite, the source stage fails qualification rather than silently dropping instability.
No SEM-based interval, hand-expanded interval, post-hoc clipping, or interval widening is allowed.

## Direction and informativeness checks
The source stage may be classified QUALIFIED_CONSTRAINT only if:
- all source/schema/integrity rules above pass;
- at least 5 distinct flies exist in each Ort-status group after deterministic filtering;
- D_calyx is finite and > 1.0;
- the bootstrap lower 95% bound is > 1.0, establishing the expected direction of increased KC response when APL inhibition is specifically removed;
- the bootstrap interval has finite positive endpoints.
If these fail, retain the extracted source result but classify it NONQUALIFYING_EXTERNAL_CONSTRAINT; do not use it to tune or constrain M6C2.

## Source-only blindness
The extraction program MUST NOT read or download:
- M6C1 report/stdout/frozen kappa scan/model state;
- M6B3 held-out lobe values;
- any alpha-prime/beta/beta-prime/gamma model transfer output;
- MNQ or market data;
- full-network simulator outputs.
It may read this protocol, Bergmann Dataset S1, and public article/code solely as necessary to identify the exact source table semantics.

## Required outputs
1. exact Dataset S1 source URL/final URL, byte size and SHA256;
2. workbook sheet names and a schema-only map of which sheet/table contains Figure 5 calyx data;
3. deterministic filter criteria actually matched;
4. counts of hemispheres and distinct flies per Ort-status group before and after pairing qualification;
5. one filtered fly-level table containing only IDs/status/before/after for the eligible CALYX subset;
6. D_calyx point estimate, R_Ort, R_noOrt, bootstrap interval, invalid-bootstrap fraction and fixed seed;
7. PASS/FAIL classification and reasons;
8. hashes of protocol, implementation, source file, report and filtered table.

## Consequence if QUALIFIED_CONSTRAINT
Only after this source-only artifact is frozen may a separate M6C2 model protocol be written. That model protocol must keep the M6C1 raw-synapse-site architecture, frozen s, frozen lambda, one shared positive kappa, and previously frozen global-coding/Lin-alpha constraints. The new Bergmann calyx interval may be intersected with those constraints using the Seki isopentyl-acetate input. The still-blinded alpha-prime/beta/beta-prime/gamma transfer values remain forbidden until the combined kappa interval is nonempty and has multiplicative width <=1.10. No threshold may be changed after source values are seen.

MNQ/reward/PnL/strategy/prop-firm evaluation remains CLOSED.
