$ErrorActionPreference = "Stop"

$Repo = "https://github.com/Suprcode/Crystal.Database.git"
$Commit = "a19f6dca8f5e238d4ed79801820777abbf0a9ca4"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Cache = Join-Path $Root ".cache\crystal-database-source"
$Dest = Join-Path $Root "vendor\crystal-database\Jev"

New-Item -ItemType Directory -Force -Path (Split-Path $Cache -Parent) | Out-Null
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

if (-not (Test-Path (Join-Path $Cache ".git"))) {
    if (Test-Path $Cache) { Remove-Item -Recurse -Force $Cache }
    git clone --filter=blob:none --no-checkout $Repo $Cache
}

git -C $Cache remote set-url origin $Repo
git -C $Cache fetch --depth=1 origin $Commit
$Actual = (git -C $Cache rev-parse FETCH_HEAD).Trim()
if ($Actual -ne $Commit) { throw "Crystal.Database revision mismatch. Expected $Commit, got $Actual" }

$DbBytes = git -C $Cache show "$Commit`:Jev/Server.MirDB" --output=(Join-Path $Dest "Server.MirDB")
if ($LASTEXITCODE -ne 0) { throw "Failed to extract Jev/Server.MirDB" }
git -C $Cache show "$Commit`:Jev/README.md" | Set-Content -Encoding utf8 (Join-Path $Dest "README.md")

$Db = Join-Path $Dest "Server.MirDB"
if (-not (Test-Path $Db)) { throw "Jev/Server.MirDB was not extracted" }
$Hash = Get-FileHash -Algorithm SHA256 $Db
Write-Host "Crystal.Database/Jev pinned at $Actual"
Write-Host "Jev Server.MirDB SHA-256: $($Hash.Hash)"
