-- Homelander P1 Free-Aim Ray Probe v0.1 (v003)
-- READ-ONLY. No damage, effect spawning, physics mutation, or target mutation.
-- Requires optional v003 native bridges HL_GetCameraRay / HL_LastRayHitIndex.

local PREFIX = "[HOMELANDER_P1_FREEAIM_V003] "

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

local function parse_camera_ray(raw)
    if type(raw) ~= "string" or raw == "" then return nil end
    local values = {}
    for token in string.gmatch(raw, "[^,]+") do
        local n = tonumber(token)
        if n == nil then return nil end
        values[#values + 1] = n
    end
    if #values ~= 6 then return nil end
    return values
end

function Homelander_FreeAimProbe()
    log("BEGIN — READ ONLY")

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        log("ABORT: HOMELANDER_PLAYER missing/invalid; run F4 first")
        return false
    end

    if type(HL_GetCameraRay) ~= "function" or type(HL_LastRayHitIndex) ~= "function" then
        log("ABORT: v003 native free-aim bridges unavailable")
        return false
    end
    if type(fre_LineOfSightTest) ~= "function" then
        log("ABORT: fre_LineOfSightTest unavailable")
        return false
    end
    if type(Vector) ~= "function" then
        log("ABORT: Vector unavailable")
        return false
    end

    -- This existing read-only engine getter triggers the optional camera-manager capture hook.
    if type(cm_GetCurrentRenderCameraPosition) == "function" then
        pcall(cm_GetCurrentRenderCameraPosition)
    end

    local okRay, raw = pcall(HL_GetCameraRay)
    if not okRay then
        log("ABORT: HL_GetCameraRay error | " .. tostring(raw))
        return false
    end
    local ray = parse_camera_ray(raw)
    if ray == nil then
        log("ABORT: camera ray not captured/invalid | " .. tostring(raw))
        return false
    end

    local start = Vector(ray[1], ray[2], ray[3])
    local forward = Vector(ray[4], ray[5], ray[6])
    local fmag = forward:normalize()
    if type(fmag) ~= "number" or fmag <= 0.0001 then
        log("ABORT: degenerate camera forward")
        return false
    end

    local range = tonumber(HOMELANDER_FREEAIM_RANGE) or 500.0
    if range < 10.0 then range = 10.0 end
    if range > 1000.0 then range = 1000.0 end
    local rayEnd = start + forward * range

    local ok, hit, fraction, hitPos, hitNormal =
        pcall(fre_LineOfSightTest, start, rayEnd, true, player)
    if not ok then
        log("ABORT: fre_LineOfSightTest error | " .. tostring(hit))
        return false
    end

    HOMELANDER_FREEAIM_CAMERA_START = start
    HOMELANDER_FREEAIM_CAMERA_FORWARD = forward
    HOMELANDER_FREEAIM_RAY_END = rayEnd
    HOMELANDER_FREEAIM_HIT = nil
    HOMELANDER_FREEAIM_HIT_POS = nil
    HOMELANDER_FREEAIM_HIT_NORMAL = nil
    HOMELANDER_FREEAIM_FRACTION = nil

    if not hit then
        log("MISS | range=" .. tostring(range) .. " start=" .. tostring(start) ..
            " forward=" .. tostring(forward))
        return true
    end

    HOMELANDER_FREEAIM_HIT_POS = hitPos
    HOMELANDER_FREEAIM_HIT_NORMAL = hitNormal
    HOMELANDER_FREEAIM_FRACTION = fraction

    local playerIndex = nil
    if type(PlutoConvertGOHToIndex) == "function" then
        local okIndex, idx = pcall(PlutoConvertGOHToIndex, player)
        if okIndex then playerIndex = idx end
    end

    local hitIndexText = ""
    if playerIndex ~= nil then
        local okIndexText, text = pcall(HL_LastRayHitIndex, tostring(playerIndex))
        if okIndexText and type(text) == "string" then hitIndexText = text end
    end

    if hitIndexText ~= "" and type(PlutoConvertIndexToGOH) == "function" then
        local hitIndex = tonumber(hitIndexText)
        if hitIndex ~= nil then
            local okHit, hitGOH = pcall(PlutoConvertIndexToGOH, hitIndex)
            if okHit and valid_goh(hitGOH) and hitGOH ~= player then
                HOMELANDER_FREEAIM_HIT = hitGOH
            end
        end
    end

    log("HIT | fraction=" .. tostring(fraction) ..
        " pos=" .. tostring(hitPos) ..
        " normal=" .. tostring(hitNormal) ..
        " hitIndex=" .. tostring(hitIndexText) ..
        " hitGOH=" .. tostring(HOMELANDER_FREEAIM_HIT))
    log("END — READ ONLY")
    return true
end

log("LOADED — v003 read-only free-aim probe; F9 invokes it")
