# Prototype 1 Homelander — v007 Held Native LaserSight Gate
Date: 2026-09-19
Status: DORMANT / STAGED / RUNTIME NOT PROMOTED

## Scope
v007 tests only whether the already recovered native LaserSight lifecycle can be sustained across GOM ticks.

It does NOT:
- reacquire a new camera ray each frame
- change the F10-proven impact point
- apply damage/DOT
- spawn world effects
- change velocity or physics

The target-local F10 impact point is transformed through the target's CURRENT transform each tick, so the beam follows that same surface/local point if the target moves.

## Hard prerequisite
Held submit has a double same-session prerequisite:
1. Lua requires HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK == true and the successful F14 target to equal the current F9/F10 target.
2. Native code independently requires g_laserOneShotPassed == true before accepting the 14-argument quiet/held form of HL_LaserSightSubmitDual.

Re-running F13 clears the native one-shot pass gate.
Bootstrap also clears it.

Therefore F15 cannot bypass F14 by manipulating Lua globals alone.

## Lifecycle
At the beginning of every GOM tick:
- CleanupLaserSightHandles releases any prior left/right LaserSight handles through the recovered LaserAction release path.

When v009 held state is enabled and the Prototype window has foreground:
- validate F13/F14/F11/F9/F10 state
- reconstruct current target endpoint with go_Local2World(target, F10 local offset)
- refresh EYEPOINT with go_GetJointPosition
- native code independently reconstructs EYEPOINT center/left/right through the recovered joint-local helper
- native center must agree with the fresh Lua eye point within 0.02
- submit exactly two LaserSight events

The 14th numeric argument to HL_LaserSightSubmitDual marks a quiet held submit.
Successful held frames do not emit per-frame native success logs.
Lua emits a heartbeat every 120 successful frames.

## F15 controls
- F15 rising edge toggles held mode.
- enabling refuses unless F14 succeeded in this same runtime session.
- disabling is immediate.
- focus loss force-disables held state.
- invalid player/target/F10/F11 state auto-disables.
- native submit failure auto-disables.

## Safety bounds
Inherited from v006 on every frame:
- abs(half eye separation) <= 0.25
- thickness 0.001 .. 0.50
- RGBA each 0 .. 1
- eye-to-target distance 0.05 .. 1200
- finite vectors/numbers only
- valid LuaGOH generation/index route only

## Promotion boundary
v007 is NOT allowed into the active root until:
v003 F9 runtime PASS -> v004 F10 PASS -> v005 F11 PASS -> v006 F13 PASS -> v006 F14 visible/logged PASS.

After a live held-render stability PASS, the next independent stage may add quiet per-frame free-aim reacquisition.
Damage/DOT/VFX remain later independent gates.
