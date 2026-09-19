#!/usr/bin/env python3
"""R026: construct one NONINSTALLABLE read-only Lua overlay for an isolated game copy.

NEVER mutate original R007/v003 source, active game, ASI, loader, manager/state.
The overlay is NOT a new promotion stage and may only be evaluated after a
separately copied game root is created and its separation confirmed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path("homelander_p1_build")
BASE = ROOT / "v003_transfer" / "lua_p1" / "runtime_probe.lua"
SOURCE = {
    "original": (BASE, "bd7a6ec2006466b0f7b46f966f384103d35d5d98020bcdce1112e9b4f363a650"),
    "census": (ROOT / "tests/r024_readonly_lua_global_census_SOURCE_ONLY.lua",
               "2b35e55c10182a26c07217e53c407f7b4984dc15044d716e70fa872510a5daf1"),
    "candidate": (ROOT / "tests/r025_closest_camera_character_observer_SOURCE_ONLY.lua",
                  "8b23d37be95c2081bacd029daeafb09747bf0d505791cc1c093851ea47f8b441"),
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: assemble_r026_clone_readonly.py NEW_OUTPUT_DIR")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("REFUSE overwrite existing diagnostic output folder")
    sources = {}
    for name, (path, expected) in SOURCE.items():
        if not path.is_file():
            raise SystemExit("Missing verified source "+str(path))
        data = path.read_bytes()
        if sha(data) != expected:
            raise SystemExit("REFUSE unverified "+name+" original source sha256 mismatch at "+str(path))
        if b"\\x00" in data:
            raise SystemExit("Binary NUL in source")
        sources[name] = data
    orig = sources["original"].decode("utf-8")
    assert "HOMELANDER_PLAYER = nil" in orig
    assert "NO VERIFIED PLAYER HANDLE" in orig
    assert "HOMELANDER_SETTER_ECHO_PASSED = false" in orig
    census = sources["census"].decode("utf-8")
    candidate = sources["candidate"].decode("utf-8")
    assert 'HOMELANDER_PLAYER =' not in census
    assert 'HOMELANDER_PLAYER =' not in candidate
    assert "go_ApplyDamage(" not in candidate and "phys_SetLinearVelocity(" not in candidate
    # Current native BridgeTick invokes the original probe once at bootstrap,
    # THEN publishes HL_BRIDGE_READY for the F4 dispatch in this Lua state.
    # Its exact timing in original v003 binary still requires test on a CLONE.
    marker = "HL_BRIDGE_READY"
    overlay = (
        orig.rstrip() +
        "\n\n-- [R026 BEGIN] NEVER install in original v003 root. Clone-only diagnostic.\n" +
        '-- No game/script state change outside the ORIGINAL v003 runtime probe.\n' +
        'if rawget(_G, "' + marker + '") == "1" then\n' +
        '    local diagnosticLog = rawget(_G, "HL_Log")\n' +
        '    if type(diagnosticLog) ~= "function" then diagnosticLog = print end\n' +
        '    diagnosticLog("[P1_R026_CLONE_DIAG] BEGIN | non-promotable read-only F4 observation")\n' +
        '    local okR026 = pcall(function()\n' +
        '        -- Bounded global KEY + TYPE diagnostic only; no userdata read.\n' +
        ''.join("        "+line+"\n" for line in census.splitlines()) +
        '        -- Registered engine candidate, but closest camera character may be NPC.\n' +
        ''.join("        "+line+"\n" for line in candidate.splitlines()) +
        '        Homelander_R025_ObserveClosestCameraCharacter()\n' +
        '    end)\n' +
        '    if not okR026 then\n' +
        '        diagnosticLog("[P1_R026_CLONE_DIAG] STOP | source-only diagnostic error; no player gate")\n' +
        '    end\n' +
        '    diagnosticLog("[P1_R026_CLONE_DIAG] END | original v003 Check NOT AUTHORIZED from cloned root")\n' +
        'end\n' +
        '-- [R026 END] Existing original v003 manager and game files untouched.\n'
    )
    out.mkdir(parents=True)
    payload = out / "lua_p1"
    payload.mkdir()
    diag = payload / "runtime_probe.lua"
    diag.write_bytes(overlay.encode("utf-8"))
    report = {
        "schema": "homelander-p1-r026-isolated-clone-readonly/1",
        "status": "SOURCE_ONLY_CLONE_DIAGNOSTIC_NOT_INSTALLABLE_NOT_PROMOTION",
        "source_v003_sha256": sha(sources["original"]),
        "source_r024_sha256": sha(sources["census"]),
        "source_r025_sha256": sha(sources["candidate"]),
        "diagnostic_runtime_probe_sha256": sha(diag.read_bytes()),
        "files_to_copy": ["lua_p1/runtime_probe.lua"],
        "require_fully_independent_game_clone": True,
        "allow_original_game_root_changes": False,
        "allow_original_R007_manager_check_on_clone": False,
        "original_v003_gate_pass": False,
        "real_game_executed": False,
        "observe_only": True,
    }
    (out/"R026_DIAGNOSTIC_MANIFEST.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("P1_R026_ORIGINAL_V003_SHA256_PINNED_CLONE_ONLY_LUA_DIAGNOSTIC_BUILT_PASS")
    print("P1_R026_DIAGNOSTIC_RUNTIME_PROBE_SHA256="+report["diagnostic_runtime_probe_sha256"])

if __name__ == "__main__":
    main()
