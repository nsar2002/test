-- Deterministic read-only durability probe test; no game is launched.
local nReads,nWrites=0,0
local health,maxHealth,scale=70,100,0.3
local valid=true
local idx=0
local fail=false
HOMELANDER_PLAYER="player-A"
HL_Log=function() end
go_IsValid=function(h) return valid and h=="player-A" end
online_DeterminePlayerIndex=function(h) return h=="player-A" and idx or -1 end
go_GetHealth=function(h)
 assert(h=="player-A")
 nReads=nReads+1
 if fail then error("read unavailable") end
 return health
end
go_GetMaxHealth=function(h) assert(h=="player-A");nReads=nReads+1;return maxHealth end
go_GetDamageScale=function(h) assert(h=="player-A");nReads=nReads+1;return scale end
-- Explicitly stub dangerous setters: the observer must NEVER invoke any of them.
for _,name in ipairs({"go_SetHealth","go_SetMaxHealth","go_SetDamageScale","go_SetDamageable","go_SetNoPushback","go_ApplyDamage","phys_SetLinearVelocity"}) do
 _G[name]=function() nWrites=nWrites+1; error("FORBIDDEN MUTATION "..name) end
end
dofile("homelander_p1_build/lua_p1/durability_snapshot_v02_DORMANT.lua")
assert(nReads==0 and nWrites==0,"loading the definition must not read/mutate gameplay")
local function cleared(label)
 assert(HOMELANDER_DURABILITY_SNAPSHOT==nil and HOMELANDER_DURABILITY_SNAPSHOT_VALID==false,label)
end
assert(Homelander_DurabilitySnapshotV02(),"valid read-only sample")
local a=HOMELANDER_DURABILITY_SNAPSHOT
assert(a.player=="player-A" and a.health==70 and a.max_health==100 and a.damage_scale==0.3)
assert(nReads==3 and nWrites==0,"exactly three getters and no setters")
valid=false
assert(not Homelander_DurabilitySnapshotV02(),"invalid player blocks sample");cleared("invalid sample clears stale data")
valid=true
idx=-1
assert(not Homelander_DurabilitySnapshotV02(),"invalid player index blocks sample");cleared("invalid index")
idx=0
fail=true
assert(not Homelander_DurabilitySnapshotV02(),"health exception blocked");cleared("exception")
fail=false
health=0/0
assert(not Homelander_DurabilitySnapshotV02(),"NaN health blocked");cleared("NaN")
health=120
assert(not Homelander_DurabilitySnapshotV02(),"health exceeds max blocked");cleared("overflow")
health=70;maxHealth=0
assert(not Homelander_DurabilitySnapshotV02(),"zero max health blocked");cleared("zero max")
maxHealth=100;scale=math.huge
assert(not Homelander_DurabilitySnapshotV02(),"infinite scale blocked");cleared("infinite scale")
scale=0.3
go_GetDamageScale=nil
assert(Homelander_DurabilitySnapshotV02(),"optional damage scale getter may be missing")
assert(HOMELANDER_DURABILITY_SNAPSHOT.damage_scale==nil,"missing optional scale represented as nil")
go_GetDamageScale=function()
 HOMELANDER_PLAYER="player-B"
 return 0.3
end
assert(not Homelander_DurabilitySnapshotV02(),"player swap during getter is rejected")
cleared("stale player")
HOMELANDER_PLAYER="player-A"
go_GetDamageScale=function() return 0.3 end
go_IsValid=nil
online_DeterminePlayerIndex=nil
assert(not Homelander_DurabilitySnapshotV02(),"no validity API denies read");cleared("no validation API")
assert(nWrites==0,"no prohibited setter calls across test cases")
print("P1_DURABILITY_V02_READ_ONLY_PASS: no auto-load mutation, valid sample, stale-state clearing, player identity, exception, nonfinite, optional getter, no setter")
