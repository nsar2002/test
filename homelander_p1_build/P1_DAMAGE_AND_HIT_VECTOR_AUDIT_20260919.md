# Prototype 1 Homelander — go_ApplyDamageAndHit Vector Audit
Date: 2026-09-19
Status: STATICALLY PROVEN AGAINST ACTIVE P1 DLL / NOT RUNTIME-PROMOTED

## Binary identity
- prototypeenginef.dll
- PE32 / i386
- size: 20,210,960 bytes
- SHA256: ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51

## Typed Lua ABI
Registration RTTI proves:

`void go_ApplyDamageAndHit(engine::LuaGOH target, float damage, math::Vector hitPosition, math::Vector hitDirection)`

The type-level ABI is LuaGOH, float, Vector, Vector. The semantic names above are established by native helper behavior plus all direct internal call sites found below.

## Lua wrapper -> native helper
- Lua-facing wrapper: VA 0x10285AE0.
- shared native damage+hit helper: VA 0x10285850.
- wrapper call into helper: VA 0x10285B48.

Stack order at helper entry is:
1. target GOH
2. damage float
3. Vector #3
4. Vector #4

## Vector #4 is a direction
The helper copies Vector #4 to a local at 0x1028588B..0x102858B6 and immediately calls VA 0x107BAE80 at 0x102858BC.
0x107BAE80 is an in-place Vector normalization routine: it computes x^2+y^2+z^2, square-root magnitude, reciprocal magnitude, then rescales the three components.

Therefore Vector #4 is direction-like and magnitude is intentionally discarded by the helper.

## Native call-site proof
Direct calls to 0x10285850 found in the active DLL:
- 0x10285B48 — Lua wrapper
- 0x1028C323
- 0x1028C4B4
- 0x1028C612
- 0x1028C732

The non-Lua callers all follow the same construction pattern.

Representative call at 0x1028C323:
- target transform world position is read from object transform fields +0x34/+0x38/+0x3C into x/y/z registers.
- at 0x1028C280..0x1028C2A6 the code computes:
  `delta = targetWorldPosition - referenceWorldPosition`.
- at 0x1028C2DA..0x1028C307 that delta is multiplied by a scalar and placed in the later Vector argument slot.
- at 0x1028C30F..0x1028C31B the unmodified target world position is placed in the earlier Vector argument slot.
- target GOH and damage are then pushed and 0x10285850 is called.

The same target-position / scaled-delta construction is repeated at the calls around 0x1028C4B4, 0x1028C612 and 0x1028C732. The helper then normalizes the scaled delta, so its original magnitude cannot carry semantic information.

## Proven semantics
- Vector #3 = world-space hit/target position.
- Vector #4 = incoming hit/attack direction, constructed natively as approximately `targetPosition - source/referencePosition` and normalized by the helper.
- Vector #4 is NOT a surface normal.

## Integration consequence
A future hit-reaction gate may use:
- `hitPosition` = the fresh LOS hit position.
- `hitDirection` = normalized `hitPosition - beamSourcePosition`.

This does NOT authorize promotion yet. v010 remains the first one-shot damage mutation gate and must pass live before a separate damage+hit mutation is introduced.
