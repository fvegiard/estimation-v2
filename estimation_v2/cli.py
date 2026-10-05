"""Interface automatisable avec échec explicite et sans publication de données."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import load_job
from .exporters import export
from .io import ContractError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emballer des relevés existants sans modifier le pipeline")
    parser.add_argument("--job", required=True, type=Path, help="Contrat JSON version 1")
    parser.add_argument("--profile", required=True, choices=["granby", "chum"])
    parser.add_argument("--out", required=True, type=Path, help="Nouveau dossier de sortie privé")
    args = parser.parse_args(argv)
    try:
        manifest = export(load_job(args.job), args.profile, args.out)
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"ÉCHEC export : {exc}", file=sys.stderr)
        return 2
    print(f"Export {args.profile}: {len(manifest)} fichiers vérifiables dans {args.out}")
    return 0
