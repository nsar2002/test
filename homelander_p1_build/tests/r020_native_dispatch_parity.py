#!/usr/bin/env python3
"""R020: static native F4/F9-F21 Lua-dispatch provenance audit. NOT ABI/gameplay proof."""
from pathlib import Path
import re
import sys
base=Path("homelander_p1_build")
cpp=(base/"homelander_p1.cpp").read_text(encoding="utf-8")
stage=Path(sys.argv[1]) if len(sys.argv)==2 else Path("stage_r020_source")
lua=stage/"lua_p1"
order=(stage/"CI_EVIDENCE"/"native_bootstrap_load_order.txt").read_text().splitlines()
assert len(order)==22 and len(order)==len(set(order)), "wrong actual native definition inventory"
for name in order:
    assert re.fullmatch(r"[A-Za-z_0-9]+[.]lua", name), name
    assert (lua/name).is_file(), name
# F4 is native's *actual*, repeated ExecuteLuaFile, NOT the synthetic assignment
# of a player to A in the R018 full-source smoke.
f4=re.search(r"if\s*\(RisingEdge\(VK_F4.*?\n\s*\}(?=\s*if\s*\(RisingEdge\(VK_F5)", cpp, re.S)
assert f4, "native F4 dispatch changed"
block=f4.group()
for s in (
    'ExecuteLuaFile(L, "lua_p1\\\\runtime_probe.lua")',
    'CallLua0(L, "Homelander_FlightMathProbe_Verified")',
    'Log("F4: read-only discovery + flight math probe")',
):
    assert s in block, ("actual native F4 no longer invokes original player discovery", s)
assert block.index('ExecuteLuaFile(L, "lua_p1\\\\runtime_probe.lua")')<block.index('CallLua0(L, "Homelander_FlightMathProbe_Verified")')
source=(lua/"runtime_probe.lua").read_text()
assert 'HOMELANDER_PLAYER = nil' in source
assert 'if PLAYER ~= nil then' in source
assert 'online_DeterminePlayerIndex' in source
assert 'NO VERIFIED PLAYER HANDLE' in source
assert 'HOMELANDER_PLAYER = verified' in source
print("P1_R020_NATIVE_F4_REEXECUTES_UNMODIFIED_PLAYER_DISCOVERY_NOT_MOCK_ASSIGNMENT_PASS")
expected={
  9:"Homelander_FreeAimProbe",
  10:"Homelander_FreeAimLocalOffsetProbe",
  11:"Homelander_EyeOriginProbeV006",
  12:"Homelander_DualEyeFreeAimRenderProbe",
  13:"Homelander_LaserSightShaderProbeV008",
  14:"Homelander_LaserSightOneShotV008",
  15:"Homelander_LaserSightHeldToggleV009",
  16:"Homelander_DynamicAimToggleV010",
  17:"Homelander_HeatVisionDamageOneShotV011",
  18:"Homelander_ImpactVFXOneShotV012",
  19:"Homelander_TargetContinuityToggleV013",
  20:"Homelander_DOTDryRunToggleV014",
  21:"Homelander_DamageHitPayloadProbeV015",
}
all_lua="\n".join((lua/name).read_text() for name in order)
for key,fn in expected.items():
    m=re.search(r"if\s*\(RisingEdge\(VK_F"+str(key)+r",.*?\n\s*\}(?=\s*if\s*\(RisingEdge\(VK_F"+str(key+1)+r")",cpp,re.S)
    assert m, f"missing exact F{key} native rising-edge dispatcher"
    assert m.group().count('CallLua0(L, "'+fn+'"')==1, f"F{key} not bound to exact {fn}"
    assert len(re.findall(r"(?m)^function\s+"+re.escape(fn)+r"\s*\(",all_lua))==1, f"{fn} not exported exactly once in actual 22"
    if key==9:
        assert 'HOMELANDER_PLAYER missing/invalid' in all_lua
        assert 'valid_goh(player)' in all_lua
print("P1_R020_NATIVE_F9_F21_KEY_DISPATCH_MATCHES_EXACT_ASSEMBLED_SOURCE_PASS")
tick=cpp.split("if (inputEnabled && g_laserSightHeldReady)",1)[1].split("CallLua0(L, \"Homelander_FlightNativeTickV2\"",1)[0]
for ready,fn in (
  ("g_laserSightDynamicReady","Homelander_DynamicAimTickV010"),
  ("g_targetContinuityReady","Homelander_TargetContinuityTickV013"),
  ("g_dotDryRunReady","Homelander_DOTDryRunTickV014"),
):
    assert re.search(r"if\s*\(inputEnabled\s*&&\s*"+ready+r"\)\s*CallLua0\(L,\s*\""+fn+r"\"",tick),fn
assert re.search(r"CallLua0\(L,\s*\"Homelander_LaserSightHeldTickV009\"",tick)
print("P1_R020_NATIVE_PER_FRAME_HELD_DYNAMIC_CONTINUITY_DOT_TICKS_PRESENT_PASS")
print("P1_R020_NO_NATIVE_RECOMPILE_NO_GAME_INSTALL_NO_F4_LIVE_CLAIM_PASS")
