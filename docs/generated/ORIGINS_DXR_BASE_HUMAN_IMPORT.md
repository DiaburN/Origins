# ORIGINS-DxR — Zircon Base Human Import

- Import gate: **FAIL**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Origins-DxR HEAD tested: `d2afe5fad88108a93e13a720b94c80a21a4cd76c`
- Primary patch host from Zircon: `https://mirfiles.com/resources/mir3/zircon/patch/`
- Fetch status: **FAIL_SCRIPT**

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| Fetch M-Hum + WM-Hum | failure |
| Build ZL exporter | skipped |
| Export browser atlases | skipped |
| Validate generated pair | skipped |
| Build runnable preview | skipped |

## Boundary

- This report does not claim a real sprite import unless every download/export/validation step succeeds.
- No Crystal or placeholder artwork is substituted on failure.
