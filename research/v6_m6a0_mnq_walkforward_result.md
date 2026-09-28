# V6-M6A0 — RESULT: FAIL_M6A0_NO_CONNECTOME_ADVANTAGE

**Classification.** `FAIL_M6A0_NO_CONNECTOME_ADVANTAGE`. H1, H2 and H3 all fail at the pre-registered one-sided p < 0.01. Thresholds were not moved.

## Provenance

| Item | Value |
|---|---|
| Protocol | `research/v6_m6a0_mnq_walkforward_protocol.md`, SHA256 `893e5b5d…`, frozen in c767d89 before any MNQ data access |
| Manifest | `5cf3d0f2…` |
| Amendment A1 | Encoding, c249b23 |
| Implementation | 9e0bfe8 + A1 |
| Formal run | GitHub Actions **36382298274** (e1208df), bot commit 9ff13ce: `research/results/v6_m6a0_result.json`, input hashes `research/results/v6_m6a0_input_sha256.txt` |

**Earlier runs.** No criterion was evaluated in either.
- **36381833974:** BLOCKED. Google served an HTML throttle page; the check reported "non-ASCII".
- **36382073518:** stopped by the access probe. 8 files were byte-exact and 17 were HTML throttle pages.
- The download was then made throttle-tolerant: a pause per file and retries on HTML. This is transport only.

## Data

- 25 NinjaTrader MNQ Last contracts (06-19 … 06-25): 144,115 active 15-minute bars.
- Burn-in: 06-19 and 09-19.
- Evaluation: 133,880 bars from 12-19 onward, 133 blocks of 1,000 bars.
- The 6 newest contracts (09-25 … 12-26) remain an **untouched holdout**.
- θ = θ_ref, because M5G0 is BLOCKED.

## Criteria (mean block ρ, one-sided t-test over 133 blocks)

| Criterion | Mean | t | p | Holds |
|---|---|---|---|---|
| H1: A learns MNQ | −0.0036 | −1.33 | 0.907 | no |
| H2: A > B (connectome vs rewired) | +0.0014 | 1.96 | 0.026 | no (needs < 0.01) |
| H3: A > C (teaching-specific) | −0.0013 | −0.40 | 0.656 | no |

## Diagnostics (not criteria)

**Whole-window ρ:** A −0.0050, B −0.0057, C −0.0033, D (EW ridge) −0.0165.

The ridge baseline is significantly *negative* (mean block ρ −0.0146, t −3.51). The fly learner is less wrong than ridge (A − D +0.011, p 0.023), but it is not right.

**Trading** (1 MNQ contract, sign(s), $1.50 per side):

| Arm | Gross | Net | Sharpe | Hit rate | Turnover per bar |
|---|---|---|---|---|---|
| A connectome | −$15,105 | −$130,204 | −3.45 | 0.51 | 0.57 |
| B rewired | −$27,549 | −$145,972 | −3.87 | 0.51 | 0.59 |
| C shuffled | −$30,582 | −$151,456 | −4.01 | 0.50 | 0.60 |
| D ridge | −$29,857 | −$131,354 | −3.48 | 0.50 | 0.51 |

Every calendar year is net negative for every arm.

## Reading

Under this frozen design, the MaleCNS mushroom-body learner does **not** predict next-bar 15-minute MNQ returns out of sample:
- Its correlation is indistinguishable from zero.
- It is not specific to teaching, which is consistent with the M5F0 G failure.
- The real wiring's small edge over rewired (p 0.026) does not reach the pre-registered bar and is economically void.

Costs of about $1.9 per bar of turnover dominate any sign strategy at this horizon.

This is a clean negative result. Any variant (horizon, features, θ, readout) is a **new** hypothesis. It needs its own frozen protocol, and the reserved holdout exists for confirmation.
