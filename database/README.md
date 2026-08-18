# ORIGINS Database

ORIGINS keeps Zircon as the authoritative database and server data model.

## Runtime split verified from Zircon

The current Zircon server initializes one `MirDB.Session` with two model assemblies:

1. **LibraryCore** — static/game definitions.
2. **ServerLibrary** — persistent player/server data.

The MirDB engine used by this runtime lives inside `LibraryCore/MirDB`.

> The top-level legacy `MirDB/SystemModels` project also exists upstream, but it is **not** the source loaded by the current `SEnvir.LoadDatabase()` runtime. ORIGINS must follow the LibraryCore + ServerLibrary path.

## ORIGINS rule

- DB engine: Zircon `LibraryCore/MirDB`.
- Static definitions: Zircon `LibraryCore/SystemModels`.
- Persistent/player definitions: Zircon `ServerLibrary/DBModels`.
- Runtime collection wiring: Zircon `ServerLibrary/Envir/SEnvir.LoadDatabase()`.
- Crystal never replaces these database layers.
- Crystal spell catalogue maps into Zircon `MagicInfo`; learned/player spell state remains Zircon `UserMagic`.
- ORIGINS adds execution metadata only when a Crystal spell cannot be represented by Zircon native execution.

See:

- `zircon-model-manifest.json`
- `zircon-runtime-collections.json`
- `magic/execution-profiles.json`
