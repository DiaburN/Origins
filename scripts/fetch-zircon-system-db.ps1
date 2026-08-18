$ErrorActionPreference = "Stop"

$Url = "https://files.lomcn.co.uk/resources/mir3/zircon/Database.7z"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Cache = Join-Path $Root ".cache\zircon-database"
$Archive = Join-Path $Cache "Database.7z"
$Extracted = Join-Path $Cache "extracted"
$Dest = Join-Path $Root "Database"

$SevenZip = Get-Command 7zz -ErrorAction SilentlyContinue
if (-not $SevenZip) { $SevenZip = Get-Command 7z -ErrorAction SilentlyContinue }
if (-not $SevenZip) { throw "7-Zip is required (7zz.exe or 7z.exe on PATH)." }

New-Item -ItemType Directory -Force -Path $Cache | Out-Null
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
if (Test-Path $Extracted) { Remove-Item -Recurse -Force $Extracted }
New-Item -ItemType Directory -Force -Path $Extracted | Out-Null

Invoke-WebRequest -Uri $Url -OutFile $Archive
$Hash = Get-FileHash -Algorithm SHA256 $Archive
Write-Host "Archive source: $Url"
Write-Host "Archive SHA-256: $($Hash.Hash)"

& $SevenZip.Source x -y "-o$Extracted" $Archive | Out-Null
if ($LASTEXITCODE -ne 0) { throw "7-Zip extraction failed with exit code $LASTEXITCODE" }

$SystemDb = Get-ChildItem -Path $Extracted -Recurse -File | Where-Object { $_.Name -ieq "System.db" } | Select-Object -First 1
if (-not $SystemDb) { throw "System.db was not found inside Database.7z" }

Copy-Item -Force $SystemDb.FullName (Join-Path $Dest "System.db")
Write-Host "Installed candidate Zircon System.db -> $(Join-Path $Dest 'System.db')"
Write-Host "The file has NOT been rewritten or upgraded. Run:"
Write-Host "dotnet run --project tools/Origins.Database.Verify/Origins.Database.Verify.csproj -- `"$Dest`""
