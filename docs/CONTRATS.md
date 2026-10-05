# Contrats version 1

Tous les CSV utilisent virgule, UTF-8 avec BOM et en-têtes exacts, dans l'ordre
ci-dessous. Lecture UTF-8 avec ou sans BOM. Nombres décimaux non négatifs, finis;
virgule décimale acceptée dans une cellule CSV citée. Aucun remplacement silencieux
des valeurs invalides. Champs facultatifs explicitement vides restent vides.

## Contrat JSON d'entrée

```json
{
  "version": 1,
  "project": "DEMO",
  "scope": "Relevé partiel synthétique, portée explicitement déclarée.",
  "reserves": "reserves.md",
  "dpi": 200,
  "adapter": {"type": "tables", "equipment": "equipment.csv"},
  "sheets": [
    {
      "id": "E001",
      "annotation": {"path": "Plans-annotes.pdf", "page": 1},
      "tables": [{"kind": "equipment", "path": "E001.csv"}]
    }
  ],
  "breakers_detail": "breakers.csv"
}
```

Requis : `version`, `project`, `scope`, `reserves`, `adapter`, `sheets` non vide.
`dpi` facultatif (200 par défaut, entier 72–600); `breakers_detail` facultatif.
Les autres clés sont refusées. `scope` et le fichier de réserves doivent contenir
du texte, même pour déclarer « aucune réserve connue dans la portée fournie ».
Les chemins sont relatifs au JSON (ou absolus explicitement donnés); seuls les
fichiers nommés sont lus, jamais un import récursif de dossier.

`project` et `sheets[].id` : ASCII portable, 1–80 caractères, première lettre/chiffre,
puis lettres/chiffres/point/tiret/underscore; pas de nom réservé Windows ni point
final. Feuilles uniques même sans distinction de casse.

`annotation` est obligatoire pour chaque feuille du profil Granby. PDF : page
**1-based** obligatoire, dans le PDF annoté, pas dans le dossier complet avec rapport.
Le renderer source peut intercaler des pages de bordereau entre les plans : la page
de `estimate.json` concerne `vecteur\plans.pdf`, **pas nécessairement** la page
du PDF annoté. Déclarer le numéro réel de chaque plan annoté après inspection;
ne pas recopier automatiquement l'index de `estimate.json`.
Image : pas de page, dimensions conservées et conversion RGB sur fond blanc.
JPEG : qualité 95, sous-échantillonnage désactivé. PDF : rendu au DPI demandé.
Les chemins ne sont pas incorporés au nom de sortie. CHUM n'exporte pas d'images.

Chaque feuille peut avoir plusieurs `tables`, mais pas deux avec le même suffixe de
sortie (par exemple `equipment` et `positions`). Une feuille avec aucune table peut
quand même produire son JPEG. CHUM émet un CSV avec en-tête même si une feuille est vide.

## Adaptateurs

### `tables`

`adapter.equipment` désigne un CSV déjà conforme au consolidé CHUM. Obligatoire
pour le profil CHUM, facultatif pour Granby. Les lignes restent inchangées, dans
l'ordre source. Les doublons exacts sont refusés, pas fusionnés silencieusement.
Les tables spécialisées sont déclarées par `kind` et `path`, pas devinées par leur nom.

### `pipeline`

```json
{"type": "pipeline", "directory": "sortie/vecteur", "metadata": "metadata.csv"}
```

Le chemin JSON emploie ici `/` pour être portable; en commandes Windows, utiliser `\`.

`directory` contient les sorties de `src.estimer.render.from_releve.build` :
`estimate.json` avec `source="releve"`, `sheets` (sheet, page, width_px, height_px)
et `counters[].elements[]` (sheet, repere, x, y, page); dimensions et coordonnées
**en points PDF**, malgré les noms historiques `_px`. `bordereau.csv` contient :

`feuille,repere,source,materiel,designation,qte,portee,modele,prescription,parent,reserve`

Des colonnes supplémentaires (`ref,code,format,note`) sont admises. Jointure
exhaustive 1:1, pages compatibles et coordonnées dans les dimensions déclarées.
Les identifiants affichés du pont sont utilisés tels quels, sans refaire les alias.
La liste `sheets` du JSON doit correspondre à celle de `estimate.json`, y compris
les feuilles sans repères. Sortie Granby : CSV de positions par feuille. Aucun repère
inventé, ré-ancré ou dédupliqué. `qte` est validée mais n'est pas transformée en
plusieurs symboles; le CSV de positions représente un repère, pas son multiplicateur.

`metadata` est obligatoire pour CHUM seulement, avec ces colonnes exactes :

`feuille,repere,Discipline,Localisation,Unité,Action,Règle appliquée,Ref feuille`

Jointure exhaustive avec le bordereau; Code ← materiel, Description ← designation,
Modèle / Réf ← modele, Quantité ← qte; les autres champs métier viennent de metadata.
Toutes les décisions d'action/unité/portée sont donc explicites et traçables.
Les réserves du pont, si présentes, sont ajoutées à celles du JSON; chaque repère
dont `reserve` n'est pas explicitement `0`, `false` ou `non` est listé à revalider.
Les fichiers d'entrée ne sont jamais modifiés.

## Granby : sorties spécialisées

Préfixe `<project>-<sheet>` suivi du suffixe indiqué :

| `kind` | Suffixe | Colonnes exactes |
|---|---|---|
| `equipment` | `-equipment.csv` | Type, Description, Quantité, Source |
| `levels` | `-equipment.csv` | Type, Description, **colonnes de niveaux déclarées**, Total |
| `positions` | `-equipment.csv` | Type, Repère, Description, X points, Y points |
| `symbols` | `-symbols.csv` | Type, Description, Symboles dessinés - pas quantité finale |
| `rooms` | `-by-room-type.csv` | Type de chambre - un extrait, PC, MF, PTAC, LC, LA, AP, CH, TH, DF, SF, RCFF, TV, CUI |
| `details` | `-details.csv` | Détail, Sujet, Portée / réserve |
| `breakers` | `-breakers.csv` | Panel, Ampere, Poles, Quantity |

Pour `levels`, déclarer `levels: ["Niveau 2", "Niveau 3"]` (exemple de noms de
colonnes, non de données client). Chaque Total doit être égal à la somme exacte
de ces colonnes. Les lignes `rooms` ne sont **jamais multipliées** par un nombre de
chambres, les symboles ne deviennent **jamais des quantités finales**. Les tables
ne sont pas additionnées entre plans, schémas et détails.

Si `breakers_detail` est fourni, son contrat est :

`panel,circuits,ampere,poles,quantity,description,protection_source,sheet`

Clé unique `(sheet,panel,circuits)`, feuilles déclarées. Calibre positif et pôles
entiers positifs ou cellules vides **à confirmer**; quantités finies non négatives.
Produit `<project>-breakers-detailed.csv`, des résumés par feuille agrégés uniquement
par `(panel,ampere,poles)` et `<project>-breakers-by-panel.xlsx`.
`breakers_detail` et les tables `breakers` sont mutuellement exclusifs : pas de double
autorité. Les tableaux `breakers` seuls ne contiennent pas de circuits/provenance
suffisants pour inventer un classeur détaillé.

Onglets XLSX : `Purchase list`, `All breakers`, `P001...` (un par panneau), `Panel index`
(nom d'onglet → nom intégral du panneau), `Before ordering` (réserves fournies).
Les alias `P001...` évitent les collisions et caractères Excel interdits, au lieu
de tronquer un nom de panneau. Colonnes par panneau :

`Circuit(s),Calibre (A),Pôles,Quantité,Charge desservie,Protection inscrite,Source`

Les données restent du texte Excel (pas des formules, même avec `=` en tête).
La feuille Purchase list est une agrégation de relevé, **pas un bon de commande**.
Pas d'onglet « service breakers » artificiel : les disjoncteurs de service doivent
être des lignes explicites du CSV détaillé avec leur panneau et source.

## CHUM : sorties

Consolidé `<project>-equipment-consolidated.csv` :

`Plan,Discipline,Code,Description,Modèle / Réf,Localisation,Quantité,Unité,Action,Règle appliquée,Ref feuille`

Unités autorisées : `un`, `Lot`. Actions : `INSTALLER`, `ENLEVER`, `CONSERVER`.
Plan, Discipline, Code, Description, Règle appliquée et Ref feuille non vides.
Le modèle et la localisation peuvent être vides, sans substitution inventée.
Ni sélection de prix ni facturation automatique des fournitures client.

Par feuille `<project>-<sheet>-equipment.csv` :

`Type,Description,Quantité,Source`

Type = `Code | Action | Unité`, Description inchangée, Quantité inchangée,
Source = Ref feuille. Cet enrichissement textuel explicite évite de perdre la
dépose/conservation ou de confondre un forfait avec un appareil dans le format
court. Pour les autres informations, **le consolidé est l'autorité**, pas ce CSV
de présentation.

Sommaire `<project>-summary.csv` :

`Discipline,Action,Qte (un),Lots`

Somme décimale exacte des Quantité, séparée par unité et par `(Discipline,Action)`.
Lots = somme des quantités de forfait, **pas nombre de lignes**. Aucun total mélangeant
unités, lots, actions ou disciplines. Les données de feuilles et du consolidé ne
doivent jamais être additionnées ensemble : ce sont deux vues du même relevé.

## Audit et erreurs

`export-report.json` donne version, profil, portée, feuilles, état « incomplète »,
noms de fichiers d'entrée sans chemin absolu, tailles et SHA256. Les noms identiques
d'entrées distinctes peuvent apparaître plusieurs fois; chaque hash reste conservé.
`manifest.json` est une liste de `{file,bytes,sha256}`, couvrant aussi README,
réserves et rapport. Pas d'auto-hash impossible du manifeste.

Pas d'écrasement. Les exports sont construits dans un dossier temporaire frère,
puis renommés après succès; un échec supprime ce dossier temporaire seulement.
La validation d'intégrité ne certifie ni le relevé ni le PDF contre l'estimateur.
