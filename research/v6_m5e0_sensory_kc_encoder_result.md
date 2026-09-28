# V6-M5E0 formal result

Classification: **PASS_M5E0_SENSORY_KC_ENCODER_QUALIFIED**

All criteria A–G held.

## Provenance

- **Protocol:** `research/v6_m5e0_sensory_kc_encoder_protocol.md`, SHA256 `037704788249ac288324524ff2da426b59f6ad057c069fdd3e3ae7a49f32eb79`. Frozen in the protocol-only commit `ce8543e9add81f6114b2a0d42230e58dc1fd9a34` before the encoder was implemented or run.
- **Implementation:** commit `33051974ff7fe4ff4522a72bfe07e34b38851e8b`, `fly_mnq/v6_m5e0_sensory_kc_encoder.py`, SHA256 `35c3181380d9647a06a2fb0a47f6a1f924ee1f38531d90846090e20e82cf1a47`.
- **GitHub Actions:**
  - run 36361200150, job 108738609581, head `14db21c14260c324677f2692ac7531351eb84286`;
  - artifact 10946190205, digest `sha256:05638292ac0c419b50fea231fba50d60d8310e9d5004033e292836a38d910e06`;
  - result commit `a5fa4d73e1602e1185e7a979ebfb2e44a13ea654`.
- **Formal result JSON:** SHA256 `a778a02d5efef468b4860a020d3985fbfb664fb1ae8e3758cea941807c0a451f` (CI).
- **Wiring file:** `research/results/v6_m5e0_wiring.npz`, SHA256 `e31c8e0e…4ecd31b`. It is byte-identical between CI and the local run.

### Local/CI parity

The independent local result JSON (`789157d8…`) differs from CI in exactly two diagnostic values, both in `decorrelation.corr20`, and only in the last floating-point digits:
- `code_overlap_vs_input_cosine_correlation`: …638 in CI against …637 locally;
- `mean_input_cosine`: −…431119 in CI against −…431136 locally.

The cause is that these diagnostics use BLAS floating-point dot products, whose summation order is CPU-dependent. Everything else is identical: every criterion, every KC-code digest, the W and rewired-W digests, and the wiring npz. The encoder itself uses exact int64 drive by design, precisely so that its codes cannot differ across machines.

## Criteria

| Criterion | Outcome |
|---|---|
| A. Prerequisite parity | All hashes match. KC 4,064 (2,019 L / 2,045 R). 314 ALPN bodies, 88 types, 22,586 edges, 390,928 synapses. |
| B. Exact arithmetic | The int64 drive equals the dense float64 product bitwise, for all 5 streams in both arms. |
| C. Exact sparsity | Every code has 202 L and 205 R active KCs. |
| D. Memorylessness | Codes are unchanged when inputs at other steps change. |
| E. Channel map | Deterministic ranking; F = 44 maps 88 distinct types; F = 0, F = 45 and non-finite inputs raise. |
| F. Wiring control | Degrees and PN out-weight multisets are preserved; no duplicates; 206,063 of 225,860 swaps accepted. Retention is **0.0462**, against R0 = 0.0468 and a bound of 0.0585. The graph is fully mixed. Regeneration is identical. |
| G. Determinism | Two complete runs give identical digests. |

**Deliberate-mutant controls** were run locally on patched copies after the reference run:
- a drive offset fails B;
- one extra active KC fails C;
- step-to-step memory fails D;
- random KC reassignment fails F;
- an unseeded rewiring fails F and G;
- removing the F bound is rejected as BLOCKED, not through E. F = 45 then overflows the 88-channel map with an `IndexError`, and the run records an execution error.

## Diagnostics (not criteria)

- **Channel ranking.** The strongest channels are DP1m, DM1, DC1, DM2, DM4, VA2, DP1l, DA1, DM6, VM5d, DL1 and VA6 (all adPN/lPN uniglomerular).
- **Connectome structure.** The PN-type × KC-class χ² is **2,522 for the connectome against 264 when rewired**. Glomeruli feed specific KC classes, as in structured PN→KC sampling, and the control removes that structure about tenfold.
- **The arms code differently.** On the same i.i.d. inputs, the connectome and rewired codes share only **13.9 %** of active KCs.
- **Decorrelation.** Code overlap tracks input cosine: r = 0.754 for the i.i.d. stream and 0.936 for the correlated stream. Mean overlap is 0.45 for similar pairs (cosine > 0.5) and 0.11 for opposite pairs (cosine < −0.5), on the i.i.d. stream.
- **Coverage.** With F = 20, about 1,770 KCs per hemisphere receive positive drive, so the top-k code never falls into the zero-drive tie regime (0 % of steps).
  - With impulses (one channel active), the tie regime is entered on 50 % of steps.
  - With all-zero input it is entered on 100 % of steps. Codes there are set by bodyId ties, as declared.
- **Code composition** (connectome, i.i.d. F = 20): γ 59.9 %, αβ 31.9 %, α′β′ 8.1 %.

## Consequence

The encoder and its wiring control are frozen for later V6 gates.

- **Encoder:** market features u(t) (F ≤ 44, causally standardized by a later protocol) → ON/OFF ALPN channels → exact KC drive → M4B0 top-10 % code.
- **Control arm:** `research/results/v6_m5e0_wiring.npz` (`k_rewired`) is the degree-preserving rewired PN→KC wiring. It makes the connectome-structure hypothesis testable.

**Still to be frozen before MNQ reward opens:** DAN teaching semantics, and the MNQ walk-forward evaluation protocol with its baselines.

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED. θ is not selected.
