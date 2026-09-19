# Prototype 1 — Flight V2.3: canonical v003 F5 entrypoint integration
Date: 2026-09-19
Branch: homelander-p1-flight-v23-f5-entrypoint-20260919
Base: Flight V2.2 @ a7efb0ea39648bb86df68edf6306bf2f12490dd8
Status: DORMANT. Cloud static/CI proof does not imply in-game success.

## Source-confirmed defect
The unmodified v003 setter_echo_probe.lua exposes Homelander_SetterEchoProbe_Verified(), Homelander_SetterEchoProbe_PLAYER() and Homelander_SetterEchoProbe(handle). Both public entrypoints call the global core. The verified route binds the player in Flight V2.2, but the alternate _PLAYER entrypoint could run a successful echo for a different handle, set HOMELANDER_SETTER_ECHO_PASSED=true and leave HOMELANDER_FLIGHT_V22_ECHO_PLAYER from the earlier verified F5 unchanged. Before V2.3, the F6 gate could then accept a stale handle-specific F5 proof. This is a code-path finding, not an observed runtime event.

## Narrow fix
- Wrap the canonical core Homelander_SetterEchoProbe function to clear the flight-only handle binding on entry, before the canonical setter operation.
- The existing verified-F5 wrapper rebinds the proof only after the original verified F5 call succeeds with the unchanged, valid, captured current HOMELANDER_PLAYER.
- F6, active flight tick and optional F7 restore require the current functions to retain the exact core and verified wrapper identities. Reloading or replacing either entrypoint fails closed.
- The canonical v003 F5 file is not modified. The actual original verified/core/_PLAYER implementations continue to perform their own checks and same-vector echo.
- No additional direct flight velocity submit site or unrelated gameplay mutation is added.

## Test precision
The new offline test homelander_p1_build/tests/flight_v23_real_f5_integration.lua executes the original repository v003_transfer/lua_p1/setter_echo_probe.lua verbatim via dofile, then the Flight V2.3 controller. It mocks only engine APIs, vectors, player handles and physical velocity. It covers canonical verified echo and alternate PLAYER echo, invalidation after alternate echo, error/delta mismatch/mid-call player switch, player A/B binding, active flight tick and F7 restore after proof invalidation, and replaced function entrypoints. Run alongside the earlier synthetic F5/F7/finite-state tests under Lua 5.1. A source-level test cannot establish a real engine ABI or live game behavior.

## Deployment boundary
Flight V2.3 remains an independent dormant overlay, not standalone. It relies on the four baseline Lua scripts from the ordered v003 promotion chain and must not be installed in place of the first live v003/F9 test. The game root, existing canonical Flight V2/V2.1/V2.2 releases, and the v003-v016 promotion sequence are unchanged. Real in-game F5/F6/F7, camera and collision proof is still outstanding.
