# Prototype 1 Homelander — v003 Clean Runtime Session Harness
Date: 2026-09-19
Status: RUNTIME TOOLING / DOES NOT ADVANCE THE GATE BY ITSELF

## Why this exists
The original v003 transfer already had hash-locked install, rollback and a log checker. The remaining reliability problem was evidence scope: an accumulated runtime log could contain old READY/F9 lines, and the old checker mainly printed booleans instead of enforcing a transaction-level verdict.

This harness does not change the v003 ASI or Lua payload.

## Default workflow
Run one command from the extracted v003 runtime-kit folder:

`powershell -ExecutionPolicy Bypass -File .\RUN_V003_LIVE_GATE.ps1`

The harness:
1. verifies every file covered by the original validated `SHA256SUMS.txt`
2. invokes the original hash-locked v003 installer in a child PowerShell process
3. re-verifies active v003 ASI and loader hashes
4. creates a unique session directory
5. moves any pre-existing runtime log into that session as `pre_session_runtime.log`
6. launches `prototypef.exe`
7. waits for the exact v003 READY line from the newly-created log
8. asks only for the unavoidable in-game actions: F4 once, aim at a clear nearby target, F9 once, then exit
9. evaluates only the clean session evidence
10. writes `v003_gate_report.json` and returns exit code 0 only on a complete PASS

## Hard PASS requirements
- exact READY build ID
- F4 dispatch
- verified player handle
- discovery END
- flight-math END
- F9 dispatch
- free-aim BEGIN
- valid CAMERA measurement with axis 1..3, finite positive camera-player distance and strictly positive measured winner margin
- a fresh HIT, not merely a MISS
- finite LOS hit fraction in [0,1]
- non-nil hit position and normal
- free-aim END
- no fatal/signature/Lua/free-aim-abort marker
- no F5/F6/F7 dispatch during the gate

A valid hit GOH/debug name is recorded when available but is not required at v003 because terrain/world geometry can legitimately have no target GOH.

## Failure behavior
The harness does not kill the game automatically and does not roll back automatically by default.
On a gate failure it prints the exact rollback command.

Optional:
`-RollbackOnFail`
restores the verified v001 backup after the game exits and the clean-session checker fails.

## Safety boundary
This harness adds no gameplay code and never promotes to v004 automatically. It only makes the first allowed live promotion test deterministic, session-scoped and fail-closed.
