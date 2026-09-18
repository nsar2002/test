# V6-M3F5 PROTOCOL — AMIN A1/B1 ORDINAL HOLDOUT AFTER PUBLISHED-LOCATION ELIGIBILITY

**STATUS: FROZEN BEFORE M3F4 OUTPUT AND BEFORE ANY AMIN A1/B1 RESPONSE VALUE IS OPENED.**

M3F1 remains blocked by M3F0. M3F3 remains blocked by M3F2B.

M3F5 is the one final held-out validation route for the preregistered M3F4 published-location source model.

## Hard prerequisite
Execute only if M3F4 returns:
`PASS_M3F4_PUBLISHED_LOCATION_HV_ORDINAL_ELIGIBILITY`.

Otherwise A1/B1 remains blind.

## Source/statistics
Use exactly the already-frozen M3F3 source identity, ranges and statistics:
- workbook SHA256 `ba1d7c4dfaa2007aa3e71f668b72ee81845ea20094012f44450117a3a2165e9c`
- sheet `Fig 7`
- A1 `A261:C274`, labels C,H,V from row 260
- B1 `A277:C290`, labels C,H,V from row 276
- complete paired numeric rows only; >=8 each
- A1 `dA=H-0.5*(C+V)`
- B1 `dB=V-0.5*(C+H)`
- paired median
- 100,000 paired bootstrap replicates
- PCG64 seeds A1 `2026091801`, B1 `2026091802`
- linear 95% percentile interval
- same four pairwise median diagnostics.

## PASS
`PASS_M3F5_INDEPENDENT_ORDINAL_APL_LOCALITY` requires:
- M3F4 PASS
- >=8 complete A1 and B1 cases
- both composite lower 95% bounds >0
- median(H-C)>0
- median(H-V)>0
- median(V-C)>0
- median(V-H)>0.

Otherwise valid unblinding:
`FAIL_M3F5_INDEPENDENT_ORDINAL_APL_LOCALITY`.

## Firewall
Emit summaries only. Do not emit raw cases.

Do not read:
- C1 as rescue
- A4/B4
- p-values for acceptance.

No magnitude comparison or voltage→GCaMP calibration is allowed.

A M3F5 failure closes this passive published-location output-spatial model for independent validation; no further source-support retuning on Amin is allowed.

Market firewall remains CLOSED.
