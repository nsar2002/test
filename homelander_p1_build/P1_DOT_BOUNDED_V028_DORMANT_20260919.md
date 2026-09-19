# Homelander Prototype 1 — bounded continuous heat-vision trial v0.28 (DORMANT)
Date: 2026-09-19
Branch: homelander-p1-dot-bounded-staging-20260919
Base: independent, validated 22-file native bootstrap source head f4024b1b64fae5d920eb31f791b4655e58d3f38c.
Status: Lua definitions / offline tests ONLY. This version is NOT loaded by native C++, not mapped to a hotkey, not promoted into the canonical game installation.

## Source-grounded sequence
Canonical one-shot F17 source sets HOMELANDER_DAMAGE_ONESHOT_PASSED on a single go_ApplyDamage success; canonical F18 impact code CONSUMES that F17 token when impact VFX is submitted. Thus this later prototype MUST NOT require the already-consumed F17 boolean to remain true. Its evidence chain is the F18 impact submission token, F19 player-to-target continuity, the unchanged original F17 target reference, and the F20 dry-run proof (same target, >=3.0s, >=10 events, 0.10s interval and minimum event gap >=0.10s).

## Deliberately strict envelope
A manually invoked Homelander_DOTBoundedToggleV028() must refuse without all the matching Lua evidence fields, current verified player GOH, valid DIFFERENT target GOH with online_DeterminePlayerIndex(target) < 0 and a live 0 < health <= maxHealth reading. It checks actual API availability (Vector, camera and ray bridges, health getters, go_ApplyDamage).
The explicitly invoked Homelander_DOTBoundedTickV028() requires the SAME player, SAME original F17/F19/F20 target and all matching evidence on each call, finite simulation delta [0,0.25], live healthy target, fresh measured camera/LOS against that precise GOH, and a final post-callback validation immediately before the one damage setter. LOS miss, terrain hit, different GOH, expired/dead target, player swap, missing proof, invalid dt or camera aborts rather than selecting a replacement target. Only one go_ApplyDamage(target,0.10) call may occur per GOM tick after >=0.10 accumulated simulation seconds. No while/catch-up, no repeated event in the same tick. Local session budget is MAX_EVENTS=3 and MAX_PER_EVENT=0.10, so <=0.30 total damage per Lua module lifetime before any explicit fresh bootstrap. The local budget is consumed BEFORE invoking the native setter, so setter exceptions cannot accidentally generate a retry. On any trial stop the prior F20 dry-run token is consumed. Public telemetry cannot reset the local one-shot lifetime cap.
No health setter, hit vector, world effect, player velocity, teleport, go_ApplyDamageAndHit or attachment API is called.

## The significant distinction
This is a potentially MUTATING DAMAGE prototype, NOT a read-only telemetry gate. It is solely staged as a separately reviewable Lua source and not installed, auto-loaded, or wired to a live key. Offline Lua 5.1 mock tests cannot prove that the real engine's damage routing, target-class semantics, character model, AI reactions, mission scripting or LOS record are safe. The required v003-v016 real-game promotion/visual evidence must exist and a separate explicitly authorized manual live-damage stage must be built and checked before using such a module on the user's game root. Do not merge this directly into the validated active pipeline.

## Offline QA
tests/dot_bounded_v028_test.lua invokes the actual staged source with mock API/Vector and deliberately missing F20 evidence, invalid spacing, player-as-target, NaN simulation dt, LOS miss, callback player switch, two 0.05s ticks, one 0.25s tick and a final 0.10s tick. It asserts zero on-load damage, no damage after failed proof/target/miss, at most one damage on the accepted long tick, exactly three 0.10 damage calls total, consumed F20 token and inability to restart with manually reset public counter.
