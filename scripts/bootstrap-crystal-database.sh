#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/Suprcode/Crystal.Database.git"
COMMIT="a19f6dca8f5e238d4ed79801820777abbf0a9ca4"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="$ROOT/.cache/crystal-database-source"
DEST="$ROOT/vendor/crystal-database/Jev"

mkdir -p "$ROOT/.cache" "$DEST"

if [ ! -d "$CACHE/.git" ]; then
  rm -rf "$CACHE"
  git clone --filter=blob:none --no-checkout "$REPO" "$CACHE"
fi

git -C "$CACHE" remote set-url origin "$REPO"
git -C "$CACHE" fetch --depth=1 origin "$COMMIT"

ACTUAL="$(git -C "$CACHE" rev-parse FETCH_HEAD)"
if [ "$ACTUAL" != "$COMMIT" ]; then
  echo "ERROR: Crystal.Database revision mismatch. Expected $COMMIT, got $ACTUAL" >&2
  exit 1
fi

git -C "$CACHE" show "$COMMIT:Jev/Server.MirDB" > "$DEST/Server.MirDB"
git -C "$CACHE" show "$COMMIT:Jev/README.md" > "$DEST/README.md"

if [ ! -s "$DEST/Server.MirDB" ]; then
  echo "ERROR: Jev/Server.MirDB was not extracted" >&2
  exit 1
fi

echo "Crystal.Database/Jev pinned at $ACTUAL"
echo "Jev Server.MirDB SHA-256:"
sha256sum "$DEST/Server.MirDB" || shasum -a 256 "$DEST/Server.MirDB"
