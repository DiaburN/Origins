#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/Suprcode/Zircon.git"
COMMIT="cbf1aa919083bc13fc3f23f93772a8ab8370632d"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/vendor/zircon"
OVERRIDES="$ROOT/overrides/zircon"
PATCHES="$ROOT/patches/zircon"

mkdir -p "$ROOT/vendor"

if [ ! -d "$DEST/.git" ]; then
  rm -rf "$DEST"
  git clone --filter=blob:none --no-checkout "$REPO" "$DEST"
fi

git -C "$DEST" remote set-url origin "$REPO"
git -C "$DEST" fetch --depth=1 origin "$COMMIT"
git -C "$DEST" checkout --detach --force "$COMMIT"
git -C "$DEST" clean -fd

ACTUAL="$(git -C "$DEST" rev-parse HEAD)"
if [ "$ACTUAL" != "$COMMIT" ]; then
  echo "ERROR: Zircon revision mismatch. Expected $COMMIT, got $ACTUAL" >&2
  exit 1
fi

if [ -d "$OVERRIDES" ]; then
  while IFS= read -r -d '' source; do
    relative="${source#"$OVERRIDES/"}"
    target="$DEST/$relative"
    mkdir -p "$(dirname "$target")"
    cp "$source" "$target"
    echo "Applied ORIGINS Zircon override: $relative"
  done < <(find "$OVERRIDES" -type f ! -name 'README.md' -print0 | sort -z)
fi

if [ -d "$PATCHES" ]; then
  # Parse every patch before applying the first one. This catches malformed
  # unified-diff hunk counts in a single CI run instead of failing one patch
  # at a time during the sequential context/application pass below.
  syntax_fail=0
  while IFS= read -r -d '' patch; do
    relative="${patch#"$ROOT/"}"
    err_file="$(mktemp)"
    if ! git -C "$DEST" apply --numstat "$patch" >/dev/null 2>"$err_file"; then
      echo "ERROR: malformed ORIGINS Zircon patch: $relative" >&2
      sed 's/^/  /' "$err_file" >&2
      syntax_fail=1
    fi
    rm -f "$err_file"
  done < <(find "$PATCHES" -type f -name '*.patch' -print0 | sort -z)

  if [ "$syntax_fail" -ne 0 ]; then
    echo "ERROR: one or more ORIGINS Zircon patches failed syntax preflight" >&2
    exit 1
  fi

  while IFS= read -r -d '' patch; do
    relative="${patch#"$ROOT/"}"
    git -C "$DEST" apply --check "$patch"
    git -C "$DEST" apply --whitespace=nowarn "$patch"
    echo "Applied ORIGINS Zircon patch: $relative"
  done < <(find "$PATCHES" -type f -name '*.patch' -print0 | sort -z)
fi

echo "Official Suprcode/Zircon pinned at $ACTUAL with ORIGINS overrides/patches applied"
