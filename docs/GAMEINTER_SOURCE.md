# ORIGINS DxR — GameInter source

The approved ORIGINS interface is frozen as the client presentation base.

## Consolidated package

`Origins_GameInter_Navegable_v1.0_MINIMAP_CONTROLES_BAJADOS.zip`

Supporting master instructions:

`ORIGINS_GAMEINTER_INSTRUCCIONES_CURSOR.txt`

## Integration rule

When the consolidated package is available in the repository checkout, import it intact. Do not reconstruct an approximation from screenshots or older standalone HTML files.

Preserve 100% of approved behavior and placement, including:

- lower HUD and its statistics;
- minimap and controls;
- MagicDialog/magic trees visual shell;
- Bag, Character, Map, Quests, Settings and other approved windows;
- original GameInter assets and their offsets;
- dynamic/translatable text rather than text burned into PNG assets;
- existing navigation and hitboxes that already work.

For magic integration, keep the visual shell but replace its data source with the active Zircon four-class `MagicInfo`/`UserMagic` state. The interface must not contain a parallel spell behavior engine.

## Current repository state

The consolidated ZIP bytes are not currently committed in `DiaburN/Origins`. Therefore this branch records the exact approved package and integration contract rather than substituting a different UI build.

Do not mark GameInter binary integration complete until that exact package (or a byte-identical extracted tree) has been added to the repository.
