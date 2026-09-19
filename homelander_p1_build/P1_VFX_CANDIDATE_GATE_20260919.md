# Prototype 1 Homelander — v016 Exact VFX Candidate Resolver Gate
Date: 2026-09-19
Status: DORMANT / READ-ONLY / NO EFFECT SPAWN

## Purpose
F23 converts the F22 classification route into an exact, statically proven startup_effects candidate set.
It does not spawn any effect.

## Prerequisite
F23 requires:
- `HOMELANDER_TARGET_CLASSIFICATION_PASSED == true`
- classification target equals the exact F21/F20/F19/F17 target chain
- `HOMELANDER_VFX_ROUTE_RUNTIME_PROVEN == false`

## Candidate sets
- HELICOPTER_METAL -> primary `squibMetal001`, secondary `debrisSparks001`, fallback `missileImpact001`
- INFECTED_ORGANIC_UNRESOLVED -> primary `squibBlood001`, secondary `goreBloodMistFanOut001`, fallback `missileImpact001`
- MILITARY_UNRESOLVED -> primary/fallback `missileImpact001`
- GENERIC -> primary/fallback `missileImpact001`

All names above are exact top-level Pure3D `0x23000` effect-object names from the audited startup_effects payload.

## Output
F23 stores:
- exact target
- route key
- primary candidate
- optional secondary candidate
- generic fallback
- `HOMELANDER_VFX_CANDIDATE_STATIC_PROVEN=true`
- `HOMELANDER_VFX_CANDIDATE_RUNTIME_PROVEN=false`

## Safety
No damage, world effect, laser, physics, health, teleport or velocity mutation is permitted.
