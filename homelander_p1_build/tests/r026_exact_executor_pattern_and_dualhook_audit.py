#!/usr/bin/env python3
"""R026: source-pinned *static* Lua executor compatibility audit.

Never loads, executes, hooks or patches a game DLL. 14 source-derived pattern
matches only establish exact-build signature availability, NOT dual-ASI safety.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

GAME_SHA = "ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51"
GAME_SIZE = 20210960
LOADER_SHA = "bc48bab2cf07eaf616e23ba9eef1922ea5e8590f722b6657a8f2ed986fe6f20e"
UPSTREAM_COMMIT = "c54b297105b54dec992885e81b083c4c0b95f7d3"
UPSTREAM_INTERFACES_BLOB = "3d334b20f20842cf63f1fa964d76c3cf13b40730"
UPSTREAM_HOOKS_BLOB = "04c5aef179a2bc82e5c78d3a34d98de398ad8323"
EXPECTED_LUA = ("LuaPcall", "LuaGetField", "LuaSetTop", "LuaGetTop",
                "LuaToLString", "LuaLoadBuffer", "LuaPushCClosure",
                "LuaPushLString", "LuaPushValue", "LuaSetTable", "LuaSetField")

def extract_patterns(interfaces: str, hooks: str, native: str) -> dict[str,str]:
    found = dict(re.findall(
        r'RESOLVE_OR_FAIL\(\s*(Lua\w+)\s*,\s*"([A-Fa-f0-9? ]+)"\s*\)',
        interfaces))
    if set(found) != set(EXPECTED_LUA):
        raise ValueError("executor required Lua patterns missing/extra: " +
                         repr(sorted(set(found) ^ set(EXPECTED_LUA))))
    do = re.search(r'auto addr\s*=\s*mod\.find_pattern\("([A-Fa-f0-9? ]+)"\)',interfaces)
    man = re.search(r'GetFromSig<void\*>\([^;\n]*?"([A-Fa-f0-9? ]+)"\s*,\s*"g_pLuaScriptManager"',interfaces)
    gom = re.search(r'safetyhook::create_inline\(prototypeengine\.find_pattern\("([A-Fa-f0-9? ]+)"\)', hooks)
    own = re.search(r'kSigGOMUpdate\s*=\s*"([A-Fa-f0-9? ]+)"',native)
    if not all((do,man,gom,own)):
        raise ValueError("original or third-party mandatory dispatch signatures missing")
    if not all(x in hooks for x in ("GOMUpdate::Fn", "GetDeviceState::Fn", "GetDeviceStateKB::Fn",
                                     "EndScene::Fn", "Reset::Fn")):
        raise ValueError("third-party source changed hook surface; manual re-review required")
    if not all(x in native for x in ("bool InstallGOMUpdateHook(", "WriteBranch(target, 0xE9",
                                      "GOMUpdateHook(", "g_originalGOMUpdate")):
        raise ValueError("original native hook implementation changed; re-review required")
    found["DoLuaBuffer"] = do.group(1)
    found["LuaScriptManagerGlobal"] = man.group(1)
    found["ExecutorGOMUpdate"] = gom.group(1)
    if gom.group(1).split() != own.group(1).split():
        raise ValueError("executor and original native no longer select same GOM signature")
    if len(found) != 14:
        raise ValueError("not exactly fourteen independent required signatures")
    return found

def pattern_regex(pattern: str) -> bytes:
    parts = pattern.split()
    if not parts or any(x!="?" and not re.fullmatch(r"[A-Fa-f0-9]{2}",x) for x in parts):
        raise ValueError("invalid pattern syntax")
    return b"".join(b"." if x=="?" else re.escape(bytes.fromhex(x)) for x in parts)

def audit(image: bytes, patterns: dict[str,str], *, exact: bool=True) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if exact and (len(image)!=GAME_SIZE or digest != GAME_SHA):
        raise ValueError("wrong engine DLL: original v003 evidence SHA256/size pin failed")
    rows = []
    for name, signature in patterns.items():
        hits = [m.start() for m in re.finditer(pattern_regex(signature),image,re.DOTALL)]
        rows.append({"name":name, "matches":len(hits),
                     "file_offsets":[f"0x{x:08x}" for x in hits[:4]]})
        if len(hits) != 1:
            raise ValueError(f"{name} fails uniqueness: {len(hits)} hits")
    original_gom = next(x for x in rows if x["name"]=="ExecutorGOMUpdate")
    return {
        "schema":"homelander-p1-r026-exact-executor-source-pattern-audit/1",
        "exact_original_game_sha256":digest,
        "exact_original_game_size":len(image),
        "pinned_original_game_verified":exact,
        "upstream_commit":UPSTREAM_COMMIT,
        "source_signatures_unique":len(rows),
        "signatures":rows,
        "same_gom_update_hook_target":True,
        "same_gom_target_file_offset":original_gom["file_offsets"][0],
        "loader_allows_multiple_asi_plugins_but_not_proven_coexistence":True,
        "dual_asi_safety_verified":False,
        "lua_runtime_execution_tested":False,
        "real_player_goh_identified":False,
        "original_v003_live_gate_passed":False,
        "original_game_files_changed":False,
        "safe_next_step":"isolated disposable game copy; inspect whether both native GOM hooks coexist before any read-only Lua diagnostic, never touch frozen active v003",
    }

def selftest():
    # Synthetic non-game binary; verify a unique pattern, wildcard, duplicate,
    # missing pattern and SHA pin failure cannot silently report compatibility.
    sigs={"TestA":"53 55 ? 57","TestB":"8B 4C 24 ? 83",
          "ExecutorGOMUpdate":"12 34 56"}
    b=b"\x00"*31+bytes.fromhex("53 55 22 57")+b"\x00"*23+bytes.fromhex("8B 4C 24 44 83")+b"\x00"*8+bytes.fromhex("12 34 56")+b"\x00"*8
    out=audit(b,sigs,exact=False)
    assert out["source_signatures_unique"]==3
    assert out["dual_asi_safety_verified"] is False
    for damaged in (b+bytes.fromhex("53 55 66 57"),b.replace(bytes.fromhex("53 55 22 57"),b"\x00"*4)):
        try: audit(damaged,sigs,exact=False)
        except ValueError: pass
        else: raise AssertionError("missing/duplicate signature must fail closed")
    try: audit(b,sigs,exact=True)
    except ValueError: pass
    else: raise AssertionError("synthetic bytes accepted as user's original game")
    print("P1_R026_UNIQUE_WILDCARD_MISSING_DUPLICATE_AND_ORIGINAL_GAME_SHA_FAILCLOSED_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--engine",type=Path)
    p.add_argument("--loader",type=Path)
    p.add_argument("--upstream-interfaces",type=Path)
    p.add_argument("--upstream-hooks",type=Path)
    p.add_argument("--original-native",type=Path)
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:
        selftest();return
    if not all((a.engine,a.loader,a.upstream_interfaces,a.upstream_hooks,a.original_native)):
        p.error("all five explicit read-only input paths required")
    orig=a.original_native.read_text(encoding="utf-8")
    upstream=a.upstream_interfaces.read_text(encoding="utf-8")
    hooks=a.upstream_hooks.read_text(encoding="utf-8")
    sigs=extract_patterns(upstream,hooks,orig)
    loader=a.loader.read_bytes()
    if hashlib.sha256(loader).hexdigest()!=LOADER_SHA or b"IsUltimateASILoader\x00" not in loader:
        raise ValueError("not original user's frozen Ultimate ASI Loader")
    out=audit(a.engine.read_bytes(),sigs)
    out["exact_original_loader_sha256"]=LOADER_SHA
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
