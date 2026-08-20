#!/usr/bin/env python3
"""Render the ORIGINS-DxR four-class Zircon magic audit as Markdown."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CLASS_ORDER = ("Warrior", "Wizard", "Taoist", "Assassin")
STATUS_LABELS = {
    "PLAYABLE": "PLAYABLE",
    "ENUM_ONLY": "ENUM ONLY",
    "DB_PRESENT_NO_RUNTIME_HANDLER": "DB / NO HANDLER",
    "RUNTIME_HANDLER_NO_DB": "HANDLER / NO DB",
    "UPSTREAM_NOT_CODED": "NOT CODED",
    "UPSTREAM_UNUSED": "UNUSED",
}


def esc(value: object) -> str:
    if value is None:
        return "—"
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return text if text else "—"


def powers(info: dict | None) -> str:
    if not info:
        return "—"
    return (
        f"B {esc(info.get('minBasePower'))}-{esc(info.get('maxBasePower'))}; "
        f"L {esc(info.get('minLevelPower'))}-{esc(info.get('maxLevelPower'))}"
    )


def handler_name(entry: dict) -> str:
    handler = entry.get("runtimeHandler")
    if not handler:
        return "—"
    return f"{handler.get('className')} ({handler.get('path')})"


def summary_row(label: str, counts: dict) -> str:
    return (
        f"| {label} | {counts['enum']} | {counts['dbPresent']} | {counts['handlerPresent']} | "
        f"{counts['playable']} | {counts['enumOnly']} | {counts['dbWithoutHandler']} | "
        f"{counts['handlerWithoutDb']} | {counts['upstreamNotCoded']} | {counts['upstreamUnused']} |"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.input.read_text(encoding="utf-8-sig"))
    source = report["source"]
    total = report["totals"]
    level_delay = report["pinnedMagicInfoModel"]["levelDelayReduction"]

    lines: list[str] = [
        "# ORIGINS-DxR — Auditoría final de magias Zircon",
        "",
        f"- Fuente: `{source['repository']}` @ `{source['commit']}`",
        f"- Definición de jugable: `{report['policy']['playableDefinition']}`",
        "- Crystal / Crystal-Monk: **fuera del runtime y fuera de esta auditoría**.",
        f"- `LevelDelayReduction`: **NO EXISTE** en el `MagicInfo` del Zircon fijado; valor reportado = `N/A`. {level_delay['note']}",
        "",
        "## Resumen real",
        "",
        "| Clase | Enum | MagicInfo DB | Handlers | Jugables | Enum only | DB sin handler | Handler sin DB | NOT CODED | UNUSED |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for class_name in CLASS_ORDER:
        lines.append(summary_row(class_name, report["classes"][class_name]["counts"]))
    lines.append(summary_row("TOTAL", total))

    lines.extend(
        [
            "",
            "## Criterio",
            "",
            "Una entrada solo figura como `PLAYABLE` cuando está `ENUM_DEFINED`, tiene exactamente una fila `MagicInfo` de la clase y exactamente un handler registrado por la regla nativa de `SEnvir.CreateMagic`. Las entradas `UPSTREAM_NOT_CODED` y `UPSTREAM_UNUSED` nunca se promocionan a jugables aunque exista material parcial.",
            "",
        ]
    )

    for class_name in CLASS_ORDER:
        payload = report["classes"][class_name]
        counts = payload["counts"]
        lines.extend(
            [
                f"## {class_name.upper()}",
                "",
                f"Enum **{counts['enum']}** · DB **{counts['dbPresent']}** · handlers **{counts['handlerPresent']}** · jugables **{counts['playable']}** · enum-only **{counts['enumOnly']}** · DB sin handler **{counts['dbWithoutHandler']}** · handler sin DB **{counts['handlerWithoutDb']}** · NOT CODED **{counts['upstreamNotCoded']}** · UNUSED **{counts['upstreamUnused']}**.",
                "",
                "| MagicType | Nombre | Estado | DB idx | Icon | School | Property | Need L1/L2/L3 | Exp 1/2/3 | Base/Level Cost | Delay | Powers | Handler |",
                "|---:|---|---|---:|---:|---:|---:|---|---|---|---:|---|---|",
            ]
        )

        for entry in payload["entries"]:
            info = entry.get("magicInfo")
            if info:
                needs = f"{esc(info.get('needLevel1'))}/{esc(info.get('needLevel2'))}/{esc(info.get('needLevel3'))}"
                exps = f"{esc(info.get('experience1'))}/{esc(info.get('experience2'))}/{esc(info.get('experience3'))}"
                costs = f"{esc(info.get('baseCost'))}/{esc(info.get('levelCost'))}"
                db_index = esc(info.get("index"))
                icon = esc(info.get("icon"))
                school = esc(info.get("school"))
                prop = esc(info.get("property"))
                delay = esc(info.get("delay"))
            else:
                needs = exps = costs = db_index = icon = school = prop = delay = "—"

            lines.append(
                "| "
                + " | ".join(
                    [
                        esc(entry["magicType"]),
                        esc(entry["magicTypeName"]),
                        STATUS_LABELS.get(entry["status"], entry["status"]),
                        db_index,
                        icon,
                        school,
                        prop,
                        needs,
                        exps,
                        costs,
                        delay,
                        powers(info),
                        esc(handler_name(entry)),
                    ]
                )
                + " |"
            )
        lines.append("")

    outside = report.get("registeredHandlersOutsideFourClassCatalog", [])
    rejected = report.get("annotatedClassesRejectedByRegistrationGate", [])
    errors = report.get("errors", [])
    lines.extend(
        [
            "## Integridad de registro",
            "",
            f"- Handlers registrados fuera del catálogo activo de cuatro clases: **{len(outside)}**.",
            f"- Clases anotadas que no pasan la regla de registro de `SEnvir.CreateMagic`: **{len(rejected)}**.",
            f"- Errores de consistencia del auditor: **{len(errors)}**.",
            "",
            "El JSON generado junto a este informe conserva todos los campos reales de `MagicInfo`, incluido `Description`, y la ruta/clase exacta del handler cuando existe.",
            "",
        ]
    )

    if errors:
        lines.extend(["### Errores", ""])
        lines.extend(f"- {esc(error)}" for error in errors)
        lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rendered {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
