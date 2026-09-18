# V6-M3F3 PROTOCOL — AMIN A1/B1 ORDINAL HOLDOUT AFTER OFFICIAL-ROI ELIGIBILITY

**STATUS: FROZEN BEFORE M3F2A RESULT, BEFORE M3F2B OUTPUT, AND BEFORE ANY AMIN A1/B1 RESPONSE VALUE IS OPENED.**

## Relationship to prior protocol
V6-M3F1 remains permanently BLOCKED because its frozen prerequisite M3F0 failed.

M3F3 is a new validation path with a different independently sourced stimulation-support definition (official MaleCNS neuropil ROI volume), but the **same direction-only held-out statistic and acceptance logic** as M3F1. No A1/B1 numeric response has been opened between these protocol versions.

## Hard execution prerequisite
M3F3 may execute only if:
1. M3F2A = `PASS_M3F2A_OFFICIAL_ROI_SOURCE_MAPPING`;
2. M3F2B = `PASS_M3F2B_OFFICIAL_ROI_HV_ORDINAL_ELIGIBILITY`.

Those prerequisites must freeze, before Amin unblinding:
- horizontal local APL stimulation prediction: H > C and H > V;
- vertical local APL stimulation prediction: V > C and V > H;
for both APL morphologies and the complete frozen passive q grid.

Otherwise A1/B1 remains blind.

## Exact source identity
Official eLife workbook:
`elife-56954-fig7-data1-v2.xlsx`
SHA256:
`ba1d7c4dfaa2007aa3e71f668b72ee81845ea20094012f44450117a3a2165e9c`
sheet `Fig 7`.

No source p-value enters this gate.

## Frozen source ranges
A1 horizontal direct APL activation:
- header `A259 = Bottom panel A1`
- labels `A260:C260 = C,H,V`
- candidate data `A261:C274`.

B1 vertical direct APL activation:
- header `A275 = Bottom panel B1`
- labels `A276:C276 = C,H,V`
- candidate data `A277:C290`.

Published expected sample size: each n=10 neurons (6 flies).

Rows with all three C/H/V values numeric are complete paired cases. No imputation. Fewer than 8 complete cases in either panel => `BLOCKED_M3F3_SOURCE_PAIRING_INSUFFICIENT`.

## Frozen experimental statistics
A1:
`dA_i = H_i - 0.5*(C_i+V_i)`
and `D_A_exp=median(dA_i)`.

Diagnostics:
- median(H-C)
- median(H-V).

B1:
`dB_i = V_i - 0.5*(C_i+H_i)`
and `D_B_exp=median(dB_i)`.

Diagnostics:
- median(V-C)
- median(V-H).

No alternative contrast after unblinding.

## Frozen uncertainty
Paired bootstrap:
- 100,000 replicates;
- preserve C/H/V row pairing;
- NumPy PCG64;
- seed A1 `2026091801`;
- seed B1 `2026091802`;
- statistic = median composite locality contrast;
- two-sided percentile 95% interval using linear quantiles.

These are exactly the M3F1 bootstrap rules.

## PASS
`PASS_M3F3_INDEPENDENT_ORDINAL_APL_LOCALITY`
requires all:
1. both M3F2 prerequisites PASS;
2. >=8 complete paired A1 cases;
3. >=8 complete paired B1 cases;
4. A1 composite 95% lower bound >0;
5. B1 composite 95% lower bound >0;
6. median(H-C)>0;
7. median(H-V)>0;
8. median(V-C)>0;
9. median(V-H)>0.

Otherwise valid unblinding => `FAIL_M3F3_INDEPENDENT_ORDINAL_APL_LOCALITY`.

No magnitude comparison is allowed because no electrical→GCaMP calibration exists.

## Output firewall
Emit only:
- complete-case counts;
- composite medians;
- bootstrap intervals;
- four pairwise median diagnostics;
- formal classification.

Do not print raw per-neuron values.

## Guardrails
After unblinding:
- no ROI source set, q range, morphology or operator change;
- no voltage→GCaMP fit;
- no passive-parameter selection from A1/B1;
- no C1 rescue;
- no A4/B4 read;
- no market/MNQ/reward/PnL/strategy output.

A failure requires a new model version and new independent holdout for any redesigned architecture.

Market firewall remains CLOSED.
