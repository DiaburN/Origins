#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/Suprcode/Crystal.git"
COMMIT="0e315fe327192afe52c3d7357ddd1f5b7e26c5b8"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/vendor/crystal"

mkdir -p "$ROOT/vendor"

if [ ! -d "$DEST/.git" ]; then
  rm -rf "$DEST"
  git clone --filter=blob:none --no-checkout "$REPO" "$DEST"
fi

git -C "$DEST" remote set-url origin "$REPO"
git -C "$DEST" fetch --depth=1 origin "$COMMIT"
git -C "$DEST" checkout --detach "$COMMIT"

ACTUAL="$(git -C "$DEST" rev-parse HEAD)"
if [ "$ACTUAL" != "$COMMIT" ]; then
  echo "ERROR: Crystal revision mismatch. Expected $COMMIT, got $ACTUAL" >&2
  exit 1
fi

echo "Official Suprcode/Crystal pinned at $ACTUAL"
