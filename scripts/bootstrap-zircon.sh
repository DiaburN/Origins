#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/mir-ethernity/mir3-zircon.git"
COMMIT="820bf6d4a11d89cac7f87b81446567095f2e38b8"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/vendor/zircon"

mkdir -p "$ROOT/vendor"

if [ ! -d "$DEST/.git" ]; then
  rm -rf "$DEST"
  git clone --filter=blob:none --no-checkout "$REPO" "$DEST"
fi

git -C "$DEST" fetch --depth=1 origin "$COMMIT"
git -C "$DEST" checkout --detach "$COMMIT"

echo "Zircon pinned at $(git -C "$DEST" rev-parse HEAD)"
