# Prototype 1 Homelander — Flight V2 Staging Design
Date: 2026-09-19
Status: DORMANT / NOT LIVE-PROVEN

## Goal
Replace the old instant-velocity Flight v1.3 controller with a simulation-delta controller that keeps the already-proven physics ABI but adds:
- gradual horizontal acceleration
- stronger boost acceleration
- air braking when W/A/S/D are released
- vertical acceleration
- hover damping toward zero vertical velocity
- measured render-camera direction with conservative fallbacks
- focus-loss fail-safe
- periodic telemetry

## Proven primitives reused
- phys_SetLinearVelocity(LuaGOH, Vector, int)
- ai_GetPhysicsVelocity(target) -> Vector strong existing runtime assumption from the v001/v003 gate chain
- time_GetSimulationDelta() -> float
- go_GetPosition / go_Local2World
- Vector constructor and mutating normalize/cross semantics
- current native held-input bridge
- HL_GetCameraFrame render-camera capture

## Deliberately NOT implemented yet
Automatic landing/takeoff thresholds are not guessed.
F4 receives a new read-only downward ground-ray telemetry probe. It records actual player-to-ground and ray-start-to-ground distances. Landing logic will be enabled only after live standing/air samples establish safe thresholds.

## Flight V2 control law
Every simulation tick:
1. read and validate simulation delta
2. read actual current physics velocity
3. decompose velocity into world-up and horizontal components
4. derive measured camera-horizontal basis; fall back to legacy camera, then player-local basis
5. build desired horizontal target from W/A/S/D
6. move current horizontal velocity toward target using acceleration * dt
7. when no horizontal input, move horizontal velocity toward zero using air-brake * dt
8. move vertical velocity toward Space/Ctrl target using vertical acceleration * dt
9. when no vertical input, move vertical velocity toward zero using hover-brake * dt
10. submit exactly one phys_SetLinearVelocity call

The controller never teleports the player and does not toggle physics/collision/health.

## Default staged values
These are tuning defaults, not claims of final feel:
- cruise speed 28
- boost speed 75
- vertical speed 22
- planar acceleration 55
- boost acceleration 90
- air brake 80
- vertical acceleration 60
- hover brake 75

All are clamped and can be overridden by Lua globals before enable.

## Safety gates
- F5 same-velocity setter echo PASS remains mandatory
- player handle is revalidated on enable and every active tick
- if player/setter identity changes, controller fail-closes
- dt outside 0..0.25 fail-closes
- smoothing step dt is capped at 0.05
- focus loss disables controller without writing a replacement velocity
- F7 remains explicit disable with pre-flight velocity restore
- no automatic PASS is emitted

## Ground telemetry
F4 downward probe:
- read-only fre_LineOfSightTest
- ignores the player
- start offset and ray length are clamped
- logs hit fraction, player-to-hit distance, ray-start-to-hit distance, hit position, normal and optional hit GOH
- no landing threshold is consumed by Flight V2

## Runtime proof still required
This branch must not be promoted based on static CI.
A later live test must separately demonstrate:
- F4 ground telemetry sanity
- F5 setter echo PASS
- F6 stationary hover behavior
- smooth W/A/S/D acceleration
- brake-to-hover behavior
- boost behavior
- vertical ascend/descend
- F7 velocity restore
- focus-loss control release
