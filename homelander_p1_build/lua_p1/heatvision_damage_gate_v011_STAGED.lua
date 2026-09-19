-- Homelander P1 Heat-Vision One-Shot Damage Gate v0.11
-- DORMANT / STAGED. Explicit F17 rising edge only.
-- Requires BOTH Lua + native v009/F16 120-submit dynamic stability proof.
-- Reacquires a fresh camera LOS hit and accepts only a valid non-player GOH.
-- Exactly one go_ApplyDamage(target, float) call on success.
-- NO DOT loop, hit-reaction vectors, world effects, velocity or physics mutation.

local PREFIX = "[HOMELANDER_P1_DAMAGE_V011] "

HOMELANDER_DAMAGE_ONESHOT_PASSED = false
HOMELANDER_DAMAGE_LAST_TARGET = nil
HOMELANDER_DAMAGE_LAST_AMOUNT = nil
HOMELANDER_DAMAGE_LAST_HIT_POS = nil
HOMELANDER_DAMAGE_LAST_FRACTION = nil
HOMELANDER_DAMAGE_LAST_HIT_NORMAL = nil

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function finite_number(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

local function valid_goh(h)
    if h == nil then return false end
    if type(go_IsValid) == "function" then
        local ok, v = pcall(go_IsValid, h)
        if not ok or not v then return false end
    end
    return true
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

-- Keep the exact measured 3-axis camera-forward selection method used by F16.
local function select_view_axis(frame, player_pos)
    local camera_pos = Vector(frame[1], frame[2], frame[3])
    local to_player = normalized(player_pos - camera_pos)
    if to_player == nil then return nil, nil, "camera/player separation degenerate" end

    local axes = {
        Vector(frame[4], frame[5], frame[6]),
        Vector(frame[7], frame[8], frame[9]),
        Vector(frame[10], frame[11], frame[12])
    }

    local best_axis = nil
    local best_score = -1.0
    local signed_dot = nil

    for i = 1, 3 do
        local axis, mag = normalized(axes[i])
        if axis == nil then
            return nil, nil, "camera basis axis " .. tostring(i) ..
                " degenerate | magnitude=" .. tostring(mag)
        end
        local d = axis:dot(to_player)
        if not finite_number(d) then
            return nil, nil, "camera basis dot failed for axis " .. tostring(i)
        end
        local score = math.abs(d)
        if score > best_score then
            best_score = score
            best_axis = axis
            signed_dot = d
        end
    end

    if best_axis == nil then return nil, nil, "no camera basis axis selected" end
    if signed_dot < 0.0 then best_axis = best_axis * -1.0 end
    return camera_pos, best_axis, nil
end

local function native_dynamic_stability_ok()
    if type(HL_LaserSightDynamicStabilityProbe) ~= "function" then
        return false, "native F16 stability probe unavailable"
    end
    local ok, passed = pcall(HL_LaserSightDynamicStabilityProbe)
    if not ok or passed ~= true then
        return false, "native 120-submit F16 stability proof missing"
    end
    return true, nil
end

local function required_api_ok()
    return type(Vector) == "function"
       and type(HL_GetCameraFrame) == "function"
       and type(HL_LastRayHitGOH) == "function"
       and type(HL_LaserSightDynamicStabilityProbe) == "function"
       and type(cm_GetCurrentRenderCameraPosition) == "function"
       and type(go_GetPosition) == "function"
       and type(fre_LineOfSightTest) == "function"
       and type(go_ApplyDamage) == "function"
end

function Homelander_HeatVisionDamageOneShotV011()
    if HOMELANDER_DAMAGE_ONESHOT_PASSED == true then
        log("REFUSED: one-shot damage already passed in this Lua-state bootstrap")
        return false
    end

    if HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED ~= true or
       tonumber(HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES) == nil or
       tonumber(HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES) < 120 then
        log("REFUSED: Lua 120-frame F16 dynamic stability proof missing")
        return false
    end

    local nativeOK, nativeWhy = native_dynamic_stability_ok()
    if not nativeOK then
        log("REFUSED: " .. tostring(nativeWhy))
        return false
    end

    if not required_api_ok() then
        log("REFUSED: required camera/LOS/damage API unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        log("REFUSED: current player invalid")
        return false
    end

    local okCam, camPos = pcall(cm_GetCurrentRenderCameraPosition)
    if not okCam or camPos == nil then
        log("REFUSED: render-camera getter failed")
        return false
    end

    local okFrame, rawFrame = pcall(HL_GetCameraFrame)
    if not okFrame then
        log("REFUSED: HL_GetCameraFrame error | " .. tostring(rawFrame))
        return false
    end
    local frame = parse_frame(rawFrame)
    if frame == nil then
        log("REFUSED: camera frame missing/invalid")
        return false
    end

    local okP, playerPos = pcall(go_GetPosition, player)
    if not okP or playerPos == nil then
        log("REFUSED: player position unavailable")
        return false
    end

    local start, forward, axisErr = select_view_axis(frame, playerPos)
    if start == nil or forward == nil then
        log("REFUSED: camera forward resolution failed | " .. tostring(axisErr))
        return false
    end

    local range = tonumber(HOMELANDER_DAMAGE_RAY_RANGE) or
                  tonumber(HOMELANDER_DYNAMIC_FREEAIM_RANGE) or 500.0
    if not finite_number(range) then
        log("REFUSED: damage ray range non-finite")
        return false
    end
    if range < 10.0 then range = 10.0 end
    if range > 1000.0 then range = 1000.0 end
    local rayEnd = start + forward * range

    local okLOS, hit, fraction, hitPos, hitNormal =
        pcall(fre_LineOfSightTest, start, rayEnd, true, player)
    if not okLOS then
        log("REFUSED: fre_LineOfSightTest error | " .. tostring(hit))
        return false
    end
    if not hit or hitPos == nil then
        log("REFUSED: fresh LOS did not hit a damageable GOH")
        return false
    end

    local okGOH, target = pcall(HL_LastRayHitGOH)
    if not okGOH or not valid_goh(target) then
        log("REFUSED: fresh LOS hit has no valid GOH; terrain/world hits are render-only")
        return false
    end
    if target == player then
        log("REFUSED: fresh LOS resolved to player")
        return false
    end

    -- v010 safety envelope: deliberately tiny one-shot damage only.
    local damage = tonumber(HOMELANDER_DAMAGE_ONESHOT_AMOUNT) or 1.0
    if not finite_number(damage) then
        log("REFUSED: damage amount non-finite")
        return false
    end
    if damage < 0.01 then damage = 0.01 end
    if damage > 1.0 then damage = 1.0 end

    HOMELANDER_DAMAGE_LAST_TARGET = target
    HOMELANDER_DAMAGE_LAST_AMOUNT = damage
    HOMELANDER_DAMAGE_LAST_HIT_POS = hitPos
    HOMELANDER_DAMAGE_LAST_FRACTION = fraction
    HOMELANDER_DAMAGE_LAST_HIT_NORMAL = hitNormal

    -- Exact active-P1 ABI proven statically: void go_ApplyDamage(LuaGOH, float).
    local okDamage, damageResult = pcall(go_ApplyDamage, target, damage)
    if not okDamage then
        log("FAIL: go_ApplyDamage raised | " .. tostring(damageResult))
        return false
    end

    HOMELANDER_DAMAGE_ONESHOT_PASSED = true
    log("PASS: one-shot go_ApplyDamage submitted | amount=" .. tostring(damage))

    -- Fail closed after one mutation. Another attempt needs a new F16 proof.
    if type(Homelander_DynamicAimForceDisableV010) == "function" then
        pcall(Homelander_DynamicAimForceDisableV010)
    end
    HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED = false
    HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES = nil
    if type(HL_LaserSightResetDynamicGate) == "function" then
        pcall(HL_LaserSightResetDynamicGate)
    end

    return true
end

log("LOADED — v011 dormant F17 one-shot damage gate; dual F16 stability required")
