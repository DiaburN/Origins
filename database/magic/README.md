# ORIGINS DxR magic workflow

ORIGINS-DxR uses **Zircon only** for active player magic.

## Active classes

- Warrior
- Wizard
- Taoist
- Assassin

Archer and Monk are not part of the current runtime or database scope.

## Authoritative sources

Pinned source: `Suprcode/Zircon@cbf1aa919083bc13fc3f23f93772a8ab8370632d`.

The active spell chain is:

```text
LibraryCore/Enum.cs::MagicType
        ↓
System.db::MagicInfo
        ↓
ServerLibrary MagicObject registration/execution
        ↓
UserMagic player state
        ↓
Zircon client spell/action/effect presentation
```

There is no Crystal translation layer and no Crystal magic overlay.

## Catalog

`zircon-four-class-magic-types.json` contains the 195 player-class enum entries in the pinned Zircon source.

Statuses are deliberately conservative:

- `ENUM_DEFINED`
- `DB_PRESENT`
- `RUNTIME_HANDLER_PRESENT`
- `PLAYABLE`
- `UPSTREAM_NOT_CODED`
- `UPSTREAM_UNUSED`

Do not mark a spell `PLAYABLE` merely because it appears in the enum. Its canonical Zircon `System.db` row and runtime path must also exist.

## Upstream incomplete entries

The pinned source explicitly marks these as incomplete/unused and ORIGINS-DxR will not silently invent implementations for them:

- Warrior: `FlameArt`
- Wizard: `Storm`, `Tornado`, `UnityWithNature`
- Taoist: `SupremeHealing`
- Assassin: `Unused`, `ManaBurn`

The first objective is a faithful four-class Zircon game. Custom ORIGINS balancing/content comes later and must remain native to the Zircon architecture.
