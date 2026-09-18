-- Homelander P1 Free-Aim Ray Probe v0.4 (v003 staged runtime)
-- READ-ONLY. No damage, effect spawning, physics mutation, or target mutation.
-- Requires native bridges HL_GetCameraFrame / HL_LastRayHitGOH.
-- fre_LineOfSightTest ABI was statically reconstructed from this exact P1 build.

local PREFIX = "[HOMELANDER_P1_FREEAIM_V004] "

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

local function parse_frame(raw)
    if type(raw) ~= "string" or raw == "" then return nil end
    local values = {}
    for token in string.gmatch(raw, "[^,]+") do
        local n = tonumber(token)
        if n == nil then return nil end
        values[#values + 1] = n
    end
    if #values ~= 12 then return nil end
    return values
end

local function normalized(v)
    local c = Vector(v)
    local mag = c:normalize()
    if type(mag) ~= "number" or mag <= 0.0001 then return nil, mag end
    return c, mag
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
    local score_text = {}

    for i = 1, 3 do
        local axis, mag = normalized(axes[i])
        if axis == nil then
            return nil, nil, nil, "camera basis axis " .. tostring(i) ..
                " degenerate | magnitude=" .. tostring(mag)
        end

        local d = axis:dot(to_player)
        if type(d) ~= "number" then
            return nil, nil, nil, "camera basis dot failed for axis " .. tostring(i)
        end

        local score = math.abs(d)
        score_text[#score_text + 1] = tostring(i) .. ":" .. tostring(score)

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

    if best_axis == nil then
        return nil, nil, nil, "no camera basis axis selected"
    end

    -- Do not guess a fixed matrix row/sign. Choose the basis axis whose
    -- measured direction is most aligned with camera->player; flip only if
    -- the measured dot product is negative.
    if signed_dot < 0.0 then
        best_axis = best_axis * -1.0
    end

    return camera_pos, best_axis, {
        axis_index = best_index,
        best_score = best_score,
        second_score = second_score,
        margin = best_score - second_score,
        scores = table.concat(score_text, ","),
        camera_player_distance = to_player_mag
    }, nil
end

function Homelander_FreeAimProbe()
    log("BEGIN — READ ONLY")

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        log("ABORT: HOMELANDER_PLAYER missing/invalid; run F4 first")
        return false
    end

    if type(HL_GetCameraFrame) ~= "function" or type(HL_LastRayHitGOH) ~= "function" then
        log("ABORT: v003 native free-aim bridges unavailable")
        return false
    end
    if type(fre_LineOfSightTest) ~= "function" then
        log("ABORT: fre_LineOfSightTest unavailable")
        return false
    end
    if type(Vector) ~= "function" or type(go_GetPosition) ~= "function" then
        log("ABORT: Vector/go_GetPosition unavailable")
        return false
    end

    -- This engine getter passes through the native capture hook and refreshes
    -- the current render-camera object pointer without mutating gameplay state.
    if type(cm_GetCurrentRenderCameraPosition) ~= "function" then
        log("ABORT: cm_GetCurrentRenderCameraPosition unavailable")
        return false
    end
    local okCamGetter, camPosition = pcall(cm_GetCurrentRenderCameraPosition)
    if not okCamGetter or camPosition == nil then
        log("ABORT: render-camera position getter failed | " .. tostring(camPosition))
        return false
    end

    local okFrame, raw = pcall(HL_GetCameraFrame)
    if not okFrame then
        log("ABORT: HL_GetCameraFrame error | " .. tostring(raw))
        return false
    end
    local frame = parse_frame(raw)
    if frame == nil then
        log("ABORT: camera frame not captured/invalid | " .. tostring(raw))
        return false
    end

    local okPlayerPos, playerPos = pcall(go_GetPosition, player)
    if not okPlayerPos or playerPos == nil then
        log("ABORT: player position unavailable | " .. tostring(playerPos))
        return false
    end

    local start, forward, axisInfo, axisErr = select_view_axis(frame, playerPos)
    if start == nil or forward == nil then
        log("ABORT: camera forward resolution failed | " .. tostring(axisErr))
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

    log("CAMERA | axis=" .. tostring(axisInfo.axis_index) ..
        " scores=" .. tostring(axisInfo.scores) ..
        " margin=" .. tostring(axisInfo.margin) ..
        " cameraPlayerDistance=" .. tostring(axisInfo.camera_player_distance))

    if not hit then
        log("MISS | range=" .. tostring(range) ..
            " start=" .. tostring(start) ..
            " forward=" .. tostring(forward))
        log("END — READ ONLY")
        return true
    end

    HOMELANDER_FREEAIM_HIT_POS = hitPos
    HOMELANDER_FREEAIM_HIT_NORMAL = hitNormal
    HOMELANDER_FREEAIM_FRACTION = fraction

    local okHitGOH, hitGOH = pcall(HL_LastRayHitGOH)
    if okHitGOH and valid_goh(hitGOH) and hitGOH ~= player then
        HOMELANDER_FREEAIM_HIT = hitGOH
    end

    local hitName = nil
    if HOMELANDER_FREEAIM_HIT ~= nil and type(go_GetDebugName) == "function" then
        local okName, name = pcall(go_GetDebugName, HOMELANDER_FREEAIM_HIT)
        if okName then hitName = name end
    end

    log("HIT | fraction=" .. tostring(fraction) ..
        " pos=" .. tostring(hitPos) ..
        " normal=" .. tostring(hitNormal) ..
        " hitGOH=" .. tostring(HOMELANDER_FREEAIM_HIT) ..
        " hitName=" .. tostring(hitName))
    log("END — READ ONLY")
    return true
end

log("LOADED — v004 read-only free-aim probe; F9 invokes it")
