# Zircon geometry resolver v2

Current source-geometry validation found a resolver-order bug: root tokens such as `Size.Width` were being replaced inside named-control expressions such as `CloseButton.Size.Width` before the named control could be resolved.

The v2 target resolves named controls first, then root `Size` / `DisplayArea` / `ClientArea` tokens. Local validation reduced suspicious non-zero source locations falling back to `(0,0)` from 331 to 61 out of 742 controls with explicit `Location`.

This note is temporary provenance for the geometry hardening pass and must not be treated as a replacement for the executable resolver or CI validation.
