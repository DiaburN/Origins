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

$host = $match.Groups[1].Value
$expectedHost = 'https://mirfiles.com/resources/mir3/zircon/patch/'
if ($host -ne $expectedHost) { throw "Unexpected Zircon patch host: $host" }

$dataRoot = Join-Path $OutputRoot 'Data'
New-Item -ItemType Directory -Force $dataRoot | Out-Null
New-Item -ItemType Directory -Force (Split-Path -Parent $ReportPath) | Out-Null

$targets = @(
    @{ Library = 'M_Hum'; FileName = 'M-Hum.Zl'; WebName = 'Data-M-Hum.Zl.gz' },
    @{ Library = 'WM_Hum'; FileName = 'WM-Hum.Zl'; WebName = 'Data-WM-Hum.Zl.gz' }
)

$rows = @()

foreach ($target in $targets) {
    $url = $host + $target.WebName
    $gzPath = Join-Path $env:RUNNER_TEMP $target.WebName
    $destPath = Join-Path $dataRoot $target.FileName

    Write-Host "Downloading $($target.Library) from $url"
    Invoke-WebRequest -Uri $url -OutFile $gzPath -UseBasicParsing -Headers @{ 'User-Agent' = 'ORIGINS-DxR-ZirconAssetImporter/1.0' }

    if (-not (Test-Path $gzPath)) { throw "Download missing: $gzPath" }
    if ((Get-Item $gzPath).Length -le 0) { throw "Downloaded gzip is empty: $url" }

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
        patchUrl = $url
        compressedBytes = (Get-Item $gzPath).Length
        compressedSha256 = $gzSha
        bytes = $item.Length
        sha256 = $sha
    }
}

$report = [ordered]@{
    schema = 'origins.zircon.base-human-fetch.v1'
    patchHost = $host
    patchHostSource = 'vendor/zircon/Launcher/Config.cs'
    source = 'official-zircon-launcher-patch-host'
    libraries = $rows
}

$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $ReportPath
Write-Host ($report | ConvertTo-Json -Depth 8)
