-- Homelander P1 Held Native LaserSight Gate v0.9
-- DORMANT / STAGED. Explicit F15 toggle only.
-- Requires a successful F14 one-shot in the SAME runtime session.
-- Re-renders the SAME F10-proven target-local impact point each GOM tick.
-- NO new raycast/retarget, NO damage, NO DOT, NO VFX, NO physics mutation.

local PREFIX = "[HOMELANDER_P1_LASERSIGHT_HELD_V009] "
local S = {
    enabled = false,
    target = nil,
    frames = 0
}

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

local function disable(reason)
    local was_enabled = S.enabled
    S.enabled = false
    S.target = nil
    S.frames = 0
    if was_enabled then
        log("DISABLED" .. (reason and (" | " .. tostring(reason)) or ""))
    end
    return true
end

local function current_gate_state()
    if HOMELANDER_LASERSIGHT_SHADER_PASSED ~= true then
        return nil, "F13 shader gate no longer passed"
    end
    if HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK ~= true then
        return nil, "F14 one-shot gate not passed in this session"
    end

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        return nil, "current player invalid"
    end
    if HOMELANDER_EYE_ORIGIN_VERIFIED ~= true or
       HOMELANDER_EYE_ORIGIN_NAME ~= "EYEPOINT" or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player then
        return nil, "F11 EYEPOINT state missing/stale"
    end

    local target = HOMELANDER_FREEAIM_HIT
    if not valid_goh(target) or target == player then
        return nil, "current F9 target invalid"
    end
    if HOMELANDER_LASERSIGHT_ONESHOT_LAST_TARGET ~= target then
        return nil, "current target differs from successful F14 target"
    end

    local local_offset = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET
    if HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH ~= target or
       local_offset == nil or
       not finite_number(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR) then
        return nil, "F10 local-impact state missing/stale"
    end

    return {
        player = player,
        target = target,
        local_offset = local_offset
    }, nil
end

function Homelander_LaserSightHeldToggleV009()
    if S.enabled then
        return disable("manual F15 toggle")
    end

    if type(HL_LaserSightSubmitDual) ~= "function" or
       type(go_GetJointPosition) ~= "function" or
       type(go_Local2World) ~= "function" then
        log("REFUSED: required native/Lua transform API unavailable")
        return false
    end

    local G, why = current_gate_state()
    if G == nil then
        log("REFUSED: " .. tostring(why))
        return false
    end

    if type(HL_LaserSightResetHeldGate) ~= "function" then
        log("REFUSED: native held-stability reset bridge unavailable")
        return false
    end
    local okReset, resetResult = pcall(HL_LaserSightResetHeldGate)
    if not okReset or resetResult ~= true then
        log("REFUSED: native held-stability reset failed | " .. tostring(resetResult))
        return false
    end

    HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED = false
    HOMELANDER_LASERSIGHT_HELD_STABILITY_TARGET = nil
    S.enabled = true
    S.target = G.target
    S.frames = 0
    log("ENABLED — held render at the F10-proven local impact point; no retarget/damage")
    return true
end

function Homelander_LaserSightHeldForceDisableV009()
    return disable("focus lost / bootstrap / explicit safety stop")
end

function Homelander_LaserSightHeldTickV009()
    if not S.enabled then return false end

    local G, why = current_gate_state()
    if G == nil then
        disable(why)
        return false
    end
    if G.target ~= S.target then
        disable("target changed since held mode was armed")
        return false
    end

    local okTarget, target_pos = pcall(go_Local2World, G.target, G.local_offset)
    if not okTarget or target_pos == nil then
        disable("current target local->world reconstruction failed")
        return false
    end

    local okEye, eye_pos = pcall(go_GetJointPosition, G.player, "EYEPOINT")
    if not okEye or eye_pos == nil then
        disable("fresh EYEPOINT getter failed")
        return false
    end

    local ex, ey, ez = vector_components(eye_pos)
    local tx, ty, tz = vector_components(target_pos)
    if ex == nil or tx == nil then
        disable("non-finite eye/target world components")
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

    -- 14th numeric arg = quiet held submit.
    -- Native code independently requires its own g_laserOneShotPassed=true.
    local ok, result = pcall(
        HL_LaserSightSubmitDual,
        G.player,
        ex, ey, ez,
        tx, ty, tz,
        sep, thickness,
        red, green, blue, alpha,
        1
    )

    if not ok or result ~= true then
        disable("native held LaserSight submit failed | " .. tostring(result))
        return false
    end

    S.frames = S.frames + 1

    local max_frames = tonumber(HOMELANDER_LASERSIGHT_MAX_HELD_FRAMES) or 600
    if max_frames < 60 then max_frames = 60 end
    if max_frames > 3600 then max_frames = 3600 end

    if S.frames == 120 then
        HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED = true
        HOMELANDER_LASERSIGHT_HELD_STABILITY_TARGET = S.target
        log("STABILITY PASS | 120 consecutive successful held render frames")
    elseif (S.frames % 120) == 0 then
        log("HEARTBEAT | successful held render frames=" .. tostring(S.frames) ..
            " maxFrames=" .. tostring(max_frames))
    end

    if S.frames >= max_frames then
        disable("automatic held-render timeout at " .. tostring(max_frames) .. " frames")
    end

    return true
end

function Homelander_LaserSightHeldStatusV009()
    return S.enabled, S.target, S.frames
end

log("LOADED — v009 dormant held renderer; explicit F15 toggle; requires same-session F14 PASS")
