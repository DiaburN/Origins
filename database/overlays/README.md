# ORIGINS database overlays

The generated Zircon snapshot is the immutable base. ORIGINS changes live here as small deterministic overlays and are applied in filename order.

Pipeline:

```text
published Zircon System.db
  -> current Zircon schema upgrade
  -> generated base snapshot (JSON)
  -> database/overlays/*.json
  -> ORIGINS snapshot
  -> current Zircon importer
  -> System.db
  -> preflight validation
```

Rules:

- Never edit the downloaded/generated base snapshot by hand.
- Preserve existing `Index` values unless a deliberate migration requires otherwise.
- `upsert` modifies an existing row or creates a new row at the explicit index.
- `delete` removes an existing row but does not rewind the collection index.
- References use the exported shape: `{"$refAssembly":"LibraryCore","$refType":"Library.SystemModels.ItemInfo","Index":123}`.
- Crystal spell content belongs in `70-magics-crystal.json`; combat execution still uses Zircon `MagicObject` handlers.
- Monk-specific content stays out until its item/stat phase is explicitly started.

The numbered files define dependency/application order. They intentionally start empty; real source data is added only after the generated Zircon snapshot has passed the full round-trip validation.
