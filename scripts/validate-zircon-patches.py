#!/usr/bin/env python3
"""Validate the stored ORIGINS context-patch dialect.

ORIGINS patches are applied by exact source context. Historical files may carry
stale unified-diff line counts or use a bare `@@` separator, so those numeric
headers are advisory rather than authoritative. This validator checks the
structural rules required by `apply-origins-patches.py` without rejecting valid
context patches for stale line-number metadata. Raw empty lines are accepted as
hunk separators; real blank source context remains space-prefixed.
"""
from __future__ import annotations

import pathlib
import re
import sys

DIFF_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
HUNK_RE = re.compile(r"^@@(?: .*)?$")


def validate_patch(path: pathlib.Path) -> tuple[list[str], int]:
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    errors: list[str] = []
    target: str | None = None
    hunks = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        diff = DIFF_RE.match(line)
        if diff:
            if diff.group(1) != diff.group(2):
                errors.append(f"{path}:{i + 1}: renames are unsupported")
            target = diff.group(2)
            i += 1
            continue

        if not line.startswith("@@"):
            i += 1
            continue

        if target is None:
            errors.append(f"{path}:{i + 1}: hunk appears before diff header")
            i += 1
            continue
        if not HUNK_RE.match(line):
            errors.append(f"{path}:{i + 1}: malformed hunk separator: {line}")
            i += 1
            continue

        hunks += 1
        old_count = 0
        new_count = 0
        start = i + 1
        i += 1

        while i < len(lines):
            current = lines[i]
            if current.startswith("diff --git ") or current.startswith("@@"):
                break
            if current == r"\ No newline at end of file":
                i += 1
                continue
            if not current:
                i += 1
                break

            prefix = current[0]
            if prefix == " ":
                old_count += 1
                new_count += 1
            elif prefix == "-":
                old_count += 1
            elif prefix == "+":
                new_count += 1
            elif current.startswith("--- ") or current.startswith("+++ "):
                break
            else:
                errors.append(
                    f"{path}:{i + 1}: invalid hunk line prefix {prefix!r} in hunk beginning at line {start}"
                )
            i += 1

        if old_count == 0:
            errors.append(
                f"{path}:{start}: hunk has no old/context lines; anchorless insertion is unsupported"
            )
        if new_count == 0:
            errors.append(f"{path}:{start}: hunk would delete its entire anchored block")

    if hunks == 0:
        errors.append(f"{path}: contains no context hunks")
    return errors, hunks


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "patches/zircon")
    patches = sorted(root.glob("*.patch"))
    if not patches:
        print(f"No patch files found under {root}", file=sys.stderr)
        return 1

    errors: list[str] = []
    total_hunks = 0
    for patch in patches:
        patch_errors, hunks = validate_patch(patch)
        errors.extend(patch_errors)
        total_hunks += hunks

    if errors:
        print("Zircon context-patch syntax FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Zircon context-patch syntax OK: {len(patches)} patch files / {total_hunks} hunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
