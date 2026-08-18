# Vendor sources

Vendor source trees are intentionally not committed.

## Zircon

Run `scripts/bootstrap-zircon.sh` or `scripts/bootstrap-zircon.ps1`.

Pinned upstream:
- repository: `Suprcode/Zircon`
- branch: `master`
- commit: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- upstream commit date: 2026-08-12

ORIGINS references the current official projects directly:
- `vendor/zircon/LibraryCore/LibraryCore.csproj`
- `vendor/zircon/ServerLibrary/ServerLibrary.csproj`

## Crystal

Run `scripts/bootstrap-crystal.sh` or `scripts/bootstrap-crystal.ps1`.

Pinned upstream:
- repository: `Suprcode/Crystal`
- branch: `master`
- commit: `0e315fe327192afe52c3d7357ddd1f5b7e26c5b8`
- upstream commit date: 2026-08-12

Crystal is a **read-only spell-content/behavior reference**. ORIGINS never adopts Crystal's database engine or player persistence.

ORIGINS-specific code remains under `src/`, `tools/`, `scripts/` and `database/`.
