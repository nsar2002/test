# Prototype 1 — complete native Lua bootstrap inventory (DORMANT)
Date: 2026-09-19
Branch: homelander-p1-bootstrap-complete-20260919
Base: validated native F24 observer source head 81e5feac81fb54cda73f465e8584860bbb0ff4d2.

## Why another checkpoint is required
Previous Flight V2/V2.1/V2.2/V2.3/V2.4/V2.5 and multisystem/F24 staging ZIPs were source overlays with four baseline Lua definitions absent. They relied on the original v003 package already having been installed into the target Lua folder. To remove that hidden content dependency from the TEST ARTIFACT, this branch packages the original, unmodified v003 baseline Lua files alongside the 18 current staged Lua definitions and an automated build-time bootstrap-path completeness report.

## Exact provenance
The four original repo files from homelander_p1_build/v003_transfer/lua_p1:
- runtime_probe.lua — Git blob SHA e0bf06ebb2b91188eb11be20bae6d719f6148823
- setter_echo_probe.lua — Git blob SHA 0f28b36eb95dd6caef910f91b05ed62db629a5d1
- flight_math_probe.lua — Git blob SHA 4913677c4955d16450e297d12f81ed31ca4e5815
- heatvision_probe.lua — Git blob SHA 82076a9d2c42f28a2631139d2ce6e91bfc60efb8

Their actual text was independently read from the validated original v003 Drive folder and compared exactly to the repository v003_transfer sources on 2026-09-19. Neither source nor Drive originals are modified. CI only copies these four files into the isolated staging artifact.

## Machine-checkable invariants
tests/bootstrap_lua_dependency_audit.py parses literal ExecuteLuaFile(L, "lua_p1\\...") references from the native C++ source, deduplicates them and requires exactly 22 unique Lua basenames. It requires all 22 staged files to exist, no unreferenced '*.lua' files in the archive's Lua folder, the four baseline files to be byte-for-byte identical to the original v003_transfer files and emits CI_EVIDENCE/bootstrap_lua_dependencies.json with SHA256 per Lua file. CI also runs the Lua 5.1 parser on all packaged Lua files and adds dependency evidence to SHA256SUMS. Real game DLL/ABI/player/asset behavior is not simulated by these completeness checks.

## Crucial boundary
A complete *Lua file inventory* is NOT a complete game mod, a standalone installer, a live promotion receipt or an authorization to skip any canonical v003-v016 live gate. The full game DLL, game archives, correct ASI loader, original effects and verified real engine calls remain necessary. The separate source ZIP contains a dormant ASI and must not overwrite an active v001 game root or bypass the official promotion manager. First real-game test remains v003 BOOT -> F4 -> F9, then authoritative Check -Stage v003. Flight F5/F6/F7 and read-only F24 must receive their own later in-game evidence.
