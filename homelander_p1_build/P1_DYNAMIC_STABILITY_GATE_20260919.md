# Prototype 1 Homelander — v009 Dynamic Aim Stability Gate
Date: 2026-09-19
Status: DORMANT / STAGED / RUNTIME NOT PROMOTED

## Purpose
v009 does not add a new power or gameplay mutation.
It hardens v008 dynamic free-aim rendering into a two-sided promotion proof before any future damage/DOT gate can be staged for live use.

## Native dynamic proof
New native state:
- g_laserDynamicSubmitFrames
- g_laserDynamicStabilityPassed

Only successful mode-2 / F16 dual LaserSight submits increment the dynamic counter.
At >=120 successful dynamic submits:
- g_laserDynamicStabilityPassed becomes true
- one native STABILITY PASS line is logged

HL_LaserSightDynamicStabilityProbe exposes the native proof read-only.
HL_LaserSightResetDynamicGate resets only the dynamic native counter/proof.

## Reset / invalidation graph
A new upstream proof invalidates every downstream proof:
- F13 resets F14/F15/F16 native proof
- F14 success resets F15/F16 native proof
- every new F15 enable resets F15 native proof and downstream F16 native proof
- every new F16 enable resets F16 native proof

Lua mirrors the same hierarchy:
- F13/F14 clear HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED and HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED
- new F15 clears held + dynamic Lua proof
- new F16 clears dynamic Lua proof
- Lua-state bootstrap/reload clears both

## Lua/native agreement at frame 120
v010 counts only successful native mode-2 submissions in S.frames.

When S.frames reaches exactly 120:
1. v010 queries HL_LaserSightDynamicStabilityProbe
2. if native proof is not true, dynamic mode immediately disables as a Lua/native mismatch
3. only when native proof is true does Lua set:
   - HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=true
   - HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES=120

Therefore a manually altered Lua global cannot by itself establish the full v009 proof.

## Mutation boundary
v009 remains render-only:
- no go_ApplyDamage
- no go_ApplyDamageAndHit
- no em_AddWorldEffect*
- no physics setters
- no ai_Laser

## Future mutation gate rule
A later one-shot damage probe must require BOTH:
- HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED == true
- HL_LaserSightDynamicStabilityProbe() == true

and must still reacquire/validate a fresh non-player GOH before any damage call.

Nothing in v009 is permitted to alter the active Prototype installation before the full earlier runtime chain passes.
