#!/usr/bin/env python3
"""ORIGINS HPR -> ZIRCON MASTER BUILDER.

This program deliberately separates:
  A) VISUAL DATA: HPR FrameSet, image IDs, offsets, timing, directions.
  B) SERVER BEHAVIOUR: Race/AI/damage/projectile/heal/stats.

It consumes the proven ORIGINS HPR analyzer output and creates a global master
sheet plus deterministic per-monster Cursor instructions. It can also create an
index-preserving Zircon legacy .Zl from exported RGBA PNG frames.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from zl_writer import ZlWriterError, build_legacy_zl, discover_pngs


TOOL_VERSION = "1.0.0"
REVIEW_PREFIXES = ("REVIEW", "SPECIAL")
STRUCTURAL_ACTIONS = {
    "standing": "Standing",
    "walking": "Moving",
    "running": "Moving",
    "pushed": "Pushed",
    "struck": "Struck",
    "die": "Die",
    "dead": "Dead",
    "revive": "Revive",
}


class BuilderError(RuntimeError):
    pass


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def as_int(v: Any, default=0) -> int:
    try:
        if v is None or str(v).strip() == "":
            return default
        return int(float(v))
    except (TypeError, ValueError):
        return default


def as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "y", "si", "sí")


def natural_key(text: str):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", str(text))]


def monster_id_from_path(path: Path) -> str:
    # Prefer folder names such as 1829, HPR_1829, MONSTER_1829.
    for part in reversed(path.parts):
        m = re.search(r"(?:^|[^0-9])(\d{1,6})(?:$|[^0-9])", part)
        if m:
            return m.group(1).zfill(3) if len(m.group(1)) < 3 else m.group(1)
    return path.stem


def _first(obj: Dict[str, Any], *keys: str, default=None):
    for k in keys:
        if k in obj:
            return obj[k]
    # insensitive fallback
    norm = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in obj.items()}
    for k in keys:
        nk = re.sub(r"[^a-z0-9]", "", k.lower())
        if nk in norm:
            return norm[nk]
    return default


def normalize_action(a: Dict[str, Any], ordinal: int = 0) -> Dict[str, Any]:
    name = str(_first(a, "visual_action", "action", "name", "frameset", default=f"Action{ordinal}"))
    zircon = str(_first(a, "zircon_animation_slot", "zircon_slot", "mir_animation", default=""))
    start = as_int(_first(a, "start", "start_index", "startindex"), 0)
    count = as_int(_first(a, "count", "frame_count", "framecount"), 0)
    stride = as_int(_first(a, "stride", "direction_stride", "offset", "skip_stride"), count)
    delay = as_int(_first(a, "delay_ms", "delay", "interval"), 100)
    reverse = as_bool(_first(a, "reverse", "reversed", default=False))
    semantic = str(_first(a, "semantic", default=""))
    semantic_source = str(_first(a, "semantic_source", default=""))
    holley = str(_first(a, "holley_name", default=""))
    return {
        "visual_action": name,
        "zircon_animation_slot": zircon,
        "start": start,
        "count": count,
        "stride": stride,
        "delay_ms": delay,
        "reverse": reverse,
        "semantic": semantic,
        "semantic_source": semantic_source,
        "holley_name": holley,
    }


def actions_from_profile(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = _first(profile, "actions", "animations", "frames", default=[])
    if isinstance(raw, dict):
        converted = []
        for name, spec in raw.items():
            if isinstance(spec, dict):
                x = dict(spec)
                x.setdefault("visual_action", name)
                converted.append(x)
        raw = converted
    if not isinstance(raw, list):
        return []
    return [normalize_action(x, i) for i, x in enumerate(raw) if isinstance(x, dict)]


def profile_candidates(root: Path) -> List[Path]:
    # CURSOR_PROFILE is preferred. If the global manifest is provided, caller
    # should use master_from_manifest instead.
    return sorted(root.rglob("CURSOR_PROFILE.json"), key=lambda p: natural_key(str(p)))


def find_related(profile_path: Path, filename: str) -> Optional[Path]:
    # Same folder first; then parent/child nearby.
    direct = profile_path.parent / filename
    if direct.exists():
        return direct
    for p in profile_path.parent.rglob(filename):
        return p
    return None


def find_frames_dir(monster_root: Path) -> Optional[Path]:
    preferred = [
        "FRAMES_PNG", "FRAMES", "PNG", "IMAGES", "IMAGES_PNG", "EXTRACTED_PNG"
    ]
    for name in preferred:
        p = monster_root / name
        if p.is_dir() and any(p.rglob("*.png")):
            return p
    # Search one level down but reject preview/direction-only folders.
    for p in monster_root.iterdir() if monster_root.exists() else []:
        if not p.is_dir():
            continue
        n = p.name.lower()
        if "preview" in n or "direction" in n or "contact" in n or "gif" in n:
            continue
        if any(p.rglob("*.png")):
            return p
    return None


def normalize_ranges(v: Any) -> List[Dict[str, int]]:
    if not isinstance(v, list):
        return []
    out = []
    for x in v:
        if not isinstance(x, dict):
            continue
        s = as_int(_first(x, "start"), -1)
        e = as_int(_first(x, "end"), -1)
        c = as_int(_first(x, "count"), (e - s + 1) if s >= 0 and e >= s else 0)
        if s >= 0:
            out.append({"start": s, "end": e, "count": c})
    return out


def record_from_profile(profile_path: Path) -> Dict[str, Any]:
    p = read_json(profile_path, {}) or {}
    mid = str(_first(p, "hpr", "id", "monster_id", default=monster_id_from_path(profile_path.parent)))
    status = str(_first(p, "status", default="UNKNOWN"))
    actions = actions_from_profile(p)
    issues = _first(p, "issues", default=[]) or []
    warnings = _first(p, "warnings", default=[]) or []
    unr = normalize_ranges(_first(p, "unreferenced_nonempty_ranges", "unreferenced_ranges", default=[]))
    metadata = find_related(profile_path, "IMAGE_METADATA.csv")
    frames_dir = find_frames_dir(profile_path.parent)
    return {
        "hpr": mid,
        "status": status,
        "slot_count": as_int(_first(p, "slot_count", "image_count", "slots"), 0),
        "nonempty_image_count": as_int(_first(p, "nonempty_image_count", "present_count", "images_nonempty"), 0),
        "actions": actions,
        "unreferenced_nonempty_ranges": unr,
        "issues": [str(x) for x in issues],
        "warnings": [str(x) for x in warnings],
        "profile_path": str(profile_path),
        "monster_root": str(profile_path.parent),
        "metadata_path": str(metadata) if metadata else "",
        "frames_dir": str(frames_dir) if frames_dir else "",
    }


def records_from_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    data = read_json(manifest_path, [])
    if isinstance(data, dict):
        data = data.get("monsters", data.get("items", data.get("libraries", [])))
    if not isinstance(data, list):
        raise BuilderError(f"Manifest no reconocido: {manifest_path}")
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        mid = str(_first(item, "hpr", "id", "monster_id", default=""))
        result.append({
            "hpr": mid,
            "status": str(_first(item, "status", default="UNKNOWN")),
            "slot_count": as_int(_first(item, "slot_count", "image_count", "slots"), 0),
            "nonempty_image_count": as_int(_first(item, "nonempty_image_count", "present_count"), 0),
            "actions": actions_from_profile(item),
            "unreferenced_nonempty_ranges": normalize_ranges(_first(item, "unreferenced_nonempty_ranges", default=[])),
            "issues": [str(x) for x in (_first(item, "issues", default=[]) or [])],
            "warnings": [str(x) for x in (_first(item, "warnings", default=[]) or [])],
            "profile_path": "",
            "monster_root": "",
            "metadata_path": "",
            "frames_dir": "",
        })
    return result


def status_needs_review(status: str) -> bool:
    s = status.upper()
    return s.startswith(REVIEW_PREFIXES) or s in ("INVALID", "PARTIAL", "UNKNOWN")


def action_summary(actions: Sequence[Dict[str, Any]]) -> str:
    parts = []
    for a in actions:
        rev = "R" if a.get("reverse") else ""
        parts.append(
            f"{a.get('visual_action')}:{a.get('start')}+{a.get('count')}/s{a.get('stride')}/{a.get('delay_ms')}ms{rev}"
        )
    return " | ".join(parts)


def range_summary(ranges: Sequence[Dict[str, int]]) -> str:
    return ", ".join(f"{r['start']}-{r['end']}({r['count']})" for r in ranges)


def make_cursor_text(rec: Dict[str, Any], built_zl: Optional[str] = None) -> str:
    mid = rec["hpr"]
    actions = rec.get("actions", [])
    lines = [
        f"# CURSOR IMPORT - HISPA HPR {mid}",
        "",
        "## REGLA PRINCIPAL",
        "Este paquete describe el VISUAL del monstruo. No deduzcas AI, daño, rango, heal ni proyectiles desde Attack/AttackRange/Spell/Special.",
        "",
        f"- Status: `{rec.get('status','UNKNOWN')}`",
        f"- Slot count: `{rec.get('slot_count',0)}`",
        f"- Imagenes no vacias: `{rec.get('nonempty_image_count',0)}`",
    ]
    if built_zl:
        lines.append(f"- Libreria construida: `{built_zl}`")
    lines += [
        "",
        "## FRAMESET VISUAL EXACTO",
        "",
        "| Visual | Zircon slot | Start | Count | OffSet/Stride | Delay | Reverse | Semantic | Source |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for a in actions:
        lines.append(
            f"| {a['visual_action']} | {a.get('zircon_animation_slot','')} | {a['start']} | {a['count']} | {a['stride']} | {a['delay_ms']} ms | {str(a['reverse']).lower()} | {a.get('semantic','')} | {a.get('semantic_source','')} |"
        )
    lines += [
        "",
        "## INSTRUCCIONES CLIENTE",
        "1. NO modificar `FrameSet.DefaultMonster`.",
        "2. Registrar un FrameSet aislado para este MonsterImage/ID.",
        "3. `Frame.OffSet` debe ser exactamente el `stride` de la tabla.",
        "4. Mantener StartIndex porque la .Zl conserva IDs originales.",
        "5. Mantener X/Y de IMAGE_METADATA.csv.",
        "6. No reasignar automaticamente frames no referenciados; pueden ser FX/proyectiles/overlays.",
        "7. La direccion/orden debe respetar el perfil HPR; no corregir visualmente a ojo sin comparar todas las vistas.",
        "",
        "## SERVIDOR",
        "Race/AI/stats/daño/rango/heal/proyectil se configuran por separado. Un nombre visual `AttackRange1` NO demuestra ataque a distancia.",
    ]
    if rec.get("unreferenced_nonempty_ranges"):
        lines += ["", "## FRAMES NO REFERENCIADOS", range_summary(rec["unreferenced_nonempty_ranges"])]
    if rec.get("issues"):
        lines += ["", "## ISSUES", *[f"- {x}" for x in rec["issues"]]]
    if rec.get("warnings"):
        lines += ["", "## WARNINGS", *[f"- {x}" for x in rec["warnings"]]]
    lines += [
        "",
        "## ORDEN DE TRABAJO PARA CURSOR",
        f"Cuando el usuario indique `MonX slotY`, usa exclusivamente este perfil visual para HPR {mid}, inserta/asigna la libreria indicada y crea el registro FrameSet custom sin alterar monstruos existentes.",
    ]
    return "\n".join(lines) + "\n"


def frameset_json(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "format": "ORIGINS_ZIRCON_MONSTER_FRAMESET_V1",
        "hpr": rec["hpr"],
        "status": rec.get("status", "UNKNOWN"),
        "slot_count": rec.get("slot_count", 0),
        "actions": rec.get("actions", []),
        "unreferenced_nonempty_ranges": rec.get("unreferenced_nonempty_ranges", []),
        "server_behavior_inferred": False,
        "notes": [
            "Frame.OffSet = stride",
            "Attack/AttackRange/Spell/Special are visual labels only",
            "Do not modify FrameSet.DefaultMonster",
        ],
    }


def frameset_cs(rec: Dict[str, Any]) -> str:
    lines = [
        f"// HPR {rec['hpr']} - generated visual FrameSet source",
        "// IMPORTANT: animation slots are visual containers only; no AI semantics inferred.",
        "// Insert these Frame definitions into an isolated MonsterImage-specific FrameSet.",
        "",
    ]
    for a in rec.get("actions", []):
        slot = a.get("zircon_animation_slot") or a.get("visual_action")
        lines.append(
            f"// {a['visual_action']} -> {slot}\n"
            f"[MirAnimation.{slot}] = new Frame({a['start']}, {a['count']}, {a['stride']}, TimeSpan.FromMilliseconds({a['delay_ms']})),"
        )
        if a.get("reverse"):
            lines.append("// Reverse=true: reproduce the action in reverse order; do not alter the source indices.")
    return "\n".join(lines) + "\n"


def master_rows(records: Sequence[Dict[str, Any]], output_root: Path):
    rows = []
    for r in sorted(records, key=lambda x: natural_key(x.get("hpr", ""))):
        monster_dir = output_root / "MONSTERS" / r["hpr"]
        metadata_ok = bool(r.get("metadata_path")) and Path(r["metadata_path"]).exists()
        frames_ok = bool(r.get("frames_dir")) and Path(r["frames_dir"]).exists()
        rows.append({
            "hpr": r["hpr"],
            "status": r.get("status", "UNKNOWN"),
            "needs_review": status_needs_review(r.get("status", "UNKNOWN")),
            "slot_count": r.get("slot_count", 0),
            "nonempty_image_count": r.get("nonempty_image_count", 0),
            "action_count": len(r.get("actions", [])),
            "actions": action_summary(r.get("actions", [])),
            "unreferenced_ranges": range_summary(r.get("unreferenced_nonempty_ranges", [])),
            "issues": " | ".join(r.get("issues", [])),
            "warnings": " | ".join(r.get("warnings", [])),
            "metadata_available": metadata_ok,
            "frames_available": frames_ok,
            "build_ready": metadata_ok and frames_ok and not bool(r.get("issues")),
            "cursor_file": str((monster_dir / "CURSOR_IMPORT_THIS_MONSTER.md").relative_to(output_root)).replace("\\", "/"),
        })
    return rows


def write_master_outputs(records: Sequence[Dict[str, Any]], output_root: Path):
    output_root.mkdir(parents=True, exist_ok=True)
    monsters_root = output_root / "MONSTERS"
    monsters_root.mkdir(exist_ok=True)

    for rec in records:
        d = monsters_root / rec["hpr"]
        d.mkdir(parents=True, exist_ok=True)
        write_json(d / "FRAMESET.json", frameset_json(rec))
        (d / "FRAMESET.cs.txt").write_text(frameset_cs(rec), encoding="utf-8")
        (d / "CURSOR_IMPORT_THIS_MONSTER.md").write_text(make_cursor_text(rec), encoding="utf-8")
        write_json(d / "MASTER_RECORD.json", rec)

    rows = master_rows(records, output_root)
    if rows:
        with (output_root / "MASTER_SHEET.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    write_json(output_root / "MASTER_SHEET.json", rows)

    heads = list(rows[0].keys()) if rows else []
    table_rows = []
    for row in rows:
        tds = "".join(f"<td>{html.escape(str(row[h]))}</td>" for h in heads)
        table_rows.append(f"<tr>{tds}</tr>")
    doc = f"""<!doctype html><html><head><meta charset='utf-8'><title>ORIGINS HPR MASTER SHEET</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:20px;background:#111;color:#eee}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{border:1px solid #444;padding:5px;vertical-align:top}}th{{position:sticky;top:0;background:#252525}}tr:nth-child(even){{background:#191919}}.note{{padding:10px;background:#242424}}</style></head><body>
<h1>ORIGINS HPR MASTER SHEET</h1><div class='note'>Visual only. Attack/AttackRange/Spell/Special do not define server AI.</div>
<p>Total: {len(rows)} | Generated by v{TOOL_VERSION}</p>
<table><thead><tr>{''.join(f'<th>{html.escape(h)}</th>' for h in heads)}</tr></thead><tbody>{''.join(table_rows)}</tbody></table></body></html>"""
    (output_root / "MASTER_SHEET.html").write_text(doc, encoding="utf-8")

    ready = [r["hpr"] for r in rows if r["build_ready"]]
    review = [r["hpr"] for r in rows if r["needs_review"] or not r["build_ready"]]
    (output_root / "READY_IDS.txt").write_text("\n".join(ready) + ("\n" if ready else ""), encoding="utf-8")
    (output_root / "REVIEW_IDS.txt").write_text("\n".join(review) + ("\n" if review else ""), encoding="utf-8")

    summary = {
        "tool_version": TOOL_VERSION,
        "total": len(rows),
        "ready": len(ready),
        "review_or_not_build_ready": len(review),
        "statuses": {},
    }
    for r in rows:
        summary["statuses"][r["status"]] = summary["statuses"].get(r["status"], 0) + 1
    write_json(output_root / "MASTER_SUMMARY.json", summary)
    (output_root / "MASTER_SUMMARY.txt").write_text(
        "ORIGINS HPR MASTER\n==================\n"
        + f"Total: {summary['total']}\nReady: {summary['ready']}\nReview/not-ready: {summary['review_or_not_build_ready']}\n"
        + "\n".join(f"{k}: {v}" for k, v in sorted(summary["statuses"].items())) + "\n",
        encoding="utf-8",
    )


def master_command(args):
    root = Path(args.analysis_root).resolve()
    out = Path(args.output).resolve()
    manifest = Path(args.manifest).resolve() if args.manifest else None
    if manifest:
        records = records_from_manifest(manifest)
        # Enrich manifest rows with per-monster files if an analysis root exists.
        indexed = {r["hpr"]: r for r in records}
        for pp in profile_candidates(root):
            rr = record_from_profile(pp)
            if rr["hpr"] in indexed:
                base = indexed[rr["hpr"]]
                for k in ("profile_path", "monster_root", "metadata_path", "frames_dir"):
                    base[k] = rr[k]
            else:
                records.append(rr)
    else:
        profiles = profile_candidates(root)
        if not profiles:
            raise BuilderError(f"No se encontro ningun CURSOR_PROFILE.json bajo {root}. Usa --manifest si solo tienes ALL_MONSTERS_CURSOR_MANIFEST.json")
        records = [record_from_profile(p) for p in profiles]

    write_master_outputs(records, out)
    print(f"MASTER terminado: {len(records)} monstruos -> {out}")


def load_record_from_monster_root(root: Path) -> Dict[str, Any]:
    profile = root / "CURSOR_PROFILE.json"
    master_rec = root / "MASTER_RECORD.json"
    if profile.exists():
        return record_from_profile(profile)
    if master_rec.exists():
        rec = read_json(master_rec, {})
        # If copied into a new root, rebind paths.
        rec["monster_root"] = str(root)
        md = root / "IMAGE_METADATA.csv"
        rec["metadata_path"] = str(md) if md.exists() else rec.get("metadata_path", "")
        fd = find_frames_dir(root)
        rec["frames_dir"] = str(fd) if fd else rec.get("frames_dir", "")
        return rec
    raise BuilderError(f"Falta CURSOR_PROFILE.json o MASTER_RECORD.json en {root}")


def build_command(args):
    root = Path(args.monster_root).resolve()
    out = Path(args.output).resolve()
    rec = load_record_from_monster_root(root)
    mid = rec["hpr"]

    metadata = Path(args.metadata).resolve() if args.metadata else Path(rec.get("metadata_path", ""))
    if not metadata.exists():
        candidate = root / "IMAGE_METADATA.csv"
        metadata = candidate if candidate.exists() else metadata
    frames = Path(args.frames).resolve() if args.frames else find_frames_dir(root)
    if frames is None or not frames.exists():
        raise BuilderError("No hay FRAMES_PNG/PNG numerados. Ejecuta primero el backend HPR que exporta los frames RGBA.")
    if not metadata.exists():
        raise BuilderError("No se encuentra IMAGE_METADATA.csv; no se construye una .Zl sin offsets X/Y fiables.")

    d = out / mid
    d.mkdir(parents=True, exist_ok=True)
    zl = d / f"{mid}.Zl"
    summary = build_legacy_zl(metadata, frames, zl, rec.get("slot_count") or None)
    write_json(d / f"{mid}.frameset.json", frameset_json(rec))
    (d / f"{mid}.frameset.cs.txt").write_text(frameset_cs(rec), encoding="utf-8")
    (d / "CURSOR_IMPORT_THIS_MONSTER.md").write_text(make_cursor_text(rec, zl.name), encoding="utf-8")
    write_json(d / "BUILD_SUMMARY.json", {"hpr": mid, "zl": zl.name, **summary})
    (d / "VALIDATION_BUILD.txt").write_text(
        f"HPR={mid}\nZL={zl.name}\nslots={summary['slot_count']}\npresent={summary['present_count']}\nbytes={summary['output_bytes']}\n"
        "indices=preserved\noffsets=IMAGE_METADATA.csv\ncontainer=legacy DXT1\nserver_ai=inferred:NO\n",
        encoding="utf-8",
    )
    print(f"BUILD terminado: {zl} ({summary['present_count']}/{summary['slot_count']} frames presentes)")


def _engine_success(out: Path) -> bool:
    return any(out.rglob("CURSOR_PROFILE.json")) or (out / "ALL_MONSTERS_CURSOR_MANIFEST.json").exists()


def analyze_command(args):
    """Run the already-proven HPR parser as a backend.

    We do not duplicate/reverse-engineer its binary parser here. The wrapper
    tries the command shapes used by ORIGINS packages, or accepts an exact
    --engine-command template.
    """
    hpr_root = Path(args.hpr_root).resolve()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    engine = Path(args.engine).resolve() if args.engine else Path(__file__).parent / "engine" / "monster_hpr_analyzer.py"
    if not engine.exists():
        raise BuilderError(
            f"No existe backend HPR: {engine}\n"
            "Copia el monster_hpr_analyzer.py probado de ORIGINS dentro de engine/ o usa --engine."
        )

    py = sys.executable
    if args.engine_command:
        command = args.engine_command.format(python=py, engine=str(engine), input=str(hpr_root), output=str(out))
        candidates = [shlex.split(command, posix=os.name != "nt")]
    else:
        candidates = [
            [py, str(engine), str(hpr_root), str(out)],
            [py, str(engine), "--input", str(hpr_root), "--output", str(out)],
            [py, str(engine), "--input-dir", str(hpr_root), "--output-dir", str(out)],
            [py, str(engine), "--source", str(hpr_root), "--output", str(out)],
        ]

    logs = []
    for cmd in candidates:
        p = subprocess.run(cmd, capture_output=True, text=True)
        logs.append({"command": cmd, "returncode": p.returncode, "stdout": p.stdout[-8000:], "stderr": p.stderr[-8000:]})
        if p.returncode == 0 and _engine_success(out):
            write_json(out / "ENGINE_RUN.json", logs[-1])
            print("Backend HPR terminado correctamente.")
            if args.master_output:
                class A: pass
                a=A(); a.analysis_root=str(out); a.output=args.master_output; a.manifest=None
                manifest = out / "ALL_MONSTERS_CURSOR_MANIFEST.json"
                if manifest.exists(): a.manifest=str(manifest)
                master_command(a)
            return
    write_json(out / "ENGINE_FAILURES.json", logs)
    raise BuilderError(
        "El backend existe pero no se ha reconocido su CLI. Revisa ENGINE_FAILURES.json y ejecuta de nuevo con "
        "--engine-command usando {python} {engine} {input} {output}."
    )


def validate_command(args):
    root = Path(args.monster_root).resolve()
    rec = load_record_from_monster_root(root)
    problems = []
    if not rec.get("actions"):
        problems.append("No actions")
    for a in rec.get("actions", []):
        if a["count"] <= 0:
            problems.append(f"{a['visual_action']}: count <= 0")
        if a["stride"] <= 0:
            problems.append(f"{a['visual_action']}: stride <= 0")
        if a["start"] < 0:
            problems.append(f"{a['visual_action']}: start < 0")
        slots = rec.get("slot_count", 0)
        # 8-direction upper-bound check. Single-orientation cases are not failed.
        if slots > 0 and a["start"] >= slots:
            problems.append(f"{a['visual_action']}: start outside library")
    md = Path(rec.get("metadata_path", ""))
    if not md.exists(): problems.append("IMAGE_METADATA.csv missing")
    fd = find_frames_dir(root)
    if fd is None: problems.append("numbered PNG frames missing")
    result = {"hpr": rec["hpr"], "ok": not problems, "problems": problems}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if problems:
        raise SystemExit(2)


def parser():
    p = argparse.ArgumentParser(description="ORIGINS HPR -> Zircon master builder")
    p.add_argument("--version", action="version", version=TOOL_VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("master", help="Create MASTER_SHEET and per-monster Cursor files from analyzer output")
    m.add_argument("--analysis-root", required=True)
    m.add_argument("--manifest", help="ALL_MONSTERS_CURSOR_MANIFEST.json (optional but recommended for the 650 batch)")
    m.add_argument("--output", required=True)
    m.set_defaults(func=master_command)

    b = sub.add_parser("build", help="Build one index-preserving legacy DXT1 Zircon .Zl")
    b.add_argument("--monster-root", required=True)
    b.add_argument("--output", required=True)
    b.add_argument("--metadata")
    b.add_argument("--frames")
    b.set_defaults(func=build_command)

    a = sub.add_parser("analyze", help="Run the proven ORIGINS monster_hpr_analyzer.py backend")
    a.add_argument("--hpr-root", required=True)
    a.add_argument("--output", required=True)
    a.add_argument("--engine", help="Path to monster_hpr_analyzer.py")
    a.add_argument("--engine-command", help="Exact template with {python} {engine} {input} {output}")
    a.add_argument("--master-output", help="If supplied, generate MASTER_SHEET immediately afterwards")
    a.set_defaults(func=analyze_command)

    v = sub.add_parser("validate", help="Validate one prepared monster folder")
    v.add_argument("--monster-root", required=True)
    v.set_defaults(func=validate_command)
    return p


def main():
    args = parser().parse_args()
    try:
        args.func(args)
    except (BuilderError, ZlWriterError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
