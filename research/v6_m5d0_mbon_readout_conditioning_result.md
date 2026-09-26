# V6-M5D0 formal result

Classification: PASS_M5D0_MBON_READOUT_CONDITIONING_QUALIFIED

Protocol: `research/v6_m5d0_mbon_readout_conditioning_protocol.md`, SHA256 `50d54b9abeaa6404ce4499f0dedc1e7cbd613916d227b960cacf1aeb5b6a2726`, frozen in the protocol-only commit `de1cba0d62f5c0c2117628813fe3be5920c225a1` before any M5D0 code existed.

GitHub Actions run 36250925180; job 108428676796; head SHA b64487462890f41b732d787b7e07a0370e765a8d.
Artifact ID 10909067371; artifact digest sha256:4bd8ce4ac75d360853d056da680f8018477411fa5ad5a4bf5e5373f1c0feb11a.
Result commit a0fead41bc4acb8365c674abda18e67290d4c804.

Output provenance:
- result JSON SHA256 30063194b47253503b937ee9939e96dcfbfeb711001eccdad9d8000f2fa1b182
- stdout SHA256 6eb06b5ea20bb890d69b9d22e93482ecb6c90ef9b07bcc47c429c76c221ca3ea
- preexecution manifest SHA256 e6643348a9453d12c9e358f318a681153872b3d284dbdbf12b511eae648730c8
- M5B3B re-execution stdout SHA256 b85ad2de513d926afa8179ee3178bd5dc8b754d0a93e02f032f0c181c08d298f (identical to the original M5B3B run)

Prerequisites: M5C PASS, every frozen M5C, M5B3B and M4B0 anchor, and the MBON structure (97 bodies: 55 single-compartment, 40 multi-compartment, 2 outside the fast map) were reproduced exactly.

All criteria A–K held at all 72 θ grid points, with 0 failure records:

| Criterion | Checks |
|---|---|
| B readout exactness and bounds | 228,097 |
| C read-before-write | 864 |
| D forward depression | 864 |
| E backward potentiation | 864 |
| F reversal | 864 |
| G overlap-only odor specificity (exact law, tolerance 1e-10) | 2,592 |
| H compartment locality | 2,592 |
| I determinism | 864 |
| J permutation equivariance | 864 |
| K interface firewall | 2 |

Frozen readout: `ρ_m = Σ_{e∈E_m} w_e · g_e · z_k(e) / W_m`. It is read before write and summed in canonical (MBON bodyId, KC bodyId) order.

Reference point (η₋ = η₊ = 0.05, λ_K = λ_D = 0.5, G_MAX = 2.0), 8 trials spaced 32 steps apart:

| Paradigm | Mean R_m(A) over tested MBONs |
|---|---|
| Forward (FWD) | 0.6 |
| Backward (BWD) | 1.4 |
| Reversal, after the forward block (REV mid) | 0.6 |
| Reversal, after the backward block (REV end) | 1.0 |

These values are the same in every compartment. In every eligible compartment, every single-compartment MBON on both sides received odor-A input, so all of them were tested. A/B KC overlaps were 34–45 KCs per compartment.

Development parity: an independent local execution produced a byte-identical result JSON and stdout. Six deliberate mutants were each rejected by their target criteria during development: write-before-read, gain-blind readout, active-weight normalization, shuffled MBON mapping, sign-swapped chronology, and nondeterministic readout.

Claim boundary: this is an integration and implementation qualification. The conditioning outcomes follow analytically from the frozen M5C rule plus the readout. It is not an independent biological validation.

Guardrails remained closed: no θ selected, no valence assigned, no action mapping, synapse coordinates unopened, market/reward/PnL not loaded, Amin and M4V0 numeric values unopened.

Consequence: ρ is the frozen MBON population readout for later V6 gates, and M5D1 (valence source gate) is authorized. MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED.
