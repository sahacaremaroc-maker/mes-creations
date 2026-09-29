"""Relie les booklets (booklets/*.md) à la maquette de la plateforme.

Usage : python3 outils/construire_booklets.py
Relance ce script après chaque modification d'un booklet.
"""
import html
import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
MAQUETTE = RACINE / "maquette" / "index.html"
DEBUT, FIN = "/*BOOKLETS:DEBUT*/", "/*BOOKLETS:FIN*/"


def inline(texte):
    texte = html.escape(texte, quote=False)
    texte = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texte)
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", texte)


def markdown_vers_html(md):
    blocs, liste, para = [], [], []

    def vider():
        if para:
            blocs.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
        if liste:
            blocs.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in liste) + "</ul>")
            liste.clear()

    for ligne in md.splitlines():
        l = ligne.strip()
        if not l:
            vider()
        elif l.startswith("# "):
            vider()
        elif l.startswith("### "):
            vider(); blocs.append(f"<h4>{inline(l[4:])}</h4>")
        elif l.startswith("## "):
            vider(); blocs.append(f"<h3>{inline(l[3:])}</h3>")
        elif l.startswith("> "):
            vider(); blocs.append(f'<p class="alerte">{inline(l[2:])}</p>')
        elif l.startswith("- "):
            if para:
                vider()
            liste.append(l[2:])
        else:
            para.append(l)
    vider()
    return "".join(blocs)


def lire_booklet(chemin):
    brut = chemin.read_text(encoding="utf-8")
    _, entete, corps = brut.split("---", 2)
    meta = dict(l.split(": ", 1) for l in entete.strip().splitlines())
    sous_titre = re.search(r"^\*(.+)\*$", corps, re.M)
    if sous_titre:
        corps = corps.replace(sous_titre.group(0), "", 1)
    return {
        "n": int(meta["numero"]),
        "titre": meta["titre"],
        "besoin": meta["besoin"],
        "duree": int(meta["duree"]),
        "sousTitre": sous_titre.group(1) if sous_titre else "",
        "html": markdown_vers_html(corps),
    }


def main():
    booklets = sorted(
        (lire_booklet(p) for p in (RACINE / "booklets").glob("[0-9][0-9]-*.md")),
        key=lambda b: b["n"],
    )
    page = MAQUETTE.read_text(encoding="utf-8")
    debut, fin = page.index(DEBUT) + len(DEBUT), page.index(FIN)
    donnees = "\n  var booklets = " + json.dumps(booklets, ensure_ascii=False) + ";\n  "
    MAQUETTE.write_text(page[:debut] + donnees + page[fin:], encoding="utf-8")
    print(f"{len(booklets)} booklets reliés à la maquette.")


if __name__ == "__main__":
    main()
