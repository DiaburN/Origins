#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/JevLOMCN/Crystal-Monk.git"
COMMIT="381e589e3d7ee736cdf0583c8315c0d144ab058f"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/vendor/crystal-monk"

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
  echo "ERROR: Crystal-Monk revision mismatch. Expected $COMMIT, got $ACTUAL" >&2
  exit 1
fi

echo "JevLOMCN/Crystal-Monk pinned at $ACTUAL"
