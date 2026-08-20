param(
    [Parameter(Mandatory = $true)]
    [string]$ZirconRoot,
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [Parameter(Mandatory = $true)]
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'

python scripts/fetch-zircon-base-humans.py `
    --zircon-root $ZirconRoot `
    --output-root $OutputRoot `
    --report $ReportPath

if ($LASTEXITCODE -ne 0) {
    throw "Python Zircon base-human downloader failed with exit code $LASTEXITCODE. See $ReportPath for exact diagnostics."
}
