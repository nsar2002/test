# Prototype 1 Homelander — v008 Dynamic Free-Aim Native LaserSight Gate
Date: 2026-09-19
Status: DORMANT / STAGED / RUNTIME NOT PROMOTED

## Purpose
v008 is the first stage that combines the proven native LaserSight renderer with fresh per-tick camera line-of-sight acquisition.

It remains render-only:
- no damage
- no DOT
- no impact/world effects
- no velocity or physics setters
- no legacy ai_Laser rendering

## Mandatory predecessor proof
F16 cannot be enabled from the earlier one-shot gate alone.

Lua requires:
- HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED == true, produced only after 120 successful F15 held-render frames.

Native code independently requires:
- g_laserHeldStabilityPassed == true, produced only after 120 successful mode-1 held submits.

Every new F15 enable calls HL_LaserSightResetHeldGate, which clears the native counter/proof.
F13, F14 and Lua-state bootstrap also invalidate held-stability proof.
HL_LaserSightHeldStabilityProbe exposes the native proof read-only so F16 can fail before arming.

## Native submit modes
HL_LaserSightSubmitDual:
- 13 args: mode 0 / F14 one-shot
- 14 args with mode=1: F15 held renderer
- 14 args with mode=2: F16 dynamic free-aim renderer
- every other 14th-arg value is refused

Mode 2 is refused unless native held stability passed.

A LaserSight slot with a still-live handle is refused rather than overwritten.
The normal GOM order remains cleanup-old-handles -> acquire/validate -> submit-current-frame.

## Dynamic camera ray
Each enabled F16 tick:
1. refresh cm_GetCurrentRenderCameraPosition so the native render-camera capture is current
2. read HL_GetCameraFrame
3. resolve camera forward exactly as the staged F9 algorithm:
   - normalize all three camera basis axes
   - compare abs(dot(axis, normalized camera->player))
   - choose the highest-scoring axis
   - flip sign only if the measured signed dot is negative
4. range defaults to 500 and is clamped 10..1000
5. call fre_LineOfSightTest(cameraStart, rayEnd, true, player)

A miss is not an error:
- prior frame handles were already released at the beginning of the GOM tick
- no new beam is submitted for that miss

A hit uses the fresh world hitpoint directly.
This is intentional: unlike held F15, F16 reacquires every frame, so there is no stale world endpoint to repair through F10 local-space reconstruction.

HL_LastRayHitGOH is called only after a LOS hit and is diagnostic:
- valid non-player GOH -> HOMELANDER_DYNAMIC_HIT stores it
- terrain/static-world hit without a valid GOH is still renderable from the fresh hitPos

The script writes only HOMELANDER_DYNAMIC_* diagnostics and does not overwrite the canonical F9/F10 free-aim globals.

## Eye/render route
Fresh go_GetJointPosition(player,"EYEPOINT") supplies the expected eye center.
Native mode 2 independently:
- resolves player GOH to GameObject through validated slot/generation
- uses the recovered native JointLocalToWorld helper and engine-preconstructed EYEPOINT Name
- checks native EYEPOINT center against the fresh Lua eye point within 0.02
- derives left/right eye endpoints with local +/-X separation
- submits exactly two real StructRenderEvent<LaserSightStruct> events

All v006 geometry/color/distance clamps still apply.

## Mutual exclusion
- F15 explicitly force-disables F16 before toggling held mode.
- F16 enabling force-disables F15 held mode.
- focus loss force-disables both modes.
- dynamic submit/native stability failure auto-disables F16.

## Bounded first-stage runtime
Defaults:
- max successful dynamic render frames: 600
- max total F16 ticks: 1800

Clamps:
- render frames: 60..3600
- total ticks: 120..7200

These bounds prevent a first-stage renderer from remaining armed indefinitely during live validation.

## Promotion rule
Do not promote v008 until the exact runtime chain passes:
v003 F9 -> v004 F10 -> v005 F11 -> v006 F13 -> v006 F14 -> v007 F15 120-frame stability -> v008 F16 dynamic rendering.

Only after F16 itself is stable may damage/DOT or target-specific impact effects be staged, and those remain separate mutation gates.
