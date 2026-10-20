# Utilisation

## Flux de création d'un monstre

### 1. Configurer le groupe (tab Statistiques)

En haut de l'onglet, la ligne **Groupe** :
- **Joueurs** : nombre (1-10, défaut 4)
- **Niveau moyen** : 1-20 (défaut 2)
- **Difficulté** : Facile / Moyen / Difficile / Mortel (défaut Moyen)

Le label coloré en dessous affiche en temps réel le **CR résultant** : `● CR 1 (200 PX / budget 400 PX)`. Toutes les stats générées découlent de ce CR — modifie le groupe et le label suit instantanément.

### 2. Saisir le concept (tab Description)

Renseigne ce que tu connais : nom, race, description, langues (pills). **Tout est optionnel** — mais plus tu donnes de contexte (surtout race et description), plus les stats générées seront crédibles (voir [Inférence de traits](Inference-traits.md)).

### 3. « Générer les champs manquants »

Le bouton principal, qui chaîne automatiquement :

1. **Correction orthographique** de tous les champs remplis (nom, race, description, scénario)
2. **Génération IA** des champs vides (nom/race/description — avec dialogue de choix)
3. **Équilibrage complet des stats** pour le CR courant (CA, PV, dés de vie, vitesse, caractéristiques, compétences, résistances, immunités, actions DMG)
4. **Actions IA** régénérées selon le contexte complet

### 4. Ajuster à la main

Chaque valeur reste éditable. Les actions sont des cartes individuelles (nom + description avec toutes les stats de combat écrites dedans, croix pour supprimer).

### 5. Scénario de combat

Bouton **« Générer scénario »** à côté du champ Scénario : produit une rencontre structurée (**Contexte / Déroulement / Tactique du monstre / Récompense**) basée sur les stats actuelles et le groupe.

### 6. Exporter et sauvegarder

- **Exporter ▾** → *Exporter en PDF* ou *Exporter en PNG* (style stat block officiel)
- **Bibliothèque > Gérer les monstres sauvegardés** : mini gestionnaire de sauvegardes (voir [Bibliothèque](Bibliothèque.md))

## Raccourcis utiles

- **Double-clic** sur une sauvegarde de la bibliothèque = chargement direct
- La barre de statut (en bas) indique les champs générés après un équilibrage
- L'étiquette en haut de la fenêtre montre le mode IA actif et son état
