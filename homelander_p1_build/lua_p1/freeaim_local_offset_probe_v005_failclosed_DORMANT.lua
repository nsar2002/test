-- Homelander P1 Free-Aim Local Offset Probe v0.5
-- READ-ONLY / STAGED. Requires a successful F9 hit with a real target GOH.
-- Converts HOMELANDER_FREEAIM_HIT_POS (world) to target-local coordinates by
-- sampling go_Local2World(target, 0/+X/+Y/+Z), then roundtrip-verifies it.
-- NO laser, damage, VFX, velocity, physics, or target mutation.

local PREFIX = "[HOMELANDER_P1_LOCALOFFSET_V005] "

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

local function safe_mag(v)
    local ok, m = pcall(function() return v:magnitude() end)
    if not ok or type(m) ~= "number" then return nil end
    return m
end

local function safe_dot(a, b)
    local ok, d = pcall(function() return a:dot(b) end)
    if not ok or type(d) ~= "number" then return nil end
    return d
end

local function cosine_abs(a, b, aa, bb)
    local d = safe_dot(a, b)
    if d == nil or aa <= 1e-8 or bb <= 1e-8 then return nil end
    return math.abs(d) / math.sqrt(aa * bb)
end

-- Every new F10 attempt invalidates an earlier local offset immediately.
-- Otherwise a failed later transform could let F12 reuse the previous F10 proof.
local function clear_f10_results()
    HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET = nil
    HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH = nil
    HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR = nil
end

function Homelander_FreeAimLocalOffsetProbe()
    clear_f10_results()
    log("BEGIN — READ ONLY")
    local original_player = HOMELANDER_PLAYER

    local target = HOMELANDER_FREEAIM_HIT
    local hit_pos = HOMELANDER_FREEAIM_HIT_POS
    if not valid_goh(target) or hit_pos == nil then
        log("ABORT: no verified F9 hit GOH/world hitpoint; run F4 then F9 on an object")
        return false
    end
    if target == HOMELANDER_PLAYER then
        log("ABORT: target unexpectedly equals player")
        return false
    end
    if type(go_Local2World) ~= "function" or type(Vector) ~= "function" then
        log("ABORT: go_Local2World/Vector unavailable")
        return false
    end

    local ok0, origin = pcall(go_Local2World, target, Vector(0,0,0))
    local okX, wx = pcall(go_Local2World, target, Vector(1,0,0))
    local okY, wy = pcall(go_Local2World, target, Vector(0,1,0))
    local okZ, wz = pcall(go_Local2World, target, Vector(0,0,1))
    if not ok0 or not okX or not okY or not okZ or
       origin == nil or wx == nil or wy == nil or wz == nil then
        log("ABORT: go_Local2World basis sampling failed")
        return false
    end

    local bx = wx - origin
    local by = wy - origin
    local bz = wz - origin
    local delta = hit_pos - origin

    local xx = safe_dot(bx, bx)
    local yy = safe_dot(by, by)
    local zz = safe_dot(bz, bz)
    if xx == nil or yy == nil or zz == nil or xx <= 1e-8 or yy <= 1e-8 or zz <= 1e-8 then
        log("ABORT: degenerate target transform basis")
        return false
    end

    local cxy = cosine_abs(bx, by, xx, yy)
    local cxz = cosine_abs(bx, bz, xx, zz)
    local cyz = cosine_abs(by, bz, yy, zz)
    if cxy == nil or cxz == nil or cyz == nil then
        log("ABORT: basis orthogonality measurement failed")
        return false
    end

    local max_cross = math.max(cxy, math.max(cxz, cyz))
    if max_cross > 0.02 then
        log("ABORT: target basis not sufficiently orthogonal | maxAbsCos=" .. tostring(max_cross))
        return false
    end

    local dx = safe_dot(delta, bx)
    local dy = safe_dot(delta, by)
    local dz = safe_dot(delta, bz)
    if dx == nil or dy == nil or dz == nil then
        log("ABORT: world->local projection failed")
        return false
    end

    local local_offset = Vector(dx / xx, dy / yy, dz / zz)
    local okRoundtrip, reconstructed = pcall(go_Local2World, target, local_offset)
    if not okRoundtrip or reconstructed == nil then
        log("ABORT: local->world roundtrip failed")
        return false
    end

    local error_vec = reconstructed - hit_pos
    local error_mag = safe_mag(error_vec)
    local delta_mag = safe_mag(delta)
    if error_mag == nil or delta_mag == nil then
        log("ABORT: roundtrip error measurement failed")
        return false
    end

    local tolerance = math.max(0.02, delta_mag * 0.002)
    log("BASIS | lenX=" .. tostring(math.sqrt(xx)) ..
        " lenY=" .. tostring(math.sqrt(yy)) ..
        " lenZ=" .. tostring(math.sqrt(zz)) ..
        " cosXY=" .. tostring(cxy) ..
        " cosXZ=" .. tostring(cxz) ..
        " cosYZ=" .. tostring(cyz))
    log("ROUNDTRIP | localOffset=" .. tostring(local_offset) ..
        " reconstructed=" .. tostring(reconstructed) ..
        " hitPos=" .. tostring(hit_pos) ..
        " error=" .. tostring(error_mag) ..
        " tolerance=" .. tostring(tolerance))

    if error_mag > tolerance then
        log("ABORT: roundtrip error exceeds tolerance")
        return false
    end

    -- Roundtrip, debug getters and transform callbacks must not rebind the
    -- active player or previous verified F9 target before publishing F10 proof.
    if HOMELANDER_PLAYER ~= original_player or not valid_goh(original_player) or
       HOMELANDER_PLAYER ~= original_player or
       HOMELANDER_FREEAIM_HIT ~= target or not valid_goh(target) then
        log("ABORT: player/F9 target changed during F10 callbacks")
        return false
    end
    HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET = local_offset
    HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH = target
    HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR = error_mag
    log("PASS: stored verified target-local offset for later render gate")
    log("END — READ ONLY")
    return true
end

log("LOADED — v005 read-only world->target-local roundtrip probe; explicit F10 dispatch only")
