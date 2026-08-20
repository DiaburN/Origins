#!/usr/bin/env python3
# Shared ORIGINS-DxR player-asset CI retrigger: 2026-08-20.
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

OLD_BLOCK = r'''                SquishFlags flags = codec == ZlImageCodec.Dxt1 ? SquishFlags.Dxt1 : SquishFlags.Dxt5;
                int expectedSize = Squish.GetStorageRequirements(width, height, flags);
                if (bytes.Length < expectedSize)
                {
                    byte[] padded = new byte[expectedSize];
                    Buffer.BlockCopy(bytes, 0, padded, 0, bytes.Length);
                    bytes = padded;
                }

                fixed (byte* source = bytes)
                    Squish.DecompressImage(data.Scan0, width, height, (IntPtr)source, flags);

                byte* dest = (byte*)data.Scan0;

                for (int i = 0; i < height * width * 4; i += 4)
                {
                    byte b = dest[i];
                    dest[i] = dest[i + 2];
                    dest[i + 2] = b;
                }

                bitmap.UnlockBits(data);
                return bitmap;'''

NEW_BLOCK = r'''                bitmap.UnlockBits(data);
                bitmap.Dispose();

                CompressionFormat format = codec == ZlImageCodec.Dxt1 ? CompressionFormat.Bc1 : CompressionFormat.Bc3;
                return DecodeManagedBc(bytes, width, height, format);'''

MARKER = r'''            private static Bitmap DecodeBc7(byte[] bytes, int width, int height)
            {'''

HELPER = r'''            private static Bitmap DecodeManagedBc(byte[] bytes, int width, int height, CompressionFormat format)
            {
                int bytesPerBlock = format == CompressionFormat.Bc1 ? 8 : 16;
                int expectedSize = ((width + 3) / 4) * ((height + 3) / 4) * bytesPerBlock;
                if (bytes.Length < expectedSize)
                {
                    byte[] padded = new byte[expectedSize];
                    Buffer.BlockCopy(bytes, 0, padded, 0, bytes.Length);
                    bytes = padded;
                }

                BcDecoder decoder = new BcDecoder();
                ColorRgba32[] rgbaPixels = decoder.DecodeRaw(bytes, width, height, format);
                byte[] bgraPixels = new byte[width * height * 4];

                for (int i = 0; i < rgbaPixels.Length; i++)
                {
                    int offset = i * 4;
                    ColorRgba32 pixel = rgbaPixels[i];
                    bgraPixels[offset] = pixel.b;
                    bgraPixels[offset + 1] = pixel.g;
                    bgraPixels[offset + 2] = pixel.r;
                    bgraPixels[offset + 3] = pixel.a;
                }

                Bitmap bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
                BitmapData data = bitmap.LockBits(new Rectangle(0, 0, width, height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);

                try
                {
                    int rowBytes = width * 4;
                    for (int y = 0; y < height; y++)
                        Marshal.Copy(bgraPixels, y * rowBytes, IntPtr.Add(data.Scan0, y * data.Stride), rowBytes);
                }
                finally
                {
                    bitmap.UnlockBits(data);
                }

                return bitmap;
            }

'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zircon-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    root = Path(args.zircon_root)
    source = root / "LibraryEditor" / "Mir3Library.cs"
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not source.is_file():
        raise SystemExit(f"Missing pinned Zircon source: {source}")

    before = sha256(source)
    text = source.read_text(encoding="utf-8-sig")

    # Bootstrap already pins the exact Zircon commit. These narrow source-contract
    # checks make the transient exporter-only patch fail closed if upstream layout changes.
    if OLD_BLOCK not in text:
        raise SystemExit("Pinned Zircon DXT decode block no longer matches expected source contract.")
    if MARKER not in text:
        raise SystemExit("Pinned Zircon DecodeBc7 marker not found.")
    if "using BCnEncoder.Shared;" not in text or "using BcDecoder = BCnEncoder.Decoder.BcDecoder;" not in text:
        raise SystemExit("Pinned Zircon no longer exposes the managed BCnEncoder decoder contract expected by exporter tooling.")

    patched = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    patched = patched.replace(MARKER, HELPER + MARKER, 1)
    source.write_text(patched, encoding="utf-8-sig")
    after = sha256(source)

    report = {
        "schema": "origins.zircon.exporter-managed-dxt-patch.v1",
        "status": "PASS",
        "scope": "transient-vendor-tooling-only",
        "source": "LibraryEditor/Mir3Library.cs",
        "sourceSha256Before": before,
        "sourceSha256After": after,
        "decoder": {
            "Dxt1": "BCnEncoder.Net CompressionFormat.Bc1",
            "Dxt5": "BCnEncoder.Net CompressionFormat.Bc3",
            "nativeSquishRequiredForDecode": False
        }
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
