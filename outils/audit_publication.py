"""Garde de la liste de fichiers publiables, à lancer dans le dépôt neuf."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXACT = {
    ".gitignore", "pyproject.toml", "README.md", "docs/CONTRATS.md",
    "docs/CONFIDENTIALITE.md", "examples/synthetic.py",
    "outils/audit_publication.py", ".github/workflows/tests.yml",
}
PATTERNS = [r"estimation_v2/[a-z_]+\.py", r"tests/test_[a-z_]+\.py"]
SECRET_PATTERNS = [r"gh[pousr]_[A-Za-z0-9]{30,}", r"sk-ant-[A-Za-z0-9_-]{30,}",
                   r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]


def main() -> int:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    files = [f for f in result.stdout.decode("utf-8").split("\0") if f]
    if not files:
        print("ÉCHEC: aucun fichier suivi/indexé à vérifier")
        return 1
    bad = []
    for filename in files:
        if filename not in EXACT and not any(re.fullmatch(p, filename) for p in PATTERNS):
            bad.append(f"{filename}: hors liste autorisée")
            continue
        # Auditer les octets qui seront publiés, pas seulement le fichier de travail.
        content = subprocess.run(["git", "show", f":{filename}"], cwd=ROOT, check=True, capture_output=True).stdout
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            bad.append(f"{filename}: fichier non texte UTF-8")
            continue
        if "\0" in text or any(re.search(p, text) for p in SECRET_PATTERNS):
            bad.append(f"{filename}: binaire ou marqueur de secret")
    if bad:
        print("ÉCHEC publication:\n" + "\n".join(bad))
        return 1
    print(f"Liste autorisée vérifiée : {len(files)} fichiers texte; revue humaine du contenu toujours requise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
