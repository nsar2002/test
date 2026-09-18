# Prototype 1 Homelander — F10 Target-Local Roundtrip Static Gate
Date: 2026-09-18
Status: STAGED / READ-ONLY / RUNTIME NOT YET EXECUTED

## go_Local2World ABI
Registration name string VA: 0x10DE2300.
Registered native wrapper/function VA: 0x102887E0.
The wrapper has a unique 24-byte prefix in the active prototypeenginef.dll:
F3 0F 10 44 24 0C 8B 44 24 08 56 8B 74 24 08 F3 0F 11 06 F3 0F 10 44 24

Static argument layout proves a hidden Vector return pointer followed by:
- LuaGOH target
- Vector localPoint

Therefore the Lua-facing contract used by existing flight code is:
    Vector go_Local2World(LuaGOH target, Vector localPoint)

The function resolves the GOH through the same 0x11282FC4 GOH table and applies the object's transform to the supplied local vector.

## Read-only inverse construction
No unproven World2Local API is required.
For a verified F9 hit GOH:
- O = go_Local2World(target, Vector(0,0,0))
- X = go_Local2World(target, Vector(1,0,0)) - O
- Y = go_Local2World(target, Vector(0,1,0)) - O
- Z = go_Local2World(target, Vector(0,0,1)) - O
- D = worldHit - O

The v005 probe requires sampled axes to be non-degenerate and effectively orthogonal.
It then computes:
- local.x = dot(D,X) / dot(X,X)
- local.y = dot(D,Y) / dot(Y,Y)
- local.z = dot(D,Z) / dot(Z,Z)

Finally it proves the result by roundtrip:
    reconstructed = go_Local2World(target, localOffset)
and requires the world-space reconstruction error to be within a small scale-aware tolerance.

## Promotion rule
F10 is read-only and only stores HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET after the roundtrip passes.
No ai_Laser, damage, VFX, velocity, physics or target mutation is executed.
The later render gate may consume this local offset only after F9 and F10 both pass in runtime logs.
