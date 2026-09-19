# Prototype 1 Homelander — v015 Target Classification / VFX Route Gate
Date: 2026-09-19
Status: DORMANT / READ-ONLY / NO EFFECT SPAWN

## Purpose
v015 classifies the exact F21-proven heat-vision target and selects a conservative future impact-VFX route without spawning any effect.

This is intentionally separated from v011/F18. F18 proved only the generic one-shot `missileImpact001` submission path. F22 prepares target-aware routing but performs no world-effect call.

## Prerequisite chain
F22 refuses unless:
- `HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED == true`
- F21 target equals F20 dry-run target, F19 continuity target and original F17 target
- player and target handles are still valid and distinct
- target-classification helper APIs are present

## Read-only classification inputs
The active P1 binary has already been statically confirmed to expose:
- `ai_GetClassName(target)`
- `go_IsHelicopter(target)`
- `go_IsFactionMilitary(target)`
- `go_IsFactionInfected(target)`
- `go_GetDebugName(target)`
- `go_GetHealth(target)`
- `go_GetMaxHealth(target)`

F22 records each query independently through `pcall`. Missing optional classification helpers fail closed only for route certainty; they do not mutate game state.

## Conservative route policy
The first route table deliberately avoids guessing detailed vehicle/character classes:

1. `go_IsHelicopter == true`
   - route: `HELICOPTER_METAL`
   - candidate effect: `debrisSparks001`
   - rationale: startup_effects analysis confirmed this real effect chunk and it is the current metal/vehicle candidate

2. `go_IsFactionInfected == true`
   - route: `INFECTED_ORGANIC_UNRESOLVED`
   - candidate effect: `missileImpact001`
   - rationale: goreBlood-family resources exist, but an exact runtime world-effect identifier has not yet been proven; therefore do not guess one

3. `go_IsFactionMilitary == true`
   - route: `MILITARY_UNRESOLVED`
   - candidate effect: `missileImpact001`
   - rationale: faction alone does not prove human vs ground vehicle vs structure

4. otherwise
   - route: `GENERIC`
   - candidate effect: `missileImpact001`

The stored candidate is advisory only. `HOMELANDER_VFX_ROUTE_RUNTIME_PROVEN` remains false.

## F22 PASS output
One successful snapshot stores:
- `HOMELANDER_TARGET_CLASSIFICATION_PASSED=true`
- exact target
- debug name
- class name string
- helicopter/military/infected flags
- health/max-health
- route key
- candidate effect
- `HOMELANDER_VFX_ROUTE_RUNTIME_PROVEN=false`

## Mutation boundary
The F22 source contains no:
- `go_ApplyDamage`
- `go_ApplyDamageAndHit`
- `em_AddWorldEffect*`
- health setter
- velocity/physics/teleport setter
- `ai_Laser`
- `HL_LaserSightSubmitDual`

## Promotion rule
A future target-specific VFX mutation must:
- preserve the exact target identity proved by F17-F22
- require a visible F18 generic effect proof first
- independently prove each new effect name in-game before treating that route as runtime-valid
- never infer organic/vehicle effect identifiers from filenames alone
