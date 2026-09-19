# Prototype 1 — Homelander Flight V2.1 safety hardening
Date: 2026-09-19
Branch: homelander-p1-flight-v21-safety-20260919
Base: homelander-p1-flight-v2-staging-20260919 @ 87f4d1138af88cfa01a1305bbef2cbb1b22b38c1
Status: DORMANT / not installed / not live-proven

## Source-grounded defects in V2
1. Homelander_FlightDisableV2 previously called phys_SetLinearVelocity(h, savedVelocity, selector) when wasEnabled=true without rechecking current HOMELANDER_PLAYER, go_IsValid/online player proof or F5 setter token. A stale handle could be written during explicit F7 disable after a player transition. V2.1 skips restore when identity/validity/F5 changes or no validation API is present.
2. Flight enable stored the preflight velocity without validating finite vector magnitude or guarding Vector(v) copying. V2.1 rejects invalid velocity/copy before changing enabled state.
3. FlightTickV2 clamped tonumber(input) without testing finiteness; NaN can pass clamp comparisons. V2.1 neutralizes non-finite input and rejects non-finite measured or desired velocity before a setter call.
4. Ground telemetry clamp accepted NaN/Inf config values; a hit without hitPos could raise during vector subtraction. V2.1 restores safe defaults for non-finite ground-ray offsets/length and fails closed with PROBE_VALID=false for malformed hits/invalid vector distance operations.

## Intended and explicitly unchanged behavior
- Flight remains disabled by default and F5 setter echo remains mandatory.
- No new automatic landing/takeoff threshold is inferred.
- F7 restore on the same valid player is retained.
- Focus-loss stop writes no replacement velocity.
- No new damage, health, physics-mode, teleport, world effects or LaserSight renderer added.
- No change to native homelander_p1.cpp, the active game root or the canonical v003-v016 live promotion sequence.
- The V2.1 branch is a separate staging candidate and does not supersede the previous canonical Flight V2 package by implication.

## Offline regression scope
Run homelander_p1_build/tests/flight_v21_safety_test.lua on Lua 5.1 with local mock vectors/engine API. The suite tests authorized restore; changed/invalid player, revoked F5 and focus-loss restore suppression; NaN input; NaN preflight/current velocity; non-finite ground-ray settings; and malformed hit without position. These mocks test only Lua control flow; they do NOT validate the Prototype engine ABI, collision handling, gameplay stability or real flight behavior.

## Promotion boundary
First in-game gate remains v003 BOOT -> F4 -> F9 and authorized v003 PASS through the existing promotion manager. Flight V2.1 must stay dormant until the separate F4 standing/air ground probe and F5/F6/F7 flight-specific live tests are performed; no cloud CI PASS may be called in-game proof.
