# Prototype 1 Homelander — v010 One-Shot Damage Gate
Date: 2026-09-19
Status: DORMANT / STAGED / RUNTIME NOT PROMOTED

## Purpose
v010 introduces the first deliberately bounded gameplay-mutation checkpoint for heat vision. It does not introduce continuous damage, DOT, hit reactions or impact VFX.

## F17 prerequisites
F17 refuses unless all of the following are true in the current Lua state:
1. `HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED == true`
2. `HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES >= 120`
3. `HL_LaserSightDynamicStabilityProbe() == true`
4. current player GOH is valid
5. camera/LOS/damage APIs are present

Therefore editing a Lua boolean alone cannot satisfy the gate.

## Fresh target acquisition
F17 does not consume a stale F9/F10/F16 endpoint.
It refreshes the render-camera capture, reads the same 12-float camera frame used by F16, resolves forward using the same measured three-axis method, and performs a new `fre_LineOfSightTest` while ignoring the player.

Mutation is refused when:
- LOS misses
- the hit has no valid GOH (terrain/world)
- the hit GOH is the player
- the target fails optional `go_IsValid` when available

## Mutation envelope
The only gameplay mutation in the v011 staged Lua is exactly one:
`pcall(go_ApplyDamage, target, damage)`

Damage defaults to 1.0 and is clamped to 0.01..1.0.
There is no go_ApplyDamageAndHit call, no DOT loop, no world effect, no velocity/physics mutation, and no legacy ai_Laser renderer.

## Fail-closed post-success behavior
After one successful submission:
- `HOMELANDER_DAMAGE_ONESHOT_PASSED=true`
- F16 dynamic rendering is force-disabled
- Lua F16 stability proof is cleared
- native F16 dynamic proof is reset

A second damage attempt therefore requires a fresh F16 enable and a new 120-submit Lua+native stability proof.

## Promotion boundary
This build remains dormant. Active game files must not be replaced before the complete earlier live chain passes:
v003/F9 -> v004/F10 -> v005/F11 -> v006/F13/F14 -> v007/F15 -> v009/F16 stability -> v010/F17.
