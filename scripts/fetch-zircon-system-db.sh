#!/usr/bin/env bash
set -euo pipefail

URL="https://files.lomcn.co.uk/resources/mir3/zircon/Database.7z"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="$ROOT/.cache/zircon-database"
ARCHIVE="$CACHE/Database.7z"
EXTRACTED="$CACHE/extracted"
DEST="$ROOT/Database"

command -v curl >/dev/null 2>&1 || { echo "curl is required" >&2; exit 1; }

SEVEN_ZIP=""
for candidate in 7zz 7z; do
  if command -v "$candidate" >/dev/null 2>&1; then
    SEVEN_ZIP="$candidate"
    break
  fi
done

if [ -z "$SEVEN_ZIP" ]; then
  echo "7-Zip is required (7zz or 7z on PATH)." >&2
  exit 1
fi

mkdir -p "$CACHE" "$DEST"
rm -rf "$EXTRACTED"
mkdir -p "$EXTRACTED"

curl --fail --location --retry 3 --output "$ARCHIVE" "$URL"

echo "Archive source: $URL"
echo "Archive SHA-256:"
sha256sum "$ARCHIVE" || shasum -a 256 "$ARCHIVE"

"$SEVEN_ZIP" x -y -o"$EXTRACTED" "$ARCHIVE" >/dev/null

SYSTEM_DB="$(find "$EXTRACTED" -type f -iname 'System.db' -print -quit)"
if [ -z "$SYSTEM_DB" ]; then
  echo "System.db was not found inside Database.7z" >&2
  exit 1
fi

cp "$SYSTEM_DB" "$DEST/System.db"
echo "Installed candidate Zircon System.db -> $DEST/System.db"
echo "The file has NOT been rewritten or upgraded. Run the verifier next:"
echo "dotnet run --project tools/Origins.Database.Verify/Origins.Database.Verify.csproj -- '$DEST'"
