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
    param(
        [string]$Status,
        [string]$ErrorMessage = $null,
        [object[]]$Attempts = @()
    )

    $report = [ordered]@{
        schema = 'origins.zircon.base-human-fetch.v1'
        status = $Status
        primaryPatchHost = $expectedHost
        approvedPatchHosts = @($expectedHost, $mirrorHost)
        patchHostSource = 'vendor/zircon/Launcher/Config.cs'
        currentLibrary = $currentLibrary
        error = $ErrorMessage
        attempts = $Attempts
        libraries = $rows
    }
    $report | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $ReportPath
}

Write-FetchReport -Status 'STARTED'

try {
    $configPath = Join-Path $ZirconRoot 'Launcher/Config.cs'
    if (-not (Test-Path $configPath)) { throw "Missing pinned Zircon Launcher/Config.cs: $configPath" }

    $configText = Get-Content $configPath -Raw
    if (-not $configText.Contains($expectedHost)) {
        throw "Pinned Zircon Launcher/Config.cs does not contain the expected patch host: $expectedHost"
    }

    $hosts = @($expectedHost, $mirrorHost)
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

        foreach ($host in $hosts) {
            $url = $host + $target.WebName
            Write-Host "Downloading $($target.Library) from $url"

            & curl.exe `
                --fail `
                --location `
                --retry 2 `
                --retry-delay 2 `
                --connect-timeout 30 `
                --max-time 300 `
                --user-agent 'ORIGINS-DxR-ZirconAssetImporter/1.0' `
                --output $gzPath `
                $url
            $curlExit = $LASTEXITCODE

            if ($curlExit -eq 0 -and (Test-Path $gzPath) -and (Get-Item $gzPath).Length -gt 0) {
                $downloadedFrom = $url
                $attempts += [ordered]@{ url = $url; success = $true; exitCode = $curlExit; error = $null }
                break
            }

            $attempts += [ordered]@{
                url = $url
                success = $false
                exitCode = $curlExit
                error = "curl exit code $curlExit"
            }
            if (Test-Path $gzPath) { Remove-Item -Force $gzPath }
        }

        if (-not $downloadedFrom) {
            Write-FetchReport -Status 'FAIL_DOWNLOAD' -ErrorMessage "No approved MirFiles host returned $($target.WebName)." -Attempts $attempts
            throw "Unable to download $($target.Library) from approved MirFiles Zircon patch hosts."
        }

        $input = [System.IO.File]::OpenRead($gzPath)
        try {
            $gzip = New-Object System.IO.Compression.GZipStream($input, [System.IO.Compression.CompressionMode]::Decompress)
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

    if ($existing -and $existing.status -eq 'FAIL_DOWNLOAD') {
        Write-Host (Get-Content $ReportPath -Raw)
    }
    else {
        Write-FetchReport -Status 'FAIL_SCRIPT' -ErrorMessage $_.Exception.Message
        Write-Host (Get-Content $ReportPath -Raw)
    }
    throw
}
