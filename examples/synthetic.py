"""Fabriquer uniquement des entrées fictives pour les deux contrats.

python examples\\synthetic.py demo-output\\inputs
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from estimation_v2 import contracts as c
from estimation_v2.io import write_csv


def build(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "reserves.md").write_text(
        "# Réserves synthétiques\n\nJeu fictif, aucun chantier réel.\n"
        "Calibre du panneau P-B non précisé : à confirmer, aucune commande autorisée.\n"
        "Chambre type : UN dessin, pas de multiplicateur bâtiment.\n", encoding="utf-8")
    sheets = ["E001", "E002", "E003", "E004", "E005", "E006", "E007", "E008"]
    pdf = pymupdf.open()
    colors = [(0.1, 0.5, 0.7), (0.7, 0.4, 0.1), (0.6, 0.15, 0.5)]
    for sid in sheets:
        page = pdf.new_page(width=420, height=300)
        page.insert_text((20, 26), f"SYNTHETIQUE - {sid} - aucune donnee client", fontsize=12)
        page.draw_rect((20, 40, 400, 180), color=(0.65, 0.65, 0.65))
        for i, (x, color) in enumerate(zip([70, 180, 290], colors), 1):
            page.draw_circle((x, 90), 2.5, color=(0, 0, 0), width=0.7)
            page.draw_line((x - 2, 90), (x + 2, 90), color=(0, 0, 0))
            page.draw_circle((x, 90), 4.2, color=color,
                             fill=tuple(0.85 + 0.15 * v for v in color),
                             fill_opacity=0.45, width=0.7, overlay=True)
            page.insert_text((x + 8, 88), f"M0{i}-01" + (" *" if i == 3 else ""),
                             fontsize=9, color=color)
        page.draw_rect((20, 195, 400, 283), color=(0.2, 0.2, 0.2), width=0.7)
        page.insert_text((28, 210), f"RELEVE {sid} - MATERIEL", fontsize=11)
        page.insert_text((28, 226), "M01: appareil A (1) | M02: appareil B (1) | M03*: appareil C (1)", fontsize=8)
        page.insert_text((28, 242), "Reperes | Source | Materiel | Qte | Portee | Modele | Prescription | RES", fontsize=7)
        page.insert_text((28, 257), "3 reperes fictifs - pastilles sur les symboles, non sur le texte", fontsize=9)
        page.insert_text((28, 273), "RESERVE * : appareil C a revalider. Aucun metre reel.", fontsize=8)
    pdf.save(destination / "annotated.pdf")
    pdf.close()
    data = [
        ("equipment", c.EQUIPMENT, [{"Type": "A", "Description": "Appareil fictif", "Quantité": "3", "Source": "E001 note fictive"}]),
        ("levels", ["Type", "Description", "Niveau fictif 1", "Niveau fictif 2", "Total"],
         [{"Type": "A", "Description": "Appareil fictif", "Niveau fictif 1": "2", "Niveau fictif 2": "1", "Total": "3"}]),
        ("positions", c.POSITIONS, [{"Type": "A", "Repère": "M01-01", "Description": "Appareil fictif", "X points": "70", "Y points": "90"}]),
        ("symbols", c.SYMBOLS, [{"Type": "A", "Description": "Symbole fictif", c.SYMBOLS[2]: "2"}]),
        ("rooms", c.ROOMS, [dict(zip(c.ROOMS, ["Chambre fictive", *["1"] * 13]))]),
        ("details", c.DETAILS, [{"Détail": "D-01", "Sujet": "Détail fictif", "Portée / réserve": "À confirmer"}]),
    ]
    sheet_specs = []
    for i, sid in enumerate(sheets, 1):
        tables = []
        if i <= len(data):
            kind, columns, rows = data[i - 1]
            filename = f"table-{kind}.csv"
            write_csv(destination / filename, columns, rows)
            table = {"kind": kind, "path": filename}
            if kind == "levels":
                table["levels"] = columns[2:-1]
            tables.append(table)
        sheet_specs.append({"id": sid, "annotation": {"path": "annotated.pdf", "page": i}, "tables": tables})
    breakers = [
        dict(zip(c.DETAILED_BREAKERS, ["P-A", "1", "20", "1", "1", "Charge fictive A", "Note fictive", "E007"])),
        dict(zip(c.DETAILED_BREAKERS, ["P-A", "2", "20", "1", "2", "Charge fictive B", "Note fictive", "E007"])),
        dict(zip(c.DETAILED_BREAKERS, ["P-B", "3", "", "2", "1", "Charge fictive C", "Calibre à confirmer", "E008"])),
    ]
    write_csv(destination / "breakers.csv", c.DETAILED_BREAKERS, breakers)
    equipment = [
        dict(zip(c.CONSOLIDATED, ["E001", "Éclairage", "DEL-A", "Luminaire fictif fourni client", "",
                                "Local fictif", "2", "un", "INSTALLER", "Fourni client, pose seule", "Note fictive A"])),
        dict(zip(c.CONSOLIDATED, ["E001", "Éclairage", "DEL-B", "Luminaire fictif", "MODELE-FICTIF",
                                "Local fictif", "1,5", "un", "INSTALLER", "Quantité fournie explicitement", "Note fictive B"])),
        dict(zip(c.CONSOLIDATED, ["E001", "Démolition", "EX-A", "Appareil fictif existant", "",
                                "", "3", "un", "ENLEVER", "Dépose, pas une fourniture", "Note fictive C"])),
        dict(zip(c.CONSOLIDATED, ["E002", "Éclairage", "CC-A", "Appareil fictif conservé", "",
                                "", "4", "un", "CONSERVER", "Hors remplacement", "Note fictive D"])),
        dict(zip(c.CONSOLIDATED, ["E008", "Mise en service", "LOT-A", "Programmation fictive", "",
                                "", "2", "Lot", "INSTALLER", "Forfait, non additionné aux unités", "Devis fictif"])),
    ]
    write_csv(destination / "equipment.csv", c.CONSOLIDATED, equipment)
    job = {"version": 1, "project": "DEMO", "scope": "Essai synthétique partiel; aucune quantité réelle.",
           "reserves": "reserves.md", "dpi": 144, "sheets": sheet_specs,
           "adapter": {"type": "tables", "equipment": "equipment.csv"}, "breakers_detail": "breakers.csv"}
    path = destination / "job.json"
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build(Path(sys.argv[1])))
