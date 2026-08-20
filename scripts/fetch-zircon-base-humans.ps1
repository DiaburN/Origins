param(
    [Parameter(Mandatory = $true)]
    [string]$ZirconRoot,

    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [Parameter(Mandatory = $true)]
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'

$configPath = Join-Path $ZirconRoot 'Launcher/Config.cs'
if (-not (Test-Path $configPath)) { throw "Missing pinned Zircon Launcher/Config.cs: $configPath" }

$configText = Get-Content $configPath -Raw
$match = [regex]::Match($configText, 'Host\s*\{\s*get;\s*set;\s*\}\s*=\s*@"([^"]+)"')
if (-not $match.Success) { throw 'Could not extract Launcher.Config.Host from pinned Zircon source.' }

$primaryHost = $match.Groups[1].Value
$expectedHost = 'https://mirfiles.com/resources/mir3/zircon/patch/'
if ($primaryHost -ne $expectedHost) { throw "Unexpected Zircon patch host: $primaryHost" }

# MirFiles exposes the same public Zircon patch directory on its .co.uk host.
# Always try the exact host embedded in pinned Zircon first; use the mirror only
# if the primary host is unavailable from the runner.
$hosts = @(
    $primaryHost,
    'https://mirfiles.co.uk/resources/mir3/zircon/patch/'
) | Select-Object -Unique

$dataRoot = Join-Path $OutputRoot 'Data'
New-Item -ItemType Directory -Force $dataRoot | Out-Null
New-Item -ItemType Directory -Force (Split-Path -Parent $ReportPath) | Out-Null

$targets = @(
    @{ Library = 'M_Hum'; FileName = 'M-Hum.Zl'; WebName = 'Data-M-Hum.Zl.gz' },
    @{ Library = 'WM_Hum'; FileName = 'WM-Hum.Zl'; WebName = 'Data-WM-Hum.Zl.gz' }
)

$rows = @()

foreach ($target in $targets) {
    $gzPath = Join-Path $env:RUNNER_TEMP $target.WebName
    $destPath = Join-Path $dataRoot $target.FileName
    $downloadedFrom = $null
    $attempts = @()

    if (Test-Path $gzPath) { Remove-Item -Force $gzPath }

    foreach ($host in $hosts) {
        $url = $host + $target.WebName
        Write-Host "Downloading $($target.Library) from $url"
        try {
            Invoke-WebRequest `
                -Uri $url `
                -OutFile $gzPath `
                -UseBasicParsing `
                -MaximumRedirection 10 `
                -TimeoutSec 180 `
                -Headers @{ 'User-Agent' = 'ORIGINS-DxR-ZirconAssetImporter/1.0' }

            if ((Test-Path $gzPath) -and (Get-Item $gzPath).Length -gt 0) {
                $downloadedFrom = $url
                $attempts += [ordered]@{ url = $url; success = $true; error = $null }
                break
            }
            throw "Downloaded file is missing or empty."
        }
        catch {
            $attempts += [ordered]@{ url = $url; success = $false; error = $_.Exception.Message }
            Write-Warning "Download failed from $url : $($_.Exception.Message)"
            if (Test-Path $gzPath) { Remove-Item -Force $gzPath }
        }
    }

    if (-not $downloadedFrom) {
        $failure = [ordered]@{
            schema = 'origins.zircon.base-human-fetch.v1'
            status = 'FAIL_DOWNLOAD'
            primaryPatchHost = $primaryHost
            patchHostSource = 'vendor/zircon/Launcher/Config.cs'
            failedLibrary = $target.Library
            attempts = $attempts
            libraries = $rows
        }
        $failure | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $ReportPath
        throw "Unable to download $($target.Library) from any approved MirFiles Zircon patch host."
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

    $sha = (Get-FileHash -Path $destPath -Algorithm SHA256).Hash
    $gzSha = (Get-FileHash -Path $gzPath -Algorithm SHA256).Hash

    $rows += [ordered]@{
        libraryFile = $target.Library
        sourcePath = "Data/$($target.FileName)"
        patchUrl = $downloadedFrom
        attempts = $attempts
        compressedBytes = (Get-Item $gzPath).Length
        compressedSha256 = $gzSha
        bytes = $item.Length
        sha256 = $sha
    }
}

$report = [ordered]@{
    schema = 'origins.zircon.base-human-fetch.v1'
    status = 'PASS'
    primaryPatchHost = $primaryHost
    approvedPatchHosts = $hosts
    patchHostSource = 'vendor/zircon/Launcher/Config.cs'
    source = 'official-zircon-launcher-patch-host-or-mirfiles-public-mirror'
    libraries = $rows
}

$report | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $ReportPath
Write-Host ($report | ConvertTo-Json -Depth 10)
