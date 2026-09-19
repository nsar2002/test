# Flight V2.5 — fail-closed player proof across engine callbacks
Date: 2026-09-19
Status: DORMANT branch; not live-proven, not promoted to canonical v003-v016 stage chain.
Branch: homelander-p1-flight-v25-callback-guard-20260919
Base: previously validated multisystem Flight V2.4 head c600e0c726e14f09288d60ca25d5bc522d75f4e9.

Static finding: Flight V2.4 checks the current player/F5 proof at a tick's start, but later calls time_GetSimulationDelta, ai_GetPhysicsVelocity, camera/player transforms and vector methods before the only per-tick phys_SetLinearVelocity. A Lua/engine callback could replace HOMELANDER_PLAYER or revoke the F5 proof between the initial guard and velocity submit. Enable similarly reads physics/camera after its initial guard before committing state; F7 reads the saved vector magnitude after its first identity guard. These are source-level races/callback re-entrancy possibilities, not confirmed in-game occurrences.

V2.5 changes:
- valid_player requires the result of online_DeterminePlayerIndex be a finite, nonnegative integral number (NaN, positive/negative Inf and fractions rejected).
- flight_provenance_ok(h) checks exact current player, unchanged original F5 wrapper/core identities, player-validity API, and player/F5 globals once again AFTER the validity callback. On any observed mismatch it invalidates HOMELANDER_FLIGHT_V22_ECHO_PLAYER, so A->B->A cannot reuse a previously invalidated F5 token.
- F6 uses this provenance check before readback AND immediately after velocity/camera/vector callbacks, before committing S.handle / S.enabled.
- Flight tick uses this check at entry AND immediately before its sole per-tick physics setter. Any mutation of current player/F5 proof during callbacks disables flight without submitting a new velocity.
- Optional F7 restore checks provenance before reading preflight vector magnitude AND again after the magnitude read, before its separate guarded restore setter.
- No new gameplay mutation sites, no new native C++ wiring, no changes to canonical base F5 code, v003-v016 promotion stages, or original game root.

Test homelander_p1_build/tests/flight_v25_callback_guard.lua executes the actual Flight controller and original v003 setter_echo_probe.lua under engine mocks, with injected callbacks that change player during enable velocity/camera, active tick delta/velocity/camera/final validity and F7 saved-velocity read. Asserts no stale physics write and F5 binding invalidated. Includes nonfinite/fraction player-index cases plus normal tick/restore counterexamples. All historical v2.1–v2.4 and multisystem integration suites remain in CI.

Cannot prove real engine player-handle lifetime, cross-thread/native engine behavior, camera feel, collision, gravity, visual models or mission streaming via Lua mocks. Before any runtime promotion first execute the existing validated v003 BOOT/F4/F9 real game test and authoritative manager Check; Flight V2.5 remains overlay-only and dormant.
