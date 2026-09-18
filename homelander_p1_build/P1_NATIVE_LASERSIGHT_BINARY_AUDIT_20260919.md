# Prototype 1 Homelander — v006 Native LaserSight Binary Re-Audit
Date: 2026-09-19
Target: active prototypeenginef.dll
Target size: 20,210,960 bytes
Target SHA256: ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51
PE: i386 / PE32, ImageBase 0x10000000

Status: STATIC BYTE AUDIT PASS; RUNTIME NOT YET EXECUTED.

## Unique v006 signature hits in active DLL
- LuaToUserData: 0x107AD0A0 — unique 1/1
- LuaToNumber: 0x107ACEE0 — unique 1/1
- LuaPushBoolean: 0x107AD320 — unique 1/1
- NameCtor: 0x1005D5D0 — unique 1/1
- JointLocalToWorld: 0x10127810 — unique 1/1
- LaserShaderRoute: 0x100E49FC — unique 1/1
- LaserEventCreate route: 0x100E4A19 — unique 1/1
- LaserCleanupRoute: 0x100E4996 — unique 1/1
- LaserSubmit: 0x1009CEF0 — unique 1/1

## Derived LaserAction render route
LaserShaderRoute at 0x100E49FC proves:
- shader manager global slot = 0x11283350
- shader lookup thunk = 0x1002A8EC
- thunk target = 0x1009D430
- 0x1009D430 explicitly supplies DynamicCaster<pure3d::Shader> type token 0x10D9B620.

The allowlisted shader name "proto_lit_glow" occurs exactly once as ASCII in the active DLL, file offset 0xE553A0.

## StructRenderEvent<LaserSightStruct>
The LaserAction path at 0x100E4A19 pushes callback thunk 0x10020C84 and calls event allocator thunk 0x100013CA.

Thunk resolution:
- callback thunk 0x10020C84 -> 0x100E4780
- event allocator thunk 0x100013CA -> 0x100E4470

0x100E4470 proves:
- allocates 0x44 bytes
- vtable = 0x10DA2980 (RTTI-confirmed StructRenderEvent<LaserSightStruct>)
- callback stored at object +0x04
- payload handle initialized to -1 at object +0x08
- global staging event slot = 0x1130C808
- returns object +0x08, i.e. the exact 0x3C-byte LaserSight payload

Therefore v006 LaserSightPayload size 0x3C and offsets match the active native writer:
- +0x00 handle
- +0x04 context
- +0x08 flag/padding
- +0x0C endpoint A xyz
- +0x18 endpoint B xyz
- +0x24 thickness
- +0x28/+0x2C/+0x30/+0x34 RGBA
- +0x38 pure3d::Shader*

## Handle lifecycle
- handle allocator = 0x10805120
- handle validity wrapper = 0x107D4FA0 -> native validity check 0x10804BF0
- handle release = 0x107DA140
- LaserAction itself validates/releases the previous handle before creating the next render event.

The v006 one-shot bridge stores the two created handles and releases them at the beginning of the following GOM tick, matching the discovered replace/release lifecycle rather than leaking handles.

## Render context helper
0x1061AC80 initially looked as if it consumed a stack argument. Full call-site audit proves it takes no stack arguments:
- it pushes incoming ECX only as scratch storage,
- 0x10627000 overwrites that scratch with a thread-local value,
- it returns that TLS value on success or zero on failure.
Thus v006 RenderContextFn() with zero explicit arguments is correct.

## Event submit
0x1004A63D in LaserAction is only a JMP thunk to 0x1009CEF0.

0x1009CEF0 proves:
- reads global event slot 0x1130C808
- passes it to 0x10805650
- clears 0x1130C808 afterward
- returns

The v006 submit bridge therefore uses the same native event-submit function and checks that the staging slot is empty before allocation and cleared after submit.

## Joint/local endpoint transform
0x10127810 has the cdecl contract:
    Vec3* JointLocalToWorld(Vec3* out,
                            GameObject* object,
                            EngineName* jointName,
                            const Vec3* localOffset)

It copies the object's base transform, optionally combines the resolved joint transform, then calls the engine matrix*vector transform helper. v006 uses this exact helper for EYEPOINT center, left eye and right eye.

## LuaGOH packing audit
Internal packed GOH validation uses:
- low16 = slot index
- high16 = generation

0x107DB7D0 explicitly swaps the two 16-bit halves before the value is pushed through lua_pushlightuserdata.
Therefore the Lua-side lightuserdata numeric value is:
- high16 = slot index
- low16 = generation

v006 ResolveLuaGOHObject uses exactly that Lua representation, validates index/generation against GOH table 0x11282FC4, and only then returns the GameObject pointer.

## Reproducibility
v006 successful CI run #1: 35405552417
- raw ASI SHA256: 3a631118c8ee09ac4ab9463f552767ccb8ebd9ccaf0dbf80055d3323d3f2a018

v006 successful CI run #2: 35405646860
- raw ASI SHA256: cd518a3f6efd5debf497d517edc2f861817eeb5435fde8152e386657da871f80

Both binaries:
- exactly 2,212,801 bytes
- differ at only 3 byte positions
- differences map only to COFF TimeDateStamp, PE CheckSum, IMAGE_EXPORT_DIRECTORY TimeDateStamp

After zeroing those three metadata fields, the complete binaries are byte-for-byte identical:
- normalized SHA256 = 341c48a36b6cbc8c9268daff78717f7bdc3ef96f4e8ce41e30f7617036112833
- normalized remaining diff count = 0

## Promotion boundary
This audit proves static address/signature/layout/reproducibility consistency only.
It does NOT prove live renderer behavior.
Active root must remain unchanged until the earlier runtime gates pass.
