# Vendor sources — ORIGINS DxR

Vendor source trees are intentionally not committed.

## Zircon

Run `scripts/bootstrap-zircon.sh` or `scripts/bootstrap-zircon.ps1`.

Pinned upstream:

- repository: `Suprcode/Zircon`
- branch: `master`
- commit: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- upstream commit date: 2026-08-12

The bootstrap performs a source-pure checkout and rejects local modifications. ORIGINS-DxR uses this Zircon revision as the sole runtime/vendor source for the active game foundation.

Referenced projects include:

- `vendor/zircon/LibraryCore/LibraryCore.csproj`
- `vendor/zircon/ServerLibrary/ServerLibrary.csproj`

ORIGINS-specific database tooling remains under `src/`, `tools/`, `scripts/` and `database/`, but it must not replace Zircon's combat/magic engine.

Previous experimental source integrations are preserved only in archived Git branches and are not bootstrapped by `Origins-DxR`.
