# Prototype 1 Homelander — Free-Aim Static ABI Checkpoint
Date: 2026-09-18
Target: user's active prototypeenginef.dll (PE32 x86, 20,210,960 bytes)
Status: STATICALLY PROVED / RUNTIME NOT YET EXECUTED
Safety: read-only bridge stage; no damage, VFX, physics or game-file mutation.

## 1. fre_LineOfSightTest
Wrapper address in active image: 0x1058FB80.

Accepted Lua arguments:
1. Vector start
2. Vector end
3. bool
4. optional GOH ignore-object

Return contract:
- miss: one return value, boolean false
- hit: four return values: boolean true, normalized fraction, hit position Vector, hit normal Vector

Selected collision record:
- stride: 0x30 bytes
- +0x00: collision distance
- +0x04: secondary collision/object index used later by the wrapper
- +0x08: packed physics handle (low16 index / high16 generation)
- +0x18: additional collision-data selector

The wrapper's selected-record pointer is loaded at 0x1058FEA9:
  8B 74 24 14    mov esi,[esp+14h]
  6A 00          push 0

Signature used by staged v003:
  8B 74 24 14 6A 00 55 E8 ? ? ? ? 83 C4 08 85 F6 5F 5B 0F 84
Static scan result: exactly 1 match.

## 2. Physics handle -> owner game object
The LOS wrapper itself validates record+0x08 as:
- low16 physics slot index
- high16 generation
- capacity at physicsManager+0x14
- slot table at physicsManager+0x0C
- 8-byte slot layout: object pointer + generation metadata

After validation, the wrapper calls the physics object's virtual method at vtable+0x14.
The result is compared directly against the optional ignored GOH's resolved owner pointer.
Therefore this method is a proven route from the collision physics object to its owner game object.

Physics-manager reference pattern:
  0F B7 01 8B 0D ? ? ? ? 8B 51 0C 8B 04 C2 C3
Static scan: 29 matches; every match embeds the same absolute global 0x1127C600.
v003 accepts this only through a fail-closed 'all matches must agree' resolver.

## 3. Game-object handle (GOH) table
GOH resolver logic proves:
- global table pointer storage: 0x11282FC4
- packed raw GOH: low16 slot index, high16 generation
- invalid index sentinel: 0xFFFF
- slot size: 8 bytes
- slot+0x00: object pointer
- slot+0x04: generation word

Initializer allocation proves table storage size 0xC000 bytes.
0xC000 / 8 = 0x1800 = 6144 GOH slots.

GOH-table reference pattern:
  0F B7 01 66 3D FF FF 74 ? 8B 15 ? ? ? ? 0F B7 C0 8D 04 C2
  66 8B 50 04 66 3B 51 02 75 03 8B 00 C3 33 C0 C3
Static scan: 3 identical resolver bodies; every match embeds 0x11282FC4.
v003 again requires all matches to agree.

This supersedes the earlier staged PlutoConvertIndexToGOH approach:
Pluto indexes are manager-local indexes and are NOT proven to equal raw GOH slot indexes.

## 4. Pushing a real GOH into Lua
The engine helper at 0x107AD340 pushes a tag-2 Lua value:
  8B 44 24 04 8B 48 08 8B 54 24 08 89 11
  C7 41 04 02 00 00 00 83 40 08 08 C3
Static scan result: exactly 1 match.

The engine conversion at 0x107DB7D0 swaps the two 16-bit halves of the raw packed GOH before this push.
Therefore staged v003 can:
1. resolve collision physics owner pointer,
2. scan the proven 6144-slot GOH table for that owner,
3. build raw = generation<<16 | index,
4. swap the 16-bit halves,
5. push the actual Lua GOH.

Bridge name: HL_LastRayHitGOH().

## 5. Render camera capture
cm_GetCurrentRenderCameraPosition wrapper address: 0x1032C290.
It resolves:
- state = [manager+0x14]
- render camera = [state+0x44]
- output position = renderCamera + {0xC0,0xC4,0xC8}

Unique staged hook signature:
  8B 41 14 85 C0 74 28 8B 48 44 85 C9 74 21
  8B 44 24 04 D9 81 C0 00 00 00
Static scan result: exactly 1 match.

The render-camera transform begins at renderCamera+0x90.
Its three basis vectors occupy the first three 0x10-byte rows and translation is the fourth row at +0x30 (= camera+0xC0).

v003 captures the current render-camera pointer without changing the getter's behavior.
HL_GetCameraFrame() exposes:
- camera position xyz
- basis row 0 xyz
- basis row 1 xyz
- basis row 2 xyz

Before exposure it cross-checks that the position returned by the hooked engine getter agrees with camera+0xC0.

## 6. Free-aim axis selection
A fixed matrix row/sign is intentionally NOT hard-coded.
The staged Lua probe measures all three normalized camera basis rows against the normalized camera->player vector and chooses the basis axis with the highest absolute dot product, flipping only from the measured dot sign.

This is a read-only runtime disambiguation mechanism. It logs all three scores and the best-vs-second margin so the first runtime observation can confirm the camera basis semantics before any heat-vision mutation is promoted.

## 7. Staged v003 implementation
Local generated source:
- homelander_p1_v003_STAGED.cpp
- SHA256: 92df233b9c84a21ecd18ce99a0912dd3f4794987564cf033514ecdd03f69dacd

Local generated Lua:
- freeaim_probe_v004_STAGED.lua
- SHA256: 89885eecdf1dcd1f324c6cd3c3580013674639167e0849688ed7036c75678cd1

New read-only F9 path:
- refresh render-camera capture through cm_GetCurrentRenderCameraPosition
- obtain camera frame through HL_GetCameraFrame
- derive runtime view axis
- call fre_LineOfSightTest(start,end,true,player)
- obtain hit GOH through HL_LastRayHitGOH
- log/store start, forward, ray end, hit fraction, hit position, normal and GOH
- no damage, VFX, velocity or other gameplay mutation

## 8. Promotion gate
NOT runtime-promoted.
Next required checks:
1. build v003 as Win32 PE DLL/ASI;
2. verify CI/file/objdump/import/hash;
3. stage ASI + Lua additively, do not overwrite active v001/v002 files;
4. first runtime F9 must remain read-only;
5. only after F9 proves camera axis + LOS + hit GOH should free-aim heat rendering be wired into the already-proved dual-eye ai_Laser path.