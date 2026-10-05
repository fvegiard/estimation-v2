# Confidentialité et publication

Les exemples locaux ont été **consultés pour leur structure seulement**. Ne pas
copier, versionner ou envoyer leurs images, PDF, CSV, XLSX, notes, manifestes, noms
de panneaux, modèles, quantités ou autre contenu spécifique au chantier.

La politique publique du projet source n'est pas une autorisation de republier
des fichiers client dans ce nouveau projet. L'historique source peut en contenir :
**ne jamais le pousser dans estimation-v2**, même après suppression des fichiers.
Un dépôt neuf et une liste de fichiers autorisés sont nécessaires.

## Garde de publication

Admis : `estimation_v2\*.py`, `tests\*.py` synthétiques, `examples\synthetic.py`,
`outils\audit_publication.py`, les documents nouveaux, `.gitignore`, `pyproject.toml`
et `.github\workflows\tests.yml`. Aucune dépendance à un chemin du PC de l'auteur.

Avant tout premier push :

```powershell
git status --short
git ls-files
git diff --cached --stat
git diff --cached
python outils\audit_publication.py
git log --oneline --all
git remote -v
```

Le garde n'est pas un détecteur sémantique de toute donnée privée : **relire le
contenu exact** reste obligatoire. Il vérifie extensions, répertoires, liste de
fichiers, contenu texte UTF-8 et quelques marqueurs de secrets, pas le consentement
de publication. Ne jamais utiliser `git add -f` pour contourner `.gitignore`.

## Exécution locale

Utiliser un répertoire privé pour les entrées et sorties réelles, de préférence
hors dépôt. `INBOX`, `OUTBOX`, `private`, `demo-output` et les formats binaires métier
sont ignorés; cela ne remplace pas une inspection Git. Ne pas ajouter les fichiers
CSV/JSON réels, même s'ils ne sont pas ignorés : les CSV/JSON synthétiques sont
créés pendant les tests, **aucune donnée tabulaire n'est nécessaire dans Git**.

Aucun accès réseau, téléversement, publication ou appel à un modèle par les
exporteurs. Pas de secret d'API requis. Les fichiers privés ne sont lus que si le
contrat les nomme. Les hashes ne permettent pas de restaurer un document, mais les
livrables et leurs noms peuvent révéler des informations : ne pas publier les
paquets réels ni leurs rapports d'audit sans autorisation distincte.

Les CSV préservent le texte source; lors de leur ouverture dans un tableur,
importer les champs comme texte et ne pas activer des formules de données non
fiables. Le XLSX produit force les cellules libres en texte, pas en formules.

## Vérification réelle encore nécessaire

Il faut les PDF/addendas originaux, un relevé amont vérifié, les décisions de portée
et la référence de l'estimateur pour certifier une livraison. Rien de cela n'est
fourni par ce dépôt synthétique. Le profil Granby/CHUM valide un **contrat de
livraison**, pas une prétendue reproduction de ces chantiers.
