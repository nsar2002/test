#!/usr/bin/env python3
"""Assemble a SOURCE-ONLY, non-installable 22-Lua P1 native-path integration candidate.

No executable/installer or promotion-state mutation. The FOUR guarded variants
replace only F9/F10/F11/F12 payload bytes under the native's existing stage names.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import sys

repo = pathlib.Path("homelander_p1_build")
native = repo / "homelander_p1.cpp"
destination = pathlib.Path(sys.argv[1]) if len(sys.argv) == 2 else pathlib.Path("stage_r008_22lua_SOURCE_ONLY")
lua_dest = destination / "lua_p1"

overrides = {
    "freeaim_probe_v004_STAGED.lua": "freeaim_probe_v004_numeric_epoch_DORMANT.lua",
    "freeaim_local_offset_probe_v005_STAGED.lua": "freeaim_local_offset_probe_v005_epoch_DORMANT.lua",
    "eye_origin_probe_v006_STAGED.lua": "eye_origin_probe_v006_failclosed_DORMANT.lua",
    "dual_eye_freeaim_render_v007_STAGED.lua": "dual_eye_freeaim_render_v007_epoch_DORMANT.lua",
}
baselines = {
    "runtime_probe.lua", "setter_echo_probe.lua",
    "flight_math_probe.lua", "heatvision_probe.lua",
}

cpp = native.read_text(encoding="utf-8")
references = []
for line in cpp.splitlines():
    anchor = 'ExecuteLuaFile(L, "'
    if anchor not in line:
        continue
    literal = line.split(anchor, 1)[1].split('"', 1)[0]
    if not literal.startswith("lua_p1" + chr(92)):
        continue
    assert literal.count(chr(92)) == 2, f"Unexpected native Lua path: {literal!r}"
    name = literal.split(chr(92))[-1]
    assert re.fullmatch(r"[A-Za-z0-9_]+[.]lua", name), name
    references.append(name)

names = sorted(set(references))
assert len(references) == 24, f"Native load occurrences changed: {len(references)}"
assert len(names) == 22, f"Native script inventory changed: {names}"
assert set(overrides) <= set(names)
assert baselines <= set(names)
load_order = []
for name in references:
    if name not in load_order:
        load_order.append(name)
assert len(load_order) == 22
assert not destination.exists(), f"Refuse to overwrite previous candidate: {destination}"
lua_dest.mkdir(parents=True)

inventory = []
for name in names:
    if name in overrides:
        source = repo / "lua_p1" / overrides[name]
        role = "guarded-F9-F12-byte-override"
    elif name in baselines:
        source = repo / "v003_transfer" / "lua_p1" / name
        role = "original-v003-byte-identical-baseline"
    else:
        source = repo / "lua_p1" / name
        role = "unmodified-native-runtime-source"
    assert source.is_file(), f"Missing complete runtime dependency: {source}"
    payload = source.read_bytes()
    assert b"\0" not in payload, f"Binary data unexpectedly stored as Lua: {source}"
    (lua_dest / name).write_bytes(payload)
    assert (lua_dest / name).read_bytes() == payload
    inventory.append({
        "native_path": "lua_p1/" + name,
        "source": str(source).replace(chr(92), "/"),
        "role": role,
        "sha256": hashlib.sha256(payload).hexdigest(),
    })
assert len(inventory) == 22
assert len([v for v in inventory if v["role"] == "guarded-F9-F12-byte-override"]) == 4

report = {
    "schema": "homelander-p1-r008-staged-source-integration/1.0",
    "status": "SOURCE_ONLY_DORMANT_NOT_INSTALLABLE",
    "native_file": str(native),
    "native_sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
    "native_lua_load_occurrences": len(references),
    "native_lua_unique_files": len(names),
    "baseline_copied_unchanged": sorted(baselines),
    "overrides_are_atomic": overrides,
    "members": inventory,
    "real_game_tested": False,
    "asi_included": False,
    "frozen_r007_release_modified": False,
    "first_live_gate": "ORIGINAL R007 stage v003 BOOT -> F4 -> F9; close game; Check",
}
(destination / "CI_EVIDENCE").mkdir(parents=True, exist_ok=True)
(destination / "CI_EVIDENCE" / "native_bootstrap_load_order.txt").write_text(
    "\\n".join(load_order) + "\\n", encoding="utf-8"
)
(destination / "INTEGRATION_MANIFEST.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print("P1_R008_22_LUA_NATIVE_PATH_INTEGRATION_PASS: 22/22, four guarded override bytes, original v003 baselines intact")
