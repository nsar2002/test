-- Homelander P1 One-Shot Impact VFX Gate v0.12
-- DORMANT / STAGED. Explicit F18 rising edge only.
-- Requires a successful v010/F17 one-shot damage transaction.
-- Uses the exact saved F17 world hit position.
-- Exactly one em_AddWorldEffect submission; no damage, DOT or physics mutation.

local PREFIX = "[HOMELANDER_P1_IMPACT_V012] "
local EFFECT = "missileImpact001"

HOMELANDER_IMPACT_VFX_SUBMITTED = false
HOMELANDER_IMPACT_VFX_RESERVED = false
HOMELANDER_IMPACT_VFX_ATTEMPT = 0
HOMELANDER_IMPACT_VFX_RUNTIME_PASSED = false
HOMELANDER_IMPACT_VFX_LAST_EFFECT = nil
HOMELANDER_IMPACT_VFX_LAST_POSITION = nil
HOMELANDER_IMPACT_VFX_LAST_SCALE = nil
HOMELANDER_IMPACT_VFX_LAST_NATIVE_RETURN = nil

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function finite_number(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

local function vector_components(v)
    if v == nil or type(Vector) ~= "function" then return nil end
    local ex = Vector(1, 0, 0)
    local ey = Vector(0, 1, 0)
    local ez = Vector(0, 0, 1)
    local okx, x = pcall(function() return v:dot(ex) end)
    local oky, y = pcall(function() return v:dot(ey) end)
    local okz, z = pcall(function() return v:dot(ez) end)
    if not okx or not oky or not okz or
       not finite_number(x) or not finite_number(y) or not finite_number(z) then
        return nil
    end
    return x, y, z
end

function Homelander_ImpactVFXOneShotV012()
    -- An opaque/void native effect may render and then raise. Only one
    -- submission is permissible even when its visual outcome is ambiguous.
    if HOMELANDER_IMPACT_VFX_RESERVED == true then
        log("REFUSED: impact VFX already submitted/ambiguous in this Lua state")
        return false
    end
    local previous = HOMELANDER_IMPACT_VFX_ATTEMPT
    if type(previous) ~= "number" or previous ~= previous or
       previous < 0 or previous >= 9007199254740991 or
       previous ~= math.floor(previous) then
        log("REFUSED: invalid/overflowed F18 VFX attempt generation")
        return false
    end
    local attempt = previous + 1
    HOMELANDER_IMPACT_VFX_ATTEMPT = attempt
    if HOMELANDER_IMPACT_VFX_SUBMITTED == true then
        log("REFUSED: one-shot impact VFX already submitted in this chain")
        return false
    end

    if HOMELANDER_DAMAGE_ONESHOT_PASSED ~= true then
        log("REFUSED: successful v010/F17 damage proof missing")
        return false
    end

    if type(em_AddWorldEffect) ~= "function" then
        log("REFUSED: em_AddWorldEffect unavailable")
        return false
    end

    local hitPos = HOMELANDER_DAMAGE_LAST_HIT_POS
    local x, y, z = vector_components(hitPos)
    if x == nil then
        log("REFUSED: stored F17 world hit position missing/non-finite")
        return false
    end

    local scale = tonumber(HOMELANDER_IMPACT_VFX_SCALE) or 0.15
    if not finite_number(scale) then
        log("REFUSED: impact scale non-finite")
        return false
    end
    if scale < 0.05 then scale = 0.05 end
    if scale > 0.50 then scale = 0.50 end

    -- Earlier health/debug/Vector callbacks may synchronously call newer
    -- F18. Revalidate original F17 transaction and source hitpoint just
    -- before the irreversible native VFX submission.
    if HOMELANDER_IMPACT_VFX_ATTEMPT ~= attempt or
       HOMELANDER_IMPACT_VFX_RESERVED == true or
       HOMELANDER_DAMAGE_ONESHOT_PASSED ~= true or
       HOMELANDER_DAMAGE_ONESHOT_RESERVED ~= true or
       HOMELANDER_DAMAGE_LAST_HIT_POS ~= hitPos then
        log("REFUSED: F17 source proof or F18 generation changed before effect")
        return false
    end

    -- Reserve and consume upstream F17 BEFORE native effect. Nested F18
    -- cannot submit a second effect through a Lua/native callback, and a
    -- native exception-after-effect cannot safely be retried.
    HOMELANDER_IMPACT_VFX_RESERVED = true
    HOMELANDER_DAMAGE_ONESHOT_PASSED = false
    local ok, nativeReturn = pcall(em_AddWorldEffect, EFFECT, hitPos, scale)
    if not ok then
        log("FAIL: native VFX result ambiguous; one-shot consumed | " .. tostring(nativeReturn))
        return false
    end

    HOMELANDER_IMPACT_VFX_SUBMITTED = true
    HOMELANDER_IMPACT_VFX_LAST_EFFECT = EFFECT
    HOMELANDER_IMPACT_VFX_LAST_POSITION = hitPos
    HOMELANDER_IMPACT_VFX_LAST_SCALE = scale
    HOMELANDER_IMPACT_VFX_LAST_NATIVE_RETURN = nativeReturn

    -- Consume the upstream mutation proof. A reload cannot re-arm F18 without
    -- a new successful F17 transaction.
    HOMELANDER_DAMAGE_ONESHOT_PASSED = false

    log("SUBMITTED: one-shot impact VFX | effect=" .. EFFECT ..
        " scale=" .. tostring(scale) ..
        " nativeReturn=" .. tostring(nativeReturn) ..
        " | visible runtime result still required for PASS")
    return true
end

log("LOADED — v012 dormant F18 one-shot impact VFX gate")
