# V6-M2B execution freeze manifest

Frozen before any V6-M2B numerical Prisco workbook execution.

Canonical private protocol repository: `nsar2002/test15`, branch `fly-mnq-v5-m6a-20260916`.
- M2B protocol path: `research/v6_m2b_prisco_two_parameter_identification_protocol.md`
- protocol commit: `472a3c5d1f152b703aed3612b729869ec65d78bc`
- pre-execution clarification path: `research/v6_m2b_protocol_clarification_v1.md`
- clarification commit: `98ca1d0877293a533d96188171dc2fbfc622ae50`

Public source-only implementation:
- path: `fly_mnq/v6_m2b_prisco_identification.py`
- implementation commit introducing frozen executor: `cd29086682e58cd47a2d93946c6484f25bfde357`

Scientific invariants:
- `eta_ff` is not fit;
- `g_apl_kc` uses only the frozen Figure4-supp1 C-vs-D median-ratio causal statistic and frozen bootstrap;
- `lambda_z` uses only the frozen Figure5C + responding-MG spatial profiles and one-parameter exponential section kernel;
- Amin values are not loaded;
- M6C3/V5 residuals are not loaded;
- MNQ/market/reward/PnL are not loaded;
- no threshold may be changed after the numeric run.
