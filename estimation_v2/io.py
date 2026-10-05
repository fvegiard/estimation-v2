"""Lectures strictes, nombres exacts et noms de fichiers portables."""
from __future__ import annotations

import csv
import hashlib
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ContractError(ValueError):
    """Entrée incompatible avec le contrat déclaré."""


def keys(obj: dict, required: set[str], optional: set[str], context: str) -> None:
    if not isinstance(obj, dict):
        raise ContractError(f"{context}: objet attendu")
    missing, extra = required - obj.keys(), obj.keys() - required - optional
    if missing or extra:
        raise ContractError(f"{context}: clés manquantes {sorted(missing)}, inconnues {sorted(extra)}")


def name(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value):
        raise ContractError(f"Nom non portable: {value!r}")
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"{p}{i}" for p in ("COM", "LPT") for i in range(1, 10)}
    if value.endswith(".") or value.split(".")[0].upper() in reserved:
        raise ContractError(f"Nom réservé Windows: {value!r}")
    return value


def text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{context}: texte non vide attendu")
    return value


def number(value: object, context: str) -> Decimal:
    try:
        q = Decimal(str(value).replace(",", "."))
    except InvalidOperation as exc:
        raise ContractError(f"{context}: nombre invalide {value!r}") from exc
    if not q.is_finite() or q < 0:
        raise ContractError(f"{context}: nombre fini positif ou nul attendu")
    return q


def coordinate(value: object, context: str) -> float:
    q = float(number(value, context))
    if not math.isfinite(q):
        raise ContractError(f"{context}: coordonnée hors plage")
    return q


def fmt(value: Decimal) -> str:
    return format(value.normalize(), "f")


def read_csv(path: Path, columns: list[str], *, exact: bool = True) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames
        if (header != columns if exact else not header or not set(columns) <= set(header)):
            raise ContractError(f"{path.name}: colonnes attendues {columns}, reçues {header}")
        if len(header) != len(set(header)):
            raise ContractError(f"{path.name}: colonnes dupliquées")
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ContractError(f"{path.name}:{line}: largeur de ligne incorrecte")
            if not any(row.values()):
                continue
            rows.append(row)
        return rows


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def unique(rows: list[dict], columns: list[str], context: str) -> dict[tuple, dict]:
    out = {}
    for row in rows:
        key = tuple(text(row[c], f"{context}.{c}") for c in columns)
        if key in out:
            raise ContractError(f"{context}: clé dupliquée {key}")
        out[key] = row
    return out
