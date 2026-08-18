# Zircon JSON vs ORIGINS database snapshots

Current Zircon includes its own JSON exporter/import converters (`Server/Helpers/JsonExporter.cs` and `ServerLibrary/Converter/DBObjectConverter.cs`). Those tools are useful for editing individual tables through the server UI and resolve DBObject references through identity fields.

ORIGINS keeps that capability, but uses a separate **full database snapshot format** for automated rebuilds.

## Why ORIGINS uses a second JSON shape

The ORIGINS pipeline must prove that a complete `System.db` can be rebuilt without shifting object indices. Some Zircon systems and configuration values refer to explicit database indices, so a content migration must preserve them.

The ORIGINS snapshot therefore records for every system collection:

- assembly + full CLR type
- collection `Index`
- every existing object `Index`
- only fields persisted by Zircon `DBMapping`
- DBObject references as explicit type + index references
- exact encodings for every scalar type accepted by Zircon `DBValue`

Reverse `DBBindingList<>` associations are not duplicated in JSON; they are rebuilt by Zircon's normal `OnChanged/CreateLink` association logic when references are restored.

## Rebuild rule

The importer follows the same construction path used by `DBCollection.Load()` rather than `CreateNewObject()`.

This is mandatory because some system models execute default creation logic. For example, creating a new `QuestInfo` normally creates a default `QuestRequirement`. That behavior is correct for an editor creating a new quest, but wrong while replaying an existing database snapshot because it would create additional rows and shift indices.

After all objects are instantiated with their original indices, references and scalar values are restored, the database is saved through the real Zircon `Session`, reopened, and validated.

## Editing ORIGINS

Never hand-edit the generated base snapshot. Put game changes in `database/overlays/`.

```text
SnapshotBase
 + ordered ORIGINS overlays
 = SnapshotOrigins
 -> import
 -> System.db
 -> reopen/preflight/index validation
```

Crystal spell catalogue changes belong to the magic overlay, but spell execution remains implemented by Zircon `MagicObject` classes.
