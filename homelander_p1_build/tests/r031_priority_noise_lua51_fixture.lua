-- R031 engine-free regression: 512 matching function globals cannot mask an opaque handle.
local script=assert(arg[1],"R031 Lua source required")
local lines={}
HL_Log=function(x) lines[#lines+1]=x end
PLAYER=nil
HOMELANDER_PLAYER="UNVERIFIED_KEEP"
local h=io.stdout
assert(type(h)=="userdata")
PlayerValidatedGOH=h
AlexCharacterGOH=h
AvatarCharacterNode={private="DO NOT PRINT VALUE"}
for i=1,512 do _G[string.format("SyntheticPlayerFunction%04d",i)]=function() end end
local function run()
 lines={}
 assert(loadfile(script))()
 local all=table.concat(lines,"\n")
 assert(all:find("GLOBAL | PlayerValidatedGOH type=userdata",1,true))
 assert(all:find("GLOBAL | AlexCharacterGOH type=userdata",1,true))
 assert(all:find("GLOBAL | AvatarCharacterNode type=table",1,true))
 assert(all:find("functions_total=512",1,true))
 assert(all:find("userdata_total=2 userdata_emitted=2",1,true))
 assert(all:find("truncated=true",1,true))
 assert(not all:find("userdata:",1,true))
 assert(not all:find("table:",1,true))
 assert(not all:find("UNVERIFIED_KEEP",1,true))
 assert(HOMELANDER_PLAYER=="UNVERIFIED_KEEP")
 assert(#lines<=72)
 return all
end
local first=run()
for i=1,512 do _G[string.format("SyntheticPlayerFunction%04d",i)]=nil end
for i=512,1,-1 do _G[string.format("SyntheticPlayerFunction%04d",i)]=function() end end
assert(first==run(),"must be deterministic independent of Lua table insertion order")
print("P1_R031_512_FUNCTION_NOISE_USERDATA_TABLE_PRIORITY_AND_NO_GAME_WRITE_PASS")
