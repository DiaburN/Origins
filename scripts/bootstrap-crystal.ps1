$ErrorActionPreference = "Stop"

$Repo = "https://github.com/Suprcode/Crystal.git"
$Commit = "0e315fe327192afe52c3d7357ddd1f5b7e26c5b8"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Vendor = Join-Path $Root "vendor"
$Dest = Join-Path $Vendor "crystal"

New-Item -ItemType Directory -Force -Path $Vendor | Out-Null

if (-not (Test-Path (Join-Path $Dest ".git"))) {
    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
    git clone --filter=blob:none --no-checkout $Repo $Dest
}

git -C $Dest remote set-url origin $Repo
git -C $Dest fetch --depth=1 origin $Commit
git -C $Dest checkout --detach $Commit

$Head = (git -C $Dest rev-parse HEAD).Trim()
if ($Head -ne $Commit) {
    throw "Crystal revision mismatch. Expected $Commit, got $Head"
}

Write-Host "Official Suprcode/Crystal pinned at $Head"
