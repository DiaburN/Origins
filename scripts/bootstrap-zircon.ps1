$ErrorActionPreference = "Stop"

$Repo = "https://github.com/mir-ethernity/mir3-zircon.git"
$Commit = "820bf6d4a11d89cac7f87b81446567095f2e38b8"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Vendor = Join-Path $Root "vendor"
$Dest = Join-Path $Vendor "zircon"

New-Item -ItemType Directory -Force -Path $Vendor | Out-Null

if (-not (Test-Path (Join-Path $Dest ".git"))) {
    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
    git clone --filter=blob:none --no-checkout $Repo $Dest
}

git -C $Dest fetch --depth=1 origin $Commit
git -C $Dest checkout --detach $Commit

$Head = (git -C $Dest rev-parse HEAD).Trim()
Write-Host "Zircon pinned at $Head"
