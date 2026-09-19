# Prototype 1 Homelander — v016 VFX Asset Allowlist Gate
Date: 2026-09-19
Status: DORMANT / READ-ONLY / NO WORLD-EFFECT CALL

## Purpose
F23 turns the F22 classification route into a STATIC, explicit effect-candidate allowlist. It never calls `em_AddWorldEffect`.

## Prerequisites
F23 refuses unless:
- `HOMELANDER_TARGET_CLASSIFICATION_PASSED == true`
- F22 target equals F21/F20/F19/F17 target
- player/target remain valid and distinct
- F22 route key is one of the known staged route values

## Static allowlist
- `HELICOPTER_METAL` -> primary `debrisSparks001`
- `INFECTED_ORGANIC_UNRESOLVED` -> primary `squibBlood001`
  - alternate 1: `goreBloodMistFanOut001`
  - alternate 2: `goreBloodGush001`
- `MILITARY_UNRESOLVED` -> primary `missileImpact001`; route remains unresolved
- `GENERIC` -> primary `missileImpact001`

The organic primary is now exact static asset evidence from `startup_effects.p3d.rz`, not a guessed family prefix.

## F23 output
F23 stores Lua diagnostics:
- exact target
- source F22 route
- primary effect candidate
- alternate candidate table
- asset-audit digest
- `HOMELANDER_VFX_ASSET_ALLOWLIST_PASSED=true`
- `HOMELANDER_VFX_ASSET_RUNTIME_PROVEN=false`

## Mutation boundary
F23 contains no:
- `em_AddWorldEffect*`
- `go_ApplyDamage*`
- health setters
- physics/velocity/teleport mutation
- beam/laser submit

## Runtime promotion rule
F23 is not authorization to spawn the selected effect.
A later one-shot effect gate must independently test the selected candidate after the ordered earlier live chain has passed. A candidate becomes runtime-proven only after a visible in-game result.
