$ErrorActionPreference = "Stop"

$Repo = "https://github.com/Suprcode/Zircon.git"
$Commit = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Vendor = Join-Path $Root "vendor"
$Dest = Join-Path $Vendor "zircon"
$Overrides = Join-Path $Root "overrides\zircon"

New-Item -ItemType Directory -Force -Path $Vendor | Out-Null

if (-not (Test-Path (Join-Path $Dest ".git"))) {
    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
    git clone --filter=blob:none --no-checkout $Repo $Dest
}

git -C $Dest remote set-url origin $Repo
git -C $Dest fetch --depth=1 origin $Commit
git -C $Dest checkout --detach --force $Commit
git -C $Dest clean -fd

$Head = (git -C $Dest rev-parse HEAD).Trim()
if ($Head -ne $Commit) {
    throw "Zircon revision mismatch. Expected $Commit, got $Head"
}

if (Test-Path $Overrides) {
    Get-ChildItem -Path $Overrides -Recurse -File | Where-Object { $_.Name -ne "README.md" } | Sort-Object FullName | ForEach-Object {
        $Relative = [System.IO.Path]::GetRelativePath($Overrides, $_.FullName)
        $Target = Join-Path $Dest $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path $Target -Parent) | Out-Null
        Copy-Item -Force $_.FullName $Target
        Write-Host "Applied ORIGINS Zircon override: $Relative"
    }
}

Write-Host "Official Suprcode/Zircon pinned at $Head with ORIGINS overrides applied"
