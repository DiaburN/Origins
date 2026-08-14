param(
    [string]$CrystalData,
    [string]$DatabaseMaps,
    [string]$Output = "origins\map-engine\themes\zuma\extracted"
)

$ErrorActionPreference = "Stop"

if (-not $CrystalData) {
    $CrystalData = Read-Host "Ruta a la carpeta Data del cliente Crystal"
}

if (-not $DatabaseMaps) {
    $DatabaseMaps = Read-Host "Ruta a la carpeta Crystal.Database\Jev\Maps"
}

if (-not (Test-Path $CrystalData)) {
    throw "No existe CrystalData: $CrystalData"
}

if (-not (Test-Path $DatabaseMaps)) {
    throw "No existe DatabaseMaps: $DatabaseMaps"
}

$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
} else {
    throw "No se ha encontrado Python (py/python) en PATH."
}

$Script = Join-Path $PSScriptRoot "extract_theme_assets.py"

Write-Host ""
Write-Host "ORIGINS - Extrayendo assets Zuma..." -ForegroundColor Cyan
Write-Host "Data: $CrystalData"
Write-Host "Maps: $DatabaseMaps"
Write-Host "Output: $Output"
Write-Host ""

& $Python $Script `
    --data $CrystalData `
    --maps $DatabaseMaps `
    --standard d501.map `
    --king d515.map `
    --theme zuma `
    --out $Output

if ($LASTEXITCODE -ne 0) {
    throw "La extraccion termino con codigo $LASTEXITCODE"
}

$Gallery = Join-Path $Output "gallery.html"
Write-Host ""
Write-Host "Extraccion completada." -ForegroundColor Green
Write-Host "Galeria: $Gallery" -ForegroundColor Green

if (Test-Path $Gallery) {
    Start-Process $Gallery
}
