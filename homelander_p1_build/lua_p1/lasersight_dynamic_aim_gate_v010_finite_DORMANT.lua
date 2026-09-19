-- Homelander P1 Dynamic Free-Aim Native LaserSight Gate v0.10
-- DORMANT / STAGED. Explicit F16 toggle only.
-- Requires BOTH Lua and native 120-frame F15 stability proof.
-- Reacquires a fresh camera LOS hit every GOM tick.
-- NO damage, DOT, world effects, velocity or physics mutation.

local PREFIX = "[HOMELANDER_P1_DYNAMIC_AIM_V010] "
local S = {
    enabled = false,
    frames = 0,
    ticks = 0,
    hits = 0,
    misses = 0,
    goh_hits = 0,
    world_hits = 0,
    last_heartbeat_frame = 0
}

-- Never inherit a dynamic stability proof across Lua-state bootstrap/reload.
HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED = false
HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES = nil

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function valid_goh(h)
    if h == nil then return false end
    if type(go_IsValid) == "function" then
        local ok, v = pcall(go_IsValid, h)
        if not ok or not v then return false end
    end
    return true
end

local function finite_number(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

local function normalized(v)
    local c = Vector(v)
    local mag = c:normalize()
    if not finite_number(mag) or mag <= 0.0001 then return nil, mag end
    return c, mag
end

local function parse_frame(raw)
    if type(raw) ~= "string" or raw == "" then return nil end
    local values = {}
    for token in string.gmatch(raw, "[^,]+") do
        local n = tonumber(token)
        if not finite_number(n) then return nil end
        values[#values + 1] = n
    end
    if #values ~= 12 then return nil end
    return values
end

local function select_view_axis(frame, player_pos)
    local camera_pos = Vector(frame[1], frame[2], frame[3])
    local to_player, to_player_mag = normalized(player_pos - camera_pos)
    if to_player == nil then
        return nil, nil, nil, "camera/player separation degenerate"
    end

    local axes = {
        Vector(frame[4], frame[5], frame[6]),
        Vector(frame[7], frame[8], frame[9]),
        Vector(frame[10], frame[11], frame[12])
    }

    local best_axis = nil
    local best_index = nil
    local best_score = -1.0
    local second_score = -1.0
    local signed_dot = nil
    local scores = {}

    for i = 1, 3 do
        local axis, mag = normalized(axes[i])
        if axis == nil then
            return nil, nil, nil, "camera basis axis " .. tostring(i) ..
                " degenerate | magnitude=" .. tostring(mag)
        end

        local d = axis:dot(to_player)
        if not finite_number(d) then
            return nil, nil, nil, "camera basis dot failed for axis " .. tostring(i)
        end

        local score = math.abs(d)
        scores[#scores + 1] = tostring(i) .. ":" .. tostring(score)
        if score > best_score then
            second_score = best_score
            best_score = score
            best_axis = axis
            best_index = i
            signed_dot = d
        elseif score > second_score then
            second_score = score
        end
    end

    if best_axis == nil then return nil, nil, nil, "no camera basis axis selected" end
    if signed_dot < 0.0 then best_axis = best_axis * -1.0 end

    return camera_pos, best_axis, {
        axis_index = best_index,
        best_score = best_score,
        second_score = second_score,
        margin = best_score - second_score,
        scores = table.concat(scores, ","),
        camera_player_distance = to_player_mag
    }, nil
end

local function vector_components(v)
    if v == nil or type(Vector) ~= "function" then return nil end
    local ex = Vector(1,0,0)
    local ey = Vector(0,1,0)
    local ez = Vector(0,0,1)
    local okx, x = pcall(function() return v:dot(ex) end)
    local oky, y = pcall(function() return v:dot(ey) end)
    local okz, z = pcall(function() return v:dot(ez) end)
    if not okx or not oky or not okz or
       not finite_number(x) or not finite_number(y) or not finite_number(z) then
        return nil
    end
    return x, y, z
end

local function native_stability_ok()
    if type(HL_LaserSightHeldStabilityProbe) ~= "function" then
        return false, "native stability query bridge unavailable"
    end
    local ok, passed = pcall(HL_LaserSightHeldStabilityProbe)
    if not ok or passed ~= true then
        return false, "native 120-frame F15 stability proof not present"
    end
    return true, nil
end

local function native_dynamic_stability_ok()
    if type(HL_LaserSightDynamicStabilityProbe) ~= "function" then
        return false, "native dynamic stability query bridge unavailable"
    end
    local ok, passed = pcall(HL_LaserSightDynamicStabilityProbe)
    if not ok or passed ~= true then
        return false, "native 120-submit F16 stability proof not present"
    end
    return true, nil
end

local function disable(reason)
    local was = S.enabled
    S.enabled = false
    if was then
        log("DISABLED" .. (reason and (" | " .. tostring(reason)) or ""))
    end
    return true
end

local function required_api_ok()
    return type(Vector) == "function"
       and type(HL_GetCameraFrame) == "function"
       and type(HL_LastRayHitGOH) == "function"
       and type(HL_LaserSightSubmitDual) == "function"
       and type(cm_GetCurrentRenderCameraPosition) == "function"
       and type(go_GetPosition) == "function"
       and type(go_GetJointPosition) == "function"
       and type(fre_LineOfSightTest) == "function"
end

function Homelander_DynamicAimToggleV010()
    if S.enabled then
        return disable("manual F16 toggle")
    end

    if HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED ~= true then
        log("REFUSED: Lua 120-frame F15 stability proof missing")
        return false
    end

    local nativeOK, nativeWhy = native_stability_ok()
    if not nativeOK then
        log("REFUSED: " .. tostring(nativeWhy))
        return false
    end

    if HOMELANDER_LASERSIGHT_SHADER_PASSED ~= true then
        log("REFUSED: F13 shader gate no longer passed")
        return false
    end

    if not required_api_ok() then
        log("REFUSED: required camera/LOS/LaserSight API unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        log("REFUSED: current player invalid")
        return false
    end
    if HOMELANDER_EYE_ORIGIN_VERIFIED ~= true or
       HOMELANDER_EYE_ORIGIN_NAME ~= "EYEPOINT" or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player then
        log("REFUSED: F11 EYEPOINT state missing/stale")
        return false
    end

    if type(Homelander_LaserSightHeldForceDisableV009) == "function" then
        pcall(Homelander_LaserSightHeldForceDisableV009)
    end

    if type(HL_LaserSightResetDynamicGate) ~= "function" then
        log("REFUSED: native dynamic-stability reset bridge unavailable")
        return false
    end
    local okReset, resetResult = pcall(HL_LaserSightResetDynamicGate)
    if not okReset or resetResult ~= true then
        log("REFUSED: native dynamic-stability reset failed | " .. tostring(resetResult))
        return false
    end

    HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED = false
    HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES = nil

    S.enabled = true
    S.frames = 0
    S.ticks = 0
    S.hits = 0
    S.misses = 0
    S.goh_hits = 0
    S.world_hits = 0
    S.last_heartbeat_frame = 0
    log("ENABLED — fresh per-tick camera LOS -> native LaserSight; render only")
    return true
end

function Homelander_DynamicAimForceDisableV010()
    return disable("focus lost / F15 switch / bootstrap / explicit safety stop")
end

function Homelander_DynamicAimTickV010()
    if not S.enabled then return false end

    S.ticks = S.ticks + 1

    -- Both limits must be finite BEFORE ANY native camera/LOS/laser callback.
    -- Lua NaN fails < and > comparisons, otherwise defeating both timeouts.
    local maxFrames = tonumber(HOMELANDER_DYNAMIC_MAX_RENDER_FRAMES) or 600
    local maxTicks = tonumber(HOMELANDER_DYNAMIC_MAX_TICKS) or 1800
    if not finite_number(maxFrames) or not finite_number(maxTicks) then
        disable("nonfinite dynamic render/tick limits; no native LOS")
        return false
    end
    if maxFrames < 60 then maxFrames = 60 end
    if maxFrames > 3600 then maxFrames = 3600 end
    if maxTicks < 120 then maxTicks = 120 end
    if maxTicks > 7200 then maxTicks = 7200 end

    if HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED ~= true or
       HOMELANDER_LASERSIGHT_SHADER_PASSED ~= true then
        disable("prerequisite Lua gate invalidated")
        return false
    end

    local nativeOK, nativeWhy = native_stability_ok()
    if not nativeOK then
        disable(nativeWhy)
        return false
    end

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        disable("player invalid")
        return false
    end
    if HOMELANDER_EYE_ORIGIN_VERIFIED ~= true or
       HOMELANDER_EYE_ORIGIN_NAME ~= "EYEPOINT" or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player then
        disable("F11 EYEPOINT state invalidated")
        return false
    end

    -- Refresh native render-camera capture before asking HL_GetCameraFrame.
    local okCam, camPos = pcall(cm_GetCurrentRenderCameraPosition)
    if not okCam or camPos == nil then
        disable("render-camera getter failed")
        return false
    end

    local okFrame, rawFrame = pcall(HL_GetCameraFrame)
    if not okFrame then
        disable("HL_GetCameraFrame error | " .. tostring(rawFrame))
        return false
    end
    local frame = parse_frame(rawFrame)
    if frame == nil then
        disable("camera frame missing/invalid")
        return false
    end

    local okP, playerPos = pcall(go_GetPosition, player)
    if not okP or playerPos == nil then
        disable("player position unavailable")
        return false
    end

    local start, forward, axisInfo, axisErr = select_view_axis(frame, playerPos)
    if start == nil or forward == nil then
        disable("camera forward resolution failed | " .. tostring(axisErr))
        return false
    end

    local range = tonumber(HOMELANDER_DYNAMIC_FREEAIM_RANGE) or 500.0
    if not finite_number(range) then
        disable("nonfinite free-aim range; native LOS not called")
        return false
    end
    if range < 10.0 then range = 10.0 end
    if range > 1000.0 then range = 1000.0 end
    local rayEnd = start + forward * range

    local okLOS, hit, fraction, hitPos, hitNormal =
        pcall(fre_LineOfSightTest, start, rayEnd, true, player)
    if not okLOS then
        disable("fre_LineOfSightTest error | " .. tostring(hit))
        return false
    end

    HOMELANDER_DYNAMIC_CAMERA_START = start
    HOMELANDER_DYNAMIC_CAMERA_FORWARD = forward
    HOMELANDER_DYNAMIC_RAY_END = rayEnd
    HOMELANDER_DYNAMIC_AXIS_INDEX = axisInfo.axis_index
    HOMELANDER_DYNAMIC_AXIS_BEST_SCORE = axisInfo.best_score
    HOMELANDER_DYNAMIC_AXIS_MARGIN = axisInfo.margin
    HOMELANDER_DYNAMIC_HIT = nil
    HOMELANDER_DYNAMIC_HIT_POS = nil
    HOMELANDER_DYNAMIC_HIT_NORMAL = nil
    HOMELANDER_DYNAMIC_FRACTION = nil

    if not hit then
        S.misses = S.misses + 1
    else
        if hitPos == nil then
            disable("LOS reported hit without hit position")
            return false
        end

        HOMELANDER_DYNAMIC_HIT_POS = hitPos
        HOMELANDER_DYNAMIC_HIT_NORMAL = hitNormal
        HOMELANDER_DYNAMIC_FRACTION = fraction

        local hitGOH = nil
        local okGOH, candidate = pcall(HL_LastRayHitGOH)
        if okGOH and valid_goh(candidate) and candidate ~= player then
            hitGOH = candidate
            HOMELANDER_DYNAMIC_HIT = candidate
            S.goh_hits = S.goh_hits + 1
        else
            S.world_hits = S.world_hits + 1
        end

        local okEye, eyePos = pcall(go_GetJointPosition, player, "EYEPOINT")
        if not okEye or eyePos == nil then
            disable("fresh EYEPOINT getter failed")
            return false
        end

        local ex, ey, ez = vector_components(eyePos)
        local tx, ty, tz = vector_components(hitPos)
        if ex == nil or tx == nil then
            disable("non-finite eye/hit world components")
            return false
        end

        local sep = tonumber(HOMELANDER_EYE_HALF_SEPARATION) or 0.035
        if sep < 0 then sep = -sep end
        local thickness = tonumber(HOMELANDER_LASERSIGHT_THICKNESS) or 0.045
        local red = tonumber(HOMELANDER_LASERSIGHT_R) or 1.0
        local green = tonumber(HOMELANDER_LASERSIGHT_G) or 0.02
        local blue = tonumber(HOMELANDER_LASERSIGHT_B) or 0.01
        local alpha = tonumber(HOMELANDER_LASERSIGHT_A) or 1.0

        if not finite_number(sep) or sep > 0.25 or
           not finite_number(thickness) or thickness < 0.001 or thickness > 0.50 or
           not finite_number(red) or red < 0 or red > 1 or
           not finite_number(green) or green < 0 or green > 1 or
           not finite_number(blue) or blue < 0 or blue > 1 or
           not finite_number(alpha) or alpha < 0 or alpha > 1 then
            disable("separation/thickness/RGBA outside staged safety bounds")
            return false
        end

        -- Mode 2 = dynamic F16. Native independently requires its own
        -- 120-frame held-stability proof.
        local okSubmit, submitResult = pcall(
            HL_LaserSightSubmitDual,
            player,
            ex, ey, ez,
            tx, ty, tz,
            sep, thickness,
            red, green, blue, alpha,
            2
        )
        if not okSubmit or submitResult ~= true then
            disable("native dynamic LaserSight submit failed | " .. tostring(submitResult))
            return false
        end

        S.hits = S.hits + 1
        S.frames = S.frames + 1
    end

    if S.frames == 120 and HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED ~= true then
        local dynOK, dynWhy = native_dynamic_stability_ok()
        if not dynOK then
            disable("Lua/native F16 stability mismatch | " .. tostring(dynWhy))
            return false
        end
        HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED = true
        HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES = S.frames
        log("STABILITY PASS | 120 successful dynamic LaserSight submits (Lua + native)")
    end

    if S.frames > 0 and (S.frames % 120) == 0 and S.frames ~= S.last_heartbeat_frame then
        S.last_heartbeat_frame = S.frames
        log("HEARTBEAT | rendered=" .. tostring(S.frames) ..
            " hits=" .. tostring(S.hits) ..
            " misses=" .. tostring(S.misses) ..
            " gohHits=" .. tostring(S.goh_hits) ..
            " worldHits=" .. tostring(S.world_hits) ..
            " axis=" .. tostring(axisInfo.axis_index) ..
            " score=" .. tostring(axisInfo.best_score) ..
            " margin=" .. tostring(axisInfo.margin))
    end

    if S.frames >= maxFrames then
        disable("automatic render-frame timeout at " .. tostring(maxFrames))
    elseif S.ticks >= maxTicks then
        disable("automatic total-tick timeout at " .. tostring(maxTicks))
    end

    return true
end

function Homelander_DynamicAimStatusV010()
    return S.enabled, S.frames, S.ticks, S.hits, S.misses, S.goh_hits, S.world_hits
end

log("LOADED — v010 dormant dynamic free-aim renderer; explicit F16; render only")
