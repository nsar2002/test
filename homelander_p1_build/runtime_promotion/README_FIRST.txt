HOMELANDER — PROTOTYPE 1 — FAIL-CLOSED RUNTIME PROMOTION PACK v001
Date: 2026-09-19

PURPOSE
This package turns the previously separate dormant builds into ONE ordered, reversible live-test workflow.
It does NOT skip runtime evidence and it does NOT silently promote the newest build.

FROZEN PROMOTION ORDER
v001 -> v003 -> v004 -> v005 -> v006 -> v007 -> v009 -> v010 -> v011 -> v012 -> v013 -> v014 -> v015 -> v016
v008 is intentionally omitted because canonical v009 supersedes it for the F16 dynamic-stability proof.

SAFETY RULES BUILT INTO THE MANAGER
- Exact SHA256 check of every canonical ZIP before install.
- Exact SHA256 check of extracted ASI before install.
- Exact active predecessor required: no stage skipping.
- Previous live-gate PASS receipt required before the next stage.
- Existing verified binkw32.dll / binkw32Hooked.dll hashes are checked; the manager NEVER writes either loader file.
- Prototype must be closed for install / rollback / log reset.
- Full active ASI + lua_p1 snapshot before every promotion.
- Transactional restore if an install write/post-hash fails.
- Old runtime log is archived at every promotion so stale lines cannot satisfy a new gate.
- Fatal/signature/Lua error, ABORT or REFUSED text makes Check fail closed.
- Visual gates require explicit -ConfirmVisible; log submission alone is not enough.
- Rollback restores the exact preceding ASI and the entire preceding lua_p1 tree.

FIRST USE
Open PowerShell in this folder.

1) Validate the entire pack offline:
   powershell -ExecutionPolicy Bypass -File .\P1_PROMOTION_MANAGER.ps1 -Action ValidatePack

2) Show current state:
   powershell -ExecutionPolicy Bypass -File .\P1_PROMOTION_MANAGER.ps1 -Action Status

3) Install ONLY the next authorized build (initially v003):
   powershell -ExecutionPolicy Bypass -File .\P1_PROMOTION_MANAGER.ps1 -Action Install -Stage v003

The manager prints the exact key/evidence sequence for that build.
After executing it in Prototype, close the game and run the printed Check command.
Only a recorded PASS unlocks the next Install.

USEFUL COMMANDS
- What is next?
  .\P1_PROMOTION_MANAGER.ps1 -Action Next

- Clean retry after a failed/dirty runtime attempt:
  .\P1_PROMOTION_MANAGER.ps1 -Action ResetLog
  This archives the old log and invalidates the current stage's PASS token.

- Roll back exactly one installed stage:
  .\P1_PROMOTION_MANAGER.ps1 -Action Rollback

- If auto-detection cannot find the game:
  add -PrototypeRoot "X:\path\to\Prototype"

IMPORTANT VISUAL GATES
For stages that include real beam/world-effect rendering, Check will stop even when log evidence passes unless you add -ConfirmVisible.
Only use that switch when you actually saw the required effect described by the manager.

WHAT THIS PACK CANNOT DO
The cloud build environment cannot launch your local Windows Prototype process or visually inspect the rendered beam/effect. The manager minimizes the PC-side work, but the live aiming/key presses and visual confirmation are real runtime evidence and cannot be honestly replaced by static CI.

NO NEW MUTATION AUTHORIZATION
This pack ends at v016/F23. It does not contain continuous real DOT, real go_ApplyDamageAndHit hit reaction, or target-specific effect spawning beyond the already-bounded one-shot gates.