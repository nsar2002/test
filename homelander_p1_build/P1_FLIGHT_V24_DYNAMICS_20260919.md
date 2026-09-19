# Flight V2.4 — deterministic movement / input regression
2026-09-19 — standalone dormant test branch
Branch: homelander-p1-flight-v24-dynamics-20260919
Base: Flight V2.3 canonical 98c764ccbbee35cc2637c389e12d195f7be13906.

Scope: execute the ACTUAL staged flight controller and the canonical unmodified v003 setter echo against engine/vector mocks; do not alter physics implementation. Tests prove numerical controller behavior and exact 1-setter-per-active-tick in a controlled simulation. Real Prototype behavior, gravity, collisions, actual camera semantics and rendering remain UNKNOWN until live testing.

Coverage: F5 actual same-vector setter echo, F6 enable, measured camera +z W movement, measured +z D/right movement, W/D release air-braking, Space ascent / Ctrl and C descent / release hover, opposite key cancellation, Shift boost acceleration, zero dt no mutation, dt 0.2 bounded to 0.05 integration step, camera rotates so W follows +x, malformed camera data with missing legacy camera triggers player-local basis, loss of focus disables without velocity rewrite, invalid dt 0.26 disables without physics write.

Default tuning tested (UNVERIFIED IN GAME): planar accel 55, boost accel 90, air brake 80, vertical accel 60, hover brake 75; dt initial 0.016. This suite must not become a proxy for live flight-feel evidence.

Additional source audit: original game's art.rcf is 496,846,408 bytes. The active Google Drive connector rejects download above 268,435,456 bytes (HTTP 413). Therefore no new full archive indexing or model extraction was performed here. Original art.rcf and game root remain unchanged. Existing past 2378-asset index and startup_effects VFX evidence may be reused but do not imply a Homelander character model exists.

Only CI evidence, documentation and isolated staging ZIP may be promoted from this branch; active v003-v016 promotion chain and real-game first gate v003 BOOT/F4/F9 are untouched.
