-- Homelander P1 Flight Controller v2.0 STAGED
-- Disabled by default. Requires the proven F5 same-velocity setter echo gate.
-- Flight V2 adds simulation-delta acceleration, deceleration/air-braking and hover damping.
-- Landing thresholds remain intentionally unimplemented until F4 ground telemetry is measured live.

local PREFIX = "[HOMELANDER_P1_FLIGHT_V2] "

local S = {
    enabled=false,
    handle=nil,
    pre_velocity=nil,
    selector=0,
    camera_relative=true,
    camera_fallback_logged=false,
    tick_count=0,
    submit_count=0,
    last_telemetry_tick=0,

    cruise_speed=28.0,
    boost_speed=75.0,
    vertical_speed=22.0,
    planar_accel=55.0,
    boost_accel=90.0,
    air_brake=80.0,
    vertical_accel=60.0,
    hover_brake=75.0
}

HOMELANDER_FLIGHT_V2_ENABLED = false
HOMELANDER_FLIGHT_V2_LAST_DESIRED = nil
HOMELANDER_FLIGHT_V2_LAST_CURRENT = nil
HOMELANDER_FLIGHT_V2_LAST_DT = nil
HOMELANDER_FLIGHT_V2_SUBMITS = 0

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function hasfn(name) return type(_G[name]) == "function" end
local function key(name) return _G[name] == "1" end
local function finite(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge
end

local function clamp(n, lo, hi)
    if n < lo then return lo end
    if n > hi then return hi end
    return n
end

local function config_number(name, default, lo, hi)
    local n = tonumber(_G[name])
    if not finite(n) then n = default end
    return clamp(n, lo, hi)
end

local function valid_player(h)
    if h == nil then return false end
    -- A missing validation API must not silently authorize a physics write.
    if not (hasfn("go_IsValid") or hasfn("online_DeterminePlayerIndex")) then return false end
    if hasfn("go_IsValid") then
        local ok, v = pcall(go_IsValid, h)
        if not ok or not v then return false end
    end
    if hasfn("online_DeterminePlayerIndex") then
        local ok, idx = pcall(online_DeterminePlayerIndex, h)
        if not ok or not finite(idx) or idx < 0 or idx ~= math.floor(idx) then return false end
    end
    return true
end

-- F5 only carries a boolean in the canonical v003 probe. Bind that proof to the
-- precise player handle from the same successful, synchronous verified F5 call.
-- This is a dormant Flight-only wrapper around the unchanged baseline probe.
local OriginalSetterEcho = Homelander_SetterEchoProbe
local OriginalSetterEchoVerified = Homelander_SetterEchoProbe_Verified
HOMELANDER_FLIGHT_V22_ECHO_PLAYER = nil

-- Every echo entrypoint, including the canonical _PLAYER route, invalidates the
-- previous flight provenance before any physical velocity setter is reached.
local WrappedSetterEcho = nil
if type(OriginalSetterEcho) == "function" then
    WrappedSetterEcho = function(...)
        HOMELANDER_FLIGHT_V22_ECHO_PLAYER = nil
        return OriginalSetterEcho(...)
    end
    Homelander_SetterEchoProbe = WrappedSetterEcho
end

local WrappedSetterEchoVerified = nil
if type(OriginalSetterEchoVerified) == "function" and WrappedSetterEcho ~= nil then
    WrappedSetterEchoVerified = function(...)
        HOMELANDER_FLIGHT_V22_ECHO_PLAYER = nil
        HOMELANDER_SETTER_ECHO_PASSED = false
        local requested = HOMELANDER_PLAYER
        if not valid_player(requested) then
            log("F5 BLOCKED: player identity unavailable before echo")
            return false
        end
        local ok, passed = pcall(OriginalSetterEchoVerified, ...)
        if not ok or passed ~= true or
           HOMELANDER_SETTER_ECHO_PASSED ~= true or
           HOMELANDER_PLAYER ~= requested or not valid_player(requested) then
            HOMELANDER_SETTER_ECHO_PASSED = false
            log("F5 BLOCKED: echo failed or player identity changed")
            return false
        end
        HOMELANDER_FLIGHT_V22_ECHO_PLAYER = requested
        log("F5 BOUND: setter echo proof is tied to current player")
        return true
    end
    Homelander_SetterEchoProbe_Verified = WrappedSetterEchoVerified
else
    log("F5 BLOCKED: canonical verified/core setter echo unavailable")
end

local function exact_echo_binding(h)
    return h ~= nil and
        HOMELANDER_FLIGHT_V22_ECHO_PLAYER == h and
        WrappedSetterEcho ~= nil and WrappedSetterEchoVerified ~= nil and
        Homelander_SetterEchoProbe == WrappedSetterEcho and
        Homelander_SetterEchoProbe_Verified == WrappedSetterEchoVerified
end

-- Revalidate immediately before all velocity writes: an engine callback can
-- change the player handle or F5 proof after the entrypoint guard ran.
local function flight_provenance_ok(h)
    local good=h ~= nil and HOMELANDER_SETTER_ECHO_PASSED == true and
        HOMELANDER_PLAYER == h and exact_echo_binding(h) and valid_player(h) and
        HOMELANDER_PLAYER == h and HOMELANDER_SETTER_ECHO_PASSED == true and
        exact_echo_binding(h)
    if not good then
        -- A later A->B->A identity roundtrip must require a fresh verified F5,
        -- not reuse the approval that was invalid at any observed check.
        HOMELANDER_FLIGHT_V22_ECHO_PLAYER=nil
    end
    return good
end

local function normalized_copy(v)
    local c = Vector(v)
    local mag = c:normalize()
    if not finite(mag) or mag <= 0.0001 then return nil, mag end
    return c, mag
end

local function parse_frame(raw)
    if type(raw) ~= "string" or raw == "" then return nil end
    local values = {}
    for token in string.gmatch(raw, "[^,]+") do
        local n = tonumber(token)
        if not finite(n) then return nil end
        values[#values + 1] = n
    end
    if #values ~= 12 then return nil end
    return values
end

local function player_basis(handle)
    local p = go_GetPosition(handle)
    local right, rmag = normalized_copy(go_Local2World(handle, Vector(1,0,0)) - p)
    local forward, fmag = normalized_copy(go_Local2World(handle, Vector(0,0,1)) - p)
    if right == nil or forward == nil then
        error("invalid player basis | rmag=" .. tostring(rmag) .. " fmag=" .. tostring(fmag))
    end
    return right, forward, "player"
end

local function measured_camera_basis(handle)
    if not hasfn("cm_GetCurrentRenderCameraPosition") or type(HL_GetCameraFrame) ~= "function" then
        error("render camera frame bridge unavailable")
    end

    local okRefresh, refreshPos = pcall(cm_GetCurrentRenderCameraPosition)
    if not okRefresh or refreshPos == nil then error("render camera refresh failed") end

    local okRaw, raw = pcall(HL_GetCameraFrame)
    if not okRaw then error("HL_GetCameraFrame failed") end
    local frame = parse_frame(raw)
    if frame == nil then error("camera frame invalid") end

    local playerPos = go_GetPosition(handle)
    local cameraPos = Vector(frame[1],frame[2],frame[3])
    local toPlayer = normalized_copy(playerPos - cameraPos)
    if toPlayer == nil then error("camera/player separation degenerate") end

    local axes = {
        Vector(frame[4],frame[5],frame[6]),
        Vector(frame[7],frame[8],frame[9]),
        Vector(frame[10],frame[11],frame[12])
    }
    local best=nil
    local bestScore=-1.0
    local signedDot=0.0
    for i=1,3 do
        local axis = normalized_copy(axes[i])
        if axis == nil then error("camera axis degenerate") end
        local d = axis:dot(toPlayer)
        if not finite(d) then error("camera axis dot invalid") end
        local score=math.abs(d)
        if score > bestScore then
            bestScore=score
            best=axis
            signedDot=d
        end
    end
    if best == nil then error("camera forward unresolved") end
    if signedDot < 0.0 then best=best * -1.0 end

    local up=Vector(0,1,0)
    local vertical=best:dot(up)
    local horizontal=best - up * vertical
    horizontal=normalized_copy(horizontal)
    if horizontal == nil then error("camera horizontal forward degenerate") end

    local right=Vector(up)
    right:cross(horizontal)
    right=normalized_copy(right)
    if right == nil then error("camera right degenerate") end

    return right,horizontal,"camera_measured"
end

local function legacy_camera_basis(handle)
    local names={
        "cm_GetCurrentInGameCameraPosition",
        "cm_GetCurrentCameraPosition",
        "cm_GetCurrentRenderCameraPosition"
    }
    local cam=nil
    for _,name in ipairs(names) do
        if hasfn(name) then
            local ok,v=pcall(_G[name])
            if ok and v~=nil then cam=v break end
        end
    end
    if cam==nil then error("camera position unavailable") end

    local p=go_GetPosition(handle)
    local up=Vector(0,1,0)
    local forward=p-cam
    local vertical=forward:dot(up)
    forward=forward-up*vertical
    forward=normalized_copy(forward)
    if forward==nil then error("legacy camera forward degenerate") end
    local right=Vector(up)
    right:cross(forward)
    right=normalized_copy(right)
    if right==nil then error("legacy camera right degenerate") end
    return right,forward,"camera_legacy"
end

local function basis(handle)
    if S.camera_relative then
        local ok,r,f,kind=pcall(measured_camera_basis,handle)
        if ok then
            S.camera_fallback_logged=false
            return r,f,kind
        end
        local errMeasured=r

        local ok2,r2,f2,kind2=pcall(legacy_camera_basis,handle)
        if ok2 then
            if not S.camera_fallback_logged then
                S.camera_fallback_logged=true
                log("measured camera basis unavailable; using legacy camera fallback | " .. tostring(errMeasured))
            end
            return r2,f2,kind2
        end

        if not S.camera_fallback_logged then
            S.camera_fallback_logged=true
            log("camera basis unavailable; using player fallback | measured=" .. tostring(errMeasured) ..
                " legacy=" .. tostring(r2))
        end
    end
    return player_basis(handle)
end

local function move_towards_vector(current,target,maxDelta)
    local delta=target-current
    local mag=delta:magnitude()
    if not finite(mag) then error("non-finite vector delta") end
    if mag <= maxDelta or mag <= 0.0001 then return Vector(target) end
    delta:normalize()
    return current + delta * maxDelta
end

local function move_towards_scalar(current,target,maxDelta)
    local d=target-current
    if math.abs(d)<=maxDelta then return target end
    if d>0 then return current+maxDelta end
    return current-maxDelta
end

local function required_api_ok()
    return type(Vector)=="function"
       and hasfn("go_GetPosition")
       and hasfn("go_Local2World")
       and hasfn("ai_GetPhysicsVelocity")
       and hasfn("phys_SetLinearVelocity")
       and hasfn("time_GetSimulationDelta")
end

local function refresh_config()
    S.cruise_speed=config_number("HOMELANDER_FLIGHT_V2_CRUISE_SPEED",28.0,5.0,60.0)
    S.boost_speed=config_number("HOMELANDER_FLIGHT_V2_BOOST_SPEED",75.0,20.0,140.0)
    S.vertical_speed=config_number("HOMELANDER_FLIGHT_V2_VERTICAL_SPEED",22.0,5.0,50.0)
    S.planar_accel=config_number("HOMELANDER_FLIGHT_V2_PLANAR_ACCEL",55.0,10.0,180.0)
    S.boost_accel=config_number("HOMELANDER_FLIGHT_V2_BOOST_ACCEL",90.0,15.0,240.0)
    S.air_brake=config_number("HOMELANDER_FLIGHT_V2_AIR_BRAKE",80.0,10.0,220.0)
    S.vertical_accel=config_number("HOMELANDER_FLIGHT_V2_VERTICAL_ACCEL",60.0,10.0,180.0)
    S.hover_brake=config_number("HOMELANDER_FLIGHT_V2_HOVER_BRAKE",75.0,10.0,220.0)
end

function Homelander_FlightEnableVerifiedV2()
    if S.enabled then return true end
    if HOMELANDER_SETTER_ECHO_PASSED ~= true then
        log("ABORT: setter echo gate has not passed")
        return false
    end
    if not required_api_ok() then
        log("ABORT: required API missing")
        return false
    end

    local h=HOMELANDER_PLAYER
    if not exact_echo_binding(h) then
        log("ABORT: setter echo is not bound to the current player")
        return false
    end
    if not valid_player(h) then
        log("ABORT: HOMELANDER_PLAYER missing/invalid")
        return false
    end

    local okV,v=pcall(ai_GetPhysicsVelocity,h)
    if not okV or v==nil then
        log("ABORT: velocity read failed | "..tostring(v))
        return false
    end

    local okB,br,bf,bkind=pcall(basis,h)
    if not okB then
        log("ABORT: basis validation failed | "..tostring(br))
        return false
    end

    refresh_config()
    local okMag, preMag=pcall(function() return v:magnitude() end)
    if not okMag or not finite(preMag) then
        log("ABORT: non-finite pre-flight velocity")
        return false
    end
    local okCopy, preCopy=pcall(Vector,v)
    if not okCopy or preCopy==nil then
        log("ABORT: pre-flight velocity copy failed")
        return false
    end
    -- A getter/camera callback may have replaced the originating player.
    if not flight_provenance_ok(h) then
        log("ABORT: player/F5 proof changed during flight enable callbacks")
        return false
    end
    S.handle=h
    S.pre_velocity=preCopy
    S.enabled=true
    S.camera_fallback_logged=false
    S.tick_count=0
    S.submit_count=0
    S.last_telemetry_tick=0

    HOMELANDER_FLIGHT_V2_ENABLED=true
    HOMELANDER_FLIGHT_V2_SUBMITS=0
    log("ENABLED | basis="..tostring(bkind)..
        " cruise="..tostring(S.cruise_speed)..
        " boost="..tostring(S.boost_speed)..
        " vertical="..tostring(S.vertical_speed)..
        " accel="..tostring(S.planar_accel)..
        " brake="..tostring(S.air_brake)..
        " landingAssist=false")
    return true
end

function Homelander_FlightTickV2(inputFwd,inputRight,inputUp,boost)
    if not S.enabled or S.handle==nil then return false end
    if not flight_provenance_ok(S.handle) then
        log("FAIL-CLOSED: player/setter proof changed while flight active")
        S.enabled=false
        HOMELANDER_FLIGHT_V2_ENABLED=false
        return false
    end

    local function safe_axis(v)
        local n=tonumber(v)
        if not finite(n) then return 0 end
        return clamp(n,-1,1)
    end
    inputFwd=safe_axis(inputFwd)
    inputRight=safe_axis(inputRight)
    inputUp=safe_axis(inputUp)

    local ok,err=pcall(function()
        local dt=time_GetSimulationDelta()
        if not finite(dt) or dt<0.0 or dt>0.25 then error("invalid simulation delta "..tostring(dt)) end
        if dt==0.0 then return end
        local stepDt=math.min(dt,0.05)

        local current=ai_GetPhysicsVelocity(S.handle)
        if current==nil then error("current velocity nil") end
        local currentMagnitude=current:magnitude()
        if not finite(currentMagnitude) then error("current velocity non-finite") end

        local up=Vector(0,1,0)
        local currentUp=current:dot(up)
        if not finite(currentUp) then error("current vertical velocity invalid") end
        local currentPlanar=current-up*currentUp

        local right,forward,bkind=basis(S.handle)
        local planarInput=forward*inputFwd + right*inputRight
        local inputMag=planarInput:magnitude()
        if not finite(inputMag) then error("planar input magnitude invalid") end
        if inputMag>1.0 then planarInput:normalize() end

        local targetSpeed=(boost and S.boost_speed or S.cruise_speed)
        local targetPlanar=planarInput*targetSpeed
        local planarRate
        if inputMag<=0.0001 then
            planarRate=S.air_brake
        elseif boost then
            planarRate=S.boost_accel
        else
            planarRate=S.planar_accel
        end
        local newPlanar=move_towards_vector(currentPlanar,targetPlanar,planarRate*stepDt)

        local targetUp=inputUp*S.vertical_speed
        local verticalRate=(math.abs(inputUp)<=0.0001) and S.hover_brake or S.vertical_accel
        local newUp=move_towards_scalar(currentUp,targetUp,verticalRate*stepDt)

        local desired=newPlanar + up*newUp
        local desiredMagnitude=desired:magnitude()
        if not finite(desiredMagnitude) then error("desired velocity non-finite") end
        if not flight_provenance_ok(S.handle) then
            error("player/F5 proof changed during flight tick callbacks")
        end
        phys_SetLinearVelocity(S.handle,desired,S.selector)

        S.tick_count=S.tick_count+1
        S.submit_count=S.submit_count+1
        HOMELANDER_FLIGHT_V2_LAST_CURRENT=Vector(current)
        HOMELANDER_FLIGHT_V2_LAST_DESIRED=Vector(desired)
        HOMELANDER_FLIGHT_V2_LAST_DT=dt
        HOMELANDER_FLIGHT_V2_SUBMITS=S.submit_count

        if S.tick_count==1 or (S.tick_count-S.last_telemetry_tick)>=120 then
            S.last_telemetry_tick=S.tick_count
            log("TELEMETRY | ticks="..tostring(S.tick_count)..
                " submits="..tostring(S.submit_count)..
                " dt="..tostring(dt)..
                " input="..tostring(inputFwd)..","..tostring(inputRight)..","..tostring(inputUp)..
                " boost="..tostring(boost)..
                " basis="..tostring(bkind)..
                " currentSpeed="..tostring(current:magnitude())..
                " desiredSpeed="..tostring(desired:magnitude())..
                " groundTelemetry="..tostring(HOMELANDER_FLIGHT_GROUND_PLAYER_DISTANCE))
        end
    end)

    if not ok then
        log("TICK FAILED; controller disabled | "..tostring(err))
        S.enabled=false
        HOMELANDER_FLIGHT_V2_ENABLED=false
        return false
    end
    return true
end

function Homelander_FlightNativeTickV2()
    if not S.enabled then return false end
    local f=(key("HL_KEY_W") and 1 or 0)-(key("HL_KEY_S") and 1 or 0)
    local r=(key("HL_KEY_D") and 1 or 0)-(key("HL_KEY_A") and 1 or 0)
    local u=(key("HL_KEY_SPACE") and 1 or 0)-((key("HL_KEY_CTRL") or key("HL_KEY_C")) and 1 or 0)
    return Homelander_FlightTickV2(f,r,u,key("HL_KEY_SHIFT"))
end

function Homelander_FlightDisableV2(restorePreflightVelocity)
    if restorePreflightVelocity==nil then restorePreflightVelocity=true end
    local h,v=S.handle,S.pre_velocity
    local wasEnabled=S.enabled
    S.enabled=false
    S.handle=nil
    S.pre_velocity=nil
    HOMELANDER_FLIGHT_V2_ENABLED=false

    -- F7 must never write pre-flight velocity to a stale/replaced player handle.
    local restoreAllowed=wasEnabled and restorePreflightVelocity and h~=nil and v~=nil and
        hasfn("phys_SetLinearVelocity")
    if restoreAllowed and not flight_provenance_ok(h) then
        restoreAllowed=false
        log("RESTORE SKIPPED: player identity/validity or setter proof changed")
    end
    if restoreAllowed then
        local okMag, restoreMag=pcall(function() return v:magnitude() end)
        if not okMag or not finite(restoreMag) then
            log("RESTORE SKIPPED: saved velocity is non-finite")
        elseif not flight_provenance_ok(h) then
            log("RESTORE SKIPPED: player/F5 proof changed while checking saved velocity")
        else
            local ok,err=pcall(phys_SetLinearVelocity,h,v,S.selector)
            if not ok then log("WARN: pre-flight velocity restore failed | "..tostring(err)) end
        end
    end
    if wasEnabled then log("DISABLED | restore="..tostring(restorePreflightVelocity)) end
    return true
end

function Homelander_FlightForceDisableV2()
    if not S.enabled then return false end
    log("FOCUS LOST: disabling flight control without velocity rewrite")
    return Homelander_FlightDisableV2(false)
end

function Homelander_FlightV2Status()
    return S.enabled,S.handle,S.cruise_speed,S.boost_speed,S.vertical_speed,
        S.planar_accel,S.air_brake,S.vertical_accel,S.hover_brake,S.submit_count
end

log("LOADED — Flight V2 staged/disabled; F5 setter echo must pass before F6 enable")
