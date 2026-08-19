# ORIGINS DxR — GameInter / UI source

The active ORIGINS-DxR interface is the **closed source-faithful Zircon desktop reconstruction** restored from branch `origins-game-v1`.

## Authoritative UI baseline

Source branch: `origins-game-v1`
Closed UI baseline commit: `a3eba357359f1ce95f97020ae68d27792174c8da`
Closure branch commit: `1856944d202e30096dfe21e43fe39bd9e000b426`
Zircon source commit used for validation: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`

The restored runtime/source tree lives at:

```text
apps/zircon-ui-reference/
tools/zircon-ui-importer/
```

Validation evidence is retained in:

```text
docs/UI_FIDELITY_CHECKPOINT_2026-08-18.md
docs/ZIRCON_UI_DECISIONS.md
docs/ZIRCON_UI_FULL_SCOPE.md
docs/ZIRCON_UI_RECONSTRUCTION.md
```

## Closed fidelity status

- 65/65 GameScene windows
- 15/15 nested/transient windows
- 80/80 total windows
- 2674 browser-validated GameScene controls
- 149 browser-validated nested controls
- Browser QA PASS
- Visual Review PASS
- 0 browser failures
- 0 browser JS errors
- 0 outstanding source-backed visual corrections

## Artwork rule

The thousands of individual artwork PNGs are intentionally not committed as a static duplicate tree. The UI build pipeline downloads the original Zircon `.Zl` artwork, extracts the exact referenced frames and assembles the complete viewer from the committed source-faithful manifest/runtime tooling.

This means the interface is **present and reproducible from GitHub** even though generated `assets/.../*.png` files are build artifacts rather than source files.

## ORIGINS-DxR integration rule

Preserve this UI baseline 100% while wiring it to the active Zircon runtime/database.

- Keep the existing window geometry, controls, hit testing, navigation and source-backed artwork.
- Keep dynamic/localizable text outside PNG artwork.
- Use Zircon `MagicInfo` / `UserMagic` as the magic-window data source.
- Use Zircon runtime/server state for player, inventory, quests, guilds, maps, NPCs, monsters and all other runtime-bound payloads.
- Do not introduce a parallel Crystal UI/runtime layer.
- Mobile/Archero adaptation must be a later ORIGINS presentation layer and must not destroy this locked desktop reference.
