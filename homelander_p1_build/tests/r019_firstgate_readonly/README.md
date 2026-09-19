# R019: exact original R007 preflight + read-only first-live log chronology

This is a small optional companion tool, **not** a replacement for the frozen original R007 installer, manager or game files. The original release is stored in Google Drive as `Homelander_P1_RuntimePromotionPack_R007_CheckGameClosed_OFFLINE_CHECKED.zip`, SHA256 `d2b815620c915ff819b5b62f571d5502c53c8a7e1ad91ea88843ad74bf384a3c`. Extract that original release OUTSIDE the game folder, keep the ZIP, and identify your actual game folder containing `prototypef.exe`. Do not copy the R018 source-only candidate into the release or the game.

## Read-only preflight on your Windows PC

Open Windows PowerShell in the directory containing the R019 `P1_FIRST_GATE_READONLY_PREFLIGHT.ps1` sidecar, and run (substitute only the three actual paths):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\P1_FIRST_GATE_READONLY_PREFLIGHT.ps1 -Action Preflight -R007ZipPath "D:\Downloads\Homelander_P1_RuntimePromotionPack_R007_CheckGameClosed_OFFLINE_CHECKED.zip" -ReleaseDirectory "D:\Homelander_R007" -PrototypeRoot "D:\Games\Prototype"
```

The sidecar verifies the byte-exact original R007 ZIP, original manager and manifest, ALL 13 nested release stage ZIP hashes, exact known loader and original Bink hashes, active v001/v003 ASI and canonical five baseline Lua scripts, matching v003 F9 Lua if installed, no running Prototype process, stage-manager state and no stale v003 runtime log. A mismatch **refuses** readiness; the script does not fix/overwrite/reset anything. The examples are placeholders: use real paths. No authentic user PC/game status can be inferred from the synthetic Windows CI. R019 cannot guarantee Windows or graphics compatibility.

If the preflight prints `READY_FOR_FIRST_V003_INSTALL_AND_GAME_TEST`, run the OFFICIAL R007 `VALIDATE_PACK.cmd`, then OFFICIAL `START_V003_LIVE_TEST.cmd` from the extracted R007 directory. The original launcher is the only component permitted to promote v001→v003 with verified snapshots; R019 itself never installs, launches or records a PASS. In-game press F4, aim at a nearby NPC/vehicle and press F9; exit the game. If the preflight prints `READY_FOR_FIRST_V003_GAME_TEST`, original stage v003 is already installed with an empty log, and the same original launcher can start the test.

After the real game is closed, run R019 with `-Action InspectV003Log` and the SAME three paths. It performs an **additional non-authoritative** chronological sanity check: latest v003 READY → F4 → latest F9 dispatch → F9 BEGIN → CAMERA → nonnil HIT → END; it refuses old READY, a last F9 MISS, missing F4, incomplete/latest stale HIT or any forbidden/fatal log evidence. It does not authenticate log origin or prove visuals. Only the ORIGINAL R007 `P1_PROMOTION_MANAGER.ps1 -Action Check -Stage v003 -PrototypeRoot "ACTUAL_GAME_PATH"` can create the live-gate PASS after game shutdown, and only after actual evidence. Do not execute Check based on synthetic logs.

When a preflight is blocked by a stale log, **preserve/export the existing evidence first** using the original R007 `P1_EXPORT_LIVE_EVIDENCE.cmd`; only the original R007 manager `-Action ResetLog` may archive it for a new real attempt, and only after review. Never manually edit a log, fabricate a PASS receipt, skip v003 or install a later source-only branch. A running game blocks even the read-only snapshot to avoid racing against a changing log.

## Verification boundary

R019 source is byte-pinned to the already independently downloaded original R007 ZIP and verified original manager/manifest/v003 package hashes; it has no bypass/skip-reality switch. Windows CI validates PowerShell 5.1 parsing and synthetic positive/negative preflight plus temporal evidence. Synthetic fake game files and synthetic fake release hashes are used ONLY with a **temporary copy** of the script in CI to exercise preflight logic; the production tool's genuine R007 constants stay unchanged. No original manager, stage ZIP, native C++ code, user game, or current promotion state is modified by this sidecar or its CI. No actual game interaction is possible in CI.

The existing R008 ordered-manager candidate remains separate and not substituted into the official R007 release. Real first-live on-PC BOOT/F4/F9 remains the next necessary gate.
