-- Homelander P1 Flight Math Probe v2.2
-- READ-ONLY. No physics/state mutation.


local PREFIX = "[HOMELANDER_P1_FLIGHT_MATH_V2_2] "
local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end
local function hasfn(name) return type(_G[name]) == "function" end
local function safe(label, fn)
    local ok, a = pcall(fn)
    if ok then log(label .. " OK | " .. tostring(a)); return true, a end
    log(label .. " ERROR | " .. tostring(a)); return false, nil
end


local function normalized_copy(v)
    local c = Vector(v)
    local mag = c:normalize() -- mutates c in-place; returns original magnitude.
    return c, mag
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
            if ok and v ~= nil then
                return v, name
            end
        end
    end
    return nil, nil
end


local function probe_camera_relative_basis(player_pos)
    local cam, source = get_camera_position()
    if cam == nil then
        log("camera-relative basis unavailable: no camera position getter succeeded")
        return false
    end


    local world_up = Vector(0,1,0)
    local cam_to_player = player_pos - cam


    local ok_dot, vertical = pcall(function() return cam_to_player:dot(world_up) end)
    if not ok_dot or type(vertical) ~= "number" then
        log("camera-relative basis ERROR: dot() failed | " .. tostring(vertical))
        return false
    end


    local flat = cam_to_player - world_up * vertical
    local flat_mag = flat:normalize()
    if type(flat_mag) ~= "number" or flat_mag <= 0.0001 then
        log("camera-relative basis ERROR: degenerate horizontal forward")
        return false
    end


    -- P1 Vector:cross mutates the receiver in-place and returns no Vector.
    -- With Y-up / +Z forward, up x forward yields +X right.
    local right = Vector(world_up)
    local ok_cross, cross_err = pcall(function() right:cross(flat) end)
    if not ok_cross then
        log("camera-relative basis ERROR: cross() failed | " .. tostring(cross_err))
        return false
    end
    local right_mag = right:normalize()
    if type(right_mag) ~= "number" or right_mag <= 0.0001 then
        log("camera-relative basis ERROR: degenerate right vector")
        return false
    end


    local ortho = right:dot(flat)
    log("camera source=" .. tostring(source))
    log("camera position=" .. tostring(cam))
    log("camera flat forward=" .. tostring(flat) .. " | pre-normalize magnitude=" .. tostring(flat_mag))
    log("camera right=" .. tostring(right) .. " | pre-normalize magnitude=" .. tostring(right_mag))
    log("camera basis right·forward=" .. tostring(ortho))
    return true
end


function Homelander_FlightMathProbe(handle)
    log("BEGIN")
    if type(Vector) ~= "function" then log("ABORT: Vector unavailable"); return false end
    if not hasfn("go_GetPosition") or not hasfn("go_Local2World") then
        log("ABORT: go_GetPosition/go_Local2World unavailable"); return false
    end


    if hasfn("online_DeterminePlayerIndex") then
        local okidx, idx = pcall(online_DeterminePlayerIndex, handle)
        if not okidx or type(idx) ~= "number" or idx < 0 then
            log("ABORT: unverified player handle | " .. tostring(idx))
            return false
        end
    end


    local okp, p = safe("position", function() return go_GetPosition(handle) end)
    if not okp or p == nil then return false end


    local axes = {
        {"right +X", Vector(1,0,0)},
        {"up +Y", Vector(0,1,0)},
        {"forward +Z", Vector(0,0,1)}
    }
    for _, a in ipairs(axes) do
        local ok, wp = safe(a[1] .. " world point", function() return go_Local2World(handle, a[2]) end)
        if ok and wp ~= nil then
            local raw = wp - p
            local norm, mag = normalized_copy(raw)
            log(a[1] .. " raw=" .. tostring(raw))
            log(a[1] .. " normalized=" .. tostring(norm) .. " | magnitude=" .. tostring(mag))
        end
    end


    if hasfn("cm_GetCurrentCameraPosition") then safe("camera current", function() return cm_GetCurrentCameraPosition() end) end
    if hasfn("cm_GetCurrentInGameCameraPosition") then safe("camera ingame", function() return cm_GetCurrentInGameCameraPosition() end) end
    if hasfn("cm_GetCurrentRenderCameraPosition") then safe("camera render", function() return cm_GetCurrentRenderCameraPosition() end) end


    probe_camera_relative_basis(p)


    if hasfn("time_GetSimulationDelta") then safe("simulation delta", function() return time_GetSimulationDelta() end) end


    log("END — READ ONLY")
    return true
end


function Homelander_FlightMathProbe_Verified()
    if HOMELANDER_PLAYER == nil then
        log("ABORT: HOMELANDER_PLAYER not verified")
        return false
    end
    return Homelander_FlightMathProbe(HOMELANDER_PLAYER)
end


log("LOADED — read-only probe; explicit call required.")