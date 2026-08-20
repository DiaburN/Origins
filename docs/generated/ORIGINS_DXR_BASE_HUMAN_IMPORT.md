# ORIGINS-DxR — Zircon Base Human Import

- Import gate: **FAIL**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Origins-DxR HEAD tested: `ab8e801cec013e214e66646228a87bd682ffb642`
- Primary patch host from Zircon: `https://mirfiles.com/resources/mir3/zircon/patch/`
- Fetch status: **PASS**

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| Fetch M-Hum + WM-Hum | success |
| Build ZL exporter | success |
| Export browser atlases | failure |
| Validate generated pair | skipped |
| Build runnable preview | skipped |

## Boundary

- This report does not claim a real sprite import unless every download/export/validation step succeeds.
- No Crystal or placeholder artwork is substituted on failure.
