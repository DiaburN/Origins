# Vendor sources

`vendor/zircon` is intentionally not committed. Run `scripts/bootstrap-zircon.sh` or `scripts/bootstrap-zircon.ps1` from the ORIGINS repository to install the exact upstream source used by the database/server foundation.

Pinned upstream:

- repository: `Suprcode/Zircon`
- branch: `master`
- commit: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- upstream commit date: 2026-08-12

ORIGINS references the current official projects directly:

- `vendor/zircon/LibraryCore/LibraryCore.csproj`
- `vendor/zircon/ServerLibrary/ServerLibrary.csproj`

ORIGINS-specific code remains under `src/`; upstream code is not silently copied and modified.
