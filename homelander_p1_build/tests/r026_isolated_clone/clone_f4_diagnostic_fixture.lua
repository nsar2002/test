-- R026 independent Lua5.1 replay of clone-only original v003 F4 diagnostic overlay.
-- The fixture NEVER launches Prototype or installs a new stage.
local path=assert(arg[1],"assembled clone-only runtime_probe.lua path required")
local logs, calls, writes={}, {}, 0
HL_Log=function(s) logs[#logs+1]=tostring(s) end
local function n(k) calls[k]=(calls[k] or 0)+1 end
local h=newproxy(true)
getmetatable(h).__tostring=function() error("GOH userdata MUST NOT be stringified") end
getmetatable(h).__index=function() error("GOH userdata MUST NOT be indexed") end
PLAYER=nil
HOMELANDER_PLAYER=nil
HOMELANDER_SETTER_ECHO_PASSED=true
go_FindGOHByName=function() n("named");return nil end
go_FindTransientGOHByName=function() n("transient");return nil end
online_GetNumPlayers=function() n("players");return 1 end
go_IsValid=function(g) n("valid"); assert(g==h);return true end
go_GetPosition=function(g) n("position");assert(g==h);return {x=1,y=2,z=3} end
ai_GetPhysicsVelocity=function(g) n("velocity");assert(g==h);return {x=0,y=0,z=0} end
online_DeterminePlayerIndex=function(g) n("index");assert(g==h);return 0 end
ai_GetClosestCharacterToCamera=function() n("closest");return h end
for _,name in ipairs({"phys_SetLinearVelocity","phys_SetAngularVelocity",
    "go_SetPosition","go_ApplyDamage","em_AddWorldEffect","cm_SetCameraAvatar"}) do
 _G[name]=function() writes=writes+1;error("forbidden mutation: "..name) end
end
local function has(q)
 for _,line in ipairs(logs) do if line:find(q,1,true) then return true end end
 return false
end
-- Native bootstrap invokes original runtime_probe.lua BEFORE publishing
-- HL_BRIDGE_READY, thus this read-only overlay must not run a candidate API.
dofile(path)
assert(HOMELANDER_PLAYER==nil and HOMELANDER_SETTER_ECHO_PASSED==false)
assert(not has("P1_R026_CLONE_DIAG"),"bootstrap should not invoke optional R026 observation")
assert((calls.closest or 0)==0)
assert(writes==0)
print("P1_R026_ORIGINAL_V003_BOOTSTRAP_REMAINS_UNINSTRUMENTED_PASS")
-- In actual C++ F4 is evaluated after PublishHeldInput, and source is re-run.
HL_BRIDGE_READY="1"
logs={};calls={}
dofile(path)
assert(HOMELANDER_PLAYER==nil,"R026 must never promote nearest candidate to active player")
assert(has("[P1_R026_CLONE_DIAG] BEGIN"))
assert(has("[P1_R024_GLOBAL_CENSUS] END"))
assert(has("[P1_R025_CLOSEST_CAMERA_CANDIDATE] OBSERVED"))
assert(has("[P1_R026_CLONE_DIAG] END"))
assert((calls.closest or 0)==1 and (calls.index or 0)==1)
assert((calls.position or 0)==1 and (calls.velocity or 0)==1)
assert(writes==0)
for _,line in ipairs(logs) do
 assert(not line:find("userdata:",1,true),"GOH pointer or data was exposed")
end
print("P1_R026_F4_DIAGNOSTIC_CENSUS_AND_CANDIDATE_OBSERVATION_NO_PLAYER_PROMOTION_PASS")
-- NPC is nearer than actual player; independent index -1 MUST reject,
-- not silently spoof the official F4 or F9 gate.
online_DeterminePlayerIndex=function(g) n("index");assert(g==h);return -1 end
logs={};calls={}
dofile(path)
assert(has("[P1_R025_CLOSEST_CAMERA_CANDIDATE] REJECT"))
assert(not has("[P1_R025_CLOSEST_CAMERA_CANDIDATE] OBSERVED"))
assert(HOMELANDER_PLAYER==nil and writes==0)
print("P1_R026_NEAREST_NPC_REJECTED_AND_ORIGINAL_V003_GATE_STILL_CLOSED_PASS")
-- Even when a future evaluator accidentally replays module code out of focus
-- with a disabled readiness flag, skip the additional camera query.
HL_BRIDGE_READY="0"
logs={};calls={}
dofile(path)
assert((calls.closest or 0)==0)
assert(not has("[P1_R026_CLONE_DIAG] BEGIN"))
assert(HOMELANDER_PLAYER==nil and writes==0)
print("P1_R026_NO_BRIDGE_READY_NO_CANDIDATE_CALL_FAILCLOSED_PASS")
