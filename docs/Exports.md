# Exports

Deux formats, boutons en bas du panneau de formulaire.

## PNG — style stat block officiel

`src/export/png_exporter.py` (Pillow) reproduit la fiche du Monster Manual :

- Fond parchemin en dégradé, double bordure décorative rouge sombre
- Nom en grand rouge brique, ligne méta en italique
- Caractéristiques sur une ligne (`FOR 18 (+4) DEX 12 (+1)…`)
- Sections en titres rouges (Actions, Scénario…), filets horizontaux
- Les noms d'actions en gras, enchaînés sur leur description
- **Scénario formaté** : les sous-titres markdown (`**Tactique du monstre**`) deviennent des sous-titres en gras, sans astérisques
- Hauteur calculée selon le contenu, largeur 800 px
- Les langues vides sont **omises** (bêtes, golems)

## PDF

`src/export/pdf_exporter.py` (reportlab) : mise en page classique multi-pages, mêmes informations (stats, actions avec descriptions complètes, scénario, CR en fraction avec PX).

## Contenu couvert par les deux exports

Nom, race, méta (taille/alignement), CA, PV + dés de vie, vitesse, caractéristiques, jets de sauvegarde, compétences, résistances/immunités, sens, perception passive, langues (si présentes), CR + PX, description, actions (+ légendaires, réactions), scénario de rencontre.
