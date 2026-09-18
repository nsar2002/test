-- Homelander P1 Dual-Eye Free-Aim Render Probe v0.7
-- ONE-SHOT RENDER ONLY / STAGED. Explicit F12 only.
-- Requires prior F4 -> F9 -> F10 -> F11 runtime gates.
-- Calls ai_Laser twice. NO damage, world effects, velocity or physics mutation.

local PREFIX = "[HOMELANDER_P1_DUAL_EYE_FREEAIM_V007] "

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

function Homelander_DualEyeFreeAimRenderProbe()
    log("BEGIN — ONE-SHOT RENDER ONLY")

    if type(ai_Laser) ~= "function" or type(Vector) ~= "function" then
        log("ABORT: ai_Laser/Vector unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        log("ABORT: player missing/invalid")
        return false
    end
    if HOMELANDER_EYE_ORIGIN_VERIFIED ~= true or
       HOMELANDER_EYE_ORIGIN_NAME ~= "EYEPOINT" or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player then
        log("ABORT: F11 EYEPOINT gate not verified for current player")
        return false
    end

    if type(go_GetJointPosition) ~= "function" then
        log("ABORT: go_GetJointPosition unavailable")
        return false
    end
    local okEye, currentEye = pcall(go_GetJointPosition, player, "EYEPOINT")
    if not okEye or currentEye == nil then
        log("ABORT: current EYEPOINT no longer resolves")
        return false
    end

    local target = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH
    local targetOffset = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET
    local roundtripError = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR
    if not valid_goh(target) or target == player or targetOffset == nil or
       type(roundtripError) ~= "number" then
        log("ABORT: F10 target-local gate state missing/invalid")
        return false
    end
    if HOMELANDER_FREEAIM_HIT ~= target then
        log("ABORT: current F9 hit GOH no longer matches F10 target")
        return false
    end

    -- CRITICAL SPACE RULE:
    -- F10 proved targetOffset in the target OBJECT's local space.
    -- Therefore targetJoint MUST remain empty so ai_Laser uses the base transform.
    local targetJoint = ""
    local sourceJoint = "EYEPOINT"

    local sep = tonumber(HOMELANDER_EYE_HALF_SEPARATION) or 0.035
    if sep < 0 then sep = -sep end
    if sep > 0.25 then
        log("ABORT: half eye separation exceeds 0.25 safety clamp")
        return false
    end

    local leftOffset = Vector(-sep, 0, 0)
    local rightOffset = Vector(sep, 0, 0)

    log("FIRE RENDER ONLY | sourceJoint=EYEPOINT targetJoint=<base> halfSep=" ..
        tostring(sep) .. " target=" .. tostring(target) ..
        " targetOffset=" .. tostring(targetOffset) ..
        " F10error=" .. tostring(roundtripError))

    local okL, errL = pcall(ai_Laser, player, sourceJoint, leftOffset,
                            target, targetJoint, targetOffset)
    local okR, errR = pcall(ai_Laser, player, sourceJoint, rightOffset,
                            target, targetJoint, targetOffset)

    log("left ai_Laser=" .. tostring(okL) .. " | " .. tostring(errL))
    log("right ai_Laser=" .. tostring(okR) .. " | " .. tostring(errR))

    HOMELANDER_DUAL_EYE_RENDER_LAST_OK = (okL and okR) and true or false
    HOMELANDER_DUAL_EYE_RENDER_LAST_TARGET = target
    log("END — NO DAMAGE/VFX")
    return okL and okR
end

log("LOADED — v007 staged one-shot render-only probe; explicit F12 only")
