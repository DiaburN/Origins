#!/usr/bin/env python3
"""Validate unified-diff hunk line counts for every ORIGINS Zircon patch.

This intentionally runs without a Zircon checkout. It catches malformed @@ hunk
headers before bootstrap-zircon.sh reaches git apply, so a whole patch series can
be audited in one pass instead of failing one malformed file at a time.
"""
from __future__ import annotations

import pathlib
import re
import sys

HUNK = re.compile(
    r"^@@ -(?:\d+)(?:,(\d+))? \+(?:\d+)(?:,(\d+))? @@(?:.*)$"
)


def validate_patch(path: pathlib.Path) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    errors: list[str] = []
    i = 0
    hunks = 0

    while i < len(lines):
        line = lines[i]
        if not line.startswith("@@ "):
            i += 1
            continue

        match = HUNK.match(line)
        if not match:
            errors.append(f"{path}:{i + 1}: malformed hunk header: {line}")
            i += 1
            continue

        hunks += 1
        expected_old = int(match.group(1) or "1")
        expected_new = int(match.group(2) or "1")
        old_count = 0
        new_count = 0
        start_line = i + 1
        i += 1

        while i < len(lines):
            current = lines[i]
            if current.startswith("@@ ") or current.startswith("diff --git "):
                break
            if current.startswith("--- ") or current.startswith("+++ "):
                # File headers belong between diffs/hunks, never inside a hunk.
                break
            if current == r"\ No newline at end of file":
                i += 1
                continue
            if not current:
                errors.append(
                    f"{path}:{i + 1}: unprefixed empty line inside hunk beginning at line {start_line}"
                )
                i += 1
                continue

            prefix = current[0]
            if prefix == " ":
                old_count += 1
                new_count += 1
            elif prefix == "-":
                old_count += 1
            elif prefix == "+":
                new_count += 1
            else:
                errors.append(
                    f"{path}:{i + 1}: invalid hunk line prefix {prefix!r} in hunk beginning at line {start_line}"
                )
            i += 1

        if old_count != expected_old or new_count != expected_new:
            errors.append(
                f"{path}:{start_line}: hunk count mismatch: "
                f"header old/new={expected_old}/{expected_new}, "
                f"actual old/new={old_count}/{new_count}"
            )

    if hunks == 0:
        errors.append(f"{path}: contains no unified-diff hunks")
    return errors


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "patches/zircon")
    patches = sorted(root.glob("*.patch"))
    if not patches:
        print(f"No patch files found under {root}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for patch in patches:
        errors.extend(validate_patch(patch))

    if errors:
        print("Zircon patch syntax FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Zircon patch syntax OK: {len(patches)} patch files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
