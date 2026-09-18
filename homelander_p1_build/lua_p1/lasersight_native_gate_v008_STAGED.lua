-- Homelander P1 Native LaserSight Gate v0.8
-- DORMANT / STAGED. Explicit F13/F14 only.
-- F13 = READ-ONLY pure3d::Shader resolution.
-- F14 = ONE-SHOT native LaserSight render events.
-- No ai_Laser, damage, world effects, velocity or physics mutation.

local PREFIX = "[HOMELANDER_P1_LASERSIGHT_NATIVE_V008] "

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

function Homelander_LaserSightShaderProbeV008()
    HOMELANDER_LASERSIGHT_SHADER_PASSED = false
    log("F13 BEGIN — READ ONLY")

    if type(HL_LaserSightShaderProbe) ~= "function" then
        log("F13 ABORT: native shader bridge unavailable")
        return false
    end

    local ok, result = pcall(HL_LaserSightShaderProbe)
    if not ok or result ~= true then
        log("F13 FAIL: proto_lit_glow did not resolve through LaserAction shader route | " ..
            tostring(result))
        return false
    end

    HOMELANDER_LASERSIGHT_SHADER_PASSED = true
    log("F13 PASS: allowlisted proto_lit_glow resolved read-only")
    return true
end

function Homelander_LaserSightOneShotV008()
    log("F14 BEGIN — ONE-SHOT REAL LASERSIGHT RENDER")

    if HOMELANDER_LASERSIGHT_SHADER_PASSED ~= true then
        log("F14 ABORT: F13 shader gate has not passed")
        return false
    end
    if type(HL_LaserSightSubmitDual) ~= "function" then
        log("F14 ABORT: native LaserSight submit bridge unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        log("F14 ABORT: current player missing/invalid")
        return false
    end

    if HOMELANDER_EYE_ORIGIN_VERIFIED ~= true or
       HOMELANDER_EYE_ORIGIN_NAME ~= "EYEPOINT" or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player then
        log("F14 ABORT: F11 EYEPOINT gate not verified for current player")
        return false
    end

    local target = HOMELANDER_FREEAIM_HIT
    local target_pos = HOMELANDER_FREEAIM_HIT_POS
    if not valid_goh(target) or target == player or target_pos == nil then
        log("F14 ABORT: current F9 target/hitpoint missing or invalid")
        return false
    end

    if HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH ~= target or
       HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET == nil or
       not finite_number(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR) then
        log("F14 ABORT: F10 target-local roundtrip state missing/stale")
        return false
    end

    if type(go_GetJointPosition) ~= "function" then
        log("F14 ABORT: go_GetJointPosition unavailable")
        return false
    end

    local okEye, eye_pos = pcall(go_GetJointPosition, player, "EYEPOINT")
    if not okEye or eye_pos == nil then
        log("F14 ABORT: fresh EYEPOINT getter failed")
        return false
    end

    local ex, ey, ez = vector_components(eye_pos)
    local tx, ty, tz = vector_components(target_pos)
    if ex == nil or tx == nil then
        log("F14 ABORT: could not extract finite world-space components")
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
        log("F14 ABORT: separation/thickness/RGBA outside staged safety bounds")
        return false
    end

    local ok, result = pcall(
        HL_LaserSightSubmitDual,
        player,
        ex, ey, ez,
        tx, ty, tz,
        sep, thickness,
        red, green, blue, alpha
    )

    if not ok or result ~= true then
        log("F14 FAIL: native dual LaserSight submit rejected | " .. tostring(result))
        return false
    end

    HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK = true
    HOMELANDER_LASERSIGHT_ONESHOT_LAST_TARGET = target
    log("F14 PASS: two REAL LaserSight render events submitted; no damage/VFX/physics mutation")
    return true
end

log("LOADED — v008 dormant native LaserSight gate; F13 read-only, F14 one-shot render only")
