# Prototype 1 Homelander — v012 Target Continuity / Health Telemetry Gate
Date: 2026-09-19
Status: DORMANT / READ-ONLY / RUNTIME NOT PROMOTED

## Purpose
v012 adds no power and no gameplay mutation. F19 is a read-only proof layer designed to answer the question required before DOT: can the same valid non-player target remain freshly reacquired by camera LOS for a sustained simulation-time interval while health telemetry remains readable?

## Prerequisite chain
F19 refuses unless:
- v011 has submitted its one-shot impact VFX: `HOMELANDER_IMPACT_VFX_SUBMITTED == true`
- `HOMELANDER_DAMAGE_LAST_TARGET` from F17 is still a valid GOH
- the stored target is not the player
- camera frame, LOS, hit-GOH, health and simulation-delta APIs are available

F19 is read-only and may be used for telemetry after F18 submission, but an F19 PASS does NOT substitute for the required visible F18 live PASS.

## Continuity measurement
Every foreground GOM tick:
1. read `time_GetSimulationDelta()`
2. reject non-finite/negative values or a single delta >0.25 s
3. revalidate the original F17 target GOH
4. read target health and max health
5. refresh the render-camera frame
6. reproduce the same measured three-axis forward-selection method used by F16/F17
7. perform a fresh `fre_LineOfSightTest` with player ignored
8. read the fresh hit GOH from `HL_LastRayHitGOH()`
9. count continuity time only while the fresh hit GOH equals the exact original F17 target

A different GOH, terrain/world hit, or LOS miss resets the consecutive continuity timer but does not mutate the game.

## Read-only PASS condition
The staged proof requires BOTH:
- >=2.0 seconds of uninterrupted same-target simulation time
- >=30 same-target samples during that uninterrupted interval

On PASS the script stores:
- `HOMELANDER_TARGET_CONTINUITY_PASSED=true`
- stable target
- consecutive seconds
- consecutive sample count
- baseline/current/max health telemetry

The monitor then auto-disables.

## Safety boundaries
The F19 Lua source contains no:
- go_ApplyDamage / go_ApplyDamageAndHit
- em_AddWorldEffect*
- physics or velocity setters
- teleport/health setters
- ai_Laser or LaserSight submit calls

The only persistent changes are Lua diagnostic globals.

## Future DOT rule
A later DOT dry-run may require the F19 proof, but no actual repeated damage may be promoted until the earlier live F17 damage and visible F18 impact-VFX gates pass.
