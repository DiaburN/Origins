# ORIGINS-DxR database source policy

## Authoritative schema/runtime

ORIGINS-DxR follows the pinned official `Suprcode/Zircon` source at commit `cbf1aa919083bc13fc3f23f93772a8ab8370632d`.

The MirDB engine, `SystemModels`, `DBModels`, `MagicInfo`, `UserMagic` and server-side execution rules come from that Zircon revision.

No second database or spell-runtime source participates in the active branch.

## Published content database

The public Zircon `Database.7z` is the canonical content input. It must be opened and verified with the pinned runtime before ORIGINS-specific data is layered on top.

Base validation chain:

```text
Database.7z
 -> canonical System.db
 -> pinned Zircon source preflight
 -> complete index-preserving JSON snapshot for inspection
 -> optional Zircon-compatible ORIGINS content overlays
 -> reopen + preflight + index validation
```

If any gate fails, the candidate is rejected.

## Magic policy

The active magic source is Zircon itself:

```text
MagicType enum
 -> System.db MagicInfo
 -> MagicObject runtime handler
 -> UserMagic player state
```

Current playable-class scope is Warrior, Wizard, Taoist and Assassin. Enum entries explicitly marked `NOT CODED` or `UNUSED` upstream remain incomplete; ORIGINS-DxR does not silently invent implementations while reconstructing the Zircon base.
