# Vendor sources

`vendor/zircon` is intentionally not committed. Run one of the bootstrap scripts from the repository root to install the exact Zircon revision used by ORIGINS.

Pinned source:

- repository: `mir-ethernity/mir3-zircon`
- commit: `820bf6d4a11d89cac7f87b81446567095f2e38b8`

The ORIGINS database project references:

- `vendor/zircon/LibraryCore/LibraryCore.csproj`
- `vendor/zircon/ServerLibrary/ServerLibrary.csproj`

This keeps a clean, reproducible upstream reference while ORIGINS-specific adaptations stay in `src/`.
