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
    HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED = false
    HOMELANDER_LASERSIGHT_HELD_STABILITY_TARGET = nil
    HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED = false
    HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES = nil
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
    -- Every new F14 attempt revokes old F14/F15 proof before any game getter.
    local previous = HOMELANDER_LASERSIGHT_ONESHOT_ATTEMPT
    if previous == nil then previous = 0 end
    HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK = false
    HOMELANDER_LASERSIGHT_ONESHOT_LAST_TARGET = nil
    HOMELANDER_LASERSIGHT_ONESHOT_F9_EPOCH = nil
    HOMELANDER_LASERSIGHT_ONESHOT_F10_ATTEMPT = nil
    HOMELANDER_LASERSIGHT_ONESHOT_F11_EPOCH = nil
    if type(previous) ~= "number" or previous ~= previous or
       previous < 0 or previous >= 9007199254740991 or
       previous ~= math.floor(previous) then
        log("F14 ABORT: invalid/overflowed one-shot attempt generation")
        return false
    end
    local attempt = previous + 1
    HOMELANDER_LASERSIGHT_ONESHOT_ATTEMPT = attempt
    HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED = false
    HOMELANDER_LASERSIGHT_HELD_STABILITY_TARGET = nil
    HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED = false
    HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES = nil
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
    local original_hit_pos = HOMELANDER_FREEAIM_HIT_POS
    if not valid_goh(target) or target == player or original_hit_pos == nil then
        log("F14 ABORT: current F9 target/hitpoint missing or invalid")
        return false
    end

    local local_target_offset = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET
    if HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH ~= target or
       local_target_offset == nil or
       not finite_number(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR) then
        log("F14 ABORT: F10 target-local roundtrip state missing/stale")
        return false
    end

    -- Capture exact F9/F10/F11 provenance at the beginning of F14. Without
    -- these paired source guards the original staged F14 must fail closed.
    local f9epoch = HOMELANDER_FREEAIM_VERIFIED_EPOCH
    local f10attempt = HOMELANDER_FREEAIM_F10_VERIFIED_ATTEMPT
    local f11epoch = HOMELANDER_EYE_ORIGIN_VERIFIED_EPOCH
    local function same_proof()
        return HOMELANDER_LASERSIGHT_ONESHOT_ATTEMPT == attempt
            and type(f9epoch) == "number" and f9epoch >= 1
            and type(f10attempt) == "number" and f10attempt >= 1
            and type(f11epoch) == "number" and f11epoch >= 1
            and HOMELANDER_FREEAIM_EPOCH == f9epoch
            and HOMELANDER_FREEAIM_VERIFIED_EPOCH == f9epoch
            and HOMELANDER_FREEAIM_F10_EPOCH == f9epoch
            and HOMELANDER_FREEAIM_F10_ATTEMPT == f10attempt
            and HOMELANDER_FREEAIM_F10_VERIFIED_ATTEMPT == f10attempt
            and HOMELANDER_EYE_ORIGIN_EPOCH == f11epoch
            and HOMELANDER_EYE_ORIGIN_VERIFIED_EPOCH == f11epoch
            and HOMELANDER_PLAYER == player
            and HOMELANDER_FREEAIM_VERIFIED_PLAYER == player
            and HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER == player
            and HOMELANDER_FREEAIM_HIT == target
            and HOMELANDER_FREEAIM_HIT_POS == original_hit_pos
            and HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH == target
            and HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET == local_target_offset
            and HOMELANDER_EYE_ORIGIN_VERIFIED == true
            and HOMELANDER_EYE_ORIGIN_NAME == "EYEPOINT"
    end
    if not same_proof() then
        log("F14 ABORT: F9/F10/F11 exact provenance missing or superseded")
        return false
    end

    if type(go_GetJointPosition) ~= "function" or type(go_Local2World) ~= "function" then
        log("F14 ABORT: go_GetJointPosition/go_Local2World unavailable")
        return false
    end

    -- Reconstruct the SAME F10-proven object-local impact point against the
    -- target's CURRENT transform. This avoids aiming at a stale F9 world point
    -- when the target moved between F9/F10 and F14.
    local okTarget, target_pos = pcall(go_Local2World, target, local_target_offset)
    if not okTarget or target_pos == nil then
        log("F14 ABORT: current target local->world endpoint reconstruction failed")
        return false
    end

    local okDrift, drift = pcall(function()
        return (target_pos - original_hit_pos):magnitude()
    end)
    if okDrift and finite_number(drift) then
        log("F14 target endpoint drift since F9=" .. tostring(drift))
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

    -- Transform/joint APIs may synchronously run newer F9/F10/F11/F14.
    if not same_proof() then
        log("F14 ABORT: newer target/eye/one-shot attempt before native LaserSight")
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

    if not same_proof() then
        log("F14 ABORT: provenance superseded during native submit; effects may already be visible")
        return false
    end
    HOMELANDER_LASERSIGHT_ONESHOT_F9_EPOCH = f9epoch
    HOMELANDER_LASERSIGHT_ONESHOT_F10_ATTEMPT = f10attempt
    HOMELANDER_LASERSIGHT_ONESHOT_F11_EPOCH = f11epoch
    HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK = true
    HOMELANDER_LASERSIGHT_ONESHOT_LAST_TARGET = target
    log("F14 PASS: two REAL LaserSight render events submitted; no damage/VFX/physics mutation")
    return true
end

log("LOADED — v008 dormant native LaserSight gate; F13 read-only, F14 one-shot render only")
