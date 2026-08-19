# ORIGINS-DxR database overlays

The canonical Zircon snapshot is the immutable base. ORIGINS-specific content changes may live here as small deterministic overlays and are applied in filename order only after the Zircon base has passed verification.

Pipeline:

```text
published Zircon System.db
  -> pinned Zircon runtime verification
  -> generated base snapshot (JSON)
  -> optional ORIGINS non-magic overlays
  -> ORIGINS snapshot
  -> Zircon-compatible importer
  -> System.db
  -> preflight validation
```

Rules:

- Never edit the downloaded/generated Zircon base snapshot by hand.
- Preserve existing `Index` values unless a deliberate migration requires otherwise.
- `upsert` modifies an existing row or creates a new row at the explicit index.
- `delete` removes an existing row but does not rewind the collection index.
- References use the exported Zircon reference shape.
- The four-class magic base is not replaced by an overlay: it comes directly from canonical Zircon `MagicInfo` data.
- No external spell catalogue is injected into this branch.
- Archer and Monk remain outside the active four-class scope.

The numbered files define dependency/application order. They intentionally start empty; real ORIGINS data is added only after the generated Zircon snapshot has passed validation.
