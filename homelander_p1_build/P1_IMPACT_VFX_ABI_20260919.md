# Prototype 1 Homelander — World-Effect ABI Revalidation
Date: 2026-09-19
Status: STATICALLY REVALIDATED / DORMANT

## Binary identity
- prototypeenginef.dll
- SHA256: ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51

## Exact Lua-facing contracts
The active DLL registration factories and RTTI establish:

`int em_AddWorldEffect(const char* effectName, math::Vector worldPosition, float scale)`

`int em_AddWorldEffectOriented(const char* effectName, math::Vector worldPosition, math::Vector eulerDegrees, float scale)`

`bool em_SetPositionWorldEffect(int effectHandle, math::Vector worldPosition)`

These match the earlier Drive ABI map `P1_HEATVISION_STATIC_ABI_20260918.md`.

## em_AddWorldEffect
- real wrapper: VA 0x104F45D0.
- typed registration return RTTI: int.
- args: const char*, Vector, float.
- wrapper writes Vector #2 through VA 0x107BBBF0, which copies x/y/z into matrix translation fields +0x30/+0x34/+0x38. Thus Vector #2 is world position.
- prior static ABI work established the final float as scale; the current wrapper revalidation preserves that contract.
- wrapper explicitly ends with `or eax, 0xFFFFFFFF` at 0x104F465B, i.e. returns -1 after manager submission.

Therefore the returned int MUST NOT be treated as a spawned-effect handle.

## em_AddWorldEffectOriented
- custom typed factory: VA 0x104F3B60.
- encoded arg count: 4.
- return RTTI: int.
- args: const char*, Vector, Vector, float.
- real wrapper: VA 0x104F4C30.
- Vector #2 is again written to matrix translation via 0x107BBBF0 => world position.
- Vector #3 is multiplied component-wise by the float constant at VA 0x10D93E54.
- that constant is exactly 0.01745329238474369 = pi / 180.
- the converted vector is passed to VA 0x107BB870, which builds a rotation matrix from three angular components.

Therefore Vector #3 is Euler orientation in degrees at the Lua boundary.
The wrapper also explicitly returns -1 at 0x104F4D07.

## Asset evidence already present in Drive
The previous recursive Pure3D analysis of art.rcf / startup_effects.p3d.rz confirmed real effect/object chunks including:
- missileImpact001
- debrisSparks001
- lightGlowRed
- flare001
- headLight001

This proves asset presence, not runtime spawnability through em_AddWorldEffect.

## v011 engineering choice
The first impact-VFX gate uses only:
`em_AddWorldEffect("missileImpact001", savedF17HitPosition, scale)`

It does not use the oriented form, does not assume the -1 return is a handle, and does not call em_SetPositionWorldEffect.
Visual runtime spawnability remains a live-test item.
