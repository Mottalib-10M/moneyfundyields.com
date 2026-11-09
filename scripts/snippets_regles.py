"""Regles d'ordre des mots dans les titres (RECETTE-SITE.md §11), partagees par
check-seo.py et check-snippets.py. Une seule liste : la modifier ici suffit."""
import re

# Noms de pays : ils ne doivent PAS ouvrir un titre (le terme-clé passe avant). L’adjectif compte aussi
# (« Schweizer Lohnrechner » vaut « Schweiz »), cf. RECETTE-SITE.md §11.
COUNTRY = ['Australia', 'Canada', 'Schweiz', 'Schweizer', 'Suisse', 'Nederland',
           'España', 'France', 'Deutschland', 'Italia', 'Portugal', 'Ireland',
           'Danmark', 'Norge', 'Singapore', 'New Zealand', 'México', 'Maroc',
           # Adjectifs et noms anglais : « Canadian Tax Calculators », « Irish tax
           # credits », « Sweden Salary Calculator » passaient le controle (2026-10-03).
           'Canadian', 'Irish', 'Sweden', 'Swedish', 'Sverige', 'Norway', 'Norwegian',
           'Denmark', 'Danish', 'Australian', 'Singaporean', 'Swiss', 'Switzerland',
           'Dutch', 'Netherlands', 'German', 'Germany', 'Spanish', 'Spain', 'Italian',
           'Italy', 'Portuguese', 'French', 'Belgian', 'Belgium', 'Belgique',
           'Luxembourg', 'Österreich', 'Austria', 'Mexican', 'Mexico',
           # Golfe, Royaume-Uni, Ameriques, Maroc, Japon (2026-10-03). Les villes (Dubai,
           # Doha) n'y sont pas : elles sont souvent la requete elle-meme (« Dubai Golden Visa »).
           'UAE', 'Emirati', 'Qatar', 'Saudi', 'Kuwait', 'Bahrain', 'Oman', 'UK ',
           'United Kingdom', 'British', 'US ', 'USA', 'American', 'Brasil', 'Brazil',
           'Brazilian', 'Morocco', 'Moroccan', 'Japan', 'Japanese']

# Premiers mots interdits en tête de titre (toutes langues du portefeuille).
# L'italien et le portugais manquaient : 21 titres de calcolalordonetto.it
# s'ouvraient sur « Calcolo » sans que le controle le signale, alors que le
# mot utile — IRPEF, TFR, Tredicesima — venait en deuxieme position (2026-09-25).
GENERIC_START = re.compile(r"^(¿|simulateur\b|calculateur\b|calcul\b|calculez\b|calculer\b|calculadora\b|calcula\b|calcolo\b|calcolare\b|calcola\b|cálculo\b|calculo\b|calculator\b|calculate\b|rechner\b|berechnen\b|bereken\b|rekentool\b|à propos\b|über uns\b|sobre nosotros\b|over ons\b|about\b|méthodologie\b|methodology\b|methodik\b|metodología\b|methode\b|faq\b|questions fréquentes\b|preguntas frecuentes\b|veelgestelde vragen\b|häufige fragen\b|combien\b|comment\b|quel\b|quelle\b|how\b|what\b|when\b|wie\b|was\b|wer\b|cuánto\b|cómo\b|qué\b|hoe\b|wat\b)")
