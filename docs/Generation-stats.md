# Génération des stats

Toutes les statistiques chiffrées sont calculées par `src/rules/`, à partir des tables officielles du **Guide du Maître** (chapitre 9). Aucune IA n'intervient — le résultat est reproductible et équilibré.

## Du groupe au CR

La chaîne de calcul (`src/rules/encounter.py`) :

1. **Seuil de PX par personnage** : table niveau × difficulté. Ex. niveau 2, Moyen → 100 PX/joueur
2. **Budget de la rencontre** : seuil × nombre de joueurs. Ex. 100 × 4 = 400 PX
3. **CR cible** : le plus haut CR dont les PX ne dépassent pas le budget. 400 PX → **CR 1** (200 PX)

Exemples pour 4 joueurs de niveau 2 : Facile → CR 1, Moyen → CR 1, Difficile → CR 2, Mortel → CR 3.

## Les tables DMG (`stat_builder.py`)

Chaque CR (de 0 à 30, en fractions : 1/8, 1/4, 1/2) définit :

| Élément | Dérivation |
|---|---|
| **Bonus de maîtrise** | table (2 à 9 selon CR) |
| **CA** | CA cible du CR, ajustée du mod. DEX et d'un bonus d'armure |
| **PV + dés de vie** | fourchette du CR × dé selon la taille (d4 minuscule → d20 gigantesque) + mod. CON |
| **Caractéristiques** | la stat principale découle du bonus d'attaque attendu ; les autres suivent l'archétype |
| **Actions d'attaque** | bonus au toucher + dégâts dans la fourchette du CR, 1-3 attaques |
| **Action spéciale** | dès CR 2 : jet de sauvegarde au DD du CR |

## Garde-fous

- **CR imprévu** (0.3, 3.7, 45 depuis un JSON édité à la main) : borné à l'entrée de table la plus proche, jamais de crash
- **CON très basse** : le modificateur des dés de vie est borné pour que les dés affichés reproduisent toujours les PV
- **Cohérence vérifiée** : les dés correspondent aux PV à ±1 dé près sur 300 combinaisons testées

## Ce que l'IA complète

Les actions générées par les tables fournissent des descriptions standards. Le modèle IA peut ensuite **régénérer des actions plus originales** (noms, effets) — un fallback vérifie alors que chaque description contient bien bonus au toucher, dégâts ou DD, et complète avec les valeurs du CR sinon.
