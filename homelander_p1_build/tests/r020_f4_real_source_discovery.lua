-- R020: use the EXACT ORIGINAL v003 runtime_probe.lua, not a hand-set
-- HOMELANDER_PLAYER as R018 did. This is engine-MOCK source-only evidence.
-- The user's first genuine v001 log showed PLAYER=nil and all seven name
-- lookup candidates nil; it did NOT show a real v003 gate or real player.
local original=assert(arg[1],"original frozen v003 runtime_probe.lua path required")
local staged=assert(arg[2],"assembled 22-Lua source directory required")
local function read(path)
 local f=assert(io.open(path,"rb"),path)
 local x=f:read("*a") f:close() return x
end
assert(read(original)==read(staged.."/lua_p1/runtime_probe.lua"),
 "assembled module must be byte-identical to original frozen v003 runtime probe")
local logs={}
HL_Log=function(s) logs[#logs+1]=tostring(s) end
local function count(needle)
 local n=0
 for _,line in ipairs(logs) do if line:find(needle,1,true) then n=n+1 end end
 return n
end
local id={}
go_IsValid=function(h) return h=="A" or h=="NPC" end
go_GetPosition=function(h)
 if h=="A" or h=="NPC" then return {x=0,y=0,z=0} end
 error("not a valid position owner")
end
ai_GetPhysicsVelocity=function(h)
 if h=="A" or h=="NPC" then return {x=0,y=0,z=0} end
 error("not a valid velocity owner")
end
online_GetNumPlayers=function() return 1 end
online_DeterminePlayerIndex=function(h)
 if h=="A" then return 0 end
 return -1
end
go_GetDebugName=function(h) return tostring(h) end
go_GetOrientation=function() return true end
go_GetHealth=function() return 100 end
go_FindGOHByName=function() return nil end
go_FindTransientGOHByName=function() return nil end
PLAYER=nil
HOMELANDER_PLAYER="STALE_FROM_EARLIER_F4"
HOMELANDER_SETTER_ECHO_PASSED=true
dofile(original)
assert(HOMELANDER_PLAYER==nil,"actual original F4 MUST clear stale player's handle if PLAYER and name routes fail")
assert(HOMELANDER_SETTER_ECHO_PASSED==false,"F4 must revoke stale velocity setter proof")
assert(count("NO VERIFIED PLAYER HANDLE")==1,"original no-player branch must be executed")
print("P1_R020_REAL_ORIGINAL_F4_NIL_PLAYER_NAMELESS_FAILCLOSED_PASS")
-- R018 originally skipped the authentic F4 flow by assigning A directly after
-- definition bootstrap; verify a real engine-provided PLAYER would be accepted
-- on the very same unmodified original runtime probe.
logs={}
PLAYER="A"
dofile(original)
assert(HOMELANDER_PLAYER=="A","real original F4 must accept an engine-provided independently verified player")
assert(count("VERIFIED PLAYER INDEX=0")==1)
assert(count("HOMELANDER_PLAYER SET TO VERIFIED HANDLE")==1)
print("P1_R020_REAL_ORIGINAL_F4_PLAYER_GLOBAL_VERIFIED_SOURCE_PASS")
-- PLAYER might not exist in single-player Prototype; named NPC candidate
-- must not become the player even if its physical position and velocity work.
logs={}
PLAYER=nil
go_FindGOHByName=function(name) if name=="Alex" then return "NPC" end end
dofile(original)
assert(HOMELANDER_PLAYER==nil,"NPC named Alex is not player")
assert(count("online_DeterminePlayerIndex")==1)
assert(count("NO VERIFIED PLAYER HANDLE")==1)
print("P1_R020_REAL_ORIGINAL_F4_NAMED_NPC_INDEX_MINUS1_REJECT_PASS")
-- Found by name and positive player index: original code accepts a validated
-- handle, but still no claim that any such name is the REAL PC game name.
logs={}
go_FindGOHByName=function(name) if name=="Alex" then return "A" end end
dofile(original)
assert(HOMELANDER_PLAYER=="A","named A with verified online index accepted")
assert(count("VERIFIED PLAYER SOURCE=go_FindGOHByName:Alex")==1)
print("P1_R020_REAL_ORIGINAL_F4_NAMED_VALID_PLAYER_SOURCE_PASS")
-- Index getter exception and nil index are NOT valid player proof.
logs={}
PLAYER="A"
online_DeterminePlayerIndex=function() error("mock engine index exception") end
dofile(original)
assert(HOMELANDER_PLAYER==nil,"index getter exception must never accept player")
online_DeterminePlayerIndex=function() return nil end
dofile(original)
assert(HOMELANDER_PLAYER==nil,"nil player index must never accept player")
print("P1_R020_REAL_ORIGINAL_F4_INVALID_INDEX_FAILCLOSED_PASS")
-- Original v003 F9 MUST NOT be bypassed to mark user evidence as passed.
PLAYER=nil
HOMELANDER_PLAYER=nil
dofile(staged.."/lua_p1/freeaim_probe_v004_STAGED.lua")
assert(Homelander_FreeAimProbe()==false,"F9 must abort without F4 player proof, even on 22-Lua assembled tree")
assert(count("HOMELANDER_PLAYER missing/invalid")>=1)
print("P1_R020_REAL_ORIGINAL_V003_F9_NO_PLAYER_NO_BYPASS_PASS")
print("P1_R020_GENUINE_V001_EVIDENCE_EXPLAINS_F4_BLOCKER_NO_PLAYER_FIX_CLAIM_PASS")
