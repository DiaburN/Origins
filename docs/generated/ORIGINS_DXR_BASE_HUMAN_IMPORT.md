# ORIGINS-DxR — Zircon Base Human Import

- Import gate: **PASS**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Origins-DxR HEAD tested: `30b9271208ec48a4919ff15d6b3891a1e3e0c71c`
- Primary patch host from Zircon: `https://mirfiles.com/resources/mir3/zircon/patch/`
- Fetch status: **PASS**
- Export decode path: **managed BCnEncoder BC1/BC3**
- Exporter patch scope: `transient-vendor-tooling-only`

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| Fetch M-Hum + WM-Hum | success |
| Prepare managed DXT decoder | success |
| Build ZL exporter | success |
| Export browser atlases | success |
| Validate generated pair | success |
| Build runnable preview | success |

## Downloaded ZL files

- `M_Hum` from `https://mirfiles.com/resources/mir3/zircon/patch/Data-M-Hum.Zl.gz` — 16229006 gzip bytes → 44084120 raw bytes — SHA-256 `691FF4CCFDC7D63DA72AB740910849E4C13409C1A7F80D53E57602F748E68169`
- `WM_Hum` from `https://mirfiles.com/resources/mir3/zircon/patch/Data-WM-Hum.Zl.gz` — 15691717 gzip bytes → 43736032 raw bytes — SHA-256 `B0CE4F4F14413FA2B934E2C85B8D93E886E70656206E05860CE40F2370B09A0A`

## Exporter DXT decode

- DXT1 is decoded as `BCnEncoder.Net CompressionFormat.Bc1`.
- DXT5 is decoded as `BCnEncoder.Net CompressionFormat.Bc3`.
- The patch exists only in the transient pinned `vendor/zircon` checkout used by the exporter; no Zircon runtime source is committed or altered.

- Runtime pair: **M_Hum + WM_Hum READY**

## Browser atlases

- `M_Hum`: 16152/55000 images, 15 atlas pages, 30165114 PNG bytes
- `WM_Hum`: 12216/55000 images, 14 atlas pages, 27919891 PNG bytes

- Total generated browser payload: **64311476 bytes**
- Runnable preview artifact includes both real genders.
- Raw `.Zl` files remain transient build inputs; no Crystal fallback.
