-- Homelander P1 Flight Controller v1.3
-- STAGED / DISABLED BY DEFAULT.
-- Requires verified player + successful setter echo gate before enabling.
-- Camera-relative horizontal movement is attempted first and falls back to player-local basis.


local PREFIX = "[HOMELANDER_P1_FLIGHT_V1_3] "
local S = {
    enabled=false, handle=nil, pre_velocity=nil,
    cruise_speed=28.0, boost_speed=75.0, vertical_speed=22.0, selector=0,
    camera_relative=true,
    camera_fallback_logged=false
}
local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end
local function hasfn(name) return type(_G[name]) == "function" end
local function key(name) return _G[name] == "1" end


local function normalize_in_place(v)
    local mag = v:normalize()
    return v, mag
end


local function player_basis(handle)
    local p = go_GetPosition(handle)
    local right = go_Local2World(handle, Vector(1,0,0)) - p
    local forward = go_Local2World(handle, Vector(0,0,1)) - p
    local rmag, fmag
    right, rmag = normalize_in_place(right)
    forward, fmag = normalize_in_place(forward)
    if not rmag or not fmag or rmag <= 0.0001 or fmag <= 0.0001 then
        error("invalid player local2world basis")
    end
    return right, forward
end


local function get_camera_position()
    local names = {
        "cm_GetCurrentInGameCameraPosition",
        "cm_GetCurrentCameraPosition",
        "cm_GetCurrentRenderCameraPosition"
    }
    for _, name in ipairs(names) do
        if hasfn(name) then
            local ok, v = pcall(_G[name])
            if ok and v ~= nil then return v, name end
        end
    end
    error("no camera position getter succeeded")
end


local function camera_basis(handle)
    local p = go_GetPosition(handle)
    local cam = get_camera_position()


    local world_up = Vector(0,1,0)
    local forward = p - cam


    -- Project camera->player direction onto horizontal plane without relying on
    -- unknown x/y/z field names: v_horizontal = v - up * dot(v, up).
    local vertical = forward:dot(world_up)
    forward = forward - world_up * vertical
    local fmag
    forward, fmag = normalize_in_place(forward)
    if not fmag or fmag <= 0.0001 then error("degenerate camera horizontal forward") end


    -- P1 Vector:cross mutates receiver. up x forward => right.
    local right = Vector(world_up)
    right:cross(forward)
    local rmag
    right, rmag = normalize_in_place(right)
    if not rmag or rmag <= 0.0001 then error("degenerate camera right") end


    return right, forward
end


local function basis(handle)
    if S.camera_relative then
        local ok, right, forward = pcall(camera_basis, handle)
        if ok then
            S.camera_fallback_logged = false
            return right, forward
        end
        if not S.camera_fallback_logged then
            S.camera_fallback_logged = true
            log("camera-relative basis unavailable; falling back to player basis | " .. tostring(right))
        end
    end
    return player_basis(handle)
end


local function required_api_ok()
    return type(Vector)=="function"
       and hasfn("go_GetPosition") and hasfn("go_Local2World")
       and hasfn("ai_GetPhysicsVelocity") and hasfn("phys_SetLinearVelocity")
end


function Homelander_FlightEnable(handle)
    if S.enabled then return true end
    if HOMELANDER_SETTER_ECHO_PASSED ~= true then
        log("ABORT: setter echo gate has not passed")
        return false
    end
    if not required_api_ok() then log("ABORT: required API missing"); return false end
    if handle == nil then log("ABORT: handle nil"); return false end


    if hasfn("online_DeterminePlayerIndex") then
        local okidx, idx = pcall(online_DeterminePlayerIndex, handle)
        if not okidx or type(idx)~="number" or idx<0 then
            log("ABORT: handle does not verify as player | "..tostring(idx)); return false
        end
    end


    local ok,v=pcall(ai_GetPhysicsVelocity,handle)
    if not ok or v==nil then log("ABORT: velocity read failed | "..tostring(v)); return false end


    -- Validate at least the guaranteed player-local basis before mutating state.
    local okb,err=pcall(function() player_basis(handle) end)
    if not okb then log("ABORT: player basis failed | "..tostring(err)); return false end


    S.handle=handle
    S.pre_velocity=Vector(v)
    S.enabled=true
    S.camera_fallback_logged=false
    log("ENABLED — hover/flight starts on next native tick | camera_relative=" .. tostring(S.camera_relative))
    return true
end


function Homelander_FlightEnableVerified()
    if HOMELANDER_PLAYER==nil then log("ABORT: HOMELANDER_PLAYER not verified"); return false end
    return Homelander_FlightEnable(HOMELANDER_PLAYER)
end


function Homelander_FlightTick(input_fwd,input_right,input_up,boost)
    if not S.enabled or S.handle==nil then return false end
    input_fwd=math.max(-1,math.min(1,tonumber(input_fwd) or 0))
    input_right=math.max(-1,math.min(1,tonumber(input_right) or 0))
    input_up=math.max(-1,math.min(1,tonumber(input_up) or 0))


    local ok,err=pcall(function()
        local right,forward=basis(S.handle)
        local planar=forward*input_fwd + right*input_right
        local pmag=planar:magnitude()
        if pmag>1.0 then planar:normalize() end
        local speed=boost and S.boost_speed or S.cruise_speed
        local desired=planar*speed + Vector(0,input_up*S.vertical_speed,0)
        phys_SetLinearVelocity(S.handle,desired,S.selector)
    end)
    if not ok then
        log("TICK FAILED; controller disabled | "..tostring(err))
        S.enabled=false
        return false
    end
    return true
end


function Homelander_FlightNativeTick()
    if not S.enabled then return false end
    local f=(key("HL_KEY_W") and 1 or 0)-(key("HL_KEY_S") and 1 or 0)
    local r=(key("HL_KEY_D") and 1 or 0)-(key("HL_KEY_A") and 1 or 0)
    local u=(key("HL_KEY_SPACE") and 1 or 0)-((key("HL_KEY_CTRL") or key("HL_KEY_C")) and 1 or 0)
    return Homelander_FlightTick(f,r,u,key("HL_KEY_SHIFT"))
end


function Homelander_FlightSetCameraRelative(enabled)
    S.camera_relative = not not enabled
    S.camera_fallback_logged = false
    log("camera_relative=" .. tostring(S.camera_relative))
    return true
end


function Homelander_FlightDisable(restore_preflight_velocity)
    if restore_preflight_velocity == nil then restore_preflight_velocity = true end


    local h,v=S.handle,S.pre_velocity
    S.enabled=false
    S.handle=nil
    S.pre_velocity=nil


    if restore_preflight_velocity and h~=nil and v~=nil and hasfn("phys_SetLinearVelocity") then
        local ok,err=pcall(phys_SetLinearVelocity,h,v,S.selector)
        if not ok then log("WARN: pre-flight velocity restore failed | "..tostring(err)) end
    end
    log("DISABLED")
    return true
end


function Homelander_FlightStatus()
    return S.enabled,S.handle,S.cruise_speed,S.boost_speed,S.vertical_speed,S.camera_relative
end


log("LOADED — disabled. F5 echo gate must pass before enable.")