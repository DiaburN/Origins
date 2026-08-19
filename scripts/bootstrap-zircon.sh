#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/Suprcode/Zircon.git"
COMMIT="cbf1aa919083bc13fc3f23f93772a8ab8370632d"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/vendor/zircon"
OVERRIDES="$ROOT/overrides/zircon"

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

echo "Official Suprcode/Zircon pinned at $ACTUAL with ORIGINS overrides applied"
