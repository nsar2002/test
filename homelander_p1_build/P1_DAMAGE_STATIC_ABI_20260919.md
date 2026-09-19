# Prototype 1 Homelander — Damage ABI Static Proof
Date: 2026-09-19
Status: ACTIVE-DLL STATIC PROOF / NO GAMEPLAY MUTATION

## Authoritative binary
- File: prototypeenginef.dll
- Size: 20,210,960 bytes
- SHA256: ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51
- PE32 / i386

## go_ApplyDamage
The registered name exists in the active P1 DLL at file offset 0xDE2968.
The registration route binds native wrapper VA 0x10285730 to the two-argument typed factory at VA 0x102816E0.

Factory evidence:
- encoded argument count: 2
- return RTTI: .X = void
- arg 1 RTTI: .?AVLuaGOH@engine@@ = engine::LuaGOH
- arg 2 RTTI: .M = float

Exact Lua-facing signature class:
`void go_ApplyDamage(engine::LuaGOH, float)`

The wrapper validates the GOH against the live object table before constructing/submitting the game's damage message. The float argument is consumed as the damage value.

## go_ApplyDamageAndHit
The registered name exists at file offset 0xDE294C.
Its registration route binds native wrapper VA 0x10285AE0 to the four-argument typed factory at VA 0x10281790.

Factory evidence:
- encoded argument count: 4
- arguments: LuaGOH, float, Vector, Vector

Exact signature class:
`void go_ApplyDamageAndHit(engine::LuaGOH, float, math::Vector, math::Vector)`

The semantic meaning/order of the two Vector arguments has NOT been proven. Therefore v010 MUST NOT call go_ApplyDamageAndHit.

## Engineering decision
The first damage gate may use only `go_ApplyDamage(target, damage)`.
No hit-reaction vector API, DOT loop, world effect, velocity setter or physics mutation is promoted by this proof.
