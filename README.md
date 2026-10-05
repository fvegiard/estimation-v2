# Estimation v2

Couche **autonome d'emballage/export**, basée sur les contrats de sortie de
[`dr-estimation-ia`](https://github.com/fvegiard/dr-estimation-ia). Elle réutilise
les résultats du pipeline existant sans modifier son agent, son `.qpl`, ses
quantités ou son rendu vectoriel.

Deux profils :

| Profil | Livrables |
|---|---|
| `granby` | JPEG annoté par feuille; CSV spécialisés (équipements, niveaux, repères en points, symboles, chambres types, détails, disjoncteurs); CSV détaillé et XLSX par panneau si les données disjoncteurs sont fournies |
| `chum` | CSV équipements par feuille, consolidé métier, sommaire par discipline/action séparant unités et lots |

Les deux profils ajoutent `READ-ME.txt`, `reserves.md`, `export-report.json` et
`manifest.json` (noms, octets, SHA256 de tous les livrables sauf le manifeste lui-même).

**Ce dépôt ne contient aucun dossier client et ne produit pas un nouveau relevé à
partir des exemples.** Le dossier d'exemples local ne contient pas les PDF sources
Granby/CHUM; les quantités réelles ne peuvent donc pas être régénérées ou certifiées.
Les noms Granby/CHUM désignent ici des **formats**, pas des données embarquées.

## Utilisation (PowerShell)

```powershell
python -m pip install -e ".[test]"
python examples\synthetic.py demo-output\inputs
python -m estimation_v2 --job demo-output\inputs\job.json --profile granby --out demo-output\granby
python -m estimation_v2 --job demo-output\inputs\job.json --profile chum --out demo-output\chum
python -m pytest -q
```

Le générateur crée des PDF, CSV et réserves **entièrement fictifs** au moment de
l'exécution. Aucun plan, image, XLSX ou résultat métier n'est versionné. La commande
installée `estimation-v2` accepte les mêmes arguments que `python -m estimation_v2`.
Si le dossier Scripts de Python n'est pas dans le PATH, utiliser la forme
`python -m estimation_v2` ci-dessus, sans modifier la configuration du poste.
La destination doit être absente : pas d'écrasement et pas de paquet partiel en cas
d'échec. Code retour `0` en cas de succès, `2` pour une entrée invalide ou une erreur
de fichier; les autres erreurs techniques ne sont pas dissimulées.

## Brancher le pipeline existant

1. Exécuter **dans le projet source**, avec ses propres accès, le parcours existant.
   Il produit notamment `vecteur\estimate.json`, `vecteur\bordereau.csv`,
   `vecteur\reserves.md` et `<projet>-Plans-annotes.pdf`.
2. Créer un contrat JSON privé décrivant les feuilles et les pages du PDF annoté.
   L'adaptateur `pipeline` lit les deux premières sorties en jointure stricte
   `(feuille, repere)`, conserve les coordonnées en points et les réserves. Il ne
   charge jamais `dr-estimation-ia` comme dépendance et n'a pas besoin de son historique.
3. Pour CHUM, fournir un CSV de métadonnées métier explicites en jointure exhaustive
   1:1. Une occurrence ne dit pas si elle est à installer, à déposer, fournie client
   ou un lot : **aucune de ces décisions n'est devinée**.
4. Fournir les tables spécialisées validées si elles existent. Aucun disjoncteur,
   multiplicateur de chambre ou métré de câble n'est déduit du nom d'une famille.

Voir [le contrat d'entrée et les sorties](docs/CONTRATS.md) et
[les règles de confidentialité](docs/CONFIDENTIALITE.md).

## Limites assumées

Les JPEG sont une dérivation du **PDF déjà annoté** (ou de l'image annotée fournie),
pas un nouveau moteur de placement de marques. Le PDF vectoriel source reste intact.
L'export ne vérifie pas que la page déclarée correspond au bon cartouche, ni que
les repères désignent les bons appareils : contrôle visuel et comparaison à
l'estimateur restent des étapes amont. Le rapport porte toujours « vérification
incomplète »; un manifeste prouve des octets, pas la justesse d'un relevé.

Le sommaire n'est ni une commande ni un prix. Les règles « fourni client », inventaire,
dépose, conservation et forfait sont conservées dans le consolidé; aucune fourniture
ou heure de main-d'œuvre n'est ajoutée implicitement.

## Origine et publication

Nouveau dépôt, **historique Git neuf**, indépendant de `dr-estimation-ia`. Aucun
changement de remote du projet source. Seuls code, tests synthétiques, documentation
nouvelle et configuration sont admissibles. `python outils\audit_publication.py`
contrôle cette liste sur les fichiers suivis/indexés avant publication.
Le workflow CI ne reçoit ni secrets ni données privées; il exécute les tests
synthétiques, pas des relevés de clients.
