"""Contrats de sortie relevés dans les exemples, sans aucune donnée de chantier."""

EQUIPMENT = ["Type", "Description", "Quantité", "Source"]
POSITIONS = ["Type", "Repère", "Description", "X points", "Y points"]
SYMBOLS = ["Type", "Description", "Symboles dessinés - pas quantité finale"]
ROOMS = ["Type de chambre - un extrait", "PC", "MF", "PTAC", "LC", "LA",
         "AP", "CH", "TH", "DF", "SF", "RCFF", "TV", "CUI"]
DETAILS = ["Détail", "Sujet", "Portée / réserve"]
BREAKERS = ["Panel", "Ampere", "Poles", "Quantity"]
DETAILED_BREAKERS = ["panel", "circuits", "ampere", "poles", "quantity",
                    "description", "protection_source", "sheet"]
PANEL_BREAKERS = ["Circuit(s)", "Calibre (A)", "Pôles", "Quantité",
                 "Charge desservie", "Protection inscrite", "Source"]
CONSOLIDATED = ["Plan", "Discipline", "Code", "Description", "Modèle / Réf",
                "Localisation", "Quantité", "Unité", "Action", "Règle appliquée", "Ref feuille"]
SUMMARY = ["Discipline", "Action", "Qte (un)", "Lots"]
BORDEREAU = ["feuille", "repere", "source", "materiel", "designation", "qte",
             "portee", "modele", "prescription", "parent", "reserve"]
METADATA = ["feuille", "repere", "Discipline", "Localisation", "Unité",
            "Action", "Règle appliquée", "Ref feuille"]
TABLES = {
    "equipment": (EQUIPMENT, "equipment"),
    "positions": (POSITIONS, "equipment"),
    "symbols": (SYMBOLS, "symbols"),
    "rooms": (ROOMS, "by-room-type"),
    "details": (DETAILS, "details"),
    "breakers": (BREAKERS, "breakers"),
}
ACTIONS = {"INSTALLER", "ENLEVER", "CONSERVER"}
UNITS = {"un", "Lot"}
