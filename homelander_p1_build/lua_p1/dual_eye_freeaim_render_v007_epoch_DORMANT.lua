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


local function finite(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

-- This is the paired F9/F10/F11 provenance overlay, NOT compatible with
-- the original unguarded F9 (which does not publish VERIFIED_PLAYER).
local function bound_to_current(player, target, offset, f9epoch)
    if type(f9epoch) ~= "number" or f9epoch < 1 or
       f9epoch ~= f9epoch or
       HOMELANDER_FREEAIM_EPOCH ~= f9epoch or
       HOMELANDER_FREEAIM_VERIFIED_EPOCH ~= f9epoch or
       HOMELANDER_FREEAIM_F10_EPOCH ~= f9epoch or
       HOMELANDER_PLAYER ~= player or
       HOMELANDER_FREEAIM_VERIFIED_PLAYER ~= player or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player or
       HOMELANDER_EYE_ORIGIN_VERIFIED ~= true or
       HOMELANDER_EYE_ORIGIN_NAME ~= "EYEPOINT" or
       HOMELANDER_FREEAIM_HIT ~= target or
       HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH ~= target or
       HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET ~= offset or
       not valid_goh(player) or not valid_goh(target) or
       HOMELANDER_PLAYER ~= player or HOMELANDER_FREEAIM_HIT ~= target or
       HOMELANDER_FREEAIM_VERIFIED_PLAYER ~= player or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player or
       HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH ~= target or
       HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET ~= offset or
       HOMELANDER_FREEAIM_EPOCH ~= f9epoch or
       HOMELANDER_FREEAIM_VERIFIED_EPOCH ~= f9epoch or
       HOMELANDER_FREEAIM_F10_EPOCH ~= f9epoch then
        return false
    end
    return true
end

function Homelander_DualEyeFreeAimRenderProbe()
    -- A new attempt must not leave an earlier successful render receipt.
    HOMELANDER_DUAL_EYE_RENDER_LAST_OK = false
    HOMELANDER_DUAL_EYE_RENDER_LAST_TARGET = nil
    log("BEGIN — ONE-SHOT RENDER ONLY | guarded provenance")

    if type(ai_Laser) ~= "function" or type(Vector) ~= "function" or
       type(go_GetJointPosition) ~= "function" then
        log("ABORT: required render/joint API unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    local target = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH
    local offset = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET
    local err = HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR
    local f9epoch = HOMELANDER_FREEAIM_VERIFIED_EPOCH
    if player == nil or target == nil or player == target or offset == nil or
       not finite(err) or err < 0.0 or not bound_to_current(player,target,offset,f9epoch) then
        log("ABORT: no valid same-player F9/F10/F11 proof")
        return false
    end

    local okEye, eye = pcall(go_GetJointPosition, player, "EYEPOINT")
    if not okEye or eye == nil or not bound_to_current(player,target,offset,f9epoch) then
        log("ABORT: current eye missing or player/target changed during joint getter")
        return false
    end

    local sep = tonumber(HOMELANDER_EYE_HALF_SEPARATION)
    if sep == nil then sep = 0.035 end
    if not finite(sep) then
        log("ABORT: nonfinite eye separation")
        return false
    end
    if sep < 0.0 then sep = -sep end
    if sep > 0.25 then
        log("ABORT: half eye separation exceeds safety clamp")
        return false
    end

    -- The F10 offset is target-base-local: targetJoint must stay empty.
    local left = Vector(-sep,0,0)
    local right = Vector(sep,0,0)
    if not bound_to_current(player,target,offset,f9epoch) then
        log("ABORT: proof invalidated before left-eye call")
        return false
    end

    local okL, resultL = pcall(ai_Laser, player, "EYEPOINT", left,
                                target, "", offset)
    -- Lua pcall(true, false) is not a successful engine render result.
    if not okL or resultL == false then
        log("ABORT: left-eye render failed | "..tostring(resultL))
        return false
    end

    -- The first native call can invalidate or rebind the Lua player/target.
    -- Never submit the second call using a stale first-call snapshot.
    if not bound_to_current(player,target,offset,f9epoch) then
        log("ABORT: provenance changed after left-eye render; PARTIAL ONE-EYE EFFECT POSSIBLE")
        return false
    end
    local okR, resultR = pcall(ai_Laser, player, "EYEPOINT", right,
                                target, "", offset)
    if not okR or resultR == false then
        log("ABORT: right-eye render failed; PARTIAL ONE-EYE EFFECT POSSIBLE | "..tostring(resultR))
        return false
    end
    if not bound_to_current(player,target,offset,f9epoch) then
        log("ABORT: provenance changed after right-eye call; prior effects cannot be undone")
        return false
    end

    HOMELANDER_DUAL_EYE_RENDER_LAST_TARGET = target
    HOMELANDER_DUAL_EYE_RENDER_LAST_OK = true
    log("END — TWO RENDER CALLS SUBMITTED; NO DAMAGE/VFX")
    return true
end

log("LOADED — v007 DORMANT guarded one-shot render-only probe; explicit F12 only")
