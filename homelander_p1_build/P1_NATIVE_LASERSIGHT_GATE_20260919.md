# Prototype 1 Homelander — v006 Native LaserSight Gate
Date: 2026-09-19
Status: DORMANT / STATICALLY STAGED / RUNTIME NOT PROMOTED

## Objective
Replace the legacy ai_Laser end-solution with the real engine render path recovered from LaserTrack/LaserAction RTTI and disassembly.

The active game root is NOT modified by this stage.

## Proven native route
RTTI/disassembly on the user's active prototypeenginef.dll identifies:
- proto::fightitems::motion::LaserTrack
- proto::fightitems::motion::LaserAction
- proto::LaserSight
- proto::LaserSightState
- engine::render::StructRenderEvent<proto::fightitems::motion::LaserSightStruct>

LaserAction update constructs a single-use StructRenderEvent<LaserSightStruct>, fills handle/context/endpoints/thickness/RGBA/shader, submits it to the render queue, and releases/replaces its previous LaserSight handle on the following update.

v006 mirrors only this one-shot render lifecycle; it does NOT recreate the full fight-track scheduler.

## F13 — read-only shader gate
- Resolve only allowlisted Name "proto_lit_glow".
- Use the exact LaserAction shader-manager lookup route derived from a unique active-DLL sequence.
- Require non-null readable pure3d::Shader object/vtable.
- Store no gameplay state and submit no render event.
- F14 remains closed unless F13 passes.

## F14 — one-shot real LaserSight
Prerequisites are intentionally stricter than the legacy F12 ai_Laser test:
- valid current HOMELANDER_PLAYER
- F11 verified EYEPOINT for that same player
- current valid F9 non-player target + hitpoint
- F10 target-local roundtrip state still belongs to that F9 target
- fresh go_GetJointPosition(player,"EYEPOINT") succeeds
- native joint/local-offset helper reconstructs EYEPOINT center and must agree with the fresh Lua getter within 0.02 world units

Endpoint construction:
- left eye = native EYEPOINT + local X(-halfSep)
- right eye = native EYEPOINT + local X(+halfSep)
- target = exact current F9 world hitpoint

Safety clamps:
- abs(halfSep) <= 0.25
- thickness 0.001 .. 0.50
- RGBA each 0 .. 1
- eye-to-target distance 0.05 .. 1200
- all numeric/vector values finite

F14 submits exactly two real LaserSight render events and no damage/world-effect/physics mutation.
Handles are released at the start of the next GOM tick through the same recovered LaserAction release route.

## LuaGOH audit correction
The previously labelled "LuaPushGOH" routine is actually lua_pushlightuserdata semantics.
That is correct for Prototype LuaGOH: high16 = GOH slot index, low16 = generation.
v006 LuaGOH-to-GameObject resolution validates index/generation against the same recovered GOH slot table before using the object pointer.

## Promotion order
Do not skip:
1. v003 BOOT -> F4 -> F9 read-only runtime PASS
2. v004 F10 read-only local-offset roundtrip PASS
3. v005 F11 read-only EYEPOINT PASS
4. optional F12 legacy ai_Laser falsification only
5. v006 F13 read-only shader PASS
6. v006 F14 one-shot real LaserSight visible/logged PASS
7. only then design held/continuous beam rendering
8. damage/DOT/impact VFX remain independent later gates
