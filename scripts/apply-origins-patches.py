#!/usr/bin/env python3
"""Apply ORIGINS context patches to a pinned Zircon checkout.

Several historical ORIGINS .patch files were authored as context patches rather
than strict unified diffs: their @@ line counts may be stale and some hunks use
bare @@ separators. `git apply` rejects those files before it can evaluate the
actual code context.

This applicator deliberately ignores hunk line-number/count metadata and applies
each change by its exact old-context block. It is strict in the ways that matter:

- every hunk must identify exactly one existing source block;
- ambiguous or missing source context is fatal;
- no fuzzy/whitespace matching is performed;
- patches are processed in deterministic filename order;
- unprefixed blank separator lines terminate the current hunk;
- --check validates the complete series without writing files.

That makes the stored patches deterministic against the pinned Zircon revision
while preserving their intended source edits verbatim.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import pathlib
import re
import sys

DIFF_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
HUNK_RE = re.compile(r"^@@(?: .*)?$")


@dataclass
class Hunk:
    patch_path: pathlib.Path
    target_path: str
    header: str
    old_lines: list[str]
    new_lines: list[str]


def parse_patch(path: pathlib.Path) -> list[Hunk]:
    lines = path.read_text(encoding="utf-8").splitlines()
    hunks: list[Hunk] = []
    target: str | None = None
    i = 0

    while i < len(lines):
        line = lines[i]
        diff = DIFF_RE.match(line)
        if diff:
            if diff.group(1) != diff.group(2):
                raise RuntimeError(f"{path}:{i + 1}: renames are not supported")
            target = diff.group(2)
            i += 1
            continue

        if line.startswith("@@"):
            if target is None:
                raise RuntimeError(f"{path}:{i + 1}: hunk appears before a diff header")
            if not HUNK_RE.match(line):
                raise RuntimeError(f"{path}:{i + 1}: malformed hunk separator {line!r}")

            header = line
            old_lines: list[str] = []
            new_lines: list[str] = []
            i += 1

            while i < len(lines):
                current = lines[i]
                if current.startswith("diff --git ") or current.startswith("@@"):
                    break
                if current == r"\ No newline at end of file":
                    i += 1
                    continue

                # Some historical context patches use a raw blank line only to
                # separate a hunk from the next file diff. It is not source
                # context because real blank context is stored as a single-space
                # prefixed line, like a normal unified diff.
                if not current:
                    i += 1
                    break

                prefix, payload = current[0], current[1:]
                if prefix == " ":
                    old_lines.append(payload)
                    new_lines.append(payload)
                elif prefix == "-":
                    old_lines.append(payload)
                elif prefix == "+":
                    new_lines.append(payload)
                elif current.startswith("--- ") or current.startswith("+++ "):
                    break
                else:
                    raise RuntimeError(
                        f"{path}:{i + 1}: invalid hunk line prefix {prefix!r}"
                    )
                i += 1

            if not old_lines:
                raise RuntimeError(
                    f"{path}: hunk {header!r} for {target} has no old/context lines; "
                    "anchorless insertions are intentionally unsupported"
                )
            hunks.append(Hunk(path, target, header, old_lines, new_lines))
            continue

        i += 1

    if not hunks:
        raise RuntimeError(f"{path}: no context hunks found")
    return hunks


def find_occurrences(haystack: list[str], needle: list[str]) -> list[int]:
    width = len(needle)
    if width == 0 or width > len(haystack):
        return []
    return [i for i in range(len(haystack) - width + 1) if haystack[i:i + width] == needle]


def apply_hunks(root: pathlib.Path, hunks: list[Hunk], check_only: bool) -> int:
    cache: dict[pathlib.Path, tuple[list[str], bool]] = {}
    applied = 0

    for hunk in hunks:
        target = root / hunk.target_path
        if not target.is_file():
            raise RuntimeError(f"{hunk.patch_path}: target does not exist: {hunk.target_path}")

        if target not in cache:
            raw = target.read_text(encoding="utf-8-sig")
            cache[target] = (raw.splitlines(), raw.endswith("\n"))

        current, had_final_newline = cache[target]
        matches = find_occurrences(current, hunk.old_lines)
        if len(matches) != 1:
            detail = "not found" if not matches else f"ambiguous ({len(matches)} matches)"
            preview = "\n".join(hunk.old_lines[:6])
            raise RuntimeError(
                f"{hunk.patch_path}: {hunk.target_path} {hunk.header}: source context {detail}.\n"
                f"Old-context preview:\n{preview}"
            )

        start = matches[0]
        current[start:start + len(hunk.old_lines)] = hunk.new_lines
        cache[target] = (current, had_final_newline)
        applied += 1

    if not check_only:
        for target, (lines, had_final_newline) in cache.items():
            text = "\n".join(lines)
            if had_final_newline:
                text += "\n"
            target.write_text(text, encoding="utf-8")

    return applied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zircon_root", type=pathlib.Path)
    parser.add_argument("patch_dir", type=pathlib.Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    patches = sorted(args.patch_dir.glob("*.patch"))
    if not patches:
        raise SystemExit(f"No .patch files found under {args.patch_dir}")

    all_hunks: list[Hunk] = []
    try:
        for patch in patches:
            parsed = parse_patch(patch)
            all_hunks.extend(parsed)
            print(f"Parsed ORIGINS patch: {patch.name} ({len(parsed)} hunks)")

        count = apply_hunks(args.zircon_root, all_hunks, args.check)
    except RuntimeError as exc:
        print(f"ORIGINS patch application FAILED: {exc}", file=sys.stderr)
        return 1

    mode = "validated" if args.check else "applied"
    print(f"ORIGINS patch series {mode}: {len(patches)} patches / {count} exact-context hunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
