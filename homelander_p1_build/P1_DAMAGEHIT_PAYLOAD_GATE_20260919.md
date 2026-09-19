# Prototype 1 Homelander — v014 Damage+Hit Payload Dry-Run Gate
Date: 2026-09-19
Status: DORMANT / READ-ONLY / NO DAMAGE CALL

## Purpose
v014 prepares the exact vector payload required by `go_ApplyDamageAndHit` without calling that function.
F21 is a one-shot read-only probe.

The active-DLL semantic audit already proved:
`go_ApplyDamageAndHit(target, damage, hitPosition, hitDirection)`
where `hitDirection` is an incoming attack direction and is not a surface normal.

## Prerequisites
F21 refuses unless:
- `HOMELANDER_DOT_DRYRUN_PASSED == true`
- F20 target equals F19 continuity target and original F17 target
- current player and target GOHs are valid and different
- F11 EYEPOINT verification still belongs to the current player
- camera/LOS/joint/health APIs are available

## Fresh payload construction
F21:
1. refreshes current render-camera state
2. reconstructs camera forward using the same measured three-axis method as F16-F20
3. performs a fresh LOS with player ignored
4. requires fresh hit GOH == the exact F20-proven target
5. obtains fresh `go_GetJointPosition(player, "EYEPOINT")`
6. sets `hitPosition` to the fresh LOS hit position
7. computes raw direction = `hitPosition - EYEPOINT`
8. normalizes that vector using the engine Lua Vector method
9. verifies all world-position and direction components are finite
10. reads target health/max-health for telemetry only

## PASS output
On one valid snapshot F21 stores:
- `HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED=true`
- target GOH
- EYEPOINT source position
- fresh hitPosition
- normalized hitDirection
- raw source-to-hit distance
- target health/max-health

The probe then returns success. There is no repeated loop required beyond the one explicit F21 press.

## Mutation boundary
The F21 source contains no:
- go_ApplyDamage
- go_ApplyDamageAndHit
- em_AddWorldEffect*
- health setters
- velocity/physics/teleport setters
- ai_Laser
- HL_LaserSightSubmitDual

## Promotion rule
A future real hit-reaction mutation may consume this proven payload shape only after the live chain through F20 has passed. v014 does not authorize mutation by itself.
