# Homelander P1 – Parallel-systems integration (DORMANT, not a promotion stage)
Date: 2026-09-19
Branch: homelander-p1-multisystem-staging-20260919
Base: independently validated Flight V2.4 source head 068a634cbd8e59a75f1d491659db3faad6fa4a72.

PURPOSE: Combine three genuine, separately staged Homelander subsystems in one Lua-state source tree, then verify there is no accidental auto-load mutation, shared-global token collision or cross-system write. This is an offline integration artifact, NOT a live gameplay conversion.

Inputs from established isolated branches:
- flight_controller_v2_STAGED.lua with F5 exact-player binding, acceleration/braking, held controls and camera fallback, previously tested in Flight V2.4.
- durability_snapshot_v02_DORMANT.lua copied verbatim from homelander-p1-durability-observer-20260919 (health/max-health/optional damage scale only).
- grab_state_v01_DORMANT.lua copied verbatim from homelander-p1-grab-abi-readonly-20260919 (one exact-binder go_IsGrabbed(player) raw boolean getter).
- Actual original v003_transfer/lua_p1/setter_echo_probe.lua under read-only engine mocks, unchanged.

Tests in tests/p1_multisystem_integration.lua:
1. module load touches no physics setter or read-only getter; flight disabled.
2. explicit canonical F5 echo and flight active tick use exactly the expected physics writes.
3. durability and grab explicit samples while flight active perform zero additional writes and record the same originating player A.
4. when current player changes from A to another valid B, Flight refuses its stale F5 proof and makes no further velocity writes, while each read-only observer samples B with independent correctly bound globals.
5. failing the durability or grab getter clears only that observer and cannot forge flight readiness.
6. a new real-canonical F5 B permits flight B, read-only observers remain nonmutating, focus-loss disables without velocity rewrite.

BOUNDARIES: Lua modules remain definitions only; the native C++ still loads only Flight as wired in v2.4 and does NOT auto-load the new durability/grab files. The combined ZIP is a SOURCE/CI overlay for further development and is NOT standalone or installable on a live game root. Four baseline v003 Lua files must remain present via the ordered canonical promotion sequence. No physical grab, super-strength, health or damage mutation, Homelander model, collision fix or automatic landing is included. No simulated result substitutes for the first real v003 BOOT/F4/F9 gate and later independent on-PC validation.
