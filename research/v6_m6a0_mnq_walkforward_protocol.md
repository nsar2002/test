# V6-M6A0 — FROZEN MNQ WALK-FORWARD EVALUATION: CONNECTOME VS REWIRED VS SHUFFLED-TEACHING VS LINEAR BASELINE

**STATUS: FROZEN BEFORE ANY MNQ DATA WAS DOWNLOADED OR OPENED.** This is the gate the project memory names as the only one that may open MNQ data. No MNQ value has been seen by this project line. Only Drive file names and IDs have been listed.

## Question

Does the frozen FlyTrader learner predict next-bar MNQ returns out of sample? If so, does the real MaleCNS PN→KC wiring add information over a degree-preserving rewired wiring and over a shuffled-teaching control?

## Frozen learner (imported unchanged; hashes enforced at runtime)

| Component | Source |
|---|---|
| Structure | M5B3B, re-executed with parity |
| Plasticity | M5C `run_chronology` |
| Readout | M5D0 `raw_drive` |
| Encoder | M5E0 `Encoder`: connectome arm `k`, rewired arm `k_rewired` |
| Teaching and score | M5F0 `Teacher`, `score` and `run_learner`: two chronology steps per bar, read before write |

**θ.** If `research/results/v6_m5g0_theta_selection_result.json` is `PASS_M5G0_THETA_SELECTED`, then θ = θ\*. Otherwise θ = the M5C `REFERENCE_POINT` (η₋ = η₊ = 0.05, λ_K = λ_D = 0.5, G_MAX = 2.0), declared before any data. At freeze the M5G0 record is `BLOCKED_M5G0_PREREQUISITE` (cd9983b), so θ = θ_ref.

## Data (values never printed or committed)

**Source.** NinjaTrader minute-bar trade exports `MNQ MM-YY.Last.txt` in Drive folder `17DYp3CObxhVvip68vqSGtM_SYPCoBfVB`.
- **Used:** the 25 contracts 06-19 through 06-25, by the file IDs in `research/v6_m6a0_mnq_file_manifest.json`.
- **Reserved final holdout:** the 6 newest contracts, 09-25, 12-25, 03-26, 06-26, 09-26 and 12-26. They are not downloaded or opened by this gate. They are kept for a later confirmation gate.
- Bid/Ask files and every other folder are not used. `holdout_locked`, `validation_only` and `processed` stay untouched.
- **Execution.** Files are downloaded by file ID inside a GitHub Actions runner. No user workstation is involved. The Claude container's egress policy denies Google Drive.
- The SHA256 of every file is recorded. Files never enter git or any artifact.
- A download that is not a text file of NinjaTrader lines (for example an HTML access page) fails the format check → BLOCKED.

**Format.** Each non-empty line must be `yyyyMMdd HHmmss;open;high;low;close;volume`.
- The timestamp is the bar end.
- Prices must be positive multiples of 0.25; volume must be a non-negative integer; high ≥ max(open, close) and low ≤ min(open, close).
- Timestamps must be strictly increasing within a file.
- Any violation → **BLOCKED**. There is no repair.

**Active contract (calendar roll, causal).**
- Expiry = the third Friday of the contract month; roll date = expiry − 8 days.
- Contract k is active for bars whose timestamp date lies in [roll(k−1), roll(k)).
- The first contract is active from its first bar.

**Bars.** 1-minute bars are aggregated to 15-minute bars within each contract, as standard OHLCV. The bucket is the ceiling of the end time to 15 minutes, so a bar stamped hh:15 covers (hh:00, hh:15].

**Outcome.**
- o(t) = log(C(t+1)/C(t)) in the same contract as bar t, taken from that contract's next 15-minute bar. This holds even across its roll date.
- If that next bar ends more than 60 minutes after bar t (session break or weekend), bar t has no outcome. It is then not taught, not evaluated and not traded.
- The last bar of a contract has no outcome.

## Features u(t), F = 12, in this order

All are computed from the same contract's 15-minute bars up to and including t.
1. r1 = log(C_t/C_{t−1})
2. r2 = log(C_t/C_{t−2})
3. r4
4. r8
5. r16
6. r32
7. r92
8. hl = log(H_t/L_t)
9. vr = log(ewstd_8(r1)/ewstd_184(r1)), exponentially weighted with those halflives
10. lv = log(1+V_t)
11. sin(2π·m/1440), where m = minute of the day of the bar end
12. cos(2π·m/1440)

**Causal standardization.** Each feature is standardized over the active-bar sequence as z(t) = (x(t) − m(t−1)) / √v(t−1), where m and v are the exponentially weighted mean and variance with halflife 500 bars, updated after z(t) is formed.
- A feature is 0 until 50 defined values of it have been seen and its variance is positive.
- A feature undefined for lack of history is 0 and does not update m or v.
- m starts at the first defined value.
- u(t) = z(t) enters the frozen encoder unchanged. The encoder clips each ON/OFF channel to [0, 3].

## Arms (identical features, schedule and θ)

| Arm | Encoder | Teaching |
|---|---|---|
| A (connectome) | connectome | D(o(t)) |
| B (rewired) | rewired | D(o(t)) |
| C (shuffled teaching) | connectome | D(o(π(t))). π is a fixed permutation (PCG64 seed 20261002) of the bars that have an outcome, so its outcome distribution is identical and it carries no information about u(t). |
| D (linear baseline) | none | Exponentially weighted ridge regression of o on [1, u], λ = 1, halflife 5,000 bars. The prediction for t uses only pairs completed before t: read before write. |

Bars without an outcome are presented with no DAN event, so the schedule stays two steps per bar.

## Evaluation

**Windows.**
- Burn-in: the first two active contracts. The learner runs but is not evaluated.
- Evaluation: all later bars that have an outcome.

**Blocks.** The evaluation window is split into consecutive blocks of 1,000 evaluated bars. The final partial block is dropped. For each arm, ρ_b is the Pearson correlation of s(t) and o(t) in block b.

**Criteria.** Each is a one-sided t-test across blocks, p < 0.01.
- **H1 (learns MNQ):** mean ρ_b(A) > 0.
- **H2 (connectome adds information):** mean [ρ_b(A) − ρ_b(B)] > 0.
- **H3 (teaching-specific):** mean [ρ_b(A) − ρ_b(C)] > 0.

**Classification.**
- **`PASS_M6A0_CONNECTOME_LEARNS_MNQ`:** H1, H2 and H3 all hold.
- **`FAIL_M6A0_NO_CONNECTOME_ADVANTAGE`:** the data are valid and any of H1–H3 fails.
- **`BLOCKED_M6A0_DATA`:** any data, format or pin check fails.

Thresholds are never moved.

## Diagnostics (never criteria)

**Correlation diagnostics:**
- the whole-window ρ per arm;
- mean block ρ and p for D, and A − D.

**Trading diagnostics per arm.**
- Position p(t) = sign(s(t)), 1 MNQ contract, held over (t, t+1]. It is 0 when there is no outcome.
- PnL = p(t)·(C(t+1) − C(t))·$2 − $1.50·|p(t) − p(t−1)|.
- Reported: gross and net PnL, annualized Sharpe of net per-bar PnL, max drawdown, hit rate, turnover and a per-year breakdown.

**Run facts:** bars per contract, file SHA256s and elapsed time.

## Declared limitations and deviations

- **Single execution environment.** The run happens only in GitHub Actions: the Claude container cannot reach Google Drive, so there is no local replication. Data are downloaded inside the ephemeral runner and never committed or uploaded. Only aggregate results are persisted. The code hash, input SHA256s and output hashes are recorded.
- **The source is the raw NinjaTrader export, not the audited MNQ package.** The package's location is not established in this session.
- **Not a prop-firm evaluation.** No risk rules, no intraday position limits and a single contract.
- **Teaching is binary** (M5F0): only the sign of o is used.
- **M5F0 context.** The formal M5F0 record is `FAIL_M5F0_TEACHING_SEMANTICS`: its synthetic shuffled-teaching control failed (ρ −0.256). The learner is therefore **not qualified**, and this gate is an empirical test only. Arm C (H3) is the direct MNQ test of the same failure mode. A PASS here cannot be read without H3.

## Firewalls

- `holdout_locked`, `validation_only`, `processed`, and all Bid/Ask files stay unopened.
- No MNQ value is printed. Only the aggregate statistics listed above are reported.
