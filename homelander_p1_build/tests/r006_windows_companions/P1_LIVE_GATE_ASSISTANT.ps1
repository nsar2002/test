param(
    [ValidateSet('Status','Launch','Monitor','Observe','Snapshot','EvaluateLog','SelfTest')]
    [string]$Action = 'Status',
    [string]$Stage = '',
    [string]$PrototypeRoot = '',
    [string]$LogPath = '',
    [int]$PollMilliseconds = 250,
    [int]$MaxMinutes = 20
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ManifestPath = Join-Path $PSScriptRoot 'promotion_manifest.json'
if (!(Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "Missing manifest: $ManifestPath" }
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Stages = @($Manifest.stages)
$StageNames = @($Stages | ForEach-Object { [string]$_.stage })

function UtcNow { return [DateTime]::UtcNow.ToString('o') }
function SafeStamp { return [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') }
function Get-Sha256([string]$Path) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $Path" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Get-Stage([string]$Name) {
    $item = @($Stages | Where-Object { $_.stage -eq $Name } | Select-Object -First 1)
    if ($item.Count -ne 1) { throw "Unknown stage: $Name" }
    return $item[0]
}
function Resolve-PrototypeRoot([string]$ExplicitRoot) {
    if ($ExplicitRoot) {
        $full = [System.IO.Path]::GetFullPath($ExplicitRoot)
        if (!(Test-Path -LiteralPath (Join-Path $full 'prototypef.exe') -PathType Leaf)) {
            throw "PrototypeRoot does not contain prototypef.exe: $full"
        }
        return $full
    }
    $cursor = [System.IO.Path]::GetFullPath($PSScriptRoot)
    for ($i=0; $i -lt 8; $i++) {
        if (Test-Path -LiteralPath (Join-Path $cursor 'prototypef.exe') -PathType Leaf) { return $cursor }
        $parent = Split-Path -Parent $cursor
        if (!$parent -or $parent -eq $cursor) { break }
        $sibling = Join-Path $parent 'Prototype'
        if (Test-Path -LiteralPath (Join-Path $sibling 'prototypef.exe') -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($sibling)
        }
        $cursor = $parent
    }
    throw 'Could not locate Prototype root automatically. Re-run with -PrototypeRoot <path>.'
}
function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    $actual = Get-Sha256 $Path
    if ($actual -ne $Expected.ToLowerInvariant()) {
        throw "$Label hash mismatch. Expected=$Expected Actual=$actual File=$Path"
    }
}
function Assert-LoaderChain([string]$Root) {
    Assert-Hash (Join-Path $Root 'binkw32.dll') ([string]$Manifest.baseline.loaderSha256) 'Ultimate ASI Loader'
    Assert-Hash (Join-Path $Root 'binkw32Hooked.dll') ([string]$Manifest.baseline.originalBinkSha256) 'preserved original binkw32'
}
function Get-ActiveStage([string]$Root) {
    $asi = Join-Path $Root 'homelander_p1.asi'
    if (!(Test-Path -LiteralPath $asi -PathType Leaf)) { return 'none' }
    $h = Get-Sha256 $asi
    if ($h -eq ([string]$Manifest.baseline.asiSha256).ToLowerInvariant()) { return 'v001' }
    foreach ($s in $Stages) {
        if ($h -eq ([string]$s.asiSha256).ToLowerInvariant()) { return [string]$s.stage }
    }
    return 'unknown:' + $h
}
function Get-StateDir([string]$Root) { return Join-Path $Root '.homelander_promotion' }
function Get-StatePath([string]$Root) { return Join-Path (Get-StateDir $Root) 'state.json' }
function Read-State([string]$Root) {
    $path = Get-StatePath $Root
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
}
function Get-ObserverDir([string]$Root) { return Join-Path (Get-StateDir $Root) 'live_observer' }
function Get-SessionPath([string]$Root) { return Join-Path (Get-ObserverDir $Root) 'current_session.json' }
function Save-JsonAtomic([string]$Path, $Object) {
    $dir = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $tmp = Join-Path $dir (([Guid]::NewGuid().ToString('N')) + '.tmp')
    $Object | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Get-LogEvaluation([string]$StageName, [string]$Path) {
    $cfg = Get-Stage $StageName
    $raw = ''
    $exists = Test-Path -LiteralPath $Path -PathType Leaf
    if ($exists) { $raw = Get-Content -LiteralPath $Path -Raw }

    $forbidden = $null
    if ($raw -match [string]$Manifest.forbiddenLogRegex) {
        $forbidden = [regex]::Match($raw,[string]$Manifest.forbiddenLogRegex).Value
    }

    $checks = @()
    $allFound = $true
    foreach ($rx in @($cfg.required)) {
        $m = [regex]::Match($raw,[string]$rx)
        $found = [bool]$m.Success
        if (!$found) { $allFound = $false }
        $checks += [pscustomobject]@{
            regex = [string]$rx
            found = $found
            match = $(if($found){$m.Value}else{$null})
        }
    }

    return [pscustomobject]@{
        schema='homelander-p1-live-observer-evaluation/1.0'
        stage=$StageName
        gate=[string]$cfg.gate
        logExists=[bool]$exists
        logPath=$Path
        forbidden=$forbidden
        allRequiredFound=[bool]$allFound
        visualRequired=[bool]$cfg.visible
        checks=$checks
    }
}
function Write-Candidate([string]$Root, $Session, $Evaluation, [string]$Status) {
    $dir = Join-Path (Get-ObserverDir $Root) 'candidates'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $path = Join-Path $dir ((SafeStamp) + '_' + $Evaluation.stage + '_' + $Status + '.json')
    $logHash = $null
    if ($Evaluation.logExists) { $logHash = Get-Sha256 $Evaluation.logPath }
    $obj = [pscustomobject]@{
        schema='homelander-p1-live-observer-candidate/1.0'
        status=$Status
        createdUtc=(UtcNow)
        stage=$Evaluation.stage
        gate=$Evaluation.gate
        buildId=[string](Get-Stage $Evaluation.stage).buildId
        activeAsiSha256=$(if($Session){$Session.activeAsiSha256}else{$null})
        sessionStartedUtc=$(if($Session){$Session.startedUtc}else{$null})
        processId=$(if($Session){$Session.processId}else{$null})
        logPath=$Evaluation.logPath
        logSha256=$logHash
        forbidden=$Evaluation.forbidden
        allRequiredFound=[bool]$Evaluation.allRequiredFound
        visualRequired=[bool]$Evaluation.visualRequired
        visualConfirmed=$false
        checks=$Evaluation.checks
        authoritative=$false
        note='Observer candidate only. This file never authorizes promotion. P1_PROMOTION_MANAGER.ps1 -Action Check is the only gate recorder.'
    }
    Save-JsonAtomic $path $obj
    return $path
}
function Assert-ManagedStageReady([string]$Root, [string]$ActiveStage, $State) {
    if ($StageNames -notcontains $ActiveStage) {
        throw "Live observer requires a managed installed stage v003-v016. Active stage: $ActiveStage"
    }
    if ($null -eq $State) {
        throw 'Promotion state.json is missing. Install the stage with P1_PROMOTION_MANAGER.ps1 first.'
    }
    if ([string]$State.currentStage -ne $ActiveStage) {
        throw "Promotion state mismatch: state=$($State.currentStage), active=$ActiveStage"
    }
    $cfg = Get-Stage $ActiveStage
    Assert-Hash (Join-Path $Root 'homelander_p1.asi') ([string]$cfg.asiSha256) "active ASI $ActiveStage"
    Assert-LoaderChain $Root
    return $cfg
}
function Show-Evaluation($Evaluation) {
    Write-Host ''
    Write-Host ("Stage {0} / {1}" -f $Evaluation.stage,$Evaluation.gate)
    if ($Evaluation.forbidden) {
        Write-Host ("BLOCKED: forbidden/fatal evidence: " + $Evaluation.forbidden) -ForegroundColor Red
    }
    $i=0
    foreach ($c in @($Evaluation.checks)) {
        $i++
        if ([bool]$c.found) {
            Write-Host ("  [{0}/{1}] FOUND  {2}" -f $i,$Evaluation.checks.Count,$c.match) -ForegroundColor Green
        } else {
            Write-Host ("  [{0}/{1}] WAIT   {2}" -f $i,$Evaluation.checks.Count,$c.regex) -ForegroundColor Yellow
        }
    }
    if ($Evaluation.allRequiredFound -and !$Evaluation.forbidden) {
        Write-Host 'LOG EVIDENCE COMPLETE.' -ForegroundColor Green
        if ($Evaluation.visualRequired) {
            Write-Host 'VISUAL CONFIRMATION IS STILL REQUIRED. Observer cannot confirm visuals.' -ForegroundColor Yellow
        }
        Write-Host ("Close Prototype, then explicitly run the promotion manager Check for {0}." -f $Evaluation.stage)
    }
}
function Run-SelfTest {
    if ($Manifest.schema -ne 'homelander-p1-runtime-promotion/1.0') { throw 'Unexpected manifest schema.' }
    $expected=@('v003','v004','v005','v006','v007','v009','v010','v011','v012','v013','v014','v015','v016')
    if ($Stages.Count -ne $expected.Count) { throw "Expected $($expected.Count) stages; got $($Stages.Count)" }
    for ($i=0; $i -lt $expected.Count; $i++) {
        if ([string]$Stages[$i].stage -ne $expected[$i]) { throw ("Stage order mismatch at " + $i) }
        foreach ($rx in @($Stages[$i].required)) { [void][regex]::new([string]$rx) }
    }
    [void][regex]::new([string]$Manifest.forbiddenLogRegex)
    if ($StageNames -contains 'v008') { throw 'v008 must remain excluded.' }
    Write-Host 'SELFTEST PASS: manifest order and evidence regexes are valid.'
}

if ($Action -eq 'SelfTest') { Run-SelfTest; exit 0 }

if ($Action -eq 'EvaluateLog') {
    if (!$Stage) { throw '-Stage is required for EvaluateLog.' }
    if (!$LogPath) { throw '-LogPath is required for EvaluateLog.' }
    $e = Get-LogEvaluation $Stage ([System.IO.Path]::GetFullPath($LogPath))
    Show-Evaluation $e
    if ($e.forbidden) { exit 5 }
    if ($e.allRequiredFound) { exit 0 }
    exit 4
}

$Root = Resolve-PrototypeRoot $PrototypeRoot
$ActiveStage = Get-ActiveStage $Root
$State = Read-State $Root

if ($Action -eq 'Status') {
    Write-Host "Prototype root: $Root"
    Write-Host "Active stage: $ActiveStage"
    Write-Host ("Promotion state: " + $(if($State){[string]$State.currentStage}else{'<missing>'}))
    if ($StageNames -contains $ActiveStage) {
        $cfg = Assert-ManagedStageReady $Root $ActiveStage $State
        Write-Host ("Gate: {0}" -f $cfg.gate)
        Write-Host ("Keys: {0}" -f $cfg.keys)
        Write-Host ("Visual confirmation required: {0}" -f [bool]$cfg.visible)
        $log = Join-Path $Root 'homelander_p1_runtime.log'
        if (Test-Path -LiteralPath $log -PathType Leaf) {
            Show-Evaluation (Get-LogEvaluation $ActiveStage $log)
        } else {
            Write-Host 'Runtime log: <not created yet>'
        }
    }
    exit 0
}

$cfg = Assert-ManagedStageReady $Root $ActiveStage $State
if ($Stage -and $Stage -ne $ActiveStage) { throw "Requested stage $Stage but active stage is $ActiveStage." }
$Stage = $ActiveStage
$runtimeLog = Join-Path $Root 'homelander_p1_runtime.log'

if ($Action -eq 'Snapshot') {
    $e = Get-LogEvaluation $Stage $runtimeLog
    Show-Evaluation $e
    $session = $null
    $sp = Get-SessionPath $Root
    if (Test-Path -LiteralPath $sp -PathType Leaf) { $session = Get-Content -LiteralPath $sp -Raw | ConvertFrom-Json }
    $status = $(if($e.forbidden){'BLOCKED'}elseif($e.allRequiredFound){'LOG_COMPLETE'}else{'INCOMPLETE'})
    $p = Write-Candidate $Root $session $e $status
    Write-Host "Observer candidate: $p"
    if ($e.forbidden) { exit 5 }
    if ($e.allRequiredFound) { exit 0 }
    exit 4
}

if ($Action -eq 'Launch' -or $Action -eq 'Observe') {
    if (Get-Process -Name 'prototypef' -ErrorAction SilentlyContinue) {
        throw 'Prototype is already running. Use -Action Monitor instead.'
    }

    if (Test-Path -LiteralPath $runtimeLog -PathType Leaf) {
        $len=(Get-Item -LiteralPath $runtimeLog).Length
        if ($len -gt 0) {
            throw "A non-empty runtime log already exists. Use P1_PROMOTION_MANAGER.ps1 -Action ResetLog before a fresh attempt. Refusing stale-evidence risk."
        }
    }

    $exe = Join-Path $Root 'prototypef.exe'
    $session = [pscustomobject]@{
        schema='homelander-p1-live-observer-session/1.0'
        stage=$Stage
        gate=[string]$cfg.gate
        buildId=[string]$cfg.buildId
        startedUtc=(UtcNow)
        activeAsiSha256=(Get-Sha256 (Join-Path $Root 'homelander_p1.asi'))
        processId=$null
        authoritative=$false
    }

    $proc = Start-Process -FilePath $exe -WorkingDirectory $Root -PassThru
    $session.processId=$proc.Id
    Save-JsonAtomic (Get-SessionPath $Root) $session

    Write-Host ("Prototype launched. PID={0}" -f $proc.Id)
    Write-Host ("Stage {0} / {1}" -f $Stage,$cfg.gate)
    Write-Host ("Execute: {0}" -f $cfg.keys)
    if ([bool]$cfg.visible) { Write-Host ("Visual requirement: {0}" -f $cfg.visiblePrompt) -ForegroundColor Yellow }
    if ($Action -eq 'Launch') { exit 0 }
}

if ($Action -eq 'Monitor' -or $Action -eq 'Observe') {
    $sp = Get-SessionPath $Root
    if (!(Test-Path -LiteralPath $sp -PathType Leaf)) {
        throw 'No live observer session. Use -Action Observe or -Action Launch first.'
    }
    $session = Get-Content -LiteralPath $sp -Raw | ConvertFrom-Json
    if ([string]$session.stage -ne $Stage) {
        throw "Observer session stage $($session.stage) != active stage $Stage."
    }
    if ([string]$session.activeAsiSha256 -ne (Get-Sha256 (Join-Path $Root 'homelander_p1.asi'))) {
        throw 'Active ASI changed after observer session started.'
    }

    $seen=@{}
    $deadline=[DateTime]::UtcNow.AddMinutes([Math]::Max(1,$MaxMinutes))
    Write-Host ("Monitoring {0} every {1} ms. Observer never writes PASS receipts." -f $runtimeLog,$PollMilliseconds)

    while ([DateTime]::UtcNow -lt $deadline) {
        $e = Get-LogEvaluation $Stage $runtimeLog

        if ($e.forbidden) {
            Show-Evaluation $e
            $p=Write-Candidate $Root $session $e 'BLOCKED'
            Write-Host "BLOCKED candidate written: $p"
            exit 5
        }

        $idx=0
        foreach($c in @($e.checks)) {
            $idx++
            if ([bool]$c.found -and !$seen.ContainsKey($idx)) {
                $seen[$idx]=$true
                Write-Host ("[{0}/{1}] FOUND: {2}" -f $idx,$e.checks.Count,$c.match) -ForegroundColor Green
            }
        }

        if ($e.allRequiredFound) {
            Show-Evaluation $e
            $p=Write-Candidate $Root $session $e 'LOG_COMPLETE'
            Write-Host "LOG-COMPLETE observer candidate: $p"
            Write-Host 'No authoritative PASS was recorded.'
            exit 0
        }

        $proc=Get-Process -Id ([int]$session.processId) -ErrorAction SilentlyContinue
        if (!$proc) {
            Show-Evaluation $e
            $p=Write-Candidate $Root $session $e 'PROCESS_EXITED_INCOMPLETE'
            Write-Host "Prototype exited before complete evidence. Candidate: $p"
            exit 4
        }

        Start-Sleep -Milliseconds ([Math]::Max(100,$PollMilliseconds))
    }

    $e = Get-LogEvaluation $Stage $runtimeLog
    Show-Evaluation $e
    $p=Write-Candidate $Root $session $e 'TIMEOUT'
    Write-Host "Observer timeout. Candidate: $p"
    exit 4
}

throw "Unhandled action: $Action"
