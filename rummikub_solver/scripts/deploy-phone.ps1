param(
    [string]$DeviceId = "",
    [string]$ApiBaseUrl = "",
    [switch]$LaunchOnly,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$FrontendDir = Join-Path $ProjectRoot "frontend"
$ApkPath = Join-Path $FrontendDir "build\app\outputs\flutter-apk\app-debug.apk"
$Adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"

if (-not (Test-Path $Adb)) {
    $adbCmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($adbCmd) {
        $Adb = $adbCmd.Source
    } else {
        Write-Error "adb not found. Install Android SDK platform-tools or connect Android Studio."
    }
}

function Invoke-Adb {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Adb @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "adb failed: adb $($Arguments -join ' ')"
    }
}

function Get-ConnectedDeviceId {
    param([string]$PreferredId)

    $output = & $Adb devices 2>&1 | Out-String
    $ids = @(
        [regex]::Matches($output, '(?m)^([A-Za-z0-9]+)\s+device\s*$') |
            ForEach-Object { $_.Groups[1].Value }
    )

    if ($PreferredId -and ($ids -contains $PreferredId)) {
        return $PreferredId
    }

    if ($ids.Count -eq 1) {
        return $ids[0]
    }

    if ($ids.Count -gt 1) {
        Write-Host "Multiple devices found:"
        for ($i = 0; $i -lt $ids.Count; $i++) {
            Write-Host "  [$i] $($ids[$i])"
        }
        $choice = Read-Host "Enter device index"
        return $ids[[int]$choice]
    }

    throw "No Android device connected. Enable USB debugging and reconnect the phone."
}

if (-not $ApiBaseUrl) {
    $lanIp = & (Join-Path $PSScriptRoot "get-lan-ip.ps1")
    if (-not $lanIp) {
        Write-Error "Could not detect LAN IP. Connect to your home network and run ipconfig, or pass -ApiBaseUrl manually."
    }
    $ApiBaseUrl = "http://${lanIp}:8000/api/v1"
}

$device = Get-ConnectedDeviceId -PreferredId $DeviceId
Write-Host "[Phone] Using device: $device"
Write-Host "[Phone] API base URL: $ApiBaseUrl"

if ($ApiBaseUrl -notmatch '^https?://[^/]+/') {
    Write-Error "Invalid API base URL: '$ApiBaseUrl'. Use -ApiBaseUrl or fix LAN IP detection."
}

if (-not $LaunchOnly) {
    if (-not $SkipBuild) {
        Write-Host "[Phone] Building debug APK..."
        Push-Location $FrontendDir
        try {
            flutter pub get
            if ($LASTEXITCODE -ne 0) { throw "flutter pub get failed" }

            flutter build apk --debug --dart-define=API_BASE_URL="$ApiBaseUrl"
            if ($LASTEXITCODE -ne 0) { throw "flutter build apk failed" }
        } finally {
            Pop-Location
        }
    } elseif (-not (Test-Path $ApkPath)) {
        throw "APK not found at $ApkPath. Run without -SkipBuild first."
    }

    Write-Host "[Phone] Installing APK via adb..."
    $resolvedApk = (Resolve-Path $ApkPath).Path
    Invoke-Adb @('-s', $device, 'push', $resolvedApk, '/data/local/tmp/rummikub.apk')
    Invoke-Adb @('-s', $device, 'shell', 'pm', 'install', '-r', '/data/local/tmp/rummikub.apk')
}

Write-Host "[Phone] Launching app..."
Invoke-Adb @(
    '-s', $device, 'shell', 'am', 'start',
    '-n', 'com.rummikub.assistant.rummikub_assistant/.MainActivity'
)

Write-Host ""
Write-Host "Done. Test backend from phone browser:"
Write-Host "  $($ApiBaseUrl -replace '/api/v1$', '')/docs"
