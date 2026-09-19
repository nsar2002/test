# Prototype 1 Homelander — v013 DOT Cadence Dry-Run Gate
Date: 2026-09-19
Status: DORMANT / READ-ONLY / NO DAMAGE CALLS

## Purpose
v013 validates the timing/state machine required for continuous heat-vision DOT without applying any damage.
F20 generates diagnostic WOULD_DAMAGE schedule events only.

## Prerequisites
F20 refuses unless:
- `HOMELANDER_TARGET_CONTINUITY_PASSED == true`
- `HOMELANDER_TARGET_CONTINUITY_TARGET` is valid
- the target equals the original `HOMELANDER_DAMAGE_LAST_TARGET`
- the target is not the player
- `HOMELANDER_IMPACT_VFX_SUBMITTED == true`
- camera/LOS/health/simulation-delta APIs are available

## Fixed staged cadence
The first cadence proof is intentionally fixed:
- interval: 0.10 simulation seconds
- target-lock segment required for PASS: >=3.0 uninterrupted simulation seconds
- minimum WOULD_DAMAGE events in that segment: 10
- maximum accepted single simulation delta: 0.25 seconds
- total monitor timeout: 15 simulation seconds

No damage amount is defined by v013 because no damage is executed.

## Fresh-target rule
Every foreground GOM tick independently refreshes camera LOS.
Cadence accumulation occurs only while the fresh hit GOH equals the exact F19-proven target.
A miss, world/terrain hit, different GOH, invalid target or stale player state cannot generate a scheduled event.

A normal LOS break resets:
- current lock-segment elapsed time
- cadence accumulator
- segment event count
- previous-event timestamp

This prevents firing immediately on an old accumulated budget after reacquisition.

## No catch-up burst rule
The scheduler uses one `if accumulator >= interval` check per GOM tick, never a `while` catch-up loop.
After one WOULD_DAMAGE event the accumulator is reset to 0.0.

Consequences:
- at most one WOULD_DAMAGE event may occur per GOM tick
- a long but accepted frame never creates multiple simulated damage events
- cadence may slow under low frame rate, but it never bursts to compensate

This is intentionally safety-biased.

## PASS condition
F20 passes only when one uninterrupted same-target segment reaches:
- >=3.0 simulation seconds
- >=10 WOULD_DAMAGE events
- zero event-spacing violations

On PASS it stores:
- stable target
- fixed interval
- segment elapsed seconds
- event count
- minimum observed event spacing
- current/max health telemetry

Then F20 auto-disables.

## Mutation boundary
The F20 source contains no:
- go_ApplyDamage / go_ApplyDamageAndHit
- em_AddWorldEffect*
- go_SetHealth/go_SetMaxHealth
- physics/velocity/teleport setters
- ai_Laser
- HL_LaserSightSubmitDual

WOULD_DAMAGE means a diagnostic schedule event only.

## Promotion boundary
An eventual real DOT gate must require:
1. live v010/F17 damage proof
2. visible v011/F18 impact proof
3. live v012/F19 continuity proof
4. live v013/F20 cadence proof

v013 itself cannot substitute for any earlier runtime proof.
