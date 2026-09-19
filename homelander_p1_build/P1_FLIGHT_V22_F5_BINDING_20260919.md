# Prototype 1 Homelander Flight V2.2 — F5 proof identity binding
Date: 2026-09-19
Status: DORMANT / NOT LIVE-PROVEN
Branch: homelander-p1-flight-v22-f5-binding-20260919
Base: homelander-p1-flight-v21-safety-20260919 @ 61bf07a09af378fac42ee76bf640c25d01f206f1

## Verified reason for change
The canonical v003 setter_echo_probe.lua resets/sets HOMELANDER_SETTER_ECHO_PASSED as a boolean, but never records the target LuaGOH. A successful F5 on player A can leave a true boolean after HOMELANDER_PLAYER changes to another valid player B. V2.1 checked the active handle against its own saved handle only after flight was enabled; it did not bind a past F5 proof to the F6 candidate handle. This is a source-confirmed provenance gap, NOT a claim of a witnessed in-game incident.

## V2.2 narrowly scoped correction
Flight V2.2 installs a Lua wrapper around the existing Homelander_SetterEchoProbe_Verified function only after the canonical script is loaded by the unchanged C++ bootstrap. The wrapper clears prior proof, captures HOMELANDER_PLAYER, invokes the original verified F5 with pcall, then records HOMELANDER_FLIGHT_V22_ECHO_PLAYER only when the original returned true, the global echo token is true, the player is unchanged and at least one available API verifies a valid handle. F6 requires this bound handle to equal the current player. Each active tick and the optional F7 preflight-velocity restore require the same exact binding; otherwise flight disables / restore is skipped. If the canonical original verified F5 function is missing, no flight F5 binding is possible.

## Preservation boundary
- Original canonical v003 Lua baseline is not modified; earlier v003-v016 packages and live gates are unchanged.
- The v2.1 finite-value and stale-player safety measures remain.
- No extra velocity submit sites and no damage, health, teleport, world effects or render mutations added.
- This remains a dormant Flight-specific branch. It is neither independently deployable nor inserted into the canonical promotion-manager stage sequence.
- The Flight ZIP is an overlay: its C++ bootstrap has 20 Lua file dependencies. The standalone Flight ZIP includes 16; the 4 missing baseline scripts are flight_math_probe.lua, heatvision_probe.lua, runtime_probe.lua, setter_echo_probe.lua. All four are present in the validated v003 package and persist in the ordered, merge-based promotion chain. Never install Flight V2.2 on an arbitrary game root with unverified Lua files.

## Offline tests and proof limit
The same Lua 5.1 regression suite now supplies a stub canonical verified F5 function and tests:
- a true but unbound legacy F5 boolean is refused;
- player B cannot reuse player A's F5 proof even when B is a valid player;
- a fresh verified F5 for B allows B, but prevents subsequent reuse by A;
- authorized F7 restore and invalid/stale/revoked/focus-loss suppression;
- finite input/velocity safeguards and ground telemetry fail-closed behavior.
Mocks do not validate actual Prototype F5, player identity, LuaGOH lifetimes, physics, collisions, missions or camera feel.

## Mandatory live gate
First complete the validated v003 BOOT->F4->F9 promotion; v2.2 must remain dormant pending separate live F5/F6/F7 validation with a real player transition and measured standing/air ground telemetry.
