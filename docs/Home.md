# MonsterGen — Wiki

Bienvenue sur le wiki de **MonsterGen**, le générateur de fiches de PNJ/monstres pour Donjons & Dragons 5e.

## Sommaire

1. [Installation](Installation.md) — prérequis, installation, premier lancement
2. [Utilisation](Utilisation.md) — le flux de création d'un monstre, pas à pas
3. [Architecture](Architecture.md) — organisation du code et modules
4. [Génération des stats](Generation-stats.md) — CR, tables du DMG, équilibrage
5. [Inférence de traits](Inference-traits.md) — comment la race/description influence les stats
6. [Backends IA](Backends-IA.md) — modèle local vs API distante
7. [Configuration](Configuration.md) — tous les réglages disponibles
8. [Bibliothèque](Bibliothèque.md) — sauvegardes, chargement, suppression
9. [Exports](Exports.md) — PNG style officiel, PDF
10. [Rencontres](Rencontres.md) — rencontres multi-monstres, budget de PX, quantités automatiques

## En bref

- **Stats équilibrées** : basées sur les tables officielles du Guide du Maître, dérivées du niveau du groupe et de la difficulté choisie
- **Deux modes IA** : modèle local GGUF hors ligne (2-4,4 Go) ou API distante (Mistral/OpenAI)
- **Scénarios de combat** : génération de rencontres avec la tactique du monstre
- **Fiche officielle** : export PNG au style du stat block DnD 5e, ou PDF
- **Tout est éditable** : chaque valeur générée reste modifiable à la main
