# Homelander P1 — optional native observer dispatch (V2.6 DORMANT)
Date: 2026-09-19
Branch: homelander-p1-observer-native-20260919
Base: Flight V2.5 callback-guard head c01d4de3788b45707a4ef25c9d41631d12b7eea7.
Status: compiled/staged engineering branch ONLY; NOT installed in active Prototype game root, not in canonical promotion-manager chain.

## Real integration advancement
Previous flight/durability/grab multisystem package only contained Lua definitions for the read-only observers and did not load or call them from the native Win32 ASI. This branch adds the missing native wiring:
- BootstrapLuaState optionally loads lua_p1/durability_snapshot_v02_DORMANT.lua and lua_p1/grab_state_v01_DORMANT.lua as definition-only modules, stores separate ready flags, and preserves g_scriptsReady=setter&&math&&controller (observer loading is NOT a flight prerequisite).
- One new rising-edge VK_F24 manual diagnostic dispatch executes at most one Homelander_DurabilitySnapshotV02() call and at most one Homelander_GrabStateProbeV01() call, each individually guarded by its load-ready flag.
- The hotkey is evaluated only with game foreground input enabled; repeated GOMUpdate ticks while F24 is held do not repeat the snapshots. g_f24Prev is reset with the existing F4..F23 state on new Lua bootstrap. There are no automatic samples on boot or every frame.
- F4..F23, damage/render/flight/physics sites and canonical v003-v016 stage source remain untouched. The new observer modules do not call setter or gameplay mutation functions, and no health/strength/invulnerability/physical-grab power is enabled.
- F24 is a Windows virtual key with no dedicated key on most consumer keyboards. An eventual live test must use a verified input method; none is provided or claimed here. No automatic key injection on the user's PC is performed.

## Test boundaries and prerequisites
Win32 PE32 compile, static native source checks and Lua 5.1 simulated multisystem tests can establish that this optional dispatch is linked and intended to be read-only; none proves original Prototype runtime accepts the getter or that the logged values correspond to Homelander-strength behavior. The full staged ASI still names four baseline v003 Lua dependencies and heatvision staged Lua assets from the ordered promotion chain. This source ZIP is an overlay ONLY, NEVER standalone and NEVER install it into unverified game root. Before in-game F24 tests the validated v003 BOOT/F4/F9 real-game gate and subsequent explicit relevant stage checks remain mandatory.
