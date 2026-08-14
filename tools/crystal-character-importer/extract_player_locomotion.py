#!/usr/bin/env python3
"""Extract and align Crystal/Mir2 player standing/walking/running frames.

Uses the already validated CrystalLib decoder from ORIGINS map tooling so Lib
v1 DXT1 and v2/v3 payloads are handled consistently.

The default source is Data/CArmour/00.Lib, male/common-class base offset 0.
No hair, weapon or effects are composited in this first movement proof.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools" / "crystal-map-importer" / "extract_theme_assets.py"
spec = importlib.util.spec_from_file_location("origins_crystal_lib", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
CLIPS = {
    "idle": {"start": 0, "count": 4, "interval_ms": 500},
    "walk": {"start": 32, "count": 6, "interval_ms": 100},
    "run": {"start": 80, "count": 6, "interval_ms": 100},
}


def composite_on_shared_canvas(items: List[dict]) -> None:
    min_x = min(item["offset_x"] for item in items)
    min_y = min(item["offset_y"] for item in items)
    max_x = max(item["offset_x"] + item["width"] for item in items)
    max_y = max(item["offset_y"] + item["height"] for item in items)

    canvas_w = max_x - min_x
    canvas_h = max_y - min_y

    for item in items:
        src = item.pop("_rgba")
        out = bytearray(canvas_w * canvas_h * 4)
        dx = item["offset_x"] - min_x
        dy = item["offset_y"] - min_y
        width = item["width"]
        height = item["height"]

        for y in range(height):
            src_start = y * width * 4
            dst_start = ((dy + y) * canvas_w + dx) * 4
            out[dst_start : dst_start + width * 4] = src[src_start : src_start + width * 4]

        item["canvas_width"] = canvas_w
        item["canvas_height"] = canvas_h
        item["origin_x"] = -min_x
        item["origin_y"] = -min_y
        item["_aligned_rgba"] = bytes(out)


def generate_preview(out_dir: Path, manifest: dict) -> None:
    data_json = json.dumps(manifest)
    page = f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>ORIGINS Crystal Player Locomotion</title>
<style>
html,body{{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif}}
body{{padding:20px}}
h1{{font-size:20px;margin:0 0 6px}}
p{{color:#aaa;margin:0 0 18px}}
.controls{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:18px}}
button,select{{background:#222;color:#eee;border:1px solid #555;border-radius:6px;padding:8px 10px}}
.stage-grid{{display:grid;grid-template-columns:repeat(3,minmax(180px,1fr));gap:14px}}
.card{{background:#1b1b1b;border:1px solid #333;border-radius:10px;padding:10px;text-align:center}}
.stage{{height:270px;display:flex;align-items:center;justify-content:center;background:repeating-conic-gradient(#252525 0 25%,#1d1d1d 0 50%) 50%/24px 24px;overflow:hidden}}
.stage img{{image-rendering:pixelated;transform:scale(2);transform-origin:center center}}
.label{{margin-top:8px;font-weight:700}}
.meta{{font-size:12px;color:#888}}
@media(max-width:700px){{.stage-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<h1>ORIGINS — Crystal player locomotion</h1>
<p>Real CArmour/00 frames, aligned using their .Lib offsets. No weapon/hair/effects yet.</p>
<div class=\"controls\">
<label>Direction <select id=\"direction\">{''.join(f'<option value="{i}">{d}</option>' for i,d in enumerate(DIRECTIONS))}</select></label>
<button id=\"play\">Pause</button>
</div>
<div class=\"stage-grid\" id=\"grid\"></div>
<script>
const manifest={data_json};
let playing=true;
let direction=0;
let clocks={{idle:0,walk:0,run:0}};
const grid=document.getElementById('grid');
const cards={{}};
for(const action of ['idle','walk','run']){{
  const card=document.createElement('div'); card.className='card';
  const stage=document.createElement('div'); stage.className='stage';
  const img=document.createElement('img'); stage.appendChild(img);
  const label=document.createElement('div'); label.className='label'; label.textContent=action.toUpperCase();
  const meta=document.createElement('div'); meta.className='meta';
  card.append(stage,label,meta); grid.appendChild(card);
  cards[action]={{img,meta}};
}}
function render(){{
  for(const action of ['idle','walk','run']){{
    const clip=manifest.clips[action];
    const frames=clip.directions[direction];
    const local=Math.floor(clocks[action]/clip.interval_ms)%frames.length;
    const frame=frames[local];
    cards[action].img.src=frame.png;
    cards[action].meta.textContent=`${{manifest.directions[direction]}} · source #${{frame.source_frame}} · ${{local+1}}/${{frames.length}}`;
  }}
}}
let last=performance.now();
function tick(now){{
  const dt=now-last; last=now;
  if(playing) for(const key of Object.keys(clocks)) clocks[key]+=dt;
  render(); requestAnimationFrame(tick);
}}
document.getElementById('direction').addEventListener('change',e=>{{direction=Number(e.target.value);clocks={{idle:0,walk:0,run:0}};render();}});
document.getElementById('play').addEventListener('click',e=>{{playing=!playing;e.target.textContent=playing?'Pause':'Play';}});
render(); requestAnimationFrame(tick);
</script>
</body></html>"""
    (out_dir / "preview.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lib", required=True, type=Path, help="Crystal Data/CArmour/00.Lib")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--base-offset", type=int, default=0, help="Frame offset before Crystal locomotion layout")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    lib = base.CrystalLib(args.lib)
    manifest: Dict[str, object] = {
        "source_library": args.lib.name,
        "source_path": str(args.lib),
        "base_offset": args.base_offset,
        "directions": DIRECTIONS,
        "clips": {},
    }

    all_items: List[dict] = []
    try:
        for action, clip in CLIPS.items():
            action_data = {
                "start": clip["start"],
                "count": clip["count"],
                "interval_ms": clip["interval_ms"],
                "directions": [],
            }
            for direction_index, direction_name in enumerate(DIRECTIONS):
                direction_frames = []
                for local_frame in range(clip["count"]):
                    frame_id = args.base_offset + clip["start"] + direction_index * clip["count"] + local_frame
                    width, height, x, y, sx, sy, shadow, rgba = lib.extract(frame_id)
                    item = {
                        "action": action,
                        "direction": direction_name,
                        "direction_index": direction_index,
                        "local_frame": local_frame,
                        "source_frame": frame_id,
                        "width": width,
                        "height": height,
                        "offset_x": x,
                        "offset_y": y,
                        "shadow_x": sx,
                        "shadow_y": sy,
                        "shadow": shadow,
                        "_rgba": rgba,
                    }
                    direction_frames.append(item)
                    all_items.append(item)
                action_data["directions"].append(direction_frames)
            manifest["clips"][action] = action_data
    finally:
        lib.close()

    # Use one shared canvas across every locomotion frame. This proves offsets
    # visually and prevents apparent sprite jitter from different PNG crops.
    composite_on_shared_canvas(all_items)

    for item in all_items:
        action = item["action"]
        direction = item["direction"]
        local = item["local_frame"]
        png_path = args.out / "frames" / action / direction / f"{local:02d}.png"
        base.write_rgba_png(
            png_path,
            item["canvas_width"],
            item["canvas_height"],
            item.pop("_aligned_rgba"),
        )
        item["png"] = png_path.relative_to(args.out).as_posix()

    # Remove private extraction-only values before serializing.
    clean_manifest = json.loads(json.dumps(manifest, default=lambda _: None))
    for action in clean_manifest["clips"].values():
        for direction_frames in action["directions"]:
            for item in direction_frames:
                item.pop("_rgba", None)
                item.pop("_aligned_rgba", None)

    (args.out / "manifest.json").write_text(json.dumps(clean_manifest, indent=2), encoding="utf-8")
    generate_preview(args.out, clean_manifest)
    print(f"Extracted {len(all_items)} locomotion frames from {args.lib}")
    print(f"Open {args.out / 'preview.html'}")


if __name__ == "__main__":
    main()
