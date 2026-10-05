"""Adaptateurs explicites vers les sorties existantes, sans inférence métier."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from . import contracts as c
from .io import ContractError, coordinate, fmt, keys, name, number, read_csv, text, unique


@dataclass
class Sheet:
    id: str
    annotation: dict | None
    tables: list[tuple[str, list[str], list[dict]]] = field(default_factory=list)


@dataclass
class Job:
    project: str
    sheets: list[Sheet]
    equipment: list[dict]
    breakers: list[dict]
    reserves: str
    scope: str
    dpi: int
    inputs: set[Path]


def _file(base: Path, value: str, inputs: set[Path]) -> Path:
    path = (base / text(value, "chemin")).resolve()
    if not path.is_file():
        raise ContractError(f"Fichier d'entrée absent: {path}")
    inputs.add(path)
    return path


def _quantities(rows: list[dict], columns: list[str], context: str) -> None:
    for row in rows:
        for col in columns:
            number(row[col], f"{context}.{col}")


def validate_equipment(rows: list[dict], sheets: set[str]) -> None:
    for row in rows:
        if row["Plan"] not in sheets:
            raise ContractError(f"Plan non déclaré: {row['Plan']}")
        for col in ["Discipline", "Code", "Description", "Règle appliquée", "Ref feuille"]:
            text(row[col], col)
        number(row["Quantité"], "Quantité")
        if row["Unité"] not in c.UNITS or row["Action"] not in c.ACTIONS:
            raise ContractError(f"Unité/action non prise en charge: {row['Unité']}/{row['Action']}")
    # Les doublons exacts sont ambigus; jamais les éliminer silencieusement.
    fingerprints = [tuple(r[k] for k in c.CONSOLIDATED) for r in rows]
    if len(set(fingerprints)) != len(fingerprints):
        raise ContractError("équipement consolidé: lignes exactement dupliquées")


def _table(base: Path, spec: dict, inputs: set[Path]) -> tuple[str, list[str], list[dict]]:
    keys(spec, {"kind", "path"}, {"levels"}, "table")
    kind = spec["kind"]
    if kind == "levels":
        levels = spec.get("levels")
        if not isinstance(levels, list) or len(levels) < 1:
            raise ContractError("levels: liste de colonnes requise")
        if any(not isinstance(v, str) or not v.strip() for v in levels):
            raise ContractError("levels: noms de colonnes non vides requis")
        columns = ["Type", "Description", *levels, "Total"]
        if len(columns) != len(set(columns)):
            raise ContractError("levels: colonnes dupliquées")
        suffix = "equipment"
    elif kind in c.TABLES:
        if "levels" in spec:
            raise ContractError("levels n'est permis que pour kind=levels")
        columns, suffix = c.TABLES[kind]
    else:
        raise ContractError(f"Type de table inconnu: {kind}")
    rows = read_csv(_file(base, spec["path"], inputs), columns)
    numeric = {
        "equipment": ["Quantité"], "positions": ["X points", "Y points"],
        "symbols": [c.SYMBOLS[2]], "rooms": c.ROOMS[1:], "breakers": ["Quantity"],
        "levels": columns[2:],
    }.get(kind, [])
    _quantities(rows, numeric, kind)
    if kind == "levels":
        for row in rows:
            if sum((number(row[l], l) for l in levels), Decimal(0)) != number(row["Total"], "Total"):
                raise ContractError("levels: Total ne correspond pas à la somme des niveaux")
    if kind == "positions":
        unique(rows, ["Repère"], "positions")
    if kind == "breakers":
        for row in rows:
            text(row["Panel"], "Panel")
            _breaker_rating(row, "Ampere", "Poles")
    return suffix, columns, rows


def _breaker_rating(row: dict, ampere: str, poles: str) -> None:
    # Vide = calibre/pôles à confirmer, conservé au lieu de choisir arbitrairement.
    if row[ampere]:
        if number(row[ampere], ampere) == 0:
            raise ContractError("Calibre nul interdit")
    if row[poles]:
        q = number(row[poles], poles)
        if q != q.to_integral_value() or q == 0:
            raise ContractError("Pôles: entier strictement positif attendu")


def _pipeline(base: Path, spec: dict, inputs: set[Path], sheets: list[Sheet]) -> list[dict]:
    keys(spec, {"type", "directory"}, {"metadata"}, "adapter pipeline")
    directory = (base / text(spec["directory"], "directory")).resolve()
    rows = read_csv(_file(directory, "bordereau.csv", inputs), c.BORDEREAU, exact=False)
    bord = unique(rows, ["feuille", "repere"], "bordereau")
    for row in rows:
        number(row["qte"], "bordereau.qte")
    estimate = json.loads(_file(directory, "estimate.json", inputs).read_text(encoding="utf-8-sig"))
    if not isinstance(estimate, dict) or not isinstance(estimate.get("sheets"), list) or not isinstance(estimate.get("counters"), list):
        raise ContractError("estimate.json: sheets et counters requis")
    declared = {s.id: s for s in sheets}
    source_sheets = {}
    for row in estimate["sheets"]:
        keys(row, {"sheet", "page", "width_px", "height_px"},
             {"box_hint", "legend_shapes", "legend_rows"}, "estimate.sheets")
        sid = row["sheet"]
        if sid in source_sheets or sid not in declared:
            raise ContractError(f"Feuille dupliquée/non déclarée: {sid}")
        source_sheets[sid] = row
        for col in ("width_px", "height_px"):
            if number(row[col], col) == 0:
                raise ContractError(f"{sid}: dimension nulle")
    if set(source_sheets) != set(declared):
        raise ContractError("Liste de feuilles différente de estimate.json")
    positions: dict[str, list[dict]] = {sid: [] for sid in declared}
    seen = set()
    for counter in estimate["counters"]:
        if not isinstance(counter, dict) or not isinstance(counter.get("elements"), list):
            raise ContractError("estimate.counters: elements requis")
        for el in counter["elements"]:
            if not isinstance(el, dict):
                raise ContractError("estimate.elements: objet attendu")
            key = (el.get("sheet"), el.get("repere"))
            if key not in bord or key in seen:
                raise ContractError(f"Jointure estimate/bordereau absente ou dupliquée: {key}")
            seen.add(key)
            row, sh = bord[key], source_sheets[key[0]]
            if el.get("page", sh["page"]) != sh["page"]:
                raise ContractError(f"Page incompatible: {key}")
            x, y = coordinate(el.get("x"), "x"), coordinate(el.get("y"), "y")
            if x > coordinate(sh["width_px"], "width_px") or y > coordinate(sh["height_px"], "height_px"):
                raise ContractError(f"Coordonnée hors feuille: {key}")
            # Le pont from_releve écrit ses dimensions en points; aucun pixel arbitraire n'est converti.
            if estimate.get("source") != "releve":
                raise ContractError("pipeline: source=releve requis pour les coordonnées en points")
            positions[key[0]].append({
                "Type": row["materiel"], "Repère": row["repere"], "Description": row["designation"],
                "X points": fmt(Decimal(str(x))), "Y points": fmt(Decimal(str(y))),
            })
    if seen != set(bord):
        raise ContractError("Bordereau contient des repères sans élément estimate")
    for sheet in sheets:
        if positions[sheet.id]:
            if any(t[0] == "equipment" for t in sheet.tables):
                raise ContractError("pipeline: une table equipment supplémentaire doublerait les repères")
            sheet.tables.append(("equipment", c.POSITIONS, positions[sheet.id]))
    equipment = []
    if "metadata" in spec:
        metadata = unique(read_csv(_file(base, spec["metadata"], inputs), c.METADATA),
                          ["feuille", "repere"], "metadata")
        if metadata.keys() != bord.keys():
            raise ContractError("metadata: jointure exhaustive 1:1 requise avec bordereau")
        for key, row in bord.items():
            meta = metadata[key]
            equipment.append({
                "Plan": row["feuille"], "Discipline": meta["Discipline"],
                "Code": row["materiel"], "Description": row["designation"],
                "Modèle / Réf": row["modele"], "Localisation": meta["Localisation"],
                "Quantité": row["qte"], "Unité": meta["Unité"], "Action": meta["Action"],
                "Règle appliquée": meta["Règle appliquée"], "Ref feuille": meta["Ref feuille"],
            })
    return equipment


def load_job(path: Path) -> Job:
    path = path.resolve()
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    keys(data, {"version", "project", "scope", "reserves", "sheets", "adapter"},
         {"breakers_detail", "dpi"}, "job")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ContractError("Version de contrat non prise en charge")
    project = name(data["project"])
    scope = text(data["scope"], "scope")
    inputs, base = {path}, path.parent
    reserves = _file(base, data["reserves"], inputs).read_text(encoding="utf-8-sig")
    if not reserves.strip():
        raise ContractError("reserves: déclaration explicite requise, même en l'absence de réserve")
    dpi = data.get("dpi", 200)
    if type(dpi) is not int or not 72 <= dpi <= 600:
        raise ContractError("dpi: entier entre 72 et 600")
    if not isinstance(data["sheets"], list) or not data["sheets"]:
        raise ContractError("sheets: liste non vide requise")
    sheets = []
    for spec in data["sheets"]:
        keys(spec, {"id"}, {"annotation", "tables"}, "sheet")
        sid = name(spec["id"])
        annotation = spec.get("annotation")
        if annotation is not None:
            keys(annotation, {"path"}, {"page"}, "annotation")
            annotation = dict(annotation, path=_file(base, annotation["path"], inputs))
            if annotation["path"].suffix.lower() == ".pdf":
                if type(annotation.get("page")) is not int or annotation["page"] < 1:
                    raise ContractError("annotation PDF: page 1-based explicite requise")
            elif "page" in annotation:
                raise ContractError("annotation image: page interdite")
        table_specs = spec.get("tables", [])
        if not isinstance(table_specs, list):
            raise ContractError("tables: liste requise")
        tables = [_table(base, t, inputs) for t in table_specs]
        if len({t[0] for t in tables}) != len(tables):
            raise ContractError(f"{sid}: tables produisant le même fichier")
        sheets.append(Sheet(sid, annotation, tables))
    ids = {s.id for s in sheets}
    if len({s.id.casefold() for s in sheets}) != len(sheets):
        raise ContractError("sheets: identifiants dupliqués (sans distinction de casse)")
    adapter = data["adapter"]
    if not isinstance(adapter, dict):
        raise ContractError("adapter: objet requis")
    if adapter.get("type") == "tables":
        keys(adapter, {"type"}, {"equipment"}, "adapter tables")
        equipment = read_csv(_file(base, adapter["equipment"], inputs), c.CONSOLIDATED) if "equipment" in adapter else []
    elif adapter.get("type") == "pipeline":
        equipment = _pipeline(base, adapter, inputs, sheets)
    else:
        raise ContractError("adapter.type: tables ou pipeline attendu")
    validate_equipment(equipment, ids)
    breakers = []
    if "breakers_detail" in data:
        breakers = read_csv(_file(base, data["breakers_detail"], inputs), c.DETAILED_BREAKERS)
        unique(breakers, ["sheet", "panel", "circuits"], "disjoncteurs")
        for row in breakers:
            if row["sheet"] not in ids:
                raise ContractError(f"Disjoncteur: feuille non déclarée {row['sheet']}")
            for col in ("description", "protection_source"):
                text(row[col], col)
            number(row["quantity"], "quantity")
            _breaker_rating(row, "ampere", "poles")
        if any(t[0] == "breakers" for s in sheets for t in s.tables):
            raise ContractError("Choisir breakers_detail OU tables breakers, pas les deux")
    if adapter.get("type") == "pipeline":
        directory = (base / adapter["directory"]).resolve()
        source_reserves = directory / "reserves.md"
        if source_reserves.is_file() and source_reserves != (base / data["reserves"]).resolve():
            inputs.add(source_reserves)
            reserves += "\n\n## Réserves du pipeline (conservées)\n\n" + source_reserves.read_text(encoding="utf-8-sig")
        bord_rows = read_csv(directory / "bordereau.csv", c.BORDEREAU, exact=False)
        reserved = [r for r in bord_rows if r["reserve"].strip().lower() not in {"0", "false", "non"}]
        if reserved:
            reserves += "\n\n## Repères à revalider\n\n" + "\n".join(
                f"- {r['feuille']} / {r['repere']} : {r.get('note') or r['prescription'] or 'Réserve du bordereau'}"
                for r in reserved)
    return Job(project, sheets, equipment, breakers, reserves, scope, dpi, inputs)
