param(
    [ValidateSet('Status','Next','Install','Check','Rollback','ResetLog','ValidatePack','SelfTest')]
    [string]$Action = 'Status',
    [string]$Stage = '',
    [string]$PrototypeRoot = '',
    [switch]$ConfirmVisible,
    [switch]$SkipPackagePresence,
    [int]$TailLines = 220
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
function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    $actual = Get-Sha256 $Path
    if ($actual -ne $Expected.ToLowerInvariant()) {
        throw "$Label hash mismatch.`nExpected: $Expected`nActual:   $actual`nFile: $Path"
    }
}
function Get-Stage([string]$Name) {
    $item = @($Stages | Where-Object { $_.stage -eq $Name } | Select-Object -First 1)
    if ($item.Count -ne 1) { throw "Unknown stage: $Name" }
    return $item[0]
}
function Get-StageIndex([string]$Name) {
    for ($i=0; $i -lt $Stages.Count; $i++) { if ($Stages[$i].stage -eq $Name) { return $i } }
    if ($Name -eq 'v001') { return -1 }
    return -999
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
function Assert-GameClosed {
    if (Get-Process -Name 'prototypef' -ErrorAction SilentlyContinue) {
        throw 'Prototype is running. Close the game before installing, rolling back, or resetting the runtime log.'
    }
}
function Assert-LoaderChain([string]$Root) {
    Assert-Hash (Join-Path $Root 'binkw32.dll') ([string]$Manifest.baseline.loaderSha256) 'active Ultimate ASI Loader'
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
function New-State([string]$ActiveStage) {
    return [pscustomobject]@{
        schema = 'homelander-p1-runtime-promotion-state/1.0'
        currentStage = $ActiveStage
        passedStages = @()
        installHistory = @()
        lastUpdatedUtc = (UtcNow)
    }
}
function Read-State([string]$Root, [string]$ActiveStage) {
    $path = Get-StatePath $Root
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $s = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
        if ($null -eq $s.passedStages) { $s | Add-Member -NotePropertyName passedStages -NotePropertyValue @() -Force }
        if ($null -eq $s.installHistory) { $s | Add-Member -NotePropertyName installHistory -NotePropertyValue @() -Force }
        return $s
    }
    return New-State $ActiveStage
}
function Save-State([string]$Root, $State) {
    $dir = Get-StateDir $Root
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $State.lastUpdatedUtc = UtcNow
    $tmp = Join-Path $dir ('state.' + [Guid]::NewGuid().ToString('N') + '.tmp')
    $State | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination (Get-StatePath $Root) -Force
}
function Assert-StateMatches([string]$Root, $State, [string]$ActiveStage) {
    if ([string]$State.currentStage -ne $ActiveStage) {
        throw "Promotion state mismatch. state.json says $($State.currentStage), active ASI says $ActiveStage. Refusing mutation."
    }
}
function Archive-Log([string]$Root, [string]$Reason) {
    $log = Join-Path $Root 'homelander_p1_runtime.log'
    if (!(Test-Path -LiteralPath $log -PathType Leaf)) { return $null }
    $dir = Join-Path (Get-StateDir $Root) 'log_archive'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $dst = Join-Path $dir ((SafeStamp) + '_' + $Reason + '_homelander_p1_runtime.log')
    Move-Item -LiteralPath $log -Destination $dst -Force
    return $dst
}
function Remove-PassesAtOrAfter($State, [string]$StageName) {
    $cut = Get-StageIndex $StageName
    $keep = @()
    foreach ($p in @($State.passedStages)) {
        $pi = Get-StageIndex ([string]$p)
        if ($pi -lt $cut) { $keep += [string]$p }
    }
    $State.passedStages = $keep
}
function Add-Pass($State, [string]$StageName) {
    $p = @($State.passedStages | ForEach-Object { [string]$_ })
    if ($p -notcontains $StageName) { $p += $StageName }
    $State.passedStages = $p
}
function Backup-Current([string]$Root, [string]$FromStage, [string]$ToStage) {
    $dir = Join-Path (Get-StateDir $Root) ('backups\' + (SafeStamp) + '_' + $FromStage + '_to_' + $ToStage)
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $activeAsi = Join-Path $Root 'homelander_p1.asi'
    Copy-Item -LiteralPath $activeAsi -Destination (Join-Path $dir 'homelander_p1.asi')
    $rootLua = Join-Path $Root 'lua_p1'
    $hadLua = Test-Path -LiteralPath $rootLua -PathType Container
    if ($hadLua) { Copy-Item -LiteralPath $rootLua -Destination (Join-Path $dir 'lua_p1') -Recurse }
    $meta = [pscustomobject]@{
        fromStage=$FromStage; toStage=$ToStage; createdUtc=(UtcNow); hadLua=[bool]$hadLua;
        asiSha256=(Get-Sha256 (Join-Path $dir 'homelander_p1.asi'))
    }
    $meta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $dir 'backup_meta.json') -Encoding UTF8
    return $dir
}
function Restore-Backup([string]$Root, [string]$BackupDir) {
    $metaPath = Join-Path $BackupDir 'backup_meta.json'
    if (!(Test-Path -LiteralPath $metaPath -PathType Leaf)) { throw "Backup metadata missing: $metaPath" }
    $meta = Get-Content -LiteralPath $metaPath -Raw | ConvertFrom-Json
    $backupAsi = Join-Path $BackupDir 'homelander_p1.asi'
    Assert-Hash $backupAsi ([string]$meta.asiSha256) 'backup ASI'
    Copy-Item -LiteralPath $backupAsi -Destination (Join-Path $Root 'homelander_p1.asi') -Force
    $rootLua = Join-Path $Root 'lua_p1'
    if (Test-Path -LiteralPath $rootLua) { Remove-Item -LiteralPath $rootLua -Recurse -Force }
    if ([bool]$meta.hadLua) {
        $backupLua = Join-Path $BackupDir 'lua_p1'
        if (!(Test-Path -LiteralPath $backupLua -PathType Container)) { throw "Backup says lua_p1 existed but snapshot is missing: $backupLua" }
        Copy-Item -LiteralPath $backupLua -Destination $rootLua -Recurse
    }
}
function Normalize-RelPath([string]$p) { return $p.Replace('/', [System.IO.Path]::DirectorySeparatorChar) }
function Validate-StagePackage($Cfg, [switch]$ExtractCheck) {
    $zip = Join-Path $PSScriptRoot (Normalize-RelPath ([string]$Cfg.package))
    Assert-Hash $zip ([string]$Cfg.packageSha256) ("package " + $Cfg.stage)
    if ($ExtractCheck) {
        $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('homelander_packcheck_' + [Guid]::NewGuid().ToString('N'))
        try {
            Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
            $asi = Join-Path $tmp (Normalize-RelPath ([string]$Cfg.asiPath))
            Assert-Hash $asi ([string]$Cfg.asiSha256) ("extracted ASI " + $Cfg.stage)
            $lua = Join-Path $tmp (Normalize-RelPath ([string]$Cfg.luaRoot))
            if (!(Test-Path -LiteralPath $lua -PathType Container)) { throw "Missing lua root in $($Cfg.stage): $($Cfg.luaRoot)" }
        } finally {
            if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
        }
    }
}
function Run-SelfTest([switch]$SkipPackages) {
    if ($Manifest.schema -ne 'homelander-p1-runtime-promotion/1.0') { throw 'Unexpected manifest schema.' }
    if ($Stages.Count -ne 13) { throw "Expected 13 promotion stages; found $($Stages.Count)." }
    $expectedPred = 'v001'
    $seen = @{}
    foreach ($s in $Stages) {
        if ([string]$s.predecessor -ne $expectedPred) { throw "Broken chain at $($s.stage): expected predecessor $expectedPred, got $($s.predecessor)" }
        if ($seen.ContainsKey([string]$s.stage)) { throw "Duplicate stage $($s.stage)" }
        $seen[[string]$s.stage] = $true
        foreach ($rx in @($s.required)) { [void][regex]::new([string]$rx) }
        if (!$SkipPackages) { Validate-StagePackage $s }
        $expectedPred = [string]$s.stage
    }
    [void][regex]::new([string]$Manifest.forbiddenLogRegex)
    Write-Host "SELFTEST PASS: manifest chain, stage count, unique stages and regexes are valid."
    if (!$SkipPackages) { Write-Host 'SELFTEST PASS: all canonical package ZIP hashes are present and correct.' }
}
function Show-StageInstructions($Cfg) {
    Write-Host ''
    Write-Host ("Stage {0} - {1}" -f $Cfg.stage,$Cfg.display)
    Write-Host ("Runtime gate: {0}" -f $Cfg.gate)
    Write-Host ("Key/evidence sequence: {0}" -f $Cfg.keys)
    if ([bool]$Cfg.visible) { Write-Host ("Visual confirmation required at Check: {0}" -f $Cfg.visiblePrompt) }
    Write-Host ("Then close Prototype and run: .\P1_PROMOTION_MANAGER.ps1 -Action Check -Stage {0}{1}" -f $Cfg.stage, $(if([bool]$Cfg.visible){' -ConfirmVisible'}else{''}))
}

if ($Action -eq 'SelfTest') { Run-SelfTest -SkipPackages:$SkipPackagePresence; exit 0 }
if ($Action -eq 'ValidatePack') {
    Run-SelfTest
    foreach ($s in $Stages) { Validate-StagePackage $s -ExtractCheck }
    Write-Host 'VALIDATE PACK PASS: all 13 canonical ZIPs and extracted ASIs match the frozen manifest.'
    exit 0
}

$Root = Resolve-PrototypeRoot $PrototypeRoot
$ActiveStage = Get-ActiveStage $Root
$State = Read-State $Root $ActiveStage

if ($Action -eq 'Status') {
    Write-Host "Prototype root: $Root"
    Write-Host "Active ASI stage: $ActiveStage"
    Write-Host "State stage: $($State.currentStage)"
    Write-Host ("Passed gates: " + (@($State.passedStages) -join ', '))
    if ([string]$State.currentStage -ne $ActiveStage) { Write-Warning 'state.json and active ASI disagree; mutation actions will fail closed.' }
    if ($ActiveStage -ne 'none' -and !$ActiveStage.StartsWith('unknown:')) {
        try { Assert-LoaderChain $Root; Write-Host 'Loader chain: PASS' } catch { Write-Warning $_.Exception.Message }
    }
    if ($StageNames -contains $ActiveStage) { Show-StageInstructions (Get-Stage $ActiveStage) }
    exit 0
}

Assert-StateMatches $Root $State $ActiveStage
Assert-LoaderChain $Root

if ($Action -eq 'Next') {
    if ($ActiveStage -eq 'v001') {
        Write-Host 'Next install: v003 (first and only permitted initial promotion).'
        Write-Host '.\P1_PROMOTION_MANAGER.ps1 -Action Install -Stage v003'
        exit 0
    }
    if ($StageNames -notcontains $ActiveStage) { throw "Cannot compute next stage from $ActiveStage" }
    $idx = Get-StageIndex $ActiveStage
    $passed = @($State.passedStages | ForEach-Object { [string]$_ })
    if ($passed -notcontains $ActiveStage) {
        Write-Host "$ActiveStage is installed but its live gate is not recorded PASS."
        Show-StageInstructions (Get-Stage $ActiveStage)
        exit 3
    }
    if ($idx -eq ($Stages.Count-1)) {
        Write-Host 'v016/F23 is live-PASS. No later mutation stage is authorized by this pack.'
        exit 0
    }
    $next = $Stages[$idx+1]
    Write-Host ("Next authorized install: {0} - {1}" -f $next.stage,$next.display)
    Write-Host (".\P1_PROMOTION_MANAGER.ps1 -Action Install -Stage {0}" -f $next.stage)
    exit 0
}

if ($Action -eq 'ResetLog') {
    Assert-GameClosed
    if ($StageNames -notcontains $ActiveStage) { throw 'ResetLog is only valid while a managed promotion stage is active.' }
    $archived = Archive-Log $Root ($ActiveStage + '_retry')
    Remove-PassesAtOrAfter $State $ActiveStage
    Save-State $Root $State
    Write-Host ("Fresh retry armed for $ActiveStage. Old log: " + $(if($archived){$archived}else{'<none>'}))
    Show-StageInstructions (Get-Stage $ActiveStage)
    exit 0
}

if ($Action -eq 'Install') {
    Assert-GameClosed
    if (!$Stage) { throw '-Stage is required for Install.' }
    $cfg = Get-Stage $Stage
    if ($ActiveStage -ne [string]$cfg.predecessor) {
        throw "Install $Stage requires active predecessor $($cfg.predecessor), but active stage is $ActiveStage. No skipping is allowed."
    }
    if ($cfg.predecessor -ne 'v001') {
        $passed = @($State.passedStages | ForEach-Object { [string]$_ })
        if ($passed -notcontains [string]$cfg.predecessor) {
            throw "Previous live gate $($cfg.predecessor) is not recorded PASS. Refusing promotion."
        }
    }
    Validate-StagePackage $cfg -ExtractCheck
    $zip = Join-Path $PSScriptRoot (Normalize-RelPath ([string]$cfg.package))
    $tmp = Join-Path (Get-StateDir $Root) ('temp\' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $backup = $null
    try {
        Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
        $srcAsi = Join-Path $tmp (Normalize-RelPath ([string]$cfg.asiPath))
        $srcLua = Join-Path $tmp (Normalize-RelPath ([string]$cfg.luaRoot))
        Assert-Hash $srcAsi ([string]$cfg.asiSha256) ("payload ASI " + $Stage)
        if (!(Test-Path -LiteralPath $srcLua -PathType Container)) { throw "Payload lua root missing: $srcLua" }

        $backup = Backup-Current $Root $ActiveStage $Stage
        $archivedLog = Archive-Log $Root ($ActiveStage + '_before_' + $Stage)

        try {
            Copy-Item -LiteralPath $srcAsi -Destination (Join-Path $Root 'homelander_p1.asi') -Force
            $rootLua = Join-Path $Root 'lua_p1'
            New-Item -ItemType Directory -Force -Path $rootLua | Out-Null
            $srcBase = [System.IO.Path]::GetFullPath($srcLua).TrimEnd('\')
            foreach ($file in Get-ChildItem -LiteralPath $srcLua -File -Recurse) {
                $rel = $file.FullName.Substring($srcBase.Length).TrimStart('\')
                $dst = Join-Path $rootLua $rel
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
                Copy-Item -LiteralPath $file.FullName -Destination $dst -Force
            }
            Assert-Hash (Join-Path $Root 'homelander_p1.asi') ([string]$cfg.asiSha256) ("installed ASI " + $Stage)
        } catch {
            Write-Warning "Install write failed; restoring transaction backup $backup"
            Restore-Backup $Root $backup
            throw
        }

        Remove-PassesAtOrAfter $State $Stage
        $history = @($State.installHistory)
        $history += [pscustomobject]@{installedUtc=(UtcNow);fromStage=$ActiveStage;toStage=$Stage;backupDir=$backup;archivedLog=$archivedLog;packageSha256=[string]$cfg.packageSha256}
        $State.installHistory = $history
        $State.currentStage = $Stage
        Save-State $Root $State
        Write-Host "INSTALL PASS: $Stage is hash-correct and active. No loader files were modified."
        Write-Host "Rollback snapshot: $backup"
        Show-StageInstructions $cfg
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    }
    exit 0
}

if ($Action -eq 'Check') {
    Assert-GameClosed
    if (!$Stage) { $Stage = $ActiveStage }
    $cfg = Get-Stage $Stage
    if ($Stage -ne $ActiveStage) { throw "Check requested for $Stage but active stage is $ActiveStage." }
    Assert-Hash (Join-Path $Root 'homelander_p1.asi') ([string]$cfg.asiSha256) ("active ASI " + $Stage)
    $log = Join-Path $Root 'homelander_p1_runtime.log'
    if (!(Test-Path -LiteralPath $log -PathType Leaf)) { throw 'No runtime log. Launch Prototype and execute the stage sequence first.' }
    $raw = Get-Content -LiteralPath $log -Raw
    if ($raw -match [string]$Manifest.forbiddenLogRegex) {
        $bad = [regex]::Match($raw,[string]$Manifest.forbiddenLogRegex)
        throw "FAIL-CLOSED: forbidden/fatal runtime evidence found: $($bad.Value). Use ResetLog after fixing/retrying."
    }
    $missing = @()
    foreach ($rx in @($cfg.required)) {
        if ($raw -notmatch [string]$rx) { $missing += [string]$rx }
    }
    if ($missing.Count -gt 0) {
        Write-Host 'GATE NOT PASSED. Missing required evidence:'
        foreach ($m in $missing) { Write-Host "  - $m" }
        Write-Host ''
        Write-Host 'Latest relevant lines:'
        Get-Content -LiteralPath $log -Tail $TailLines | Where-Object { $_ -match 'READY|F[0-9]+:|PASS|HIT|CAMERA|SUBMITTED|ABORT|REFUSED|FAIL|FATAL|Lua .*error' }
        exit 4
    }
    if ([bool]$cfg.visible -and !$ConfirmVisible) {
        throw "Log evidence passed, but this gate also requires human visual confirmation. Re-run Check with -ConfirmVisible only if true: $($cfg.visiblePrompt)"
    }

    $receiptDir = Join-Path (Get-StateDir $Root) 'receipts'
    New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null
    $receiptPath = Join-Path $receiptDir ((SafeStamp) + '_' + $Stage + '_PASS.json')
    $receipt = [pscustomobject]@{
        schema='homelander-p1-live-gate-receipt/1.0';stage=$Stage;gate=[string]$cfg.gate;passedUtc=(UtcNow);
        asiSha256=(Get-Sha256 (Join-Path $Root 'homelander_p1.asi'));logSha256=(Get-Sha256 $log);
        visualRequired=[bool]$cfg.visible;visualConfirmed=[bool]$ConfirmVisible;buildId=[string]$cfg.buildId;
        requiredRegex=@($cfg.required)
    }
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
    Add-Pass $State $Stage
    Save-State $Root $State
    Write-Host "LIVE GATE PASS RECORDED: $Stage / $($cfg.gate)"
    Write-Host "Evidence receipt: $receiptPath"
    & $PSCommandPath -Action Next -PrototypeRoot $Root
    exit 0
}

if ($Action -eq 'Rollback') {
    Assert-GameClosed
    if ($ActiveStage -eq 'v001') { Write-Host 'Already at v001; nothing to roll back.'; exit 0 }
    if ($StageNames -notcontains $ActiveStage) { throw "Active ASI is not a managed stage: $ActiveStage" }
    $history = @($State.installHistory)
    if ($history.Count -lt 1) { throw 'No transaction backup history is available for rollback.' }
    $last = $history[$history.Count-1]
    if ([string]$last.toStage -ne $ActiveStage) { throw "Last backup targets $($last.toStage), but active stage is $ActiveStage. Refusing ambiguous rollback." }
    $archived = Archive-Log $Root ($ActiveStage + '_before_rollback')
    Restore-Backup $Root ([string]$last.backupDir)
    $restored = Get-ActiveStage $Root
    if ($restored -ne [string]$last.fromStage) { throw "Rollback verification failed. Expected $($last.fromStage), got $restored." }
    $State.currentStage = $restored
    $cut = Get-StageIndex $ActiveStage
    $keep = @()
    foreach ($p in @($State.passedStages)) { if ((Get-StageIndex ([string]$p)) -lt $cut) { $keep += [string]$p } }
    $State.passedStages = $keep
    if ($history.Count -eq 1) { $State.installHistory = @() } else { $State.installHistory = @($history[0..($history.Count-2)]) }
    Save-State $Root $State
    Write-Host "ROLLBACK PASS: restored $restored from verified snapshot."
    Write-Host ("Archived current-stage log: " + $(if($archived){$archived}else{'<none>'}))
    exit 0
}

throw "Unhandled action: $Action"
