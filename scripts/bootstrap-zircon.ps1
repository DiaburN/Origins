$ErrorActionPreference = "Stop"

$Repo = "https://github.com/Suprcode/Zircon.git"
$Commit = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Vendor = Join-Path $Root "vendor"
$Dest = Join-Path $Vendor "zircon"

New-Item -ItemType Directory -Force -Path $Vendor | Out-Null

if (-not (Test-Path (Join-Path $Dest ".git"))) {
    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
    git clone --filter=blob:none --no-checkout $Repo $Dest
}

git -C $Dest remote set-url origin $Repo
git -C $Dest fetch --depth=1 origin $Commit
git -C $Dest checkout --detach --force $Commit
git -C $Dest clean -fdx

$Head = (git -C $Dest rev-parse HEAD).Trim()
if ($Head -ne $Commit) {
    throw "Zircon revision mismatch. Expected $Commit, got $Head"
}

$Status = (git -C $Dest status --porcelain) -join "`n"
if (-not [string]::IsNullOrWhiteSpace($Status)) {
    throw "Zircon checkout contains local modifications after bootstrap:`n$Status"
}

Write-Host "Official Suprcode/Zircon pinned source-pure at $Head"
