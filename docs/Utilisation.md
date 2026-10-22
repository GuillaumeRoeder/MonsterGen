# Utilisation

## Flux de création d'un monstre

### 1. Configurer le groupe (tab Description)

En haut de l'onglet **Description**, la ligne **Groupe** :
- **Joueurs** : nombre (1-10, défaut 4)
- **Niveau moyen** : 1-20 (défaut 2)
- **Difficulté** : Facile / Moyen / Difficile / Mortel (défaut Moyen)

Le label coloré en dessous affiche en temps réel le **CR résultant** : `● CR 2 (450 PX / budget 400 PX)` — le CR arrondi au plus proche du budget de rencontre. Toutes les stats générées découlent de ce CR.

### 2. Saisir le concept (tab Description)

Renseigne ce que tu connais : nom, race (liste déroulante DnD 5e via ▾ ou saisie libre), langues (pills), description. **Tout est optionnel** — mais plus tu donnes de contexte (surtout race et description), plus les stats générées seront crédibles (voir [Inférence de traits](Inference-traits.md)).

Deux sections repliables en bas de l'onglet :
- **Équipement / Inventaire (optionnel)** : cartes d'objets (nom + effets). Influence la CA et les actions. Figure sur la fiche exportée dès qu'il contient quelque chose.
- **Scénario de rencontre (optionnel)** : description libre ou génération IA.

### 3. « Compléter les champs »

Le bouton principal, qui enchaîne automatiquement :

1. **Correction orthographique** des champs remplis (description, scénario)
2. **Race** : détectée dans le texte, sinon tirée au hasard dans la liste DnD 5e (sans IA)
3. **Nom / description IA** des champs vides (avec dialogue de choix)
4. **Équilibrage complet des stats** pour le CR courant (CA, PV, dés de vie, vitesse, caractéristiques, compétences, résistances, immunités — tout est régénéré)
5. **Actions IA** régénérées selon le contexte complet
6. **Langues** suggérées en dernier, selon la race et l'INT finales

### 4. Ajuster à la main

Chaque valeur reste éditable. Les actions et les objets d'inventaire sont des cartes individuelles (nom + description, croix pour supprimer).

### 5. Scénario de combat

Bouton **« Générer scénario »** dans la section Scénario : produit une rencontre structurée (**Contexte / Tactique du monstre / Récompense**) basée sur les stats actuelles et le groupe.

### 6. Exporter et sauvegarder

- Menu **Export** → *Exporter en PDF*, *Exporter en PNG* (style stat block officiel), ou *Exporter la bibliothèque...* (monstres choisis vers un fichier JSON)
- **Bibliothèque** → *Sauvegarder le monstre courant*, *Gérer les monstres sauvegardés* (charger/supprimer), ou *Importer une bibliothèque...* (fichier groupé ou monstre individuel)

## Raccourcis utiles

- **Double-clic** sur une sauvegarde de la bibliothèque = chargement direct
- L'étiquette en haut de la fenêtre montre le mode IA actif et son état
