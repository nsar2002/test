#!/usr/bin/env python3
"""Fail-closed static audit: staged ZIP's Lua inventory vs literal native bootstrap paths.
No game execution, no installer, no new gameplay mutation.
"""
import hashlib
import json
import pathlib
import sys

repo=pathlib.Path("homelander_p1_build")
staged=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path("stage_flight_v2")
cpp=(repo/"homelander_p1.cpp").read_text(encoding="utf-8")
lua_root=staged/"lua_p1"
backslash=chr(92)
refs=[]
for line in cpp.splitlines():
    anchor='ExecuteLuaFile(L, "'
    if anchor not in line:
        continue
    literal=line.split(anchor,1)[1].split('"',1)[0]
    if not literal.startswith("lua_p1"+backslash):
        continue
    # The literal C++ source escapes each Windows separator as two slashes.
    assert literal.count(backslash)==2, f"unexpected Lua path encoding: {literal!r}"
    name=literal.split(backslash)[-1]
    assert name.endswith(".lua") and "/" not in name and backslash not in name
    refs.append(name)

required=sorted(set(refs))
assert len(required)==22, f"expected exactly 22 unique native bootstrap Lua dependencies, got {len(required)}: {required}"
existing=sorted(p.name for p in lua_root.glob("*.lua") if p.is_file())
missing=sorted(set(required)-set(existing))
unexpected=sorted(set(existing)-set(required))
assert not missing, f"missing literal native Lua dependencies: {missing}"
assert not unexpected, f"unreferenced packaged Lua files need explicit review: {unexpected}"
assert len(existing)==len(required), "duplicate packaged Lua basename"

baseline=["runtime_probe.lua","setter_echo_probe.lua","flight_math_probe.lua","heatvision_probe.lua"]
for name in baseline:
    original=(repo/"v003_transfer"/"lua_p1"/name).read_bytes()
    packaged=(lua_root/name).read_bytes()
    assert original==packaged, f"baseline v003 Lua was modified during source packaging: {name}"

# These are all source paths declared by the native bootstrap. This only proves
# on-disk static completeness, not whether Lua succeeds to load in real Prototype.
manifest={
    "status":"DORMANT_STATIC_ONLY",
    "source":"homelander_p1_build/homelander_p1.cpp",
    "unique_native_bootstrap_lua_count":len(required),
    "native_load_occurrences":len(refs),
    "baseline_v003_copied_byte_exact":baseline,
    "lua":[{"file":name,"sha256":hashlib.sha256((lua_root/name).read_bytes()).hexdigest()} for name in required],
    "runtime_proof":"NOT_PERFORMED",
    "promotion_gate":"v003 BOOT/F4/F9 first; subsequent canonical ordered gates are NOT bypassed"
}
evidence=staged/"CI_EVIDENCE"/"bootstrap_lua_dependencies.json"
evidence.parent.mkdir(parents=True,exist_ok=True)
evidence.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print("P1_BOOTSTRAP_LUA_DEPENDENCY_PASS: 22/22 native Lua files; exact four validated v003 baselines; no stale/unreferenced Lua")
