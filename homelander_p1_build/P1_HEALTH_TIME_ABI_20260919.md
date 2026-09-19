# Prototype 1 Homelander — Health / Simulation-Delta ABI Audit
Date: 2026-09-19
Status: STATICALLY PROVEN AGAINST ACTIVE P1 DLL / READ-ONLY USE

## Binary identity
- prototypeenginef.dll
- PE32 / i386
- size: 20,210,960 bytes
- SHA256: ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51

## go_GetHealth
- registered name VA: 0x10E70A20
- registration xref: VA 0x10858A2A
- native wrapper: VA 0x10856950
- registration thunk: VA 0x100485FE -> typed factory VA 0x10289900
- factory encodes exactly 1 Lua argument
- return RTTI at VA 0x1106AE7C: `.M` = float
- argument RTTI at VA 0x1106ADD8: `.?AVLuaGOH@engine@@`

Exact Lua-facing contract:
`float go_GetHealth(engine::LuaGOH target)`

## go_GetMaxHealth
- registered name VA: 0x10E709E0
- registration xref: VA 0x10858ACC
- native wrapper: VA 0x10856A90
- same typed factory VA 0x10289900
- same one-argument / float-return RTTI class

Exact Lua-facing contract:
`float go_GetMaxHealth(engine::LuaGOH target)`

## time_GetSimulationDelta
- registered name VA: 0x10E09238
- registration construction region: VA 0x1048B36A..0x1048B3BC
- binder is constructed with encoded Lua argument count 0
- return RTTI used by the binder: VA 0x1106AE7C = `.M` = float
- implementation thunk stored by the binder: VA 0x10034F68
- thunk resolves to native getter VA 0x10488FF0
- native getter is exactly `fld dword ptr [ecx+0x1088]; ret`

Exact Lua-facing contract:
`float time_GetSimulationDelta()`

The hidden C++ object context is supplied by the engine binder; Lua passes no explicit arguments.

## Engineering consequence
A target-continuity monitor may safely:
- sample health/max-health read-only
- accumulate elapsed simulation time using `time_GetSimulationDelta()`
- remain independent of render frame rate

This audit authorizes read-only telemetry only. It does not authorize continuous damage/DOT.
