-- Homelander P1 durability telemetry v0.2, dormant / explicitly called only.
-- Never changes gameplay state. A sample is bound to one verified player GOH.
local PREFIX="[HOMELANDER_P1_DURABILITY_READ_ONLY_V02] "
local function log(msg)
 local line=PREFIX..tostring(msg)
 if type(HL_Log)=="function" then HL_Log(line) else print(line) end
end
local function hasfn(name) return type(_G[name])=="function" end
local function finite(n) return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge end
HOMELANDER_DURABILITY_SNAPSHOT=nil
HOMELANDER_DURABILITY_SNAPSHOT_VALID=false

function Homelander_DurabilitySnapshotV02()
 -- Clear stale snapshots even when a new sample fails.
 HOMELANDER_DURABILITY_SNAPSHOT=nil
 HOMELANDER_DURABILITY_SNAPSHOT_VALID=false
 local h=HOMELANDER_PLAYER
 if h==nil or not (hasfn("go_IsValid") or hasfn("online_DeterminePlayerIndex")) then
  log("ABORT: no verified player or validity route")
  return false
 end
 if hasfn("go_IsValid") then
  local ok,v=pcall(go_IsValid,h)
  if not ok or v~=true then log("ABORT: player invalid");return false end
 end
 if hasfn("online_DeterminePlayerIndex") then
  local ok,idx=pcall(online_DeterminePlayerIndex,h)
  if not ok or not finite(idx) or idx<0 then log("ABORT: player discriminator rejected handle");return false end
 end
 if not hasfn("go_GetHealth") or not hasfn("go_GetMaxHealth") then
  log("ABORT: required health getters missing")
  return false
 end
 local okH,health=pcall(go_GetHealth,h)
 local okM,maxHealth=pcall(go_GetMaxHealth,h)
 if not okH or not okM or not finite(health) or not finite(maxHealth) or
    maxHealth<=0 or health<0 or health>maxHealth then
  log("ABORT: invalid health/max-health sample")
  return false
 end
 local damageScale=nil
 if hasfn("go_GetDamageScale") then
  local okD,v=pcall(go_GetDamageScale,h)
  if not okD or not finite(v) or v<0 then
   log("ABORT: invalid damage-scale sample")
   return false
  end
  damageScale=v
 end
 -- Revalidate the originating GOH once more after all callbacks.
 if HOMELANDER_PLAYER~=h then
  log("ABORT: player replaced during snapshot")
  return false
 end
 if hasfn("go_IsValid") then
  local ok,v=pcall(go_IsValid,h)
  if not ok or v~=true then log("ABORT: player invalidated during snapshot");return false end
 end
 if hasfn("online_DeterminePlayerIndex") then
  local ok,idx=pcall(online_DeterminePlayerIndex,h)
  if not ok or not finite(idx) or idx<0 then log("ABORT: player discriminator changed");return false end
 end
 local snap={player=h,health=health,max_health=maxHealth,damage_scale=damageScale}
 HOMELANDER_DURABILITY_SNAPSHOT=snap
 HOMELANDER_DURABILITY_SNAPSHOT_VALID=true
 log("SAMPLE READ ONLY | health="..tostring(health).." maxHealth="..tostring(maxHealth)..
     " damageScale="..tostring(damageScale))
 return true
end

log("LOADED read-only durability probe; NO automatic sample or gameplay mutation")
