# V6-M4B0 functional APL abstraction protocol

STATUS: FROZEN BEFORE IMPLEMENTATION RESULT.

Canonical private protocol commit: 21e3c82bc091731f0ed733b01734adce3a74b905.

APL is represented only as a fixed functional KC sparsifier, not as a quantitative biophysical simulation. For each source-defined anatomical hemisphere with N eligible KCs, p=0.100 and k=floor(p*N+0.5). Require 0.095 <= k/N <= 0.105. Given finite instantaneous scores u_i, select exactly the top k by descending score with ascending immutable MaleCNS bodyId as the exact-tie breaker; selected KCs output 1 and all others 0.

No amplitude, threshold, gain, temperature, exponent, kappa, lambda, ROI coefficient, adaptive state, or trainable APL parameter is permitted.

Frozen no-market parity tests: exact active count, binary output, deterministic tie handling, top-k correctness, positive-scale invariance for {0.01,0.1,1,10,100}, common-offset invariance for {-100,-1,0,1,100}, joint score/bodyId permutation equivariance, hemisphere isolation, and absence of reward/DAN/MBON/action/market/future inputs. Synthetic tests use NumPy PCG64 seed 20260919 and 256 observations per hemisphere plus explicit ties.

Formal classes:
- PASS_M4B0_FUNCTIONAL_APL_ABSTRACTION_UNIT_PARITY
- BLOCKED_M4B0_MALECNS_KC_IDENTITY
- FAIL_M4B0_FUNCTIONAL_APL_ABSTRACTION_PARITY

A PASS authorizes only no-market downstream learning-rule/unit-test work and source-only KC/DAN/MBON circuit identification. It does not validate exact APL electrical/calcium/GABA amplitudes and does not authorize MNQ/reward/PnL learning. Amin numerical holdouts, M4V0 numerical values, M3F4 residuals, and V5 transfer residuals cannot define or tune this operator.
