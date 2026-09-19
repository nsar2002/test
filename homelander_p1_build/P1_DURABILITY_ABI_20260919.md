# Prototype 1 Homelander — Durability ABI / Reversibility Audit
Date: 2026-09-19
Status: STATIC ABI PROOF / READ-ONLY SNAPSHOT STAGING

## Active binary
Analyzed against the user's active `prototypeenginef.dll`:
- size: 20,210,960 bytes
- PE32 / x86
- SHA256: `ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51`

## Exact reversible float pairs

### Health
`float go_GetHealth(engine::LuaGOH target)`
- registered name VA: `0x10E70A20`
- registration xref VA: `0x10858A2A`
- wrapper VA: `0x10856950`
- typed getter factory thunk: `0x100485FE -> 0x10289900`

`void go_SetHealth(engine::LuaGOH target, float value)`
- registered name VA: `0x10E708C8`
- registration xrefs: `0x10858CC0`, `0x10858CD1`
- wrapper VA: `0x108568C0`
- typed setter factory thunk: `0x1001BE1E -> 0x102816E0`

### Maximum health
`float go_GetMaxHealth(engine::LuaGOH target)`
- registered name VA: `0x10E709E0`
- registration xref VA: `0x10858ACC`
- wrapper VA: `0x10856A90`
- typed getter factory: same `0x10289900`

`void go_SetMaxHealth(engine::LuaGOH target, float value)`
- registered name VA: `0x10E70898`
- registration xrefs: `0x10858D50`, `0x10858D61`
- wrapper VA: `0x10856A00`
- typed setter factory: same `0x102816E0`

### Damage scale
`float go_GetDamageScale(engine::LuaGOH target)`
- registered name VA: `0x10E70A30`
- registration xref VA: `0x10858A19`
- wrapper VA: `0x10856C60`
- typed getter factory: same `0x10289900`

`void go_SetDamageScale(engine::LuaGOH target, float value)`
- registered name VA: `0x10E708D8`
- registration xrefs: `0x10858C90`, `0x10858CA1`
- wrapper VA: `0x10856BD0`
- typed setter factory: same `0x102816E0`

## Typed factory proof
Getter factory `0x10289900` encodes:
- Lua argument count: 1
- return RTTI `.M` = float
- argument RTTI `.?AVLuaGOH@engine@@`

Float setter factory `0x102816E0` encodes:
- Lua argument count: 2
- return RTTI `.X` = void
- arg #1 RTTI `.?AVLuaGOH@engine@@`
- arg #2 RTTI `.M` = float

Therefore the three pairs above are suitable for a future reversible snapshot/apply/restore protocol, subject to live setter-echo validation.

## Non-reversible setters deliberately excluded

### Damageable
`void go_SetDamageable(engine::LuaGOH target, bool value)`
- registered name VA: `0x10E708EC`
- wrapper VA: `0x10856D10`
- bool setter factory thunk `0x10030742 -> 0x10280270`
- factory encodes void + LuaGOH + bool (`._N`)
- no exact `go_GetDamageable` or `go_IsDamageable` registered name exists in this P1 binary

### No pushback
`go_SetNoPushback` exists, but no exact `go_GetNoPushback` exists.
It must not be part of a reversible Homelander preset until a reliable original-state read path is proved.

### Other one-way durability setters
`go_SetMinHealth`, `go_SetProportionalDamageScale`, and `go_SetDamageScaleByAttackType` exist, but no proven symmetric getters are currently available for the corresponding state.
They are excluded from the first reversible preset.

## Required promotion strategy
1. F24 read-only snapshot of health/maxHealth/damageScale.
2. Later explicit same-value setter echo, one field at a time.
3. Require before/after equality within a tight tolerance.
4. Only after all three setter echoes pass may a bounded durability preset be considered.
5. Any real preset must capture originals first and provide explicit restore.
6. Never include damageable/noPushback in that preset without getter proof.

## Current gate
F24 performs getters only and stores a diagnostic snapshot in Lua globals.
No health/damage state is changed.
