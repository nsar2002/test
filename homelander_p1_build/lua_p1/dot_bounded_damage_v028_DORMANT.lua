-- Homelander P1 bounded heat-vision damage prototype v0.28.
-- DORMANT: Lua function definitions only. No C++ bootstrap, hotkey or active tick wiring.
-- Explicit manual toggle AFTER separate real-game F17/F18/F19/F20 gates ONLY.
-- At most 3 go_ApplyDamage(target, 0.1) calls per fresh authorization.
local PREFIX="[HOMELANDER_P1_DOT_BOUNDED_V028] "
local INTERVAL=0.10
local MAX_EVENTS=3
local MAX_PER_EVENT=0.10
local MAX_ELAPSED=2.0
local S={enabled=false,player=nil,target=nil,elapsed=0.0,acc=0.0,events=0}
HOMELANDER_DOT_BOUNDED_LAST_EVENTS=0
HOMELANDER_DOT_BOUNDED_ACTIVE=false
local function log(x)
 local line=PREFIX..tostring(x)
 if type(HL_Log)=="function" then HL_Log(line) else print(line) end
end
local function finite(x)
 return type(x)=="number" and x==x and x~=math.huge and x~=-math.huge
end
local function valid_target(player,target)
 if player==nil or target==nil or target==player or
    type(go_IsValid)~="function" or type(online_DeterminePlayerIndex)~="function" then return false end
 local okP,validP=pcall(go_IsValid,player)
 local okT,validT=pcall(go_IsValid,target)
 local okPi,pi=pcall(online_DeterminePlayerIndex,player)
 local okTi,ti=pcall(online_DeterminePlayerIndex,target)
 return okP and okT and validP==true and validT==true and
        okPi and finite(pi) and pi>=0 and pi==math.floor(pi) and
        okTi and finite(ti) and ti<0 and
        HOMELANDER_PLAYER==player and target~=HOMELANDER_PLAYER
end
local function read_health(target)
 local okH,h=pcall(go_GetHealth,target)
 local okM,m=pcall(go_GetMaxHealth,target)
 if not okH or not okM or not finite(h) or not finite(m) or
    m<=0 or h<=0 or h>m then return false end
 return true
end
local function normalized(v)
 local c=Vector(v)
 local mag=c:normalize()
 if not finite(mag) or mag<=0.0001 then return nil end
 return c
end
local function parse_frame(raw)
 if type(raw)~="string" or raw=="" then return nil end
 local vals={}
 for token in string.gmatch(raw,"[^,]+") do
  local num=tonumber(token)
  if not finite(num) then return nil end
  vals[#vals+1]=num
 end
 if #vals~=12 then return nil end
 return vals
end
local function select_view_axis(frame,playerPos)
 local cameraPos=Vector(frame[1],frame[2],frame[3])
 local toPlayer=normalized(playerPos-cameraPos)
 if toPlayer==nil then return nil,nil end
 local axes={
  Vector(frame[4],frame[5],frame[6]),
  Vector(frame[7],frame[8],frame[9]),
  Vector(frame[10],frame[11],frame[12])
 }
 local best=nil
 local bestScore=-1.0
 local signedDot=nil
 for i=1,3 do
  local axis=normalized(axes[i])
  if axis==nil then return nil,nil end
  local dot=axis:dot(toPlayer)
  if not finite(dot) then return nil,nil end
  if math.abs(dot)>bestScore then bestScore=math.abs(dot);best=axis;signedDot=dot end
 end
 if best==nil then return nil,nil end
 if signedDot<0 then best=best*-1.0 end
 return cameraPos,best
end
local function api_ready()
 return type(Vector)=="function" and type(go_GetHealth)=="function" and
    type(go_GetMaxHealth)=="function" and type(go_ApplyDamage)=="function" and
    type(time_GetSimulationDelta)=="function" and type(HL_GetCameraFrame)=="function" and
    type(HL_LastRayHitGOH)=="function" and type(cm_GetCurrentRenderCameraPosition)=="function" and
    type(go_GetPosition)=="function" and type(fre_LineOfSightTest)=="function"
end
local function proof_ok(target)
 return HOMELANDER_TARGET_CONTINUITY_PASSED==true and
  HOMELANDER_IMPACT_VFX_SUBMITTED==true and
  HOMELANDER_DOT_DRYRUN_PASSED==true and
  HOMELANDER_TARGET_CONTINUITY_TARGET==target and
  HOMELANDER_DAMAGE_LAST_TARGET==target and
  HOMELANDER_DOT_DRYRUN_TARGET==target and
  finite(HOMELANDER_DOT_DRYRUN_INTERVAL) and
  math.abs(HOMELANDER_DOT_DRYRUN_INTERVAL-INTERVAL)<0.000001 and
  finite(HOMELANDER_DOT_DRYRUN_SECONDS) and HOMELANDER_DOT_DRYRUN_SECONDS>=3.0 and
  finite(HOMELANDER_DOT_DRYRUN_EVENTS) and HOMELANDER_DOT_DRYRUN_EVENTS>=10 and
  finite(HOMELANDER_DOT_DRYRUN_MIN_GAP) and HOMELANDER_DOT_DRYRUN_MIN_GAP+0.000001>=INTERVAL
end
local function disable(why)
 if S.enabled then log("DISABLED | "..tostring(why)) end
 S.enabled=false;S.player=nil;S.target=nil;S.acc=0.0
 HOMELANDER_DOT_BOUNDED_ACTIVE=false
 return true
end

function Homelander_DOTBoundedToggleV028()
 if S.enabled then return disable("manual stop") end
 -- A completed bounded trial cannot be restarted with the same old Lua token.
 if HOMELANDER_DOT_BOUNDED_LAST_EVENTS>0 then
  log("REFUSED: this Lua state already submitted bounded DOT damage")
  return false
 end
 local player=HOMELANDER_PLAYER
 local target=HOMELANDER_DOT_DRYRUN_TARGET
 if not api_ready() or not proof_ok(target) or
    not valid_target(player,target) or not read_health(target) then
  log("REFUSED: live proof, target or API gate missing")
  return false
 end
 -- No gameplay mutation on enable: target and player pinned as exact GOHs.
 S.player=player;S.target=target;S.elapsed=0.0;S.acc=0.0;S.events=0
 S.enabled=true
 HOMELANDER_DOT_BOUNDED_ACTIVE=true
 log("ENABLED: manual bounded diagnostic | 3 events max, 0.1 damage/event, no native tick wiring")
 return true
end
function Homelander_DOTBoundedForceDisableV028()
 return disable("focus loss / explicit stop")
end
function Homelander_DOTBoundedTickV028()
 if not S.enabled then return false end
 local player,target=S.player,S.target
 if not proof_ok(target) or not valid_target(player,target) then
  disable("target/proof/player invalid");return false
 end
 local okDt,dt=pcall(time_GetSimulationDelta)
 if not okDt or not finite(dt) or dt<0 or dt>0.25 then
  disable("simulation delta invalid");return false
 end
 if dt==0 then return true end
 if not read_health(target) then
  disable("target health unavailable/dead");return false
 end
 local okCam,cam=pcall(cm_GetCurrentRenderCameraPosition)
 local okFrame,raw=pcall(HL_GetCameraFrame)
 local frame=okFrame and parse_frame(raw) or nil
 local okP,playerPos=pcall(go_GetPosition,player)
 if not okCam or cam==nil or frame==nil or not okP or playerPos==nil then
  disable("camera/player basis unavailable");return false
 end
 local okAxis,start,forward=pcall(select_view_axis,frame,playerPos)
 if not okAxis or start==nil or forward==nil then
  disable("camera axis invalid");return false
 end
 local range=tonumber(HOMELANDER_DOT_BOUNDED_RANGE) or 500.0
 if not finite(range) then disable("nonfinite range");return false end
 if range<10 then range=10 elseif range>1000 then range=1000 end
 local okRay,rayEnd=pcall(function() return start+forward*range end)
 if not okRay or rayEnd==nil then disable("ray geometry invalid");return false end
 local okLOS,hit,_,hitPos=pcall(fre_LineOfSightTest,start,rayEnd,true,player)
 if not okLOS or hit~=true or hitPos==nil then
  disable("fresh LOS miss/terrain/error");return false
 end
 local okGOH,candidate=pcall(HL_LastRayHitGOH)
 if not okGOH or candidate~=target then
  disable("fresh LOS changed target");return false
 end
 -- A callback in LOS/camera/health can change player or target. Recheck all
 -- mutable evidence immediately before the only damage submission.
 if not proof_ok(target) or not valid_target(player,target) or not read_health(target) then
  disable("player/target/proof changed during tick callbacks");return false
 end
 S.elapsed=S.elapsed+dt
 if S.elapsed>MAX_ELAPSED then disable("bounded test timeout");return false end
 S.acc=S.acc+dt
 if S.acc<INTERVAL then return true end
 S.acc=0.0 -- no burst catch-up even when dt > interval
 if S.events>=MAX_EVENTS or HOMELANDER_DOT_BOUNDED_LAST_EVENTS>=MAX_EVENTS then
  disable("maximum bounded events already reached");return false
 end
 -- Only one bounded damage call in one tick; published count is consumed BEFORE
 -- native submission so a setter error cannot be retried into an extra event.
 S.events=S.events+1
 HOMELANDER_DOT_BOUNDED_LAST_EVENTS=HOMELANDER_DOT_BOUNDED_LAST_EVENTS+1
 local okDamage,err=pcall(go_ApplyDamage,target,MAX_PER_EVENT)
 if not okDamage then
  disable("damage setter failed; event budget remains consumed | "..tostring(err))
  return false
 end
 log("BOUNDED DOT SUBMITTED | event="..tostring(S.events).." amount="..tostring(MAX_PER_EVENT))
 if S.events>=MAX_EVENTS then disable("bounded test complete") end
 return true
end
log("LOADED: dormant bounded damage prototype, NEVER auto-enabled or auto-ticked")
