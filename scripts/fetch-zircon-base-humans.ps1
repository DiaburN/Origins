param(
    [Parameter(Mandatory = $true)]
    [string]$ZirconRoot,
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [Parameter(Mandatory = $true)]
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'
$expectedHost = 'https://mirfiles.com/resources/mir3/zircon/patch/'
$mirrorHost = 'https://mirfiles.co.uk/resources/mir3/zircon/patch/'
$rows = @()
$currentLibrary = $null
New-Item -ItemType Directory -Force (Split-Path -Parent $ReportPath) | Out-Null

function Write-FetchReport {
    param([string]$Status, [string]$ErrorMessage = $null, [object[]]$Attempts = @())
    [ordered]@{
        schema = 'origins.zircon.base-human-fetch.v1'
        status = $Status
        primaryPatchHost = $expectedHost
        approvedPatchHosts = @($expectedHost, $mirrorHost)
        patchHostSource = 'vendor/zircon/Launcher/Config.cs'
        currentLibrary = $currentLibrary
        error = $ErrorMessage
        attempts = $Attempts
        libraries = $rows
    } | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $ReportPath
}

function Test-GZipFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        if ($stream.Length -lt 2) { return $false }
        $b0 = $stream.ReadByte()
        $b1 = $stream.ReadByte()
        return ($b0 -eq 0x1F -and $b1 -eq 0x8B)
    }
    finally { $stream.Dispose() }
}

Write-FetchReport -Status 'STARTED'

try {
    $configPath = Join-Path $ZirconRoot 'Launcher/Config.cs'
    if (-not (Test-Path $configPath)) { throw "Missing pinned Zircon Launcher/Config.cs: $configPath" }
    $configText = Get-Content $configPath -Raw
    if (-not $configText.Contains($expectedHost)) {
        throw "Pinned Zircon Launcher/Config.cs does not contain expected host: $expectedHost"
    }

    $dataRoot = Join-Path $OutputRoot 'Data'
    New-Item -ItemType Directory -Force $dataRoot | Out-Null
    $targets = @(
        @{ Library = 'M_Hum'; FileName = 'M-Hum.Zl'; WebName = 'Data-M-Hum.Zl.gz' },
        @{ Library = 'WM_Hum'; FileName = 'WM-Hum.Zl'; WebName = 'Data-WM-Hum.Zl.gz' }
    )

    foreach ($target in $targets) {
        $currentLibrary = $target.Library
        $gzPath = Join-Path $env:RUNNER_TEMP $target.WebName
        $destPath = Join-Path $dataRoot $target.FileName
        $downloadedFrom = $null
        $attempts = @()
        if (Test-Path $gzPath) { Remove-Item -Force $gzPath }
        if (Test-Path $destPath) { Remove-Item -Force $destPath }

        foreach ($host in @($expectedHost, $mirrorHost)) {
            $url = $host + $target.WebName
            Write-Host "Downloading $($target.Library) from $url"
            & curl.exe --fail --location --retry 2 --retry-delay 2 --connect-timeout 30 --max-time 300 --user-agent 'ORIGINS-DxR-ZirconAssetImporter/1.0' --output $gzPath $url
            $curlExit = $LASTEXITCODE
            $exists = (Test-Path $gzPath) -and (Get-Item $gzPath).Length -gt 0
            $gzipValid = $exists -and (Test-GZipFile $gzPath)

            if ($curlExit -eq 0 -and $gzipValid) {
                $downloadedFrom = $url
                $attempts += [ordered]@{ url = $url; success = $true; exitCode = $curlExit; gzip = $true; error = $null }
                break
            }

            $reason = if ($curlExit -ne 0) { "curl exit code $curlExit" } elseif (-not $exists) { 'empty/missing response' } else { 'response is not a GZip file' }
            $attempts += [ordered]@{ url = $url; success = $false; exitCode = $curlExit; gzip = $gzipValid; error = $reason }
            if (Test-Path $gzPath) { Remove-Item -Force $gzPath }
        }

        if (-not $downloadedFrom) {
            Write-FetchReport -Status 'FAIL_DOWNLOAD' -ErrorMessage "No approved MirFiles host returned a valid GZip for $($target.WebName)." -Attempts $attempts
            throw "Unable to download $($target.Library) as valid GZip."
        }

        $input = [System.IO.File]::OpenRead($gzPath)
        try {
            $gzip = [System.IO.Compression.GZipStream]::new($input, [System.IO.Compression.CompressionMode]::Decompress)
            try {
                $output = [System.IO.File]::Create($destPath)
                try { $gzip.CopyTo($output) } finally { $output.Dispose() }
            } finally { $gzip.Dispose() }
        } finally { $input.Dispose() }

        $item = Get-Item $destPath
        if ($item.Length -le 0) { throw "Decompressed Zircon library is empty: $destPath" }
        $rows += [ordered]@{
            libraryFile = $target.Library
            sourcePath = "Data/$($target.FileName)"
            patchUrl = $downloadedFrom
            attempts = $attempts
            compressedBytes = (Get-Item $gzPath).Length
            compressedSha256 = (Get-FileHash -Path $gzPath -Algorithm SHA256).Hash
            bytes = $item.Length
            sha256 = (Get-FileHash -Path $destPath -Algorithm SHA256).Hash
        }
        Write-FetchReport -Status 'IN_PROGRESS'
    }

    $currentLibrary = $null
    Write-FetchReport -Status 'PASS'
    Get-Content $ReportPath -Raw | Write-Host
}
catch {
    $existing = $null
    if (Test-Path $ReportPath) {
        try { $existing = Get-Content $ReportPath -Raw | ConvertFrom-Json } catch { $existing = $null }
    }
    if (-not ($existing -and $existing.status -eq 'FAIL_DOWNLOAD')) {
        Write-FetchReport -Status 'FAIL_SCRIPT' -ErrorMessage $_.Exception.Message
    }
    Get-Content $ReportPath -Raw | Write-Host
    throw
}
