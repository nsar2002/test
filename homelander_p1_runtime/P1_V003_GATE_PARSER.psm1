Set-StrictMode -Version Latest

function ConvertTo-FiniteDouble {
    param([Parameter(Mandatory=$true)][string]$Text)
    $value = 0.0
    $style = [System.Globalization.NumberStyles]::Float
    $culture = [System.Globalization.CultureInfo]::InvariantCulture
    if (![double]::TryParse($Text, $style, $culture, [ref]$value)) { return $null }
    if ([double]::IsNaN($value) -or [double]::IsInfinity($value)) { return $null }
    return $value
}

function Test-V003GateLog {
    param([Parameter(Mandatory=$true)][string]$LogText)

    $checks = [ordered]@{}
    $checks.ready = $LogText.Contains("READY build=P1_RuntimeProbe_003_FREEAIM_STAGED_20260918")
    $checks.f4_dispatch = $LogText.Contains("F4: read-only discovery + flight math probe")
    $checks.player_verified = $LogText.Contains("[HOMELANDER_P1_PROBE_V3] HOMELANDER_PLAYER SET TO VERIFIED HANDLE")
    $checks.discovery_end = $LogText.Contains("[HOMELANDER_P1_PROBE_V3] END — NO GAMEPLAY STATE WAS INTENTIONALLY MODIFIED")
    $checks.math_end = $LogText.Contains("[HOMELANDER_P1_FLIGHT_MATH_V2_2] END — READ ONLY")
    $checks.f9_dispatch = $LogText.Contains("F9: read-only free-aim camera/LOS probe")
    $checks.freeaim_begin = $LogText.Contains("[HOMELANDER_P1_FREEAIM_V004] BEGIN — READ ONLY")
    $checks.freeaim_end = $LogText.Contains("[HOMELANDER_P1_FREEAIM_V004] END — READ ONLY")

    $cameraMatches = [regex]::Matches(
        $LogText,
        '\[HOMELANDER_P1_FREEAIM_V004\] CAMERA \| axis=(\d+) scores=([^\r\n]+?) margin=([-+0-9.eE]+) cameraPlayerDistance=([-+0-9.eE]+)'
    )
    $axis = $null
    $margin = $null
    $cameraDistance = $null
    if ($cameraMatches.Count -gt 0) {
        $m = $cameraMatches[$cameraMatches.Count - 1]
        $axisCandidate = 0
        if ([int]::TryParse($m.Groups[1].Value, [ref]$axisCandidate)) { $axis = $axisCandidate }
        $margin = ConvertTo-FiniteDouble $m.Groups[3].Value
        $cameraDistance = ConvertTo-FiniteDouble $m.Groups[4].Value
    }
    $checks.camera_measurement = (
        $axis -ne $null -and $axis -ge 1 -and $axis -le 3 -and
        $margin -ne $null -and $margin -gt 0.0 -and
        $cameraDistance -ne $null -and $cameraDistance -gt 0.0
    )

    $hitMatches = [regex]::Matches(
        $LogText,
        '\[HOMELANDER_P1_FREEAIM_V004\] HIT \| fraction=([-+0-9.eE]+) pos=([^\r\n]+?) normal=([^\r\n]+?) hitGOH=([^\r\n]+?) hitName=([^\r\n]*)'
    )
    $hitFraction = $null
    $hitPositionText = $null
    $hitNormalText = $null
    $hitGOHText = $null
    $hitNameText = $null
    if ($hitMatches.Count -gt 0) {
        $h = $hitMatches[$hitMatches.Count - 1]
        $hitFraction = ConvertTo-FiniteDouble $h.Groups[1].Value
        $hitPositionText = $h.Groups[2].Value.Trim()
        $hitNormalText = $h.Groups[3].Value.Trim()
        $hitGOHText = $h.Groups[4].Value.Trim()
        $hitNameText = $h.Groups[5].Value.Trim()
    }
    $checks.fresh_hit = (
        $hitFraction -ne $null -and $hitFraction -ge 0.0 -and $hitFraction -le 1.0 -and
        $hitPositionText -and $hitPositionText -ne "nil" -and
        $hitNormalText -and $hitNormalText -ne "nil"
    )

    $forbiddenPatterns = @(
        'FATAL',
        'FAIL signature',
        'FAIL consistent ref',
        'Lua compile error',
        'Lua runtime error',
        '[HOMELANDER_P1_FREEAIM_V004] ABORT:',
        '[HOMELANDER_P1_PROBE_V3] NO VERIFIED PLAYER HANDLE'
    )
    $forbiddenFound = New-Object System.Collections.Generic.List[string]
    foreach ($pattern in $forbiddenPatterns) {
        if ($LogText.Contains($pattern)) { [void]$forbiddenFound.Add($pattern) }
    }

    $mutationHotkeys = New-Object System.Collections.Generic.List[string]
    foreach ($hotkey in @('F5:', 'F6:', 'F7:')) {
        if ($LogText.Contains($hotkey)) { [void]$mutationHotkeys.Add($hotkey) }
    }

    $checks.no_fatal_or_abort = ($forbiddenFound.Count -eq 0)
    $checks.no_mutation_hotkey_dispatch = ($mutationHotkeys.Count -eq 0)

    $failed = New-Object System.Collections.Generic.List[string]
    foreach ($key in $checks.Keys) {
        if (!$checks[$key]) { [void]$failed.Add($key) }
    }

    [pscustomobject]@{
        pass = ($failed.Count -eq 0)
        checks = [pscustomobject]$checks
        failed_checks = @($failed)
        forbidden_log_markers = @($forbiddenFound)
        mutation_hotkeys_seen = @($mutationHotkeys)
        camera_axis = $axis
        camera_margin = $margin
        camera_player_distance = $cameraDistance
        hit_fraction = $hitFraction
        hit_position_text = $hitPositionText
        hit_normal_text = $hitNormalText
        hit_goh_text = $hitGOHText
        hit_name_text = $hitNameText
    }
}

Export-ModuleMember -Function Test-V003GateLog
