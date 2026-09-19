-- Offline native-bootstrap definition-only smoke for the exact 22-file
-- R008 source payload. Engine writes are traps; game is never launched.
local stage=assert(arg[1],"source-only stage directory")
local order=assert(arg[2],"native load-order list")
local log_lines={}
HL_Log=function(line)
  log_lines[#log_lines+1]=tostring(line)
end
local forbidden={
 "ai_SetPhysicsVelocity","ai_Laser","go_ApplyDamage",
 "go_ApplyDamageAndHit","em_AddWorldEffect",
 "em_AddWorldEffectOriented","go_SetPosition","go_SetOrientation",
 "go_SetHealth","go_Kill","ai_SetDesiredVelocity",
}
local mutations=0
for _,name in ipairs(forbidden) do
 _G[name]=function(...)
   mutations=mutations+1
   error("FORBIDDEN_ENGINE_MUTATION_DURING_BOOT: "..name,2)
 end
end
local count,seen=0,{}
for name in io.lines(order) do
 assert(type(name)=="string" and string.match(name,"^[%w_]+%.lua$"),"bad native path: "..tostring(name))
 assert(not seen[name],"native definition loaded twice: "..name)
 seen[name]=true
 local ok,err=pcall(dofile,stage.."/lua_p1/"..name)
 assert(ok, "SOURCE_LOAD_FAILURE ["..name.."]: "..tostring(err))
 count=count+1
end
assert(count==22,"expected all 22 native bootstrap definitions, found "..count)
assert(mutations==0,"game mutation API called during definition-only bootstrap")
local exports={
 "Homelander_FreeAimProbe",
 "Homelander_FreeAimLocalOffsetProbe",
 "Homelander_EyeOriginProbeV006",
 "Homelander_DualEyeFreeAimRenderProbe",
 "Homelander_FlightEnableVerifiedV2",
 "Homelander_FlightDisableV2",
}
for _,symbol in ipairs(exports) do
 assert(type(_G[symbol])=="function","missing real native callback export: "..symbol)
end
assert(HOMELANDER_FLIGHT_V2_ENABLED==false,"flight automatically armed during source load")
assert(HOMELANDER_FREEAIM_VERIFIED_EPOCH==nil,"F9 target proof unexpectedly pre-authenticated")
assert(HOMELANDER_FREEAIM_F10_EPOCH==nil,"F10 offset unexpectedly pre-authenticated")
print("P1_R008_REAL_LOAD_ORDER_22_LUA_DEFINITION_SMOKE_PASS")
print("P1_R008_NO_GAME_MUTATION_DURING_SOURCE_BOOT_PASS")
print("P1_R008_SIX_REAL_NATIVE_CALLBACK_EXPORTS_PRESENT_PASS")
