#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cartes Open Graph d'un site (RECETTE §11).

Une page sans `og:image` sort sans vignette quand on la partage : sur WhatsApp,
LinkedIn ou X, elle s'affiche en lien nu. La trame savait fabriquer ces images
pour un site ecrit a la main, pas pour les autres, si bien que six sites du
portefeuille n'en avaient aucune (releve du 2026-09-26).

Ce script lit la sortie deja construite, prend le titre et la description de
chaque page, et dessine une carte 1200x630 par page dans `public/og/`. Il ecrit
dans `public/` et non dans la sortie : une carte posee dans `dist/` disparait a
la construction suivante.

    python3 og-cards.py <site> [--marque "Nom"] [--domaine exemple.fr]
                        [--accent "#e63946"] [--fond "#1a1a2e"]

Le nom du fichier suit le chemin de la page : `/guides/abc/` donne
`guides-abc.png`, la racine donne `accueil.png`. Un gabarit calcule donc son
`og:image` depuis son chemin, sans table de correspondance a tenir a jour.
"""
import argparse
import html
import os
import re
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("og-cards: il manque Pillow (pip3 install Pillow)")

SORTIES = ('dist', 'out', 'build', 'docs', 'output', '_site', 'www')
# Les polices du systeme : aucune dependance a installer, et le rendu est le
# meme d'un site a l'autre.
GRAS = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
NORMAL = "/System/Library/Fonts/Supplemental/Arial.ttf"


def couleur(v):
    v = v.lstrip('#')
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def lignes_de(d, texte, police, largeur):
    mots, ligne, lignes = texte.split(), "", []
    for mot in mots:
        essai = (ligne + " " + mot).strip()
        if d.textlength(essai, font=police) > largeur and ligne:
            lignes.append(ligne)
            ligne = mot
        else:
            ligne = essai
    if ligne:
        lignes.append(ligne)
    return lignes


def carte(titre, sous_titre, chemin, marque, domaine, accent, fond):
    blanc, clair = (255, 255, 255), (226, 226, 236)
    img = Image.new("RGB", (1200, 630), fond)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1200, 12], fill=accent)
    d.text((80, 84), marque, font=ImageFont.truetype(GRAS, 44), fill=accent)
    police = ImageFont.truetype(GRAS, 68)
    lignes = lignes_de(d, titre, police, 1040)[:3]
    y = 210
    for l in lignes:
        d.text((80, y), l, font=police, fill=blanc)
        y += 84
    if sous_titre:
        petite = ImageFont.truetype(NORMAL, 34)
        toutes = lignes_de(d, sous_titre, petite, 1040)
        gardees = toutes[:2]
        # une description coupee en plein milieu se lit mal : on le signale
        if len(toutes) > 2:
            gardees[-1] = gardees[-1].rstrip(" ,;") + "…"
        for l in gardees:
            d.text((80, y + 14), l, font=petite, fill=clair)
            y += 46
    d.text((80, 548), domaine, font=ImageFont.truetype(NORMAL, 30), fill=accent)
    img.save(chemin, "PNG", optimize=True)


def texte(balise, page):
    m = re.search(balise, page, re.S | re.I)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""


def nom_de(chemin_relatif):
    if chemin_relatif in ('.', ''):
        return "accueil.png"
    return chemin_relatif.replace(os.sep, "-").strip("-") + ".png"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("site")
    p.add_argument("--marque", default="")
    p.add_argument("--domaine", default="")
    p.add_argument("--accent", default="#e63946")
    p.add_argument("--fond", default="#1a1a2e")
    a = p.parse_args()

    site = a.site.rstrip("/")
    # Le dossier servi n'est pas le meme d'un outil a l'autre : on prend celui
    # qui contient le plus de pages, comme les autres controles de la trame.
    candidats = []
    for s in SORTIES:
        d = os.path.join(site, s)
        if os.path.isdir(d):
            n = sum(1 for _, _, f in os.walk(d) if "index.html" in f)
            if n:
                candidats.append((n, s))
    if not candidats:
        sys.exit(f"og-cards: aucune sortie construite sous {site}")
    sortie = max(candidats)[1]
    racine = os.path.join(site, sortie)

    marque = a.marque or os.path.basename(site).split(".")[0]
    domaine = a.domaine or os.path.basename(site)
    dossier = os.path.join(site, "public", "og")
    os.makedirs(dossier, exist_ok=True)

    accent, fond = couleur(a.accent), couleur(a.fond)
    n = 0
    for dirpath, dossiers, fichiers in os.walk(racine):
        dossiers[:] = [x for x in dossiers if not x.startswith("_")]
        if "index.html" not in fichiers:
            continue
        page = open(os.path.join(dirpath, "index.html"), encoding="utf-8").read()
        if 'content="noindex' in page:
            continue
        rel = os.path.relpath(dirpath, racine)
        titre = re.split(r"\s+[|—–]\s+", texte(r"<title>(.*?)</title>", page))[0]
        if not titre:
            continue
        sous = texte(r'name="description" content="(.*?)"', page)
        carte(titre, sous, os.path.join(dossier, nom_de(rel)),
              marque, domaine, accent, fond)
        n += 1
    print(f"og-cards: {n} carte(s) dans {dossier}")


if __name__ == "__main__":
    main()
