#!/usr/bin/env python3
"""Run the pinned Crystal magic catalogue generator with comment-safe parsing.

The upstream Crystal FillMagicInfoList contains a commented placeholder for
FastMove with unknown `?` values. The historical generator's regex sees that
comment as a real `if (!MagicExists(...))` initializer. This wrapper masks C#
comments before initializer extraction while preserving strings and newlines,
so commented placeholders can never become database numerics.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys


def mask_csharp_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    in_string = False
    verbatim_string = False
    escaped = False
    line_comment = False
    block_comment = False

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if line_comment:
            if ch == "\n":
                line_comment = False
                out.append(ch)
            else:
                out.append(" ")
            i += 1
            continue

        if block_comment:
            if ch == "*" and nxt == "/":
                out.extend((" ", " "))
                block_comment = False
                i += 2
                continue
            out.append("\n" if ch == "\n" else " ")
            i += 1
            continue

        if in_string:
            out.append(ch)
            if verbatim_string:
                if ch == '"' and nxt == '"':
                    out.append(nxt)
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                    verbatim_string = False
            else:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            i += 1
            continue

        if ch == "@" and nxt == '"':
            out.extend((ch, nxt))
            in_string = True
            verbatim_string = True
            i += 2
            continue

        if ch == '"':
            out.append(ch)
            in_string = True
            i += 1
            continue

        if ch == "/" and nxt == "/":
            out.extend((" ", " "))
            line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            out.extend((" ", " "))
            block_comment = True
            i += 2
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def main() -> int:
    implementation = pathlib.Path(__file__).with_name("generate-crystal-magic-catalog.py")
    spec = importlib.util.spec_from_file_location("origins_crystal_magic_catalog", implementation)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load generator implementation: {implementation}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    original_extract = module.extract_magic_initializers

    def comment_safe_extract(fill_body: str):
        return original_extract(mask_csharp_comments(fill_body))

    module.extract_magic_initializers = comment_safe_extract
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
