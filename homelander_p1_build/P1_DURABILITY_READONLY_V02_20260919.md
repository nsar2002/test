# P1 durability read-only observer — staged parallel Homelander power
Date: 2026-09-19
Branch: homelander-p1-durability-observer-20260919
Base: canonical v016 source commit 030e936dcef1196d51d9adb9c79ea71080a82b23
STATUS: definition-only, not in native bootstrap, not loaded in active game, not a durability power.

Source: the user's earlier Google Drive durability_snapshot_probe_STAGED.lua (ID 1qMzFPGlX1r13cvDr8aawFkM9ndWOL-h7) provided a preliminary read-only sample. This isolated v0.2 rewrite tightens provenance/values and preserves the no-mutation boundary.

Observed static engine API evidence: original Prototype engine DLL supports go_GetHealth(player) and go_GetMaxHealth(player), each LuaGOH -> float, documented in P1_HEALTH_TIME_ABI_20260919.md. Earlier project research named go_GetDamageScale as an available getter, but its live return range and semantics are not validated. It is optional and logged as an observation, never used to control health/damage. No write API is used.

The function Homelander_DurabilitySnapshotV02 clears prior samples, verifies current player handle via available validity/player-index routes, reads health and max-health through pcall and checks finite 0<=health<=maxHealth/maxHealth>0. Optional damage-scale read must return a finite nonnegative number if implemented. It checks player identity/validity again after callbacks and stores one Lua-only table {player, health, max_health, damage_scale} if successful. Any failed sample stays invalid rather than reusing past measurements. Simply loading the Lua file makes no engine calls.

The offline Lua 5.1 test asserts zero reads or writes on file load; valid sample, invalid/changed player, getter exceptions, invalid max health, NaN/Inf data, optional getter absence, missing validity API, and zero use of all stubbed gameplay/physics setters.

Not in the canonical promotion chain and not packaged as an active ASI. This is preparatory read-only telemetry for a later durability design. NO claim that Homelander is invulnerable, that a health/damage mutation is safe or that runtime values have been measured. Real tests require v003 player handle evidence and a separate explicit live stage. The existing v003-v016 staged packages, Flight V2/V2.1/V2.2/V2.3/V2.4 and source game installation are untouched.
