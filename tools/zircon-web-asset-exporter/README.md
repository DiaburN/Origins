# Zircon Web Asset Exporter

Build-time bridge from the pinned Zircon `.Zl` libraries to browser-readable PNG atlas pages.

The exporter intentionally references the pinned `vendor/zircon/LibraryEditor` reader so ORIGINS does not maintain a second guessed `.Zl` decoder. It preserves each image index, width, height, `OffSetX` and `OffSetY` in JSON metadata.

## Input layout

`--source-root` points to a Zircon runtime root containing `Data/`. Library paths are taken from the generated player asset contract, which itself is extracted from pinned `LibraryCore/Libraries.cs`.

Example:

```powershell
dotnet run --project tools/zircon-web-asset-exporter/ZirconWebAssetExporter.csproj -c Release -p:Platform=AnyCPU -- `
  --contract apps/origins-web-runtime/generated/zircon-player-asset-contract.json `
  --source-root C:\ZirconRuntime `
  --output-root .cache\web-player-assets `
  --library M_Hum
```

Use `--all-player-libraries` only when the complete Zircon player payload is present. `--probe` never fabricates output: it reports `READY` or `BLOCKED_MISSING_ZL` for the source root.

Generated atlases are build artifacts and should normally be deployed/cached rather than committed as source. The browser loader expects the exported `player-assets.json` tree under `apps/origins-web-runtime/assets/player/` (or another configured asset root).
