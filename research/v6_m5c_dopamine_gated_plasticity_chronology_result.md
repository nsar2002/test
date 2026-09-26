# V6-M5C formal result

Classification: PASS_M5C_DOPAMINE_GATED_KC_MBON_CHRONOLOGY_QUALIFIED

Protocol: `research/v6_m5c_dopamine_gated_plasticity_chronology_protocol.md`, SHA256 `4590ab29cfba6fe9a559003286c94146cb96082bbe2f6c6d864437c5ce26eee6`, frozen in the protocol-only commit `5fcce75f15360ca6795926217b6bcb21129cba1f` before any M5C code existed.

GitHub Actions run 36249100776; job 108423664665; head SHA 2c2f5308de5574f7e39f0a3eaaf8b514d8b1b8c6.
Artifact ID 10908264258; artifact digest sha256:99e3f22bd081c8a7405bcb9b7d018035b901aff170562fb70fc482d8dec8c308.
Result commit e99ffe64ff642b85727393a9a600104956b2fd9e.

Output provenance:
- result JSON SHA256 77b9c79a70bfc589b43a53c61df253aa908dd9052a3e5a1032a3f1df7d455d5c
- stdout SHA256 d1d75bd266fcebc9b0595977028476acb1de88e90949c4550bddd9247b3f12c9
- preexecution manifest SHA256 9b0cbed7b32143bff8078fb938f03704c4192886f72529910ceed6b7aadabbca
- M5B3B re-execution stdout SHA256 b85ad2de513d926afa8179ee3178bd5dc8b754d0a93e02f032f0c181c08d298f (identical to the original M5B3B run)

Prerequisite parity: all frozen file, source and M5B3B re-execution anchors matched. The eligible-edge npz file SHA256 also matched the recorded `cc347569…` byte for byte.

Frozen structure reproduced exactly:
- KC 4064 (L 2019 / R 2045), DAN 340, MBON 97
- 328 fast-MB DANs and 12 non-fast DANs
- 61,210 KC→MBON edges: 26,532 plastic-eligible and 34,678 nonplastic
- 16 gate compartments, 12 of them carrying eligible edges

All criteria A–M held at all 72 grid points, with 0 failure records:

| Criterion | Checks |
|---|---|
| B pairing kernel exact | 6,048 |
| C order→sign | 6,048 |
| D coincidence/KC specificity | 216 |
| E compartment locality (every one of 340 DAN bodies alone) | 72 |
| F nonplastic invariance (every step of every stream) | 31,464 |
| G bounds | 31,464 |
| G saturation | 144 |
| H causality | 288 |
| I determinism | 72 |
| J permutation equivariance | 72 |
| K shared valence-agnostic rule | 6,553 |
| L M4B0 integration | 73 |
| M interface firewall | 2 |

Kernel at the reference point (η₋ = η₊ = 0.05, λ_K = λ_D = 0.5):

| Δ | 0 | +1 | +2 | +3 | −1 | −2 | −3 |
|---|---|---|---|---|---|---|---|
| Δg | −0.05 | −0.025 | −0.0125 | −0.00625 | +0.05 | +0.025 | +0.0125 |

Forward and coincident pairings depress, backward pairings potentiate, and the magnitude decays geometrically with the lag.

Development parity: an independent local execution (Python 3.12.3, same pinned numpy/pandas/pyarrow) produced a byte-identical result JSON and stdout. Nine deliberate mutants of the chronology were each rejected by their target criteria during development: sign swap, current dopamine in potentiation, current KC excluded from depression, global dopamine, sum-instead-of-mean gating, writes to nonplastic edges, no clipping, look-ahead, and nondeterminism.

Governance note: M5C has no canonical private test15 commit. The public protocol-only freeze commit is the freeze of record.

Claim boundary: this qualifies the functional form and causal chronology of the plasticity operator on the exact MaleCNS eligible-edge set. It does not select η₋, η₊, λ_K, λ_D or G_MAX, and does not validate biological amplitudes or time constants. The declared limitations of the protocol remain: hemisphere-pooled gating, one shared rule across compartments, abstract time, aggregate-edge plasticity, and synthetic binary DAN activity.

Guardrails remained closed: no parameter value selected, no valence assigned, no MBON readout defined, synapse coordinates unopened, multi-compartment edges nonplastic, market/reward/PnL not loaded, Amin and M4V0 numeric values unopened.

Consequence: a later M5D protocol may freeze, still without market data, the MBON population readout (read-before-write), DAN teaching semantics including valence from independent sources, and a non-market θ-identification procedure. MNQ reward, PnL, strategy selection, trading and prop-firm evaluation remain CLOSED.
