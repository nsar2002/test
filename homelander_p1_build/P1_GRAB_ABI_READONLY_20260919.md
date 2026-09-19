# Prototype 1 Homelander — Grab / super-strength ABI evidence (READ-ONLY)
Date: 2026-09-19
Status: static inspection of the actual uploaded prototypeenginef.dll only; NO gameplay mutation, NO activated power.
Branch: homelander-p1-grab-abi-readonly-20260919, isolated from canonical v016 commit 030e936dcef1196d51d9adb9c79ea71080a82b23.

## Binary identity and method
Original Drive game file ID: 1OKdocmpmC35jt273M4_fLy-JsS-fmUzu, 20,210,960 bytes, PE32/i386. SHA256 ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51; this is the same binary documented by P1_HEALTH_TIME_ABI_20260919.md.
Read-only process: find exact registered API strings, follow hardcoded pointers in registration assembly to the native function and the Lua typed factory; inspect factory encoded argument count, return RTTI and argument RTTI. VAs here use image base 0x10000000 and align with file offsets for .text/.rdata in this binary. Findings are specific to THIS DLL, not generic Prototype builds.

## go_GetGrabbedObject — two Lua arguments, not one
- name bytes at file offset 0xDE28AC, VA 0x10DE28AC.
- registration push name at VA 0x1028E234 and again at VA 0x1028E245.
- registered trampoline 0x10007077 resolves to wrapper VA 0x10286280.
- constructor trampoline 0x100073FB resolves to typed factory VA 0x10280870.
- factory pushes encoded Lua argument count 2 (VA 0x10280875), return RTTI address 0x1106ADD8 (.?AVLuaGOH@engine@@), arg 1 RTTI 0x1106ADD8 (LuaGOH), arg 2 RTTI 0x1106AE1C (.PBD, pointer-to-const char).
Static signature class: engine::LuaGOH go_GetGrabbedObject(engine::LuaGOH, char const *). This does NOT establish what the second argument means (slot identifier, object name, or something else), nor safe handle lifetime or what an empty result is in Lua. DO NOT call with a guessed string.

## go_GetGrabSlot — same typed 2-argument binder class
- name file offset 0xDE2BC8, VA 0x10DE2BC8; registration xref VA 0x1028DD4B.
- registration pushes native wrapper VA 0x10284540 and calls 0x100073FB -> factory 0x10280870.
- same binder contract as above: return LuaGOH; args LuaGOH + const char*.
- slot-string semantics/allowed values and runtime return semantics are UNPROVEN. DO NOT guess-call.

## go_IsGrabbed — distinct one-argument boolean getter
- name file offset 0xDE2888, VA 0x10DE2888; registration xref VA 0x1028E267.
- registration constructor 0x1002FFC2 resolves to factory VA 0x10288FE0.
- that factory encodes Lua count 1 (VA 0x10288FF9), return RTTI 0x1106ADC8 (._N = bool), arg RTTI 0x1106ADD8 (LuaGOH).
- static signature class: bool go_IsGrabbed(engine::LuaGOH).
- what entity/state the boolean denotes for a player in actual gameplay is NOT yet proven. No runtime call is made here.

## Mutation boundary
- go_AttachObjectToGrabSlot name exists at VA 0x10DE2BDC and registers native VA 0x100295B9 using a different binder call 0x1000FE9D; its argument and side-effect semantics are NOT decoded by this audit.
- go_GrabbedDetach name exists at VA 0x10DE2898 and registers native VA 0x10002F54 via a different binder 0x10010C6C; do not call.
- No super-strength, lifting/throwing, new object attachments or physics override are deployed. The active game root and all canonical v003-v016 stages are untouched.

NEXT: First obtain v003 real-game BOOT/F4/F9 and stable player GOH. Then read-only go_IsGrabbed(player) may be gated and compared to observed grab states, with identity/validity checks and raw values logged; never interpret it as a grabbed-object identifier. The 2-argument getters require a proven second argument and observed return before any attach/detach power can be designed.
