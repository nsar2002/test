# Prototype 1 Homelander — v011 One-Shot Impact VFX Gate
Date: 2026-09-19
Status: DORMANT / STAGED / RUNTIME NOT PROMOTED

## Purpose
v011 adds a separate F18 visual-impact checkpoint after the already-staged v010/F17 one-shot damage gate.
It does not add continuous heat vision, DOT, repeated effects, physics, velocity, or a damage+hit reaction mutation.

## F18 prerequisites
F18 refuses unless:
- `HOMELANDER_DAMAGE_ONESHOT_PASSED == true`
- v010 stored `HOMELANDER_DAMAGE_LAST_HIT_POS`
- `em_AddWorldEffect` is present
- the stored position has finite x/y/z components

F18 never performs damage and never reacquires or changes a target.

## Fixed probe payload
- effect: `missileImpact001`
- position: exact stored world-space hit position from the successful F17 LOS/damage transaction
- scale: default 0.15, hard-clamped to 0.05..0.50

The effect name is not user-selectable in v011. It was previously confirmed as a real Pure3D effect/object chunk in the user's art.rcf analysis.

## Mutation envelope
Exactly one world-effect submission is allowed:
`pcall(em_AddWorldEffect, "missileImpact001", hitPos, scale)`

Forbidden in this gate:
- go_ApplyDamage / go_ApplyDamageAndHit
- em_AddWorldEffectOriented
- em_SetPositionWorldEffect
- physics or velocity setters
- loops/repeated submissions
- legacy ai_Laser

## Return-value handling
The active P1 wrapper explicitly returns -1 after AddWorldEffect manager submission.
Therefore v011 records only SUBMITTED, never PASS, from the Lua call.
A visible in-game impact is required before any VFX runtime PASS may be claimed.

## One-shot consumption
After one successful Lua/native submission call:
- `HOMELANDER_IMPACT_VFX_SUBMITTED=true`
- the F17 pass token is consumed by setting `HOMELANDER_DAMAGE_ONESHOT_PASSED=false`
- further F18 presses refuse
- reload alone cannot re-arm F18 without a new successful F17 damage event

## Promotion boundary
Active Prototype files remain untouched.
Required live order remains:
v003/F9 -> v004/F10 -> v005/F11 -> v006/F13 -> v006/F14 -> v007/F15 -> v009/F16 -> v010/F17 -> v011/F18.
