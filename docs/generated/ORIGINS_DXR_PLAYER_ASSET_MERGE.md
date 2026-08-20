# ORIGINS-DxR — Player Asset Bundle Merger

- Gate: **PASS**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- HEAD tested: `b6e2776f4300a07fa38d0375e8844f4608dcd882`

## CI

| Check | Result |
|---|---|
| Python syntax | success |
| 5 merger unit tests | success |

## Merge contract

- Every input master and library manifest must use `origins.zircon.web-atlas.v1`.
- All bundles must target the same pinned Zircon commit and atlas size.
- Library paths are constrained to their input bundle roots.
- Duplicate libraries are accepted only when manifest + every referenced atlas PNG hash identically.
- Conflicting duplicates fail closed.
- Atlas PNGs and frame metadata are copied byte-for-byte; the merger only rebuilds the top-level `player-assets.json`.
