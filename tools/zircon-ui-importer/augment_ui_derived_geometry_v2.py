#!/usr/bin/env python3
"""Compatibility runner for the hardened derived-geometry pass."""
import re
import augment_ui_derived_geometry as derived

# v1 accepted named constants only. Zircon also uses direct numeric GetSize
# calls such as GameInter2Library.GetSize(500) in MilestoneAchievedDialog.
derived.GET_SIZE_LOCAL_RE = re.compile(
    r"(?:var|Size)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\??\.GetSize\s*\(\s*([A-Za-z_][A-Za-z0-9_]*|\d+)\s*\)",
    re.S,
)

derived.main()
